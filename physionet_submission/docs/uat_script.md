# TriageAI — User Acceptance Test (UAT) Script

**Project:** TriageAI Clinical Decision Support System  
**Version:** 1.0.0  
**Test Date:** ___________  
**Tester Name:** ___________  
**Tester Role:** Clinician / Admin / Peer Reviewer  
**Facilitator:** M.S.M.Sajidh (CL/BSCSD/34/01)

---

## Instructions for Facilitator

1. **Environment:** Ensure backend (`python backend/app.py`) and frontend (`npm start`) are running.
2. **Test credentials:**
   - Admin: `admin` / `Admin123!`
   - Clinician: `dr_kemal` / `Doctor123!`
3. **Time limit:** 20–30 minutes per tester.
4. **Do not help** unless the tester is stuck for >2 minutes — note where they struggle.
5. **Record:** Pass/Fail for each task, time taken, and any comments.

---

## Pre-Test Questionnaire

| Question | Response |
|----------|----------|
| How often do you use digital health tools? | Daily / Weekly / Monthly / Never |
| What is your primary role? | Doctor / Nurse / Admin / IT / Student |
| Have you used an AI triage system before? | Yes / No |

---

## Task 1: Login & First Impressions (2 min)

**Scenario:** You are starting your shift and need to access TriageAI.

**Steps:**
1. Navigate to `http://localhost:3000`.
2. Log in with clinician credentials (`dr_kemal` / `Doctor123!`).
3. Observe the dashboard.

**Expected Result:**
- Login succeeds within 3 seconds.
- Dashboard loads with greeting, quick actions, and stats.
- Advisory banner is visible at top.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 2: New Patient Assessment (5 min)

**Scenario:** A 45-year-old male patient arrives with chest pain (pain score 8).

**Steps:**
1. Click "New Assessment" from dashboard.
2. Enter patient details:
   - Age: 45
   - Sex: Male
   - Chief Complaint: Chest Pain
   - Pain Score: 8
3. Enter vital signs:
   - Heart Rate: 105
   - SBP: 145
   - DBP: 92
   - Respiratory Rate: 22
   - SpO2: 96
   - Temperature: 37.2
   - GCS: 15
4. Submit the assessment (click button or press Ctrl+Enter).
5. Observe the Triage Result page.

**Expected Result:**
- Form submits successfully.
- Triage Result shows ESI recommendation with confidence.
- SHAP explanation panel displays top 3 contributing factors.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 3: Confirm AI Recommendation (2 min)

**Scenario:** You agree with the AI's triage recommendation.

**Steps:**
1. On the Triage Result page, click "Confirm Recommendation".
2. Wait for the success toast notification.
3. Observe the Patient Queue.

**Expected Result:**
- Confirmation succeeds.
- Toast appears: "Assessment confirmed successfully."
- Patient appears in queue with correct ESI priority.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 4: Override AI Recommendation (3 min)

**Scenario:** You disagree with the AI and want to override it.

**Steps:**
1. Create another assessment (any data).
2. On Triage Result, click "Override".
3. Select reason: "Clinical judgment — patient appears more severe".
4. Add optional notes: "Patient history of MI".
5. Submit the override.

**Expected Result:**
- Override succeeds.
- Toast appears: "Override recorded successfully."
- Audit log records the override with reason code.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 5: View Patient Queue & Sort (3 min)

**Scenario:** You need to see who is waiting and for how long.

**Steps:**
1. Navigate to "Patient Queue".
2. Observe the wait time column.
3. Sort by "Wait Time" using the dropdown.
4. Filter to show only ESI-1 and ESI-2 patients.

**Expected Result:**
- Queue displays with wait times.
- Sorting reorders rows correctly.
- Filter reduces visible rows to high-priority only.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 6: View Shift Handover (2 min)

**Scenario:** Your shift is ending. You need a summary of today's work.

**Steps:**
1. Click your avatar → "Shift Handover".
2. Review today's assessment count and priority distribution.
3. Scroll through the recent assessments table.

**Expected Result:**
- Shift handover page loads with accurate statistics.
- Priority distribution bar is visible.
- Recent assessments table shows today's confirmed/overridden cases.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 7: Change Password (2 min)

**Scenario:** You want to update your password for security.

**Steps:**
1. Click avatar → "My Profile".
2. Scroll to "Change Password" section.
3. Enter current password (`Doctor123!`).
4. Enter new password: `Doctor123!New`.
5. Confirm new password.
6. Click "Update Password".

**Expected Result:**
- Password updates successfully.
- Toast confirms: "Password updated successfully."

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 8: Admin — Create New User (3 min)

**Scenario:** (Admin only) You need to add a new nurse to the system.

**Steps:**
1. Log out, then log in as `admin` / `Admin123!`.
2. Navigate to "Admin" → "User Management".
3. Click "Create User".
4. Enter: Username `nurse_test`, Password `Test123!`, Role `clinician`.
5. Submit.
6. Verify new user appears in the table.

**Expected Result:**
- User created successfully.
- Appears in user table with "Active" status.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Task 9: Admin — View Analytics (2 min)

**Scenario:** (Admin only) You want to see system usage statistics.

**Steps:**
1. In Admin Panel, click "Analytics" tab.
2. Observe the bar chart, pie chart, and line chart.
3. Scroll down to view the clinician performance table.

**Expected Result:**
- All 3 charts render without errors.
- Data appears realistic (non-zero).
- Clinician performance table loads.

| Pass | Fail | Time (sec) | Notes |
|------|------|------------|-------|
| [ ] | [ ] | _____ | |

---

## Post-Task Observation

Ask the tester to narrate:
1. What was the most intuitive part of the system?
2. What was the most confusing part?
3. Would you trust the AI triage recommendation in a real clinical setting?
4. Any missing features you expected?

**Notes:**

_________________________________________________________________________

_________________________________________________________________________

_________________________________________________________________________

---

## Severity Classification

| Severity | Description | Count |
|----------|-------------|-------|
| Critical | Tester could not complete task, system error, or data loss | |
| Major | Task completed with significant difficulty or workaround | |
| Minor | Cosmetic issue or slight confusion, task still completed | |
| Enhancement | Suggestion for improvement, not a defect | |

---

*Total Tasks: 9 | Pass: ___ | Fail: ___ | Completion Rate: ___%*
