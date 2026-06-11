"""
TriageAI — FHIR R4 Server
==========================
Serves FHIR R4 resources for interoperability with EHR systems.

Endpoints (all under /api/fhir):
  - GET /metadata                       CapabilityStatement (public)
  - GET /Patient/<patient_id>           Patient read
  - GET /Patient/<patient_id>/$everything  Bundle of patient + reports
  - GET /DiagnosticReport/<assessment_id>  DiagnosticReport read
  - GET /Observation?patient=<id>       Observation search (vital signs)

Security & compliance:
  - All resource endpoints require a clinician/admin JWT (RBAC).
  - Every PHI read is written to the immutable audit trail (HIPAA 164.312(b)).
  - Responses use the application/fhir+json content type.

References:
  - HL7 FHIR R4 Patient:          http://hl7.org/fhir/R4/patient.html
  - HL7 FHIR R4 DiagnosticReport: http://hl7.org/fhir/R4/diagnosticreport.html
  - HL7 FHIR R4 Observation:      http://hl7.org/fhir/R4/observation.html
  - Vital-sign LOINC codes:       http://hl7.org/fhir/R4/observation-vitalsigns.html
"""
import json
from datetime import datetime
from flask import Blueprint, request, Response
from extensions import db
from models import Patient, TriageAssessment
from security import require_roles, log_phi_access

fhir_bp = Blueprint('fhir', __name__)

FHIR_BASE_URL = "http://triageai.local/fhir"
FHIR_MIME = "application/fhir+json"
FHIR_VERSION = "4.0.1"

# HL7 Administrative Gender mapping (model stores M/F/O/U)
GENDER_MAP = {"M": "male", "F": "female", "O": "other", "U": "unknown"}

# LOINC vital-sign codes: field -> (code, display, ucum_unit, human_unit)
VITAL_LOINC = {
    "heart_rate":       ("8867-4", "Heart rate", "/min", "beats/min"),
    "sbp":              ("8480-6", "Systolic blood pressure", "mm[Hg]", "mmHg"),
    "dbp":              ("8462-4", "Diastolic blood pressure", "mm[Hg]", "mmHg"),
    "respiratory_rate": ("9279-1", "Respiratory rate", "/min", "breaths/min"),
    "spo2":             ("2708-6", "Oxygen saturation", "%", "%"),
    "temperature":      ("8310-5", "Body temperature", "Cel", "Cel"),
    "gcs":              ("9269-2", "Glasgow coma score total", "{score}", "score"),
}
PAIN_LOINC = ("72514-3", "Pain severity 0-10 verbal numeric rating", "{score}", "score")


def _fhir_response(resource, status=200):
    """Serialise a FHIR resource with the correct content type."""
    return Response(json.dumps(resource), status=status, mimetype=FHIR_MIME)


def _operation_outcome(code, diagnostics, status):
    """Build a FHIR OperationOutcome error response."""
    return _fhir_response({
        "resourceType": "OperationOutcome",
        "issue": [{"severity": "error", "code": code, "diagnostics": diagnostics}]
    }, status=status)


def _fhir_gender(sex):
    if not sex:
        return "unknown"
    return GENDER_MAP.get(sex.upper()[:1], "unknown")


def _vital_observation(obs_id, patient_id, code_tuple, value):
    """Build a single vital-sign Observation resource."""
    code, display, ucum, _human = code_tuple
    return {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }]
        }],
        "code": {
            "coding": [{"system": "http://loinc.org", "code": code, "display": display}],
            "text": display
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "valueQuantity": {
            "value": value,
            "unit": ucum,
            "system": "http://unitsofmeasure.org",
            "code": ucum
        }
    }


def _vitals_to_observations(patient):
    """Return LOINC-coded vital-sign Observations for the patient's latest vitals."""
    observations = []
    if patient and patient.vitals:
        v = patient.vitals[0]
        for field, code_tuple in VITAL_LOINC.items():
            value = getattr(v, field, None)
            if value is not None:
                obs_id = f"obs-{field}-{v.vital_id}"
                observations.append(_vital_observation(obs_id, patient.patient_id, code_tuple, value))
    # Pain score lives on the Patient record
    if patient and patient.pain_score is not None:
        observations.append(_vital_observation(
            f"obs-pain-{patient.patient_id}", patient.patient_id, PAIN_LOINC, patient.pain_score
        ))
    return observations


def _patient_to_fhir(patient):
    """Convert SQLAlchemy Patient to FHIR R4 Patient resource."""
    return {
        "resourceType": "Patient",
        "id": str(patient.patient_id),
        "meta": {
            "versionId": "1",
            "lastUpdated": patient.created_at.isoformat() if patient.created_at else None
        },
        "text": {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>Patient ID: {patient.patient_id}</p></div>'
        },
        "identifier": [{
            "system": f"{FHIR_BASE_URL}/identifier/patient-id",
            "value": str(patient.patient_id)
        }],
        "gender": _fhir_gender(patient.sex),
        "birthDate": None,  # Not collected in current dataset
        "extension": [{
            "url": f"{FHIR_BASE_URL}/StructureDefinition/age-years",
            "valueInteger": patient.age
        }]
    }


def _assessment_to_diagnostic_report(assessment):
    """Convert TriageAssessment to FHIR R4 DiagnosticReport."""
    patient = db.session.get(Patient, assessment.patient_id)
    # Final ESI = clinician decision if present, else AI prediction
    final_esi = assessment.clinician_priority if assessment.clinician_priority is not None else assessment.ai_priority
    predicted_esi = assessment.ai_priority
    confirmed = assessment.clinician_priority is not None
    overridden = bool(assessment.is_override)

    report = {
        "resourceType": "DiagnosticReport",
        "id": str(assessment.assessment_id),
        "meta": {
            "versionId": "1",
            "lastUpdated": assessment.assessed_at.isoformat() if assessment.assessed_at else None
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": "LAB",
                "display": "Laboratory"
            }],
            "text": "Triage Assessment"
        }],
        "code": {
            "coding": [{
                "system": f"{FHIR_BASE_URL}/codesystem/triage-esi",
                "code": f"ESI-{final_esi}",
                "display": f"Emergency Severity Index Level {final_esi}"
            }],
            "text": f"Triage ESI Level {final_esi}"
        },
        "subject": {
            "reference": f"Patient/{assessment.patient_id}",
            "display": f"Patient/{assessment.patient_id}"
        },
        "issued": assessment.assessed_at.isoformat() if assessment.assessed_at else None,
        "performer": [{
            "reference": f"Practitioner/{assessment.clinician_id}",
            "display": f"Clinician/{assessment.clinician_id}"
        }],
        "conclusion": f"AI-predicted ESI: {predicted_esi}. "
                      f"Final ESI: {final_esi}. "
                      f"Confirmed: {confirmed}. "
                      f"Overridden: {overridden}."
    }

    # Vital signs as proper contained LOINC-coded Observation resources
    observations = _vitals_to_observations(patient)
    result_refs = [{
        "reference": f"Observation/triage-esi-{assessment.assessment_id}",
        "display": f"ESI Category: ESI-{final_esi}"
    }]
    if observations:
        report["contained"] = observations
        result_refs.extend({
            "reference": f"#{obs['id']}",
            "display": obs["code"]["text"]
        } for obs in observations)
    report["result"] = result_refs

    # Retain a human-readable summary for non-FHIR consumers
    if patient and patient.vitals:
        v = patient.vitals[0]
        vitals_text = (
            f"Heart Rate: {v.heart_rate} bpm\n"
            f"Systolic BP: {v.sbp} mmHg\n"
            f"Diastolic BP: {v.dbp} mmHg\n"
            f"Respiratory Rate: {v.respiratory_rate} /min\n"
            f"SpO2: {v.spo2}%\n"
            f"Temperature: {v.temperature}°C\n"
            f"GCS: {v.gcs}\n"
            f"Pain Score: {patient.pain_score}"
        )
        report["presentedForm"] = [{
            "contentType": "text/plain",
            "data": vitals_text
        }]

    return report


@fhir_bp.route('/metadata', methods=['GET'])
def capability_statement():
    """Public FHIR CapabilityStatement describing this server."""
    statement = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.utcnow().isoformat(),
        "publisher": "TriageAI",
        "kind": "instance",
        "software": {"name": "TriageAI FHIR Server", "version": "1.0.0"},
        "fhirVersion": FHIR_VERSION,
        "format": ["application/fhir+json"],
        "rest": [{
            "mode": "server",
            "security": {
                "cors": True,
                "service": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                        "code": "OAuth",
                        "display": "OAuth"
                    }]
                }],
                "description": "Bearer JWT (clinician/admin) required for all resource endpoints."
            },
            "resource": [
                {"type": "Patient", "interaction": [{"code": "read"}],
                 "operation": [{"name": "everything",
                                "definition": "http://hl7.org/fhir/OperationDefinition/Patient-everything"}]},
                {"type": "DiagnosticReport", "interaction": [{"code": "read"}]},
                {"type": "Observation", "interaction": [{"code": "search-type"}],
                 "searchParam": [{"name": "patient", "type": "reference"}]},
            ]
        }]
    }
    return _fhir_response(statement)


@fhir_bp.route('/Patient/<patient_id>', methods=['GET'])
@require_roles('clinician', 'admin')
def get_fhir_patient(patient_id):
    """Return FHIR R4 Patient resource."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return _operation_outcome("not-found", "Patient not found", 404)
    log_phi_access('phi_read', f'FHIR Patient read: {patient_id}')
    return _fhir_response(_patient_to_fhir(patient))


@fhir_bp.route('/Patient/<patient_id>/$everything', methods=['GET'])
@require_roles('clinician', 'admin')
def get_fhir_patient_everything(patient_id):
    """Return a Bundle of the Patient plus all their DiagnosticReports."""
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return _operation_outcome("not-found", "Patient not found", 404)

    entries = [{
        "fullUrl": f"{FHIR_BASE_URL}/Patient/{patient.patient_id}",
        "resource": _patient_to_fhir(patient)
    }]
    for assessment in patient.triage_assessments:
        entries.append({
            "fullUrl": f"{FHIR_BASE_URL}/DiagnosticReport/{assessment.assessment_id}",
            "resource": _assessment_to_diagnostic_report(assessment)
        })

    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }
    log_phi_access('phi_read', f'FHIR Patient/$everything: {patient_id}')
    return _fhir_response(bundle)


@fhir_bp.route('/DiagnosticReport/<assessment_id>', methods=['GET'])
@require_roles('clinician', 'admin')
def get_fhir_diagnostic_report(assessment_id):
    """Return FHIR R4 DiagnosticReport for a triage assessment."""
    assessment = db.session.get(TriageAssessment, assessment_id)
    if not assessment:
        return _operation_outcome("not-found", "DiagnosticReport not found", 404)
    log_phi_access('phi_read', f'FHIR DiagnosticReport read: {assessment_id}',
                   assessment_id=assessment_id)
    return _fhir_response(_assessment_to_diagnostic_report(assessment))


@fhir_bp.route('/Observation', methods=['GET'])
@require_roles('clinician', 'admin')
def search_fhir_observations():
    """Search vital-sign Observations for a patient (?patient=<patient_id>)."""
    patient_id = request.args.get('patient')
    if not patient_id:
        return _operation_outcome("required", "Missing required search parameter: patient", 400)
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return _operation_outcome("not-found", "Patient not found", 404)

    observations = _vitals_to_observations(patient)
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(observations),
        "entry": [{
            "fullUrl": f"{FHIR_BASE_URL}/Observation/{obs['id']}",
            "resource": obs
        } for obs in observations]
    }
    log_phi_access('phi_read', f'FHIR Observation search: patient={patient_id}')
    return _fhir_response(bundle)
