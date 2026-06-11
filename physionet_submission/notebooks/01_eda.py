"""
TriageAI — Exploratory Data Analysis (EDA)
==========================================
Run with: python notebooks/01_eda.py
Generates EDA report images in notebooks/figures/

This script produces the quantitative analysis required for
Chapter 4 (Data & ML) of the dissertation.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Setup
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(OUTPUT_DIR, exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ['#c62828', '#ef6c00', '#f9a825', '#2e7d32', '#0277bd']

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'triage_data_real.csv')
df = pd.read_csv(DATA_PATH)
print(f"Dataset: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"Columns: {list(df.columns)}\n")

# ── 1. MISSING VALUES REPORT ─────────────────────────────────
print("=" * 50)
print("1. MISSING VALUES")
print("=" * 50)
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({'Count': missing, 'Percent': missing_pct})
print(missing_report[missing_report['Count'] > 0] if missing.sum() > 0 else "No missing values found.")
print(f"\nTotal missing cells: {missing.sum()} / {df.size} ({missing.sum()/df.size*100:.2f}%)")

# ── 2. DESCRIPTIVE STATISTICS ────────────────────────────────
print(f"\n{'=' * 50}")
print("2. DESCRIPTIVE STATISTICS")
print("=" * 50)
desc = df.describe().round(2)
print(desc)
desc.to_csv(os.path.join(OUTPUT_DIR, 'descriptive_stats.csv'))

# ── 3. TARGET CLASS DISTRIBUTION ─────────────────────────────
print(f"\n{'=' * 50}")
print("3. ESI ACUITY DISTRIBUTION")
print("=" * 50)
acuity_dist = df['acuity'].value_counts().sort_index()
print(acuity_dist)
print(f"\nClass imbalance ratio (max/min): {acuity_dist.max()/acuity_dist.min():.1f}x")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
labels = [f'ESI {i}\n(n={acuity_dist[i]})' for i in acuity_dist.index]

axes[0].bar(range(len(acuity_dist)), acuity_dist.values, color=COLORS[:len(acuity_dist)])
axes[0].set_xticks(range(len(acuity_dist)))
axes[0].set_xticklabels(labels)
axes[0].set_ylabel('Count')
axes[0].set_title('ESI Level Distribution (Before SMOTE)')

axes[1].pie(acuity_dist.values, labels=[f'ESI {i}' for i in acuity_dist.index],
            colors=COLORS[:len(acuity_dist)], autopct='%1.1f%%', startangle=90)
axes[1].set_title('ESI Level Proportions')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'esi_distribution.png'), dpi=300, bbox_inches='tight')
plt.close()

# ── 4. VITAL SIGNS DISTRIBUTIONS ─────────────────────────────
print(f"\n{'=' * 50}")
print("4. VITAL SIGNS DISTRIBUTIONS")
print("=" * 50)
vitals = ['heartrate', 'sbp', 'dbp', 'resprate', 'o2sat', 'temp', 'pain']
vital_labels = ['Heart Rate\n(bpm)', 'Systolic BP\n(mmHg)', 'Diastolic BP\n(mmHg)',
                'Resp Rate\n(br/min)', 'SpO2\n(%)', 'Temperature\n(°C)', 'Pain\n(0-10)']

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()
for i, (col, label) in enumerate(zip(vitals, vital_labels)):
    if col in df.columns:
        axes[i].hist(df[col], bins=30, color=COLORS[i % len(COLORS)], alpha=0.7, edgecolor='white')
        axes[i].set_title(label, fontsize=10)
        axes[i].axvline(df[col].median(), color='red', linestyle='--', linewidth=1, label=f'Median: {df[col].median():.1f}')
        axes[i].legend(fontsize=8)
        print(f"  {col:15s}: mean={df[col].mean():.1f}, median={df[col].median():.1f}, std={df[col].std():.1f}")

# Hide unused subplot
if len(vitals) < len(axes):
    for j in range(len(vitals), len(axes)):
        axes[j].set_visible(False)

plt.suptitle('Vital Signs Distributions', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'vitals_distributions.png'), dpi=300, bbox_inches='tight')
plt.close()

# ── 5. AGE DISTRIBUTION BY ESI LEVEL ─────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
for esi in sorted(df['acuity'].unique()):
    subset = df[df['acuity'] == esi]['age']
    ax.hist(subset, bins=30, alpha=0.5, label=f'ESI {esi}', color=COLORS[esi-1])
ax.set_xlabel('Age')
ax.set_ylabel('Count')
ax.set_title('Age Distribution by ESI Level')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'age_by_esi.png'), dpi=300, bbox_inches='tight')
plt.close()

# ── 6. CORRELATION HEATMAP ───────────────────────────────────
print(f"\n{'=' * 50}")
print("6. CORRELATION MATRIX")
print("=" * 50)
numeric_cols = df.select_dtypes(include=[np.number]).columns
corr = df[numeric_cols].corr().round(2)
print(corr)

fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            square=True, ax=ax, linewidths=0.5)
ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'correlation_heatmap.png'), dpi=300, bbox_inches='tight')
plt.close()

# ── 7. VITAL SIGNS BY ESI LEVEL (BOX PLOTS) ──────────────────
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()
box_vitals = ['heartrate', 'sbp', 'o2sat', 'resprate', 'temp', 'pain']
box_labels = ['Heart Rate', 'Systolic BP', 'SpO2', 'Resp Rate', 'Temperature', 'Pain Score']

for i, (col, label) in enumerate(zip(box_vitals, box_labels)):
    if col in df.columns:
        data = [df[df['acuity'] == esi][col].dropna() for esi in sorted(df['acuity'].unique())]
        bp = axes[i].boxplot(data, labels=[f'ESI {e}' for e in sorted(df['acuity'].unique())],
                             patch_artist=True, showfliers=False)
        for patch, color in zip(bp['boxes'], COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        axes[i].set_title(label)
        axes[i].set_ylabel(label)

plt.suptitle('Vital Signs by ESI Level', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'vitals_by_esi_boxplot.png'), dpi=300, bbox_inches='tight')
plt.close()

# ── 8. CHIEF COMPLAINT FREQUENCY ─────────────────────────────
if 'chiefcomplaint' in df.columns:
    fig, ax = plt.subplots(figsize=(10, 6))
    complaint_counts = df['chiefcomplaint'].value_counts()
    bars = ax.barh(complaint_counts.index, complaint_counts.values, color='#0d47a1', alpha=0.8)
    ax.set_xlabel('Count')
    ax.set_title('Chief Complaint Frequency')
    for bar, val in zip(bars, complaint_counts.values):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                f'{val} ({val/len(df)*100:.1f}%)', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'chief_complaint_freq.png'), dpi=300, bbox_inches='tight')
    plt.close()

# ── 9. GENDER DISTRIBUTION ───────────────────────────────────
if 'gender' in df.columns:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    gender_counts = df['gender'].value_counts()
    axes[0].pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%',
                colors=['#0d47a1', '#c62828'], startangle=90)
    axes[0].set_title('Gender Distribution')

    gender_esi = pd.crosstab(df['gender'], df['acuity'], normalize='index') * 100
    gender_esi.plot(kind='bar', ax=axes[1], color=COLORS)
    axes[1].set_title('ESI Distribution by Gender (%)')
    axes[1].set_ylabel('Percentage')
    axes[1].legend(title='ESI Level')
    axes[1].tick_params(axis='x', rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gender_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()

# ── SUMMARY ──────────────────────────────────────────────────
print(f"\n{'=' * 50}")
print("EDA COMPLETE")
print("=" * 50)
print(f"Figures saved to: {OUTPUT_DIR}/")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  - {f}")
print(f"\nTotal records: {len(df)}")
print(f"Total features: {len(df.columns)}")
print(f"Target variable: acuity (ESI 1-5)")
print(f"Class imbalance: {acuity_dist.max()/acuity_dist.min():.1f}x (max/min)")
