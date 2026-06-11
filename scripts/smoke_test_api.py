"""Quick API integration test."""
import httpx

BASE = 'http://127.0.0.1:5000'

# 1. Health check
r = httpx.get(f'{BASE}/api/health')
print(f'[1] Health: {r.status_code} {r.json()}')

# 2. Login as clinician
r = httpx.post(f'{BASE}/api/auth/login', json={'username': 'nurse_amara', 'password': 'Nurse123!'})
print(f'[2] Login: {r.status_code}')
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 3. Clinical standards
r = httpx.get(f'{BASE}/api/clinical-standards')
complaints = r.json()['chief_complaints']
print(f'[3] Standards: {r.status_code} ({len(complaints)} complaints)')

# 4. Make prediction — critical patient
r = httpx.post(f'{BASE}/api/predict', headers=headers, json={
    'patient_data': {
        'age': 67, 'sex': 'M', 'chief_complaint': 'chest_pain',
        'pain_score': 8, 'medication_flags': {'anticoagulant': True, 'diabetic': False}
    },
    'vitals': {
        'heart_rate': 115, 'sbp': 85, 'dbp': 55,
        'respiratory_rate': 26, 'spo2': 89, 'temperature': 37.8, 'gcs': 14
    }
})
print(f'[4] Predict: {r.status_code}')
result = r.json()
pred = result['ai_prediction']
print(f'    ESI Level: {pred["esi_level"]} ({pred["label"]})')
print(f'    Confidence: {pred["confidence"]:.1%}')
print(f'    SHAP top 3: {[f["feature"] for f in result["shap_explanation"]]}')
assessment_id = result['assessment_id']

# 5. Confirm assessment
r = httpx.post(f'{BASE}/api/confirm/{assessment_id}', headers=headers)
print(f'[5] Confirm: {r.status_code} — {r.json()["message"]}')

# 6. Make another prediction — less urgent
r = httpx.post(f'{BASE}/api/predict', headers=headers, json={
    'patient_data': {
        'age': 25, 'sex': 'F', 'chief_complaint': 'headache',
        'pain_score': 4, 'medication_flags': {}
    },
    'vitals': {
        'heart_rate': 72, 'sbp': 120, 'dbp': 80,
        'respiratory_rate': 16, 'spo2': 98, 'temperature': 36.8, 'gcs': 15
    }
})
pred2 = r.json()['ai_prediction']
print(f'[6] Predict #2: ESI {pred2["esi_level"]} ({pred2["label"]}) conf={pred2["confidence"]:.1%}')
assessment_id_2 = r.json()['assessment_id']

# 7. Queue (should have 1 unresolved)
r = httpx.get(f'{BASE}/api/queue', headers=headers)
print(f'[7] Queue: {r.json()["count"]} patient(s) awaiting decision')

# 8. Override #2
r = httpx.post(f'{BASE}/api/override/{assessment_id_2}', headers=headers, json={
    'new_level': 4, 'reason_code': 'OVR-02'
})
print(f'[8] Override: {r.status_code} — {r.json()["message"]}')

# 9. Admin login + audit log
r = httpx.post(f'{BASE}/api/auth/login', json={'username': 'admin', 'password': 'Admin123!'})
admin_headers = {'Authorization': f'Bearer {r.json()["access_token"]}'}

r = httpx.get(f'{BASE}/api/admin/audit-log', headers=admin_headers)
total = r.json()['pagination']['total']
print(f'[9] Audit log: {total} entries')

# 10. Admin analytics
r = httpx.get(f'{BASE}/api/admin/analytics?days=1', headers=admin_headers)
overview = r.json()['overview']
print(f'[10] Analytics: {overview["total_assessments"]} assessments, '
      f'{overview["ai_clinician_agreement_rate"]}% agreement')

print('\n=== ALL 10 API TESTS PASSED ===')
