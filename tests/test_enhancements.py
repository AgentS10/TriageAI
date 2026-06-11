"""
TriageAI — Enhancement Tests
=============================
Covers the production-readiness features added on top of the core system:
  - Data quality validation
  - Text token (free-text chief complaint) normalisation
  - Batch prediction endpoint
  - GDPR right-to-erasure
  - Model monitoring (drift + live performance)
  - API versioning (/api/v1 parity with legacy /api)
  - Caching layer
  - Database CHECK constraints
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User, Patient, Vitals, TriageAssessment


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            db.session.add_all([
                User(username='admin', password_hash=generate_password_hash('Admin123!'),
                     role='admin', is_active=True),
                User(username='clinician', password_hash=generate_password_hash('Clinician123!'),
                     role='clinician', is_active=True),
            ])
            db.session.commit()
            yield client
            db.session.remove()
            db.drop_all()


def _token(client, username, password):
    resp = client.post('/api/auth/login', json={'username': username, 'password': password})
    return json.loads(resp.data)['access_token']


def _valid_record():
    return {
        'patient_data': {'age': 55, 'sex': 'M', 'chief_complaint': 'chest_pain', 'pain_score': 7},
        'vitals': {'heart_rate': 95, 'sbp': 130, 'dbp': 85, 'respiratory_rate': 18,
                   'spo2': 96, 'temperature': 37.0, 'gcs': 15},
    }


# ── DATA QUALITY ────────────────────────────────────────────────────
class TestDataQuality:
    def test_valid_record_passes(self):
        from ml.data_quality import validate_record
        rec = _valid_record()
        result = validate_record(rec['patient_data'], rec['vitals'])
        assert result['valid'] is True
        assert result['errors'] == []

    def test_out_of_range_vital_fails(self):
        from ml.data_quality import validate_record
        rec = _valid_record()
        rec['vitals']['spo2'] = 250  # impossible
        result = validate_record(rec['patient_data'], rec['vitals'])
        assert result['valid'] is False
        assert any('spo2' in e for e in result['errors'])

    def test_missing_field_fails(self):
        from ml.data_quality import validate_record
        rec = _valid_record()
        del rec['patient_data']['age']
        result = validate_record(rec['patient_data'], rec['vitals'])
        assert result['valid'] is False

    def test_invalid_categorical_fails(self):
        from ml.data_quality import validate_record
        rec = _valid_record()
        rec['patient_data']['chief_complaint'] = 'not_a_code'
        result = validate_record(rec['patient_data'], rec['vitals'])
        assert result['valid'] is False


# ── TEXT TOKEN NORMALISATION ────────────────────────────────────────
class TestTextNormalisation:
    def test_synonym_maps_to_code(self):
        from ml.clinical_standards import normalize_complaint_text
        code, via = normalize_complaint_text('SOB')
        assert code == 'shortness_of_breath'
        assert via in ('synonym_exact', 'synonym_keyword')

    def test_registered_code_passthrough(self):
        from ml.clinical_standards import normalize_complaint_text
        code, via = normalize_complaint_text('chest_pain')
        assert code == 'chest_pain'
        assert via == 'exact_code'

    def test_unknown_falls_back_to_other(self):
        from ml.clinical_standards import normalize_complaint_text
        code, via = normalize_complaint_text('qqqq wwww')
        assert code == 'other'
        assert via == 'fallback_other'


# ── BATCH PREDICTION ────────────────────────────────────────────────
class TestBatchPrediction:
    def test_batch_requires_auth(self, client):
        resp = client.post('/api/predict/batch', json={'records': [_valid_record()]})
        assert resp.status_code == 401

    def test_batch_predicts_valid_and_reports_invalid(self, client):
        token = _token(client, 'clinician', 'Clinician123!')
        bad = {'patient_data': {'age': 55, 'sex': 'M', 'chief_complaint': 'chest_pain',
                                'pain_score': 7}, 'vitals': {'heart_rate': 999}}
        resp = client.post('/api/predict/batch',
                           headers={'Authorization': f'Bearer {token}'},
                           json={'records': [_valid_record(), bad]})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['total'] == 2
        assert data['valid'] == 1
        assert data['invalid'] == 1

    def test_batch_size_limit(self, client):
        token = _token(client, 'clinician', 'Clinician123!')
        resp = client.post('/api/predict/batch',
                           headers={'Authorization': f'Bearer {token}'},
                           json={'records': [_valid_record()] * 101})
        assert resp.status_code == 413

    def test_batch_normalises_free_text(self, client):
        token = _token(client, 'clinician', 'Clinician123!')
        rec = _valid_record()
        rec['patient_data']['chief_complaint'] = 'chest tightness'  # free text
        resp = client.post('/api/predict/batch',
                           headers={'Authorization': f'Bearer {token}'},
                           json={'records': [rec]})
        assert resp.status_code == 200
        assert json.loads(resp.data)['valid'] == 1


# ── GDPR ERASURE ────────────────────────────────────────────────────
class TestGdprErasure:
    def _make_patient(self, client):
        app = client.application
        with app.app_context():
            p = Patient(age=40, sex='F', chief_complaint='headache', pain_score=3)
            db.session.add(p)
            db.session.commit()
            return p.patient_id

    def test_erase_requires_admin(self, client):
        pid = self._make_patient(client)
        token = _token(client, 'clinician', 'Clinician123!')
        resp = client.delete(f'/api/patient/{pid}/erase',
                             headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 403

    def test_admin_can_erase_pii(self, client):
        pid = self._make_patient(client)
        token = _token(client, 'admin', 'Admin123!')
        resp = client.delete(f'/api/patient/{pid}/erase',
                             headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        app = client.application
        with app.app_context():
            p = db.session.get(Patient, pid)
            assert p.chief_complaint == '[ERASED]'

    def test_erase_missing_patient(self, client):
        token = _token(client, 'admin', 'Admin123!')
        resp = client.delete('/api/patient/nonexistent/erase',
                             headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 404


# ── MONITORING ──────────────────────────────────────────────────────
class TestMonitoring:
    def test_drift_requires_admin(self, client):
        token = _token(client, 'clinician', 'Clinician123!')
        resp = client.get('/api/monitoring/drift',
                          headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 403

    def test_performance_endpoint(self, client):
        token = _token(client, 'admin', 'Admin123!')
        resp = client.get('/api/monitoring/performance',
                          headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'agreement_rate' in data


# ── API VERSIONING ──────────────────────────────────────────────────
class TestApiVersioning:
    def test_v1_health_alias(self, client):
        # clinical-standards is public and mounted under both prefixes
        legacy = client.get('/api/clinical-standards')
        versioned = client.get('/api/v1/clinical-standards')
        assert legacy.status_code == 200
        assert versioned.status_code == 200
        assert json.loads(legacy.data) == json.loads(versioned.data)


# ── CACHING ─────────────────────────────────────────────────────────
class TestCaching:
    def test_clinical_standards_cached(self, client):
        import cache
        cache.clear()
        first = client.get('/api/clinical-standards')
        assert first.status_code == 200
        assert cache.get('clinical_standards') is not None


# ── DATABASE CONSTRAINTS ────────────────────────────────────────────
class TestDatabaseConstraints:
    def test_invalid_age_rejected(self, client):
        from sqlalchemy.exc import IntegrityError
        app = client.application
        with app.app_context():
            db.session.add(Patient(age=999, sex='M', chief_complaint='fever', pain_score=2))
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_invalid_esi_priority_rejected(self, client):
        from sqlalchemy.exc import IntegrityError
        app = client.application
        with app.app_context():
            p = Patient(age=30, sex='M', chief_complaint='fever', pain_score=2)
            db.session.add(p)
            db.session.commit()
            clinician = User.query.filter_by(username='clinician').first()
            db.session.add(TriageAssessment(
                patient_id=p.patient_id, clinician_id=clinician.user_id,
                ai_priority=9, ai_confidence=0.5))  # 9 is invalid
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()
