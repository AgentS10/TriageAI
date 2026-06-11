"""
TriageAI — Locust Load Test
============================
A Python-based load test (alternative/companion to the JMeter plan in
jmeter/triageai_load_test.jmx). Locust is easy to run in CI and locally.

Usage (headless, 50 users, 5/s spawn, 1 minute):
    pip install locust
    locust -f scripts/locustfile.py --headless -u 50 -r 5 -t 1m \
           --host http://localhost:5000

Set TRIAGEAI_USER / TRIAGEAI_PASS env vars to override the default
clinician credentials.
"""
import os
import random

try:
    from locust import HttpUser, task, between
except ImportError:  # keep the file importable without locust installed
    HttpUser = object
    def task(*a, **k):  # noqa: D401
        def deco(f):
            return f
        return deco
    def between(*a, **k):
        return None


USERNAME = os.getenv('TRIAGEAI_USER', 'clinician')
PASSWORD = os.getenv('TRIAGEAI_PASS', 'Clinician123!')

CHIEF_COMPLAINTS = [
    'chest_pain', 'shortness_of_breath', 'abdominal_pain', 'headache', 'fever',
]


def _random_record():
    return {
        'patient_data': {
            'age': random.randint(18, 90),
            'sex': random.choice(['M', 'F']),
            'chief_complaint': random.choice(CHIEF_COMPLAINTS),
            'pain_score': random.randint(0, 10),
        },
        'vitals': {
            'heart_rate': random.randint(50, 130),
            'sbp': random.randint(90, 170),
            'dbp': random.randint(50, 100),
            'respiratory_rate': random.randint(10, 30),
            'spo2': random.randint(90, 100),
            'temperature': round(random.uniform(36.0, 39.5), 1),
            'gcs': random.randint(12, 15),
        },
    }


class TriageUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        resp = self.client.post('/api/auth/login',
                                json={'username': USERNAME, 'password': PASSWORD})
        self.token = resp.json().get('access_token') if resp.status_code == 200 else None

    def _headers(self):
        return {'Authorization': f'Bearer {self.token}'} if self.token else {}

    @task(3)
    def predict(self):
        rec = _random_record()
        self.client.post('/api/predict', json=rec, headers=self._headers(), name='/api/predict')

    @task(1)
    def batch_predict(self):
        records = [_random_record() for _ in range(10)]
        self.client.post('/api/predict/batch', json={'records': records},
                         headers=self._headers(), name='/api/predict/batch')

    @task(2)
    def queue(self):
        self.client.get('/api/queue', headers=self._headers(), name='/api/queue')

    @task(1)
    def clinical_standards(self):
        self.client.get('/api/clinical-standards', name='/api/clinical-standards')
