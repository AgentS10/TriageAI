"""
TriageAI — Fairness Evaluation
==============================
Demographic parity analysis across age and gender subgroups.
Generates subgroup metrics and charts for dissertation Chapter 5.

Run: python notebooks/02_fairness_eval.py
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load real dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'triage_data_real.csv')
df = pd.read_csv(DATA_PATH)
print(f"Dataset: {df.shape[0]} rows x {df.shape[1]} columns")

# ── 1. AGE BUCKETING ───────────────────────────────────────────
def age_bucket(age):
    if age < 18:
        return 'child'
    elif age < 35:
        return 'young_adult'
    elif age < 55:
        return 'middle_aged'
    elif age < 75:
        return 'senior'
    else:
        return 'elderly'

df['age_bucket'] = df['age'].apply(age_bucket)

# ── 2. DEMOGRAPHIC PARITY: ESI DISTRIBUTION BY SUBGROUP ──────
print("\n" + "=" * 60)
print("DEMOGRAPHIC PARITY: ESI DISTRIBUTION BY GENDER")
print("=" * 60)

gender_esi = pd.crosstab(df['gender'], df['acuity'], normalize='index') * 100
print(gender_esi.round(2))

# Statistical test: chi-squared independence
from scipy.stats import chi2_contingency
chi2, p_gender, dof, expected = chi2_contingency(pd.crosstab(df['gender'], df['acuity']))
print(f"\nChi-squared test (gender vs acuity): χ²={chi2:.2f}, p={p_gender:.4f}")
if p_gender < 0.05:
    print("  ⚠️  Significant association — gender may influence triage distribution")
else:
    print("  ✅ No significant association — gender parity holds")

print("\n" + "=" * 60)
print("DEMOGRAPHIC PARITY: ESI DISTRIBUTION BY AGE BUCKET")
print("=" * 60)

age_esi = pd.crosstab(df['age_bucket'], df['acuity'], normalize='index') * 100
print(age_esi.round(2))

chi2_age, p_age, dof_age, expected_age = chi2_contingency(pd.crosstab(df['age_bucket'], df['acuity']))
print(f"\nChi-squared test (age_bucket vs acuity): χ²={chi2_age:.2f}, p={p_age:.4f}")
if p_age < 0.05:
    print("  ⚠️  Significant association — age may influence triage distribution")
else:
    print("  ✅ No significant association — age parity holds")

# ── 3. MAX DIFFERENCE (DEMOGRAPHIC PARITY ±5%) ────────────────
print("\n" + "=" * 60)
print("MAX DIFFERENCE CHECK (±5% threshold)")
print("=" * 60)

for esi_level in sorted(df['acuity'].unique()):
    gender_pcts = df[df['acuity'] == esi_level]['gender'].value_counts(normalize=True) * 100
    max_diff_gender = gender_pcts.max() - gender_pcts.min() if len(gender_pcts) > 1 else 0
    status = "✅" if max_diff_gender <= 5 else "⚠️"
    print(f"  ESI-{esi_level} gender max diff: {max_diff_gender:.1f}% {status}")

    age_pcts = df[df['acuity'] == esi_level]['age_bucket'].value_counts(normalize=True) * 100
    max_diff_age = age_pcts.max() - age_pcts.min() if len(age_pcts) > 1 else 0
    status = "✅" if max_diff_age <= 5 else "⚠️"
    print(f"  ESI-{esi_level} age max diff: {max_diff_age:.1f}% {status}")

# ── 4. VISUALISATIONS ─────────────────────────────────────────
COLORS = ['#c62828', '#ef6c00', '#f9a825', '#2e7d32', '#0277bd']

# Gender ESI heatmap
fig, ax = plt.subplots(figsize=(8, 4))
sns.heatmap(gender_esi, annot=True, fmt='.1f', cmap='RdYlGn_r', vmin=0, vmax=60, ax=ax)
ax.set_title('ESI Distribution by Gender (%)', fontsize=12, fontweight='bold')
ax.set_xlabel('ESI Acuity Level')
ax.set_ylabel('Gender')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fairness_gender_esi.png'), dpi=300, bbox_inches='tight')
plt.close()

# Age bucket ESI heatmap
fig, ax = plt.subplots(figsize=(10, 5))
# Reorder age buckets logically
bucket_order = ['child', 'young_adult', 'middle_aged', 'senior', 'elderly']
age_esi_ordered = age_esi.reindex([b for b in bucket_order if b in age_esi.index])
sns.heatmap(age_esi_ordered, annot=True, fmt='.1f', cmap='RdYlGn_r', vmin=0, vmax=60, ax=ax)
ax.set_title('ESI Distribution by Age Bucket (%)', fontsize=12, fontweight='bold')
ax.set_xlabel('ESI Acuity Level')
ax.set_ylabel('Age Bucket')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fairness_age_esi.png'), dpi=300, bbox_inches='tight')
plt.close()

# Max difference bar chart
fig, ax = plt.subplots(figsize=(10, 5))
levels = sorted(df['acuity'].unique())
gender_diffs = []
age_diffs = []
for esi_level in levels:
    gender_pcts = df[df['acuity'] == esi_level]['gender'].value_counts(normalize=True) * 100
    gender_diffs.append(gender_pcts.max() - gender_pcts.min() if len(gender_pcts) > 1 else 0)
    age_pcts = df[df['acuity'] == esi_level]['age_bucket'].value_counts(normalize=True) * 100
    age_diffs.append(age_pcts.max() - age_pcts.min() if len(age_pcts) > 1 else 0)

x = np.arange(len(levels))
width = 0.35
bars1 = ax.bar(x - width/2, gender_diffs, width, label='Gender', color='#0d47a1')
bars2 = ax.bar(x + width/2, age_diffs, width, label='Age Bucket', color='#c62828')
ax.axhline(y=5, color='green', linestyle='--', linewidth=2, label='±5% Threshold')
ax.set_xlabel('ESI Level')
ax.set_ylabel('Max Subgroup Difference (%)')
ax.set_title('Demographic Parity: Max Subgroup Difference per ESI Level')
ax.set_xticks(x)
ax.set_xticklabels([f'ESI-{l}' for l in levels])
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fairness_max_diff.png'), dpi=300, bbox_inches='tight')
plt.close()

# ── 5. SUMMARY CSV ────────────────────────────────────────────
summary = pd.DataFrame({
    'esi_level': levels,
    'gender_max_diff_pct': [round(d, 2) for d in gender_diffs],
    'age_max_diff_pct': [round(d, 2) for d in age_diffs],
    'gender_passes_5pct': [d <= 5 for d in gender_diffs],
    'age_passes_5pct': [d <= 5 for d in age_diffs]
})
summary.to_csv(os.path.join(OUTPUT_DIR, 'fairness_summary.csv'), index=False)

print("\n" + "=" * 60)
print("FAIRNESS EVALUATION COMPLETE")
print("=" * 60)
print(f"Figures saved to: {OUTPUT_DIR}/")
for f in sorted(os.listdir(OUTPUT_DIR)):
    if 'fairness' in f:
        print(f"  - {f}")
print(f"\nSummary CSV: fairness_summary.csv")
print(f"Gender parity p-value: {p_gender:.4f}")
print(f"Age parity p-value: {p_age:.4f}")
