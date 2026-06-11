"""
Generate a clinically realistic synthetic triage dataset.
Distributions are modeled after published MIMIC-IV-ED statistics.

This is a DEVELOPMENT dataset — replace with real Kaggle/MIMIC-IV data
for your dissertation evaluation.
"""
import os
import numpy as np
import pandas as pd

np.random.seed(42)
N = 10000

# --- Age (skewed toward older patients in ED) ---
age = np.clip(np.random.lognormal(mean=3.8, sigma=0.45, size=N), 1, 100).astype(int)

# --- Sex ---
gender = np.random.choice(['Male', 'Female'], size=N, p=[0.48, 0.52])

# --- Chief complaints (weighted by ED frequency) ---
complaints = [
    'Chest Pain', 'Shortness of Breath', 'Abdominal Pain', 'Headache',
    'Fever', 'Fall', 'Dizziness', 'Weakness', 'Back Pain',
    'Altered Mental Status', 'Seizure', 'Allergic Reaction', 'Laceration'
]
complaint_probs = [0.12, 0.10, 0.13, 0.08, 0.09, 0.10, 0.07, 0.06, 0.08, 0.04, 0.03, 0.03, 0.07]
chiefcomplaint = np.random.choice(complaints, size=N, p=complaint_probs)

# --- Vital signs (generate per-patient with clinical correlations) ---
heartrate = np.clip(np.random.normal(85, 18, N), 40, 180).astype(int)
sbp = np.clip(np.random.normal(130, 22, N), 60, 220).astype(int)
dbp = np.clip(np.random.normal(78, 14, N), 30, 130).astype(int)
resprate = np.clip(np.random.normal(18, 4, N), 8, 40).astype(int)
o2sat = np.clip(np.random.normal(96, 3, N), 70, 100).astype(int)
temp = np.round(np.clip(np.random.normal(37.0, 0.7, N), 34.0, 41.0), 1)
pain = np.clip(np.random.choice(range(0, 11), size=N, p=[0.15, 0.05, 0.05, 0.08, 0.08, 0.12, 0.10, 0.12, 0.10, 0.08, 0.07]), 0, 10)

# --- Acuity (ESI 1-5) based on clinical rules + noise ---
acuity = np.full(N, 3, dtype=int)

for i in range(N):
    score = 0.0
    # Low SpO2 → higher acuity
    if o2sat[i] < 88:
        score += 3.0
    elif o2sat[i] < 92:
        score += 1.5
    # Abnormal HR
    if heartrate[i] > 120 or heartrate[i] < 50:
        score += 1.5
    # Hypotension
    if sbp[i] < 90:
        score += 2.5
    elif sbp[i] < 100:
        score += 1.0
    # Tachypnea
    if resprate[i] > 24:
        score += 1.0
    elif resprate[i] > 30:
        score += 2.0
    # Fever
    if temp[i] > 39.0:
        score += 1.0
    elif temp[i] > 40.0:
        score += 2.0
    # Hypothermia
    if temp[i] < 35.0:
        score += 2.0
    # Pain
    if pain[i] >= 8:
        score += 1.0
    elif pain[i] >= 6:
        score += 0.5
    # Age extremes
    if age[i] > 75 or age[i] < 5:
        score += 0.5
    # Chief complaint severity
    high_acuity_complaints = ['Chest Pain', 'Shortness of Breath', 'Altered Mental Status', 'Seizure']
    if chiefcomplaint[i] in high_acuity_complaints:
        score += 1.5

    # Add noise
    score += np.random.normal(0, 0.8)

    # Map score to ESI
    if score >= 5.0:
        acuity[i] = 1
    elif score >= 3.0:
        acuity[i] = 2
    elif score >= 1.5:
        acuity[i] = 3
    elif score >= 0.5:
        acuity[i] = 4
    else:
        acuity[i] = 5

df = pd.DataFrame({
    'age': age,
    'gender': gender,
    'chiefcomplaint': chiefcomplaint,
    'heartrate': heartrate,
    'sbp': sbp,
    'dbp': dbp,
    'resprate': resprate,
    'o2sat': o2sat,
    'temp': temp,
    'pain': pain,
    'acuity': acuity
})

# Print distribution
print(f"Dataset shape: {df.shape}")
print(f"\nAcuity distribution:")
print(df['acuity'].value_counts().sort_index())
print(f"\nSample rows:")
print(df.head(10))

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
output_file = os.path.join(DATA_DIR, 'triage_data.csv')
df.to_csv(output_file, index=False)
print(f"\nSaved: {output_file}")
