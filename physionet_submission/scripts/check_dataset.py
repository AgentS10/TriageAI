"""Quick check of the real Kaggle dataset columns."""
import os
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', '5v_cleandf.csv')

df = pd.read_csv(DATA_PATH, nrows=1000)
print(f"Shape (1000 rows): {df.shape}")
print(f"\nESI distribution:")
print(df['esi'].value_counts().sort_index())
print(f"\nGender: {df['gender'].unique()}")
print(f"Age range: {df['age'].min()}-{df['age'].max()}")

# Triage vitals
triage_cols = [c for c in df.columns if 'triage_vital' in c]
print(f"\nTriage vital columns: {triage_cols}")
for c in triage_cols:
    print(f"  {c}: mean={df[c].mean():.1f}, nulls={df[c].isnull().sum()}")

# Chief complaints (binary columns)
cc_cols = [c for c in df.columns if c.startswith('cc_')]
print(f"\nChief complaint columns ({len(cc_cols)}): first 15:")
for c in cc_cols[:15]:
    count = df[c].sum()
    if count > 0:
        print(f"  {c}: {int(count)} cases")

# Pain
pain_cols = [c for c in df.columns if 'pain' in c.lower()]
print(f"\nPain-related columns: {pain_cols[:5]}")

# Count total rows
import subprocess
result = subprocess.run(['wc', '-l', DATA_PATH], capture_output=True, text=True)
print(f"\nTotal lines: checking with pandas...")
# Just check shape with low_memory
df_full = pd.read_csv(DATA_PATH, usecols=['esi'], low_memory=False)
print(f"TOTAL ROWS: {len(df_full)}")
print(f"\nFull ESI distribution:")
print(df_full['esi'].value_counts().sort_index())
