"""
TriageAI Prediction Routes
============================
Uses the feature contract to build the inference vector — guaranteeing
the same feature order, count, and categorical encoding as training.
Validates vital signs against LOINC-referenced clinical ranges.
Override reasons must use coded vocabulary (no free-text).
"""
from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, limiter
from models import Patient, Vitals, TriageAssessment, AuditLog, User
from ml.feature_contract import (
    build_feature_vector, FEATURE_NAMES, EXPECTED_FEATURE_COUNT,
    validate_contract_against_model, get_contract_hash
)
from ml.clinical_standards import (
    validate_vital_sign, CHIEF_COMPLAINT_REGISTRY,
    OVERRIDE_REASON_CODES, ESI_LEVELS, normalize_complaint_text
)
from ml.data_quality import validate_record
from security import require_roles, log_phi_access
import cache
import joblib
import numpy as np
import shap
import os
import logging

logger = logging.getLogger('triageai')
predict_bp = Blueprint('predict', __name__)

# ── MODEL LOADING ─────────────────────────────────────────────────
_model_state = {'loaded': False, 'pipeline': None, 'label_encoder': None, 'explainer': None}

def _load_model():
    """Load model artifacts from ml/artifacts directory."""
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml', 'artifacts')
    pipeline_path = os.path.join(artifacts_dir, 'triage_pipeline.joblib')
    encoder_path = os.path.join(artifacts_dir, 'label_encoder.joblib')
    contract_path = os.path.join(artifacts_dir, 'feature_contract.json')

    if not os.path.exists(pipeline_path):
        logger.warning("Model artifacts not found. Train the model first.")
        return

    try:
        # Validate contract before loading
        if os.path.exists(contract_path):
            validate_contract_against_model(contract_path)

        _model_state['pipeline'] = joblib.load(pipeline_path)
        _model_state['label_encoder'] = joblib.load(encoder_path)
        _model_state['explainer'] = shap.TreeExplainer(
            _model_state['pipeline'].named_steps['model']
        )
        _model_state['loaded'] = True
        logger.info(f"Model loaded (contract hash: {get_contract_hash()})")
    except RuntimeError as e:
        logger.error(f"Model loading blocked: {e}")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")

_load_model()


@predict_bp.route('/predict', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_PREDICT', '60 per minute'))
@jwt_required()
def predict_triage():
    """Generate triage prediction using ML model with contract-enforced feature vector."""
    try:
        if not _model_state['loaded']:
            return jsonify({'error': g.translations['messages']['model_not_loaded']}), 503

        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user or user.role != 'clinician':
            return jsonify({'error': g.translations['messages']['unauthorized']}), 403

        data = request.get_json()
        if not data or 'patient_data' not in data or 'vitals' not in data:
            return jsonify({'error': 'Missing required fields: patient_data, vitals'}), 400

        patient_data = data['patient_data']
        vitals_data = data['vitals']

        # Validate patient fields
        for field in ['age', 'sex', 'chief_complaint', 'pain_score']:
            if field not in patient_data:
                return jsonify({'error': f'Missing patient field: {field}'}), 400

        # Validate chief complaint is a registered code
        if patient_data['chief_complaint'] not in CHIEF_COMPLAINT_REGISTRY:
            return jsonify({
                'error': f'Invalid chief_complaint code: {patient_data["chief_complaint"]}',
                'valid_codes': list(CHIEF_COMPLAINT_REGISTRY.keys())
            }), 400

        # Validate vitals against LOINC clinical ranges
        for field in ['heart_rate', 'sbp', 'dbp', 'respiratory_rate', 'spo2', 'temperature', 'gcs']:
            if field not in vitals_data:
                return jsonify({'error': f'Missing vital sign: {field}'}), 400
            try:
                value = float(vitals_data[field])
            except (ValueError, TypeError):
                return jsonify({'error': f'Invalid value for {field}: must be numeric'}), 400
            is_valid, error_msg = validate_vital_sign(field, value)
            if not is_valid:
                return jsonify({'error': error_msg}), 400

        # Build feature vector using the contract
        try:
            feature_vector = build_feature_vector(patient_data, vitals_data)
        except ValueError as e:
            return jsonify({'error': f'Feature vector error: {str(e)}'}), 400

        # Create database records
        patient = Patient(
            age=patient_data['age'],
            sex=patient_data['sex'],
            chief_complaint=patient_data['chief_complaint'],
            pain_score=patient_data['pain_score'],
            medication_flags=patient_data.get('medication_flags', {})
        )
        db.session.add(patient)
        db.session.flush()

        vitals = Vitals(
            patient_id=patient.patient_id,
            heart_rate=vitals_data['heart_rate'],
            sbp=vitals_data['sbp'],
            dbp=vitals_data['dbp'],
            respiratory_rate=vitals_data['respiratory_rate'],
            spo2=vitals_data['spo2'],
            temperature=vitals_data['temperature'],
            gcs=vitals_data['gcs']
        )
        db.session.add(vitals)

        # ML Inference
        pipeline = _model_state['pipeline']
        label_encoder = _model_state['label_encoder']
        explainer = _model_state['explainer']

        input_array = np.array([feature_vector])
        prediction_encoded = pipeline.predict(input_array)[0]
        probabilities = pipeline.predict_proba(input_array)[0]
        confidence = float(np.max(probabilities))
        prediction = int(label_encoder.inverse_transform([prediction_encoded])[0])

        # SHAP explanation — for multiclass, shap_values is a list per class
        scaler = pipeline.named_steps['scaler']
        shap_values = explainer.shap_values(scaler.transform(input_array))
        # Pick SHAP values for the predicted class
        if isinstance(shap_values, list):
            class_shap = shap_values[int(prediction_encoded)][0]
        else:
            class_shap = shap_values[0]
        feature_importance = []
        for i, name in enumerate(FEATURE_NAMES):
            feature_importance.append({
                'feature': name,
                'impact': round(float(class_shap[i]), 4),
                'value': round(float(input_array[0][i]), 2)
            })
        feature_importance.sort(key=lambda x: abs(x['impact']), reverse=True)
        top_features = feature_importance[:3]

        # Save assessment
        esi_info = ESI_LEVELS.get(prediction, ESI_LEVELS[3])
        assessment = TriageAssessment(
            patient_id=patient.patient_id,
            clinician_id=current_user_id,
            ai_priority=prediction,
            ai_confidence=confidence,
            shap_explanation=top_features
        )
        db.session.add(assessment)
        db.session.flush()  # Generate assessment_id before audit log

        # Immutable audit log
        audit_log = AuditLog(
            assessment_id=assessment.assessment_id,
            clinician_id=current_user_id,
            event_type='ai_prediction',
            event_detail=f'AI predicted ESI Level {prediction} (confidence: {confidence:.2%})',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            'assessment_id': assessment.assessment_id,
            'patient_id': patient.patient_id,
            'ai_prediction': {
                'esi_level': prediction,
                'confidence': round(confidence, 4),
                'color': esi_info['color'],
                'label': esi_info['label']
            },
            'shap_explanation': top_features,
            'contract_hash': get_contract_hash(),
            'timestamp': assessment.assessed_at.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Prediction failed: {e}")
        return jsonify({'error': 'Prediction failed', 'details': str(e)}), 500


MAX_BATCH_SIZE = 100


@predict_bp.route('/predict/batch', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_PREDICT', '60 per minute'))
@jwt_required()
def predict_batch():
    """
    Batch triage prediction for bulk intake (e.g. ambulance offload lists).

    Body: {"records": [{"patient_data": {...}, "vitals": {...}}, ...]}
    Each record is validated through the data-quality gate; invalid records
    are reported per-index without aborting the whole batch. Predictions are
    returned for ranking but are NOT persisted (preview semantics) unless the
    caller passes ?persist=true.
    """
    try:
        if not _model_state['loaded']:
            return jsonify({'error': g.translations['messages']['model_not_loaded']}), 503

        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user or user.role != 'clinician':
            return jsonify({'error': g.translations['messages']['unauthorized']}), 403

        data = request.get_json()
        if not data or 'records' not in data or not isinstance(data['records'], list):
            return jsonify({'error': 'Body must contain a "records" list'}), 400

        records = data['records']
        if len(records) == 0:
            return jsonify({'error': 'records list is empty'}), 400
        if len(records) > MAX_BATCH_SIZE:
            return jsonify({'error': f'Batch too large: max {MAX_BATCH_SIZE} records'}), 413

        persist = request.args.get('persist', 'false').lower() == 'true'

        pipeline = _model_state['pipeline']
        label_encoder = _model_state['label_encoder']

        results = []
        valid_vectors = []
        valid_meta = []  # (index, patient_data, vitals_data)

        for idx, record in enumerate(records):
            patient_data = (record or {}).get('patient_data', {}) or {}
            vitals_data = (record or {}).get('vitals', {}) or {}

            # Normalise free-text chief complaint to a registered code.
            if 'chief_complaint' in patient_data:
                code, _via = normalize_complaint_text(patient_data['chief_complaint'])
                patient_data['chief_complaint'] = code

            quality = validate_record(patient_data, vitals_data)
            if not quality['valid']:
                results.append({'index': idx, 'valid': False, 'errors': quality['errors']})
                continue

            try:
                vector = build_feature_vector(patient_data, vitals_data)
            except ValueError as e:
                results.append({'index': idx, 'valid': False, 'errors': [str(e)]})
                continue

            valid_vectors.append(vector)
            valid_meta.append((idx, patient_data, vitals_data))
            results.append(None)  # placeholder filled after inference

        # Vectorised inference over all valid records at once.
        if valid_vectors:
            input_matrix = np.array(valid_vectors)
            encoded = pipeline.predict(input_matrix)
            probs = pipeline.predict_proba(input_matrix)

            for (idx, patient_data, vitals_data), enc, prob in zip(valid_meta, encoded, probs):
                prediction = int(label_encoder.inverse_transform([enc])[0])
                confidence = float(np.max(prob))
                esi_info = ESI_LEVELS.get(prediction, ESI_LEVELS[3])

                entry = {
                    'index': idx,
                    'valid': True,
                    'ai_prediction': {
                        'esi_level': prediction,
                        'confidence': round(confidence, 4),
                        'color': esi_info['color'],
                        'label': esi_info['label'],
                    },
                }

                if persist:
                    patient = Patient(
                        age=patient_data['age'], sex=patient_data['sex'],
                        chief_complaint=patient_data['chief_complaint'],
                        pain_score=patient_data['pain_score'],
                        medication_flags=patient_data.get('medication_flags', {}),
                    )
                    db.session.add(patient)
                    db.session.flush()
                    db.session.add(Vitals(patient_id=patient.patient_id, **{
                        k: vitals_data[k] for k in
                        ['heart_rate', 'sbp', 'dbp', 'respiratory_rate', 'spo2', 'temperature', 'gcs']
                    }))
                    assessment = TriageAssessment(
                        patient_id=patient.patient_id, clinician_id=current_user_id,
                        ai_priority=prediction, ai_confidence=confidence,
                    )
                    db.session.add(assessment)
                    db.session.flush()
                    entry['assessment_id'] = assessment.assessment_id
                    entry['patient_id'] = patient.patient_id

                results[idx] = entry

        if persist:
            log_phi_access('ai_prediction_batch',
                           f'Batch predicted {len(valid_meta)} records')
            db.session.commit()

        # Build a priority-sorted view (ESI 1 = highest priority first).
        ranked = sorted(
            [r for r in results if r and r.get('valid')],
            key=lambda r: r['ai_prediction']['esi_level']
        )

        return jsonify({
            'total': len(records),
            'valid': len(valid_meta),
            'invalid': len(records) - len(valid_meta),
            'persisted': persist,
            'results': results,
            'ranked_assessment_ids': [r.get('assessment_id') for r in ranked] if persist else None,
            'contract_hash': get_contract_hash(),
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Batch prediction failed: {e}")
        return jsonify({'error': 'Batch prediction failed', 'details': str(e)}), 500


@predict_bp.route('/confirm/<assessment_id>', methods=['POST'])
@jwt_required()
def confirm_assessment(assessment_id):
    """Confirm AI prediction — logged to immutable audit trail."""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user or user.role != 'clinician':
            return jsonify({'error': 'Unauthorized'}), 403

        assessment = db.session.get(TriageAssessment, assessment_id)
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        if assessment.clinician_priority is not None:
            return jsonify({'error': 'Assessment already resolved'}), 409

        assessment.clinician_priority = assessment.ai_priority
        assessment.is_override = False

        audit_log = AuditLog(
            assessment_id=assessment.assessment_id,
            clinician_id=current_user_id,
            event_type='clinician_confirm',
            event_detail=f'Confirmed ESI Level {assessment.ai_priority}',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            'message': g.translations['messages']['confirm_success'],
            'assessment_id': assessment.assessment_id,
            'confirmed_level': assessment.clinician_priority
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Confirmation failed', 'details': str(e)}), 500


@predict_bp.route('/override/<assessment_id>', methods=['POST'])
@jwt_required()
def override_assessment(assessment_id):
    """Override AI prediction — requires coded reason from OVERRIDE_REASON_CODES."""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user or user.role != 'clinician':
            return jsonify({'error': 'Unauthorized'}), 403

        assessment = db.session.get(TriageAssessment, assessment_id)
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        if assessment.clinician_priority is not None:
            return jsonify({'error': 'Assessment already resolved'}), 409

        data = request.get_json()
        if 'new_level' not in data or 'reason_code' not in data:
            return jsonify({'error': 'new_level and reason_code are required'}), 400

        new_level = data['new_level']
        reason_code = data['reason_code']

        if new_level < 1 or new_level > 5:
            return jsonify({'error': 'ESI level must be between 1 and 5'}), 400

        if reason_code not in OVERRIDE_REASON_CODES:
            return jsonify({
                'error': f'Invalid reason_code: {reason_code}',
                'valid_codes': OVERRIDE_REASON_CODES
            }), 400

        assessment.clinician_priority = new_level
        assessment.is_override = True
        assessment.override_reason = reason_code

        reason_text = OVERRIDE_REASON_CODES[reason_code]
        audit_log = AuditLog(
            assessment_id=assessment.assessment_id,
            clinician_id=current_user_id,
            event_type='clinician_override',
            event_detail=(
                f'Override: AI Level {assessment.ai_priority} -> '
                f'Clinician Level {new_level}. '
                f'Reason [{reason_code}]: {reason_text}'
            ),
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            'message': g.translations['messages']['override_success'],
            'assessment_id': assessment.assessment_id,
            'ai_level': assessment.ai_priority,
            'clinician_level': new_level,
            'reason_code': reason_code,
            'reason_text': reason_text
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Override failed', 'details': str(e)}), 500


@predict_bp.route('/queue', methods=['GET'])
@jwt_required()
def get_patient_queue():
    """Get active patient queue sorted by AI priority."""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 403

        assessments = db.session.query(TriageAssessment, Patient, Vitals).join(
            Patient, TriageAssessment.patient_id == Patient.patient_id
        ).join(
            Vitals, Patient.patient_id == Vitals.patient_id
        ).filter(
            TriageAssessment.clinician_priority.is_(None)
        ).order_by(
            TriageAssessment.ai_priority.asc(),
            TriageAssessment.assessed_at.desc()
        ).limit(50).all()

        queue = []
        for assessment, patient, vitals in assessments:
            esi = ESI_LEVELS.get(assessment.ai_priority, ESI_LEVELS[3])
            queue.append({
                'assessment_id': assessment.assessment_id,
                'patient_id': patient.patient_id,
                'age': patient.age,
                'sex': patient.sex,
                'chief_complaint': patient.chief_complaint,
                'pain_score': patient.pain_score,
                'ai_priority': assessment.ai_priority,
                'confidence': round(assessment.ai_confidence, 4),
                'color': esi['color'],
                'label': esi['label'],
                'timestamp': assessment.assessed_at.isoformat(),
                'vitals': {
                    'heart_rate': vitals.heart_rate,
                    'sbp': vitals.sbp,
                    'dbp': vitals.dbp,
                    'respiratory_rate': vitals.respiratory_rate,
                    'spo2': vitals.spo2,
                    'temperature': vitals.temperature,
                    'gcs': vitals.gcs
                }
            })

        return jsonify({'queue': queue, 'count': len(queue)}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to get queue', 'details': str(e)}), 500


@predict_bp.route('/clinical-standards', methods=['GET'])
def get_clinical_standards():
    """Return clinical standards for frontend form population (cached)."""
    def _build():
        return {
            'chief_complaints': {
                code: {
                    'display': entry['display_en'],
                    'icd10': entry['icd10'],
                    'snomed': entry['snomed']
                }
                for code, entry in CHIEF_COMPLAINT_REGISTRY.items()
            },
            'override_reasons': OVERRIDE_REASON_CODES,
            'esi_levels': {
                str(k): v for k, v in ESI_LEVELS.items()
            }
        }

    # Reference data is effectively static — cache for 1 hour.
    payload = cache.get_or_set('clinical_standards', _build, ttl=3600)
    return jsonify(payload), 200


@predict_bp.route('/patient/<patient_id>/erase', methods=['DELETE'])
@require_roles('admin')
def erase_patient(patient_id):
    """
    GDPR Right to Erasure (Art. 17) — pseudonymise a patient's PII while
    preserving the immutable audit trail and aggregate clinical record.

    We do NOT physically delete rows (that would break audit integrity and
    ON DELETE RESTRICT foreign keys). Instead we irreversibly scrub direct
    identifiers: the encrypted chief complaint and medication flags are
    replaced with tombstone markers. The erasure itself is audited.
    """
    try:
        patient = db.session.get(Patient, patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        if patient.chief_complaint == '[ERASED]':
            return jsonify({'message': 'Patient already erased', 'patient_id': patient_id}), 200

        # Scrub direct identifiers (chief_complaint is encrypted PII).
        patient.chief_complaint = '[ERASED]'
        patient.medication_flags = {}

        log_phi_access('gdpr_erasure',
                       f'PII erased for patient {patient_id} (GDPR Art. 17)')
        db.session.commit()

        return jsonify({
            'message': 'Patient PII erased; audit trail preserved',
            'patient_id': patient_id,
            'erased_fields': ['chief_complaint', 'medication_flags'],
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erasure failed: {e}")
        return jsonify({'error': 'Erasure failed', 'details': str(e)}), 500


@predict_bp.route('/assessment/<assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment_detail(assessment_id):
    """Get full assessment detail including patient data, vitals, and SHAP."""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 403

        assessment = db.session.get(TriageAssessment, assessment_id)
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404

        patient = db.session.get(Patient, assessment.patient_id)
        vitals = Vitals.query.filter_by(patient_id=patient.patient_id).first()
        esi_info = ESI_LEVELS.get(assessment.ai_priority, ESI_LEVELS[3])

        return jsonify({
            'assessment_id': assessment.assessment_id,
            'patient': {
                'patient_id': patient.patient_id,
                'age': patient.age,
                'sex': patient.sex,
                'chief_complaint': patient.chief_complaint,
                'pain_score': patient.pain_score,
                'medication_flags': patient.medication_flags,
                'created_at': patient.created_at.isoformat()
            },
            'vitals': {
                'heart_rate': vitals.heart_rate,
                'sbp': vitals.sbp,
                'dbp': vitals.dbp,
                'respiratory_rate': vitals.respiratory_rate,
                'spo2': vitals.spo2,
                'temperature': vitals.temperature,
                'gcs': vitals.gcs,
                'recorded_at': vitals.recorded_at.isoformat()
            } if vitals else None,
            'ai_prediction': {
                'esi_level': assessment.ai_priority,
                'confidence': round(assessment.ai_confidence, 4),
                'color': esi_info['color'],
                'label': esi_info['label']
            },
            'clinician_decision': {
                'priority': assessment.clinician_priority,
                'is_override': assessment.is_override,
                'override_reason': assessment.override_reason
            },
            'shap_explanation': assessment.shap_explanation,
            'assessed_at': assessment.assessed_at.isoformat(),
            'status': 'resolved' if assessment.clinician_priority else 'pending'
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to get assessment', 'details': str(e)}), 500


@predict_bp.route('/patient/<patient_id>/history', methods=['GET'])
@jwt_required()
def get_patient_history(patient_id):
    """Get all past triage assessments for one patient."""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 403

        patient = db.session.get(Patient, patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        assessments = TriageAssessment.query.filter_by(
            patient_id=patient_id
        ).order_by(TriageAssessment.assessed_at.desc()).all()

        vitals = Vitals.query.filter_by(patient_id=patient_id).first()

        return jsonify({
            'patient': {
                'patient_id': patient.patient_id,
                'age': patient.age,
                'sex': patient.sex,
                'chief_complaint': patient.chief_complaint,
                'pain_score': patient.pain_score
            },
            'vitals': {
                'heart_rate': vitals.heart_rate, 'sbp': vitals.sbp, 'dbp': vitals.dbp,
                'respiratory_rate': vitals.respiratory_rate, 'spo2': vitals.spo2,
                'temperature': vitals.temperature, 'gcs': vitals.gcs
            } if vitals else None,
            'assessments': [{
                'assessment_id': a.assessment_id,
                'ai_priority': a.ai_priority,
                'ai_confidence': round(a.ai_confidence, 4),
                'clinician_priority': a.clinician_priority,
                'is_override': a.is_override,
                'override_reason': a.override_reason,
                'shap_explanation': a.shap_explanation,
                'assessed_at': a.assessed_at.isoformat(),
                'status': 'resolved' if a.clinician_priority else 'pending'
            } for a in assessments],
            'total_assessments': len(assessments)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to get patient history', 'details': str(e)}), 500


@predict_bp.route('/queue/stats', methods=['GET'])
@jwt_required()
def get_queue_stats():
    """Real-time queue statistics for dashboard."""
    try:
        pending = TriageAssessment.query.filter(
            TriageAssessment.clinician_priority.is_(None)
        ).count()

        critical = TriageAssessment.query.filter(
            TriageAssessment.clinician_priority.is_(None),
            TriageAssessment.ai_priority <= 2
        ).count()

        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        today_total = TriageAssessment.query.filter(
            TriageAssessment.assessed_at >= today_start
        ).count()

        today_confirmed = TriageAssessment.query.filter(
            TriageAssessment.assessed_at >= today_start,
            TriageAssessment.clinician_priority.isnot(None)
        ).count()

        return jsonify({
            'pending_count': pending,
            'critical_count': critical,
            'today_total': today_total,
            'today_confirmed': today_confirmed
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to get queue stats', 'details': str(e)}), 500


@predict_bp.route('/shift-handover', methods=['GET'])
@jwt_required()
def get_shift_handover():
    """Get today's assessment summary for end-of-shift handover."""
    try:
        from datetime import datetime, timedelta
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 403

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        assessments = TriageAssessment.query.filter(
            TriageAssessment.clinician_id == current_user_id,
            TriageAssessment.assessed_at >= today_start
        ).order_by(TriageAssessment.assessed_at.desc()).all()

        summary = {
            'total': len(assessments),
            'by_priority': {},
            'confirmed': 0,
            'overridden': 0,
            'pending': 0
        }
        for a in assessments:
            summary['by_priority'][a.ai_priority] = summary['by_priority'].get(a.ai_priority, 0) + 1
            if a.clinician_priority is not None:
                if a.is_override:
                    summary['overridden'] += 1
                else:
                    summary['confirmed'] += 1
            else:
                summary['pending'] += 1

        return jsonify({
            'date': today_start.isoformat(),
            'clinician': user.username,
            'summary': summary,
            'assessments': [
                {
                    'assessment_id': a.assessment_id,
                    'ai_priority': a.ai_priority,
                    'clinician_priority': a.clinician_priority,
                    'is_override': a.is_override,
                    'status': 'resolved' if a.clinician_priority else 'pending',
                    'assessed_at': a.assessed_at.isoformat()
                } for a in assessments
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get shift handover', 'details': str(e)}), 500
