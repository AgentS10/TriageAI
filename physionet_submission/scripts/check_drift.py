"""
TriageAI — Drift Check CLI
===========================
Builds a training baseline OR checks a new dataset for feature drift against
the saved baseline. Intended to run on a schedule (cron / CI) in production.

Usage:
    # Generate / refresh the baseline from the training data:
    python scripts/check_drift.py --build-baseline --data data/triage_data_real.csv

    # Check a new batch of production data against the baseline:
    python scripts/check_drift.py --data data/recent_traffic.csv

Exit code is non-zero when significant drift is detected, so CI can fail.
"""
import argparse
import os
import sys

import pandas as pd

# Make backend importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.feature_contract import FEATURE_NAMES  # noqa: E402
from ml.clinical_standards import get_complaint_index, get_sex_index  # noqa: E402
from ml.monitoring import (  # noqa: E402
    build_baseline, save_baseline, load_baseline, detect_drift,
)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'ml', 'artifacts')


def _to_feature_frame(df):
    """Map a raw triage CSV into the contract feature columns."""
    out = pd.DataFrame()
    for col in ['heart_rate', 'sbp', 'dbp', 'respiratory_rate', 'spo2',
                'temperature', 'gcs', 'age', 'pain_score']:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors='coerce')
    if 'chief_complaint' in df.columns:
        out['chief_complaint_code'] = df['chief_complaint'].map(get_complaint_index)
    if 'sex' in df.columns:
        out['sex_code'] = df['sex'].map(get_sex_index)
    # Medication flags may be absent in CSVs; default to 0.
    out['med_anticoagulant'] = 0
    out['med_diabetic'] = 0
    return out.reindex(columns=FEATURE_NAMES, fill_value=0)


def main():
    parser = argparse.ArgumentParser(description="TriageAI drift checker")
    parser.add_argument('--data', required=True, help='CSV dataset path')
    parser.add_argument('--build-baseline', action='store_true',
                        help='Build/refresh the baseline instead of checking drift')
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    feature_df = _to_feature_frame(df)

    if args.build_baseline:
        baseline = build_baseline(feature_df, FEATURE_NAMES)
        path = save_baseline(baseline, ARTIFACTS_DIR)
        print(f"Baseline written: {path}  ({baseline['n_rows']} rows)")
        return 0

    baseline = load_baseline(ARTIFACTS_DIR)
    if baseline is None:
        print("ERROR: No baseline found. Run with --build-baseline first.")
        return 2

    result = detect_drift(baseline, feature_df)
    print(f"Overall drift: {result['overall_drift']}  (max PSI={result['max_psi']})")
    for feat, m in sorted(result['features'].items(), key=lambda kv: -kv[1]['psi']):
        print(f"  {feat:22s} PSI={m['psi']:.4f}  JSD={m['jsd']:.4f}  [{m['severity']}]")

    return 1 if result['overall_drift'] == 'significant' else 0


if __name__ == '__main__':
    sys.exit(main())
