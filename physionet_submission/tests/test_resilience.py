"""
TriageAI — Resilience / Chaos Tests
====================================
Verifies the system degrades gracefully under failure conditions rather than
crashing or leaking internal errors:

  - Expired / malformed JWTs are rejected cleanly (401/422).
  - A missing or unloaded ML model returns 503, not a 500 stack trace.
  - Malformed JSON bodies are rejected with 400.
  - Corrupted datasets are caught by the data-quality gate.
  - Database integrity errors roll back without corrupting the session.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
from datetime import timedelta

import pytest
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token

from app import create_app
from extensions import db
from models import User


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            db.session.add(User(
                username='clinician', password_hash=generate_password_hash('Clinician123!'),
                role='clinician', is_active=True))
            db.session.commit()
            yield client
            db.session.remove()
            db.drop_all()


class TestAuthResilience:
    def test_expired_token_rejected(self, client):
        app = client.application
        with app.app_context():
            user = User.query.filter_by(username='clinician').first()
            expired = create_access_token(
                identity=user.user_id, expires_delta=timedelta(seconds=-1))
        resp = client.get('/api/auth/profile',
                          headers={'Authorization': f'Bearer {expired}'})
        assert resp.status_code == 401

    def test_malformed_token_rejected(self, client):
        resp = client.get('/api/auth/profile',
                          headers={'Authorization': 'Bearer not-a-real-token'})
        assert resp.status_code == 422

    def test_missing_auth_header_rejected(self, client):
        resp = client.get('/api/auth/profile')
        assert resp.status_code == 401


class TestModelResilience:
    def test_model_unloaded_returns_503(self, client):
        token = json.loads(client.post('/api/auth/login', json={
            'username': 'clinician', 'password': 'Clinician123!'}).data)['access_token']

        import routes.predict as predict_module
        saved = predict_module._model_state['loaded']
        predict_module._model_state['loaded'] = False
        try:
            resp = client.post('/api/predict',
                               headers={'Authorization': f'Bearer {token}'},
                               json={'patient_data': {}, 'vitals': {}})
            assert resp.status_code == 503
        finally:
            predict_module._model_state['loaded'] = saved


class TestInputResilience:
    def test_malformed_json_rejected(self, client):
        resp = client.post('/api/auth/login',
                           data='{not valid json',
                           content_type='application/json')
        assert resp.status_code == 400

    def test_corrupted_dataframe_caught(self):
        import pandas as pd
        from ml.data_quality import validate_dataframe
        # Missing required columns + out-of-range values.
        df = pd.DataFrame({'age': [200, -5], 'heart_rate': [9999, 80]})
        report = validate_dataframe(df)
        assert report['passed'] is False
        assert report['missing_columns']  # schema gaps detected


class TestDatabaseResilience:
    def test_integrity_error_rolls_back(self, client):
        from sqlalchemy.exc import IntegrityError
        from models import Patient
        app = client.application
        with app.app_context():
            db.session.add(Patient(age=-1, sex='M', chief_complaint='fever', pain_score=2))
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            # Session is usable again after rollback.
            assert User.query.filter_by(username='clinician').first() is not None
