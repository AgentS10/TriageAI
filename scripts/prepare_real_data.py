"""
Prepare the real Kaggle dataset (5v_cleandf.csv) for TriageAI training.
Extracts the columns we need and maps them to our feature contract format.
"""
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from ml.feature_contract import FEATURE_NAMES, EXPECTED_FEATURE_COUNT
from ml.clinical_standards import CHIEF_COMPLAINT_REGISTRY

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INPUT_PATH = os.path.join(DATA_DIR, '5v_cleandf.csv')

print("Loading 5v_cleandf.csv...")
# Only load columns we need to save memory
use_cols = ['esi', 'age', 'gender',
            'triage_vital_hr', 'triage_vital_sbp', 'triage_vital_dbp',
            'triage_vital_rr', 'triage_vital_o2', 'triage_vital_temp']

# Add chief complaint columns we can map
cc_map = {
    'cc_chestpain': 'chest_pain',
    'cc_sob': 'shortness_of_breath',
    'cc_shortnessofbreath': 'shortness_of_breath',
    'cc_abdominalpain': 'abdominal_pain',
    'cc_headache': 'headache',
    'cc_fever': 'fever',
    'cc_fall': 'trauma_injury',
    'cc_trauma': 'trauma_injury',
    'cc_dizziness': 'dizziness_syncope',
    'cc_syncope': 'dizziness_syncope',
    'cc_weakness': 'weakness_numbness',
    'cc_numbness': 'weakness_numbness',
    'cc_backpain': 'back_pain',
    'cc_alteredmentalstatus': 'altered_mental_status',
    'cc_seizure': 'seizure',
    'cc_seizures': 'seizure',
    'cc_allergicreaction': 'allergic_reaction',
}

# Read all columns first to find which cc_ columns exist
df_sample = pd.read_csv(INPUT_PATH, nrows=1)
all_cols = df_sample.columns.tolist()
cc_cols_to_load = [c for c in cc_map.keys() if c in all_cols]
use_cols.extend(cc_cols_to_load)

print(f"Loading {len(use_cols)} columns...")
df = pd.read_csv(INPUT_PATH, usecols=use_cols, low_memory=False)
print(f"Loaded: {df.shape[0]} rows x {df.shape[1]} columns")

# Drop rows with missing ESI
df = df.dropna(subset=['esi'])
df['esi'] = df['esi'].astype(int)
print(f"After dropping missing ESI: {len(df)} rows")
print(f"\nESI distribution:")
print(df['esi'].value_counts().sort_index())

# Map columns to our format
output = pd.DataFrame()
output['acuity'] = df['esi']
output['age'] = df['age']
output['gender'] = df['gender']

# Vitals — convert temp from F to C
output['heartrate'] = df['triage_vital_hr']
output['sbp'] = df['triage_vital_sbp']
output['dbp'] = df['triage_vital_dbp']
output['resprate'] = df['triage_vital_rr']
output['o2sat'] = df['triage_vital_o2']
output['temp'] = (df['triage_vital_temp'] - 32) * 5/9  # F to C

# Determine chief complaint from binary columns
def get_chief_complaint(row):
    for cc_col, code in cc_map.items():
        if cc_col in row.index and row[cc_col] == 1:
            return code
    return 'other'

print("\nMapping chief complaints...")
output['chiefcomplaint'] = df.apply(get_chief_complaint, axis=1)
print(f"Chief complaint distribution:")
print(output['chiefcomplaint'].value_counts().head(10))

# No pain score in this dataset — use 5 as default
output['pain'] = 5

# Save
output_file = os.path.join(DATA_DIR, 'triage_data_real.csv')
output.to_csv(output_file, index=False)
print(f"\nSaved: {output_file} ({len(output)} rows x {len(output.columns)} columns)")
print(f"Columns: {output.columns.tolist()}")
print(f"\nSample:")
print(output.head(3))
