"""
TriageAI — Model Monitoring Routes
===================================
Admin-only endpoints that surface production model health:

  GET  /drift          — PSI-based feature drift of recent traffic vs. the
                         training baseline (drift_baseline.json).
  GET  /performance    — live agreement rate between AI and clinician
                         decisions (a proxy for deployed model quality).

These give operators an early-warning signal that the model needs retraining,
addressing the "flying blind in production" gap.
"""
import os
import logging

from flask import Blueprint, jsonify, request

from extensions import db
from models import Patient, Vitals, TriageAssessment
from security import require_roles, log_phi_access
from ml.monitoring import load_baseline, detect_drift
from ml.feature_contract import FEATURE_NAMES
from ml.clinical_standards import get_complaint_index, get_sex_index

logger = logging.getLogger('triageai')
monitoring_bp = Blueprint('monitoring', __name__)

_ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml', 'artifacts')


def _recent_feature_dataframe(limit=500):
    """Reconstruct a feature DataFrame from the most recent assessments."""
    import pandas as pd

    rows = db.session.query(Patient, Vitals).join(
        Vitals, Patient.patient_id == Vitals.patient_id
    ).order_by(Patient.created_at.desc()).limit(limit).all()

    records = []
    for patient, vitals in rows:
        records.append({
            'heart_rate': vitals.heart_rate,
            'sbp': vitals.sbp,
            'dbp': vitals.dbp,
            'respiratory_rate': vitals.respiratory_rate,
            'spo2': vitals.spo2,
            'temperature': vitals.temperature,
            'gcs': vitals.gcs,
            'age': patient.age,
            'pain_score': patient.pain_score,
            'chief_complaint_code': get_complaint_index(patient.chief_complaint),
            'sex_code': get_sex_index(patient.sex),
            'med_anticoagulant': 1 if (patient.medication_flags or {}).get('anticoagulant') else 0,
            'med_diabetic': 1 if (patient.medication_flags or {}).get('diabetic') else 0,
        })
    return pd.DataFrame(records, columns=FEATURE_NAMES)


@monitoring_bp.route('/drift', methods=['GET'])
@require_roles('admin')
def feature_drift():
    """Compute PSI drift of recent traffic against the training baseline."""
    baseline = load_baseline(_ARTIFACTS_DIR)
    if baseline is None:
        return jsonify({
            'error': 'No drift baseline found. Retrain the model to generate '
                     'drift_baseline.json.'
        }), 404

    limit = min(int(request.args.get('limit', 500)), 5000)
    current_df = _recent_feature_dataframe(limit=limit)
    if len(current_df) == 0:
        return jsonify({'message': 'No production data available yet.', 'features': {}}), 200

    result = detect_drift(baseline, current_df)
    log_phi_access('monitoring_drift', f'Drift check on {result["n_current"]} records '
                                        f'(overall={result["overall_drift"]})')
    return jsonify(result), 200


@monitoring_bp.route('/performance', methods=['GET'])
@require_roles('admin')
def live_performance():
    """AI/clinician agreement rate — a proxy for deployed model quality."""
    resolved = TriageAssessment.query.filter(
        TriageAssessment.clinician_priority.isnot(None)
    ).count()
    agreements = TriageAssessment.query.filter(
        TriageAssessment.clinician_priority.isnot(None),
        TriageAssessment.clinician_priority == TriageAssessment.ai_priority,
    ).count()
    overrides = TriageAssessment.query.filter(
        TriageAssessment.is_override.is_(True)
    ).count()

    agreement_rate = round(agreements / resolved, 4) if resolved else None
    return jsonify({
        'resolved_assessments': resolved,
        'agreements': agreements,
        'overrides': overrides,
        'agreement_rate': agreement_rate,
        'interpretation': (
            'healthy' if (agreement_rate is None or agreement_rate >= 0.7)
            else 'review_recommended'
        ),
    }), 200
