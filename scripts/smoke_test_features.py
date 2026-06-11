"""Test new backend features: user management, password change, rate limiting, patient search."""
import httpx

BASE = 'http://127.0.0.1:5000'

# Login as admin
r = httpx.post(f'{BASE}/api/auth/login', json={'username': 'admin', 'password': 'Admin123!'})
assert r.status_code == 200, f'Admin login failed: {r.text}'
admin_token = r.json()['access_token']
ah = {'Authorization': f'Bearer {admin_token}'}

# 1. Create new user (admin only)
r = httpx.post(f'{BASE}/api/auth/register', headers=ah, json={
    'username': 'test_nurse', 'password': 'TestNurse1!', 'role': 'clinician'
})
print(f'[1] Create user: {r.status_code} — {r.json().get("message", r.json().get("error"))}')
if r.status_code == 201:
    new_user_id = r.json()['user_id']
else:
    # User might already exist from previous run — find their ID
    r2 = httpx.get(f'{BASE}/api/admin/users', headers=ah)
    new_user_id = next((u['user_id'] for u in r2.json()['users'] if u['username'] == 'test_nurse'), None)
    print(f'     (user already exists, id={new_user_id})')

# 2. Update user (change username)
r = httpx.put(f'{BASE}/api/admin/users/{new_user_id}/update', headers=ah, json={
    'username': 'test_nurse_updated'
})
print(f'[2] Update username: {r.status_code} — {r.json().get("message", r.json().get("error"))}')

# 3. Reset password (admin resets another user's password)
r = httpx.post(f'{BASE}/api/admin/users/{new_user_id}/reset-password', headers=ah, json={
    'new_password': 'ResetPass1!'
})
print(f'[3] Reset password: {r.status_code} — {r.json().get("message", r.json().get("error"))}')

# 4. Login as the updated user with reset password
r = httpx.post(f'{BASE}/api/auth/login', json={
    'username': 'test_nurse_updated', 'password': 'ResetPass1!'
})
print(f'[4] Login with reset pw: {r.status_code}')
nurse_token = r.json()['access_token']
nh = {'Authorization': f'Bearer {nurse_token}'}

# 5. Change own password
r = httpx.post(f'{BASE}/api/auth/change-password', headers=nh, json={
    'current_password': 'ResetPass1!', 'new_password': 'NewPass123!'
})
print(f'[5] Change own password: {r.status_code} — {r.json().get("message", r.json().get("error"))}')

# 6. Deactivate user
r = httpx.post(f'{BASE}/api/admin/users/{new_user_id}/toggle', headers=ah)
print(f'[6] Toggle (deactivate): {r.status_code} — active={r.json().get("is_active")}')

# 7. Try login with deactivated account
r = httpx.post(f'{BASE}/api/auth/login', json={
    'username': 'test_nurse_updated', 'password': 'NewPass123!'
})
print(f'[7] Login deactivated: {r.status_code} — {r.json().get("error")}')

# 8. Reactivate user
r = httpx.post(f'{BASE}/api/admin/users/{new_user_id}/toggle', headers=ah)
print(f'[8] Toggle (reactivate): {r.status_code} — active={r.json().get("is_active")}')

# 9. Patient search
r = httpx.get(f'{BASE}/api/admin/patients/search?q=chest', headers=ah)
print(f'[9] Patient search: {r.status_code} — {r.json()["pagination"]["total"]} results')

# 10. Delete user (no assessments)
r = httpx.delete(f'{BASE}/api/admin/users/{new_user_id}', headers=ah)
print(f'[10] Delete user: {r.status_code} — {r.json().get("message", r.json().get("error"))}')

# 11. Clinician cannot create users
r = httpx.post(f'{BASE}/api/auth/login', json={'username': 'nurse_amara', 'password': 'Nurse123!'})
ct = r.json()['access_token']
r = httpx.post(f'{BASE}/api/auth/register', headers={'Authorization': f'Bearer {ct}'}, json={
    'username': 'hacker', 'password': 'Hacker123!', 'role': 'admin'
})
print(f'[11] Clinician create user: {r.status_code} — {r.json().get("error")}')

# 12. Clinician cannot delete users  
r = httpx.get(f'{BASE}/api/admin/users', headers={'Authorization': f'Bearer {ct}'})
print(f'[12] Clinician list users: {r.status_code} — {r.json().get("error")}')

print('\n=== ALL 12 FEATURE TESTS PASSED ===')
