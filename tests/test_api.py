"""
TriageAI API Integration Tests
================================
End-to-end tests for Flask HTTP endpoints using the test client.
Run: pytest tests/test_api.py -v --tb=short
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
import json
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User, Patient, Vitals, TriageAssessment, AuditLog


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed admin
            admin = User(
                username='admin',
                password_hash=generate_password_hash('Admin123!'),
                role='admin',
                is_active=True
            )
            # Seed clinician
            clinician = User(
                username='clinician',
                password_hash=generate_password_hash('Clinician123!'),
                role='clinician',
                is_active=True
            )
            db.session.add_all([admin, clinician])
            db.session.commit()
            yield client
            db.session.remove()
            db.drop_all()


class TestHealth:
    def test_health_check(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'healthy'


class TestAuth:
    def test_login_success(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'clinician',
            'password': 'Clinician123!'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'access_token' in data
        assert data['user']['role'] == 'clinician'

    def test_login_failure(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'clinician',
            'password': 'wrongpassword'
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post('/api/auth/login', json={})
        assert resp.status_code == 400

    def test_profile_without_token(self, client):
        resp = client.get('/api/auth/profile')
        assert resp.status_code == 401

    def test_profile_with_token(self, client):
        token = self._get_token(client, 'clinician', 'Clinician123!')
        resp = client.get('/api/auth/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['username'] == 'clinician'

    def test_refresh_token(self, client):
        tokens = self._get_tokens(client, 'clinician', 'Clinician123!')
        resp = client.post('/api/auth/refresh', headers={
            'Authorization': f'Bearer {tokens["refresh_token"]}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'access_token' in data

    def test_change_password(self, client):
        token = self._get_token(client, 'clinician', 'Clinician123!')
        resp = client.post('/api/auth/change-password', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'current_password': 'Clinician123!',
            'new_password': 'NewPass123!'
        })
        assert resp.status_code == 200
        # Verify new password works
        resp2 = client.post('/api/auth/login', json={
            'username': 'clinician',
            'password': 'NewPass123!'
        })
        assert resp2.status_code == 200

    def test_register_as_admin(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        resp = client.post('/api/auth/register', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'username': 'newuser',
            'password': 'NewUser123!',
            'role': 'clinician'
        })
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['username'] == 'newuser'

    def test_register_as_clinician_fails(self, client):
        token = self._get_token(client, 'clinician', 'Clinician123!')
        resp = client.post('/api/auth/register', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'username': 'baduser',
            'password': 'BadUser123!',
            'role': 'clinician'
        })
        assert resp.status_code == 403

    @staticmethod
    def _get_token(client, username, password):
        resp = client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        return json.loads(resp.data)['access_token']

    @staticmethod
    def _get_tokens(client, username, password):
        resp = client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        data = json.loads(resp.data)
        return {'access_token': data['access_token'], 'refresh_token': data['refresh_token']}


class TestModelMetrics:
    def test_model_metrics(self, client):
        resp = client.get('/api/model-metrics')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'classification_report' in data or 'error' not in data


class TestQueueStats:
    def test_queue_stats(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        resp = client.get('/api/queue/stats', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'pending_count' in data
        assert 'critical_count' in data


class TestPredictAndConfirm:
    def test_predict_requires_clinician(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        payload = {
            'patient_data': {
                'age': 45,
                'sex': 'M',
                'chief_complaint': 'chest_pain',
                'pain_score': 7
            },
            'vitals': {
                'heart_rate': 88,
                'sbp': 130,
                'dbp': 85,
                'respiratory_rate': 18,
                'spo2': 98,
                'temperature': 36.8,
                'gcs': 15
            }
        }
        resp = client.post('/api/predict', headers={
            'Authorization': f'Bearer {token}'
        }, json=payload)
        # Model may or may not be loaded depending on artifact presence
        assert resp.status_code in (200, 503)

    def test_predict_missing_fields(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        resp = client.post('/api/predict', headers={
            'Authorization': f'Bearer {token}'
        }, json={'patient_data': {}})
        assert resp.status_code == 400

    def test_predict_unauthorized_role(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        resp = client.post('/api/predict', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'patient_data': {
                'age': 45,
                'sex': 'M',
                'chief_complaint': 'chest_pain',
                'pain_score': 7
            },
            'vitals': {
                'heart_rate': 88,
                'sbp': 130,
                'dbp': 85,
                'respiratory_rate': 18,
                'spo2': 98,
                'temperature': 36.8,
                'gcs': 15
            }
        })
        assert resp.status_code == 403

    def _create_assessment(self, client, token):
        payload = {
            'patient_data': {
                'age': 45,
                'sex': 'M',
                'chief_complaint': 'chest_pain',
                'pain_score': 7
            },
            'vitals': {
                'heart_rate': 88,
                'sbp': 130,
                'dbp': 85,
                'respiratory_rate': 18,
                'spo2': 98,
                'temperature': 36.8,
                'gcs': 15
            }
        }
        resp = client.post('/api/predict', headers={
            'Authorization': f'Bearer {token}'
        }, json=payload)
        if resp.status_code != 200:
            pytest.skip("Model not loaded — skipping confirm/override tests")
        return json.loads(resp.data)['assessment_id']

    def test_confirm_assessment(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        assessment_id = self._create_assessment(client, token)
        resp = client.post(f'/api/confirm/{assessment_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['confirmed_level'] is not None

    def test_override_missing_reason(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        assessment_id = self._create_assessment(client, token)
        resp = client.post(f'/api/override/{assessment_id}', headers={
            'Authorization': f'Bearer {token}'
        }, json={'new_level': 2})
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'reason_code' in data['error']

    def test_override_valid(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        assessment_id = self._create_assessment(client, token)
        resp = client.post(f'/api/override/{assessment_id}', headers={
            'Authorization': f'Bearer {token}'
        }, json={'new_level': 2, 'reason_code': 'OVR-01'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['clinician_level'] == 2


class TestAdminRoutes:
    def test_get_users_as_admin(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/admin/users', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'users' in data
        assert len(data['users']) >= 2

    def test_get_users_as_clinician_fails(self, client):
        token = TestAuth._get_token(client, 'clinician', 'Clinician123!')
        resp = client.get('/api/admin/users', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 403

    def test_toggle_user_status(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        # First create a new user to toggle
        resp = client.post('/api/auth/register', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'username': 'toggle_test_user',
            'password': 'ToggleTest123!',
            'role': 'clinician'
        })
        user_id = json.loads(resp.data)['user_id']
        # Toggle off
        resp2 = client.post(f'/api/admin/users/{user_id}/toggle', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp2.status_code == 200
        data = json.loads(resp2.data)
        assert data['is_active'] is False

    def test_update_user(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        # Get clinician user_id
        resp = client.get('/api/admin/users', headers={
            'Authorization': f'Bearer {token}'
        })
        users = json.loads(resp.data)['users']
        clinician = next(u for u in users if u['username'] == 'clinician')
        # Update username
        resp2 = client.put(f'/api/admin/users/{clinician["user_id"]}/update', headers={
            'Authorization': f'Bearer {token}'
        }, json={'username': 'clinician_updated'})
        assert resp2.status_code == 200
        # Revert
        resp3 = client.put(f'/api/admin/users/{clinician["user_id"]}/update', headers={
            'Authorization': f'Bearer {token}'
        }, json={'username': 'clinician'})
        assert resp3.status_code == 200

    def test_reset_password(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/admin/users', headers={
            'Authorization': f'Bearer {token}'
        })
        users = json.loads(resp.data)['users']
        clinician = next(u for u in users if u['username'] == 'clinician')
        resp2 = client.post(f'/api/admin/users/{clinician["user_id"]}/reset-password', headers={
            'Authorization': f'Bearer {token}'
        }, json={'new_password': 'ResetPass123!'})
        assert resp2.status_code == 200

    def test_audit_log(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/admin/audit-log', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'audit_log' in data
        assert 'pagination' in data

    def test_analytics(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/admin/analytics', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'overview' in data
        assert 'period' in data

    def test_search_patients(self, client):
        token = TestAuth._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/admin/patients/search?q=chest', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'results' in data


class TestFHIR:
    """FHIR R4 endpoint tests."""

    def _get_token(self, client, username, password):
        resp = client.post('/api/auth/login', json={
            'username': username, 'password': password
        })
        return json.loads(resp.data)['access_token']

    def _get_clinician_id(self):
        clinician = db.session.query(User).filter_by(username='clinician').first()
        return clinician.user_id

    def _seed_patient_and_assessment(self):
        clinician_id = self._get_clinician_id()
        patient = Patient(age=45, sex='M', chief_complaint='chest_pain', pain_score=8)
        db.session.add(patient)
        db.session.flush()
        vitals = Vitals(
            patient_id=patient.patient_id, heart_rate=105, sbp=145, dbp=92,
            respiratory_rate=22, spo2=96, temperature=37.2, gcs=15
        )
        db.session.add(vitals)
        assessment = TriageAssessment(
            patient_id=patient.patient_id, clinician_id=clinician_id,
            ai_priority=2, ai_confidence=0.91, clinician_priority=2, is_override=False
        )
        db.session.add(assessment)
        db.session.commit()
        return patient.patient_id, assessment.assessment_id

    def test_fhir_patient_found(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        patient_id, _ = self._seed_patient_and_assessment()
        resp = client.get(f'/api/fhir/Patient/{patient_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['resourceType'] == 'Patient'
        assert data['id'] == str(patient_id)
        assert data['gender'] == 'male'

    def test_fhir_patient_not_found(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/fhir/Patient/99999', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert data['resourceType'] == 'OperationOutcome'

    def test_fhir_diagnostic_report_found(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        _, assessment_id = self._seed_patient_and_assessment()
        resp = client.get(f'/api/fhir/DiagnosticReport/{assessment_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['resourceType'] == 'DiagnosticReport'
        assert data['id'] == str(assessment_id)
        assert data['status'] == 'final'
        assert data['code']['coding'][0]['code'] == 'ESI-2'
        assert 'presentedForm' in data

    def test_fhir_diagnostic_report_not_found(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        resp = client.get('/api/fhir/DiagnosticReport/99999', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert data['resourceType'] == 'OperationOutcome'

    def test_fhir_requires_auth(self, client):
        resp = client.get('/api/fhir/Patient/anything')
        assert resp.status_code in (401, 422)

    def test_fhir_content_type(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        patient_id, _ = self._seed_patient_and_assessment()
        resp = client.get(f'/api/fhir/Patient/{patient_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert 'application/fhir+json' in resp.content_type

    def test_fhir_metadata_public(self, client):
        resp = client.get('/api/fhir/metadata')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['resourceType'] == 'CapabilityStatement'
        assert data['fhirVersion'] == '4.0.1'

    def test_fhir_diagnostic_report_has_loinc_observations(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        _, assessment_id = self._seed_patient_and_assessment()
        resp = client.get(f'/api/fhir/DiagnosticReport/{assessment_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        data = json.loads(resp.data)
        assert 'contained' in data
        codes = {o['code']['coding'][0]['code'] for o in data['contained']}
        assert '8867-4' in codes  # heart rate LOINC
        assert all(o['resourceType'] == 'Observation' for o in data['contained'])

    def test_fhir_observation_search(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        patient_id, _ = self._seed_patient_and_assessment()
        resp = client.get(f'/api/fhir/Observation?patient={patient_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['resourceType'] == 'Bundle'
        assert data['total'] >= 1

    def test_fhir_patient_everything_bundle(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        patient_id, _ = self._seed_patient_and_assessment()
        resp = client.get(f'/api/fhir/Patient/{patient_id}/$everything', headers={
            'Authorization': f'Bearer {token}'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['resourceType'] == 'Bundle'
        types = {e['resource']['resourceType'] for e in data['entry']}
        assert 'Patient' in types and 'DiagnosticReport' in types

    def test_phi_read_is_audited(self, client):
        token = self._get_token(client, 'admin', 'Admin123!')
        patient_id, _ = self._seed_patient_and_assessment()
        before = AuditLog.query.filter_by(event_type='phi_read').count()
        client.get(f'/api/fhir/Patient/{patient_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        after = AuditLog.query.filter_by(event_type='phi_read').count()
        assert after == before + 1
