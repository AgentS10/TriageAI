"""
TriageAI — ML Model Training Pipeline
=======================================
This script trains the XGBoost triage classification model using the
feature contract defined in backend/ml/feature_contract.py and the
categorical mapping registry in backend/ml/clinical_standards.py.

Key guarantees:
  - Feature vector order is governed by FEATURE_VECTOR_SPEC (contract).
  - Categorical features use deterministic integer codes (no arbitrary strings).
  - The feature contract hash is saved alongside the model so that the
    inference endpoint can detect and reject mismatched models.
  - SMOTE is applied ONLY to the training fold, never to test data.

Usage:
  python train_model.py --data data/triage_data.csv --output backend/ml/artifacts
"""
import sys
import os
import json
import argparse
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import shap
import optuna
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Add backend to path so we can import the contract + standards
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from ml.feature_contract import (
    FEATURE_VECTOR_SPEC, FEATURE_NAMES, EXPECTED_FEATURE_COUNT,
    get_contract_hash, save_contract
)
from ml.clinical_standards import (
    CHIEF_COMPLAINT_REGISTRY, SEX_CODES,
    VITAL_SIGN_STANDARDS, validate_vital_sign
)
from ml.monitoring import build_baseline, save_baseline

# ────────────────────────────────────────────────────────────────────
# COLUMN MAPPING — maps raw CSV column names to contract feature names
# UPDATE THIS when you change datasets (Kaggle vs MIMIC-IV-ED)
# ────────────────────────────────────────────────────────────────────
COLUMN_MAP = {
    # Kaggle "hospital-triage-and-patient-history-data"
    'heartrate':     'heart_rate',
    'sbp':           'sbp',
    'dbp':           'dbp',
    'resprate':      'respiratory_rate',
    'o2sat':         'spo2',
    'temp':          'temperature',
    'pain':          'pain_score',
    'age':           'age',
    'acuity':        'esi_target',
    'gender':        'sex',
    'chiefcomplaint':'chief_complaint_raw',
    # Fallback: if columns already match contract names, no mapping needed
    'heart_rate':        'heart_rate',
    'respiratory_rate':  'respiratory_rate',
    'spo2':              'spo2',
    'temperature':       'temperature',
    'pain_score':        'pain_score',
    'gcs':               'gcs',
}


def load_and_explore(filepath):
    """Load dataset and print diagnostics."""
    print("=" * 70)
    print(f"  LOADING DATASET: {filepath}")
    print("=" * 70)
    df = pd.read_csv(filepath)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 3 rows:\n{df.head(3)}")
    print(f"\nMissing values:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    return df


def standardise_columns(df):
    """Rename raw CSV columns to contract-compatible names."""
    renamed = {}
    for raw_col in df.columns:
        key = raw_col.strip().lower().replace(' ', '_')
        if key in COLUMN_MAP:
            renamed[raw_col] = COLUMN_MAP[key]
    df = df.rename(columns=renamed)
    print(f"\nStandardised columns: {list(df.columns)}")
    return df


def map_chief_complaint(raw_text):
    """Map free-text chief complaint to a registry code (deterministic)."""
    if pd.isna(raw_text):
        return "other"
    text = str(raw_text).lower().strip()
    keyword_map = {
        "chest":     "chest_pain",
        "breath":    "shortness_of_breath",
        "dyspnea":   "shortness_of_breath",
        "abdom":     "abdominal_pain",
        "head":      "headache",
        "fever":     "fever",
        "trauma":    "trauma_injury",
        "fall":      "trauma_injury",
        "lacerat":   "trauma_injury",
        "dizz":      "dizziness_syncope",
        "syncope":   "dizziness_syncope",
        "faint":     "dizziness_syncope",
        "weak":      "weakness_numbness",
        "numb":      "weakness_numbness",
        "back":      "back_pain",
        "mental":    "altered_mental_status",
        "confus":    "altered_mental_status",
        "seizure":   "seizure",
        "convuls":   "seizure",
        "allerg":    "allergic_reaction",
        "anaphyl":   "allergic_reaction",
    }
    for keyword, code in keyword_map.items():
        if keyword in text:
            return code
    return "other"


def map_sex(raw_val):
    """Map raw sex/gender column to standard code."""
    if pd.isna(raw_val):
        return "U"
    val = str(raw_val).strip().upper()
    if val in ("M", "MALE", "1"):
        return "M"
    elif val in ("F", "FEMALE", "2", "0"):
        return "F"
    elif val in ("O", "OTHER"):
        return "O"
    return "U"


def preprocess(df, target_col='esi_target'):
    """
    Full preprocessing pipeline aligned with FEATURE_VECTOR_SPEC.
    Returns X, y, label_encoder with features in contract order.
    """
    print("\n" + "=" * 70)
    print("  PREPROCESSING (contract-aligned)")
    print("=" * 70)

    df = df.dropna(subset=[target_col]).copy()
    print(f"Rows after dropping missing target: {len(df)}")

    # Map categorical features to deterministic codes
    if 'chief_complaint_raw' in df.columns:
        df['chief_complaint_code'] = df['chief_complaint_raw'].apply(
            lambda x: CHIEF_COMPLAINT_REGISTRY.get(map_chief_complaint(x), CHIEF_COMPLAINT_REGISTRY["other"])["category_index"]
        )
    else:
        df['chief_complaint_code'] = CHIEF_COMPLAINT_REGISTRY["other"]["category_index"]

    if 'sex' in df.columns:
        df['sex_code'] = df['sex'].apply(lambda x: SEX_CODES.get(map_sex(x), SEX_CODES["U"])["category_index"])
    else:
        df['sex_code'] = SEX_CODES["U"]["category_index"]

    # Default medication flags (not in Kaggle dataset — set to 0)
    for flag in ['med_anticoagulant', 'med_diabetic']:
        if flag not in df.columns:
            df[flag] = 0

    # Default GCS if missing (normal = 15)
    if 'gcs' not in df.columns:
        df['gcs'] = 15

    # Default pain_score if missing
    if 'pain_score' not in df.columns:
        df['pain_score'] = 5

    # Impute missing continuous values with median
    continuous_features = [f["name"] for f in FEATURE_VECTOR_SPEC if f["type"] == "continuous"]
    for col in continuous_features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())

    # Outlier capping (1st-99th percentile) for continuous features
    for col in continuous_features:
        if col in df.columns and df[col].dtype in ['int64', 'float64']:
            low = df[col].quantile(0.01)
            high = df[col].quantile(0.99)
            df[col] = df[col].clip(low, high)

    # Build feature matrix in CONTRACT ORDER
    print(f"\nBuilding feature matrix with {EXPECTED_FEATURE_COUNT} features (contract v{get_contract_hash()}):")
    X_data = []
    for spec in FEATURE_VECTOR_SPEC:
        name = spec["name"]
        if name in df.columns:
            X_data.append(df[name].values)
            print(f"  [OK] {name:25s} — {df[name].notna().sum():>6d} valid values")
        else:
            X_data.append(np.zeros(len(df)))
            print(f"  [DEFAULT] {name:21s} — filled with 0")

    X = np.column_stack(X_data)
    assert X.shape[1] == EXPECTED_FEATURE_COUNT, (
        f"Vector width {X.shape[1]} != contract {EXPECTED_FEATURE_COUNT}"
    )

    # Encode target
    le = LabelEncoder()
    y = le.fit_transform(df[target_col].values)

    print(f"\nTarget classes: {dict(zip(le.classes_, np.bincount(y)))}")
    return X, y, le


def apply_smote(X, y):
    """Apply SMOTE to balance classes."""
    print("\n" + "=" * 70)
    print("  SMOTE — CLASS BALANCING")
    print("=" * 70)
    before = dict(zip(*np.unique(y, return_counts=True)))
    print(f"Before: {before}")

    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X, y)

    after = dict(zip(*np.unique(y_res, return_counts=True)))
    print(f"After:  {after}")
    return X_res, y_res


def tune_hyperparameters(X_train, y_train, n_trials=30):
    """Bayesian hyperparameter search with Optuna."""
    print("\n" + "=" * 70)
    print("  HYPERPARAMETER OPTIMISATION (Optuna)")
    print("=" * 70)

    def objective(trial):
        params = {
            'n_estimators':     trial.suggest_int('n_estimators', 100, 500),
            'max_depth':        trial.suggest_int('max_depth', 3, 10),
            'learning_rate':    trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample':        trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'reg_alpha':        trial.suggest_float('reg_alpha', 0.0, 1.0),
            'reg_lambda':       trial.suggest_float('reg_lambda', 0.0, 1.0),
            'eval_metric':      'mlogloss',
            'random_state':     42,
        }
        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('model', XGBClassifier(**params))
        ])
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring='f1_weighted', n_jobs=-1)
        return scores.mean()

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"\nBest F1 (weighted): {study.best_value:.4f}")
    print(f"Best params: {study.best_params}")
    return study.best_params


def train_evaluate(X_train, X_test, y_train, y_test, best_params, le, output_dir):
    """Train final pipeline + Random Forest baseline, evaluate, save plots."""
    print("\n" + "=" * 70)
    print("  TRAINING FINAL MODEL")
    print("=" * 70)

    # XGBoost pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', XGBClassifier(
            **best_params, eval_metric='mlogloss', random_state=42
        ))
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)

    n_classes = len(le.classes_)
    target_names = [f"ESI-{c}" for c in le.classes_]

    print("\n--- XGBoost Classification Report ---")
    report_dict = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    print(classification_report(y_test, y_pred, target_names=target_names))

    auc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='weighted')
    print(f"Weighted AUC-ROC: {auc:.4f}")

    # Calibration metrics
    from sklearn.metrics import brier_score_loss
    brier_scores = []
    for i in range(n_classes):
        yi = (y_test == i).astype(int)
        brier_scores.append(brier_score_loss(yi, y_prob[:, i]))
    avg_brier = np.mean(brier_scores)
    print(f"Average Brier Score (ovr): {avg_brier:.4f}")

    def expected_calibration_error(y_true, y_prob, n_bins=10):
        ece = 0.0
        for i in range(n_classes):
            prob = y_prob[:, i]
            labels = (y_true == i).astype(int)
            bin_edges = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_edges[:-1]
            bin_uppers = bin_edges[1:]
            for bl, bu in zip(bin_lowers, bin_uppers):
                in_bin = (prob > bl) & (prob <= bu)
                prop_in_bin = in_bin.mean()
                if prop_in_bin > 0:
                    avg_conf = prob[in_bin].mean()
                    avg_acc = labels[in_bin].mean()
                    ece += np.abs(avg_conf - avg_acc) * prop_in_bin
        return ece / n_classes

    ece = expected_calibration_error(y_test, y_prob)
    print(f"Expected Calibration Error: {ece:.4f}")

    # Random Forest baseline
    rf = Pipeline([
        ('scaler', StandardScaler()),
        ('model', RandomForestClassifier(n_estimators=200, random_state=42))
    ])
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_report = classification_report(y_test, rf_pred, target_names=target_names, output_dict=True)
    print(f"\n--- Baseline Comparison ---")
    print(f"Random Forest weighted F1: {rf_report['weighted avg']['f1-score']:.4f}")
    print(f"XGBoost      weighted F1: {report_dict['weighted avg']['f1-score']:.4f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=target_names, yticklabels=target_names)
    plt.title('TriageAI — XGBoost Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    cm_path = os.path.join(output_dir, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {cm_path}")

    return pipeline, auc, report_dict, avg_brier, ece


def generate_shap(pipeline, X_test, output_dir):
    """Generate and save SHAP summary plot."""
    print("\n" + "=" * 70)
    print("  SHAP EXPLAINABILITY")
    print("=" * 70)

    model = pipeline.named_steps['model']
    scaler = pipeline.named_steps['scaler']
    explainer = shap.TreeExplainer(model)

    n = min(200, len(X_test))
    X_scaled = scaler.transform(X_test[:n])
    shap_values = explainer.shap_values(X_scaled)

    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_scaled, feature_names=FEATURE_NAMES, show=False)
    plt.title('TriageAI — SHAP Feature Importance')
    plt.tight_layout()
    shap_path = os.path.join(output_dir, 'shap_summary.png')
    plt.savefig(shap_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {shap_path}")

    return explainer


def save_artifacts(pipeline, le, auc, report_dict, avg_brier, ece, output_dir):
    """Save all model artifacts + feature contract."""
    print("\n" + "=" * 70)
    print("  SAVING ARTIFACTS")
    print("=" * 70)

    os.makedirs(output_dir, exist_ok=True)

    joblib.dump(pipeline, os.path.join(output_dir, 'triage_pipeline.joblib'))
    joblib.dump(le, os.path.join(output_dir, 'label_encoder.joblib'))

    # Save feature contract (hash-stamped)
    contract_path = save_contract(output_dir)
    print(f"  Feature contract: {contract_path}  (hash={get_contract_hash()})")

    # Save categorical registry snapshot
    registry = {
        "chief_complaints": {k: v["category_index"] for k, v in CHIEF_COMPLAINT_REGISTRY.items()},
        "sex_codes": {k: v["category_index"] for k, v in SEX_CODES.items()},
    }
    reg_path = os.path.join(output_dir, 'categorical_registry.json')
    with open(reg_path, 'w') as f:
        json.dump(registry, f, indent=2)

    # Save metrics
    metrics = {
        "model_type": "XGBoost",
        "auc_roc": auc,
        "weighted_f1": report_dict['weighted avg']['f1-score'],
        "brier_score": avg_brier,
        "expected_calibration_error": ece,
        "feature_count": EXPECTED_FEATURE_COUNT,
        "feature_names": FEATURE_NAMES,
        "contract_hash": get_contract_hash(),
    }
    with open(os.path.join(output_dir, 'model_metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"  Pipeline:   triage_pipeline.joblib")
    print(f"  Encoder:    label_encoder.joblib")
    print(f"  Registry:   categorical_registry.json")
    print(f"  Metrics:    model_metrics.json")
    print("\n  TRAINING COMPLETE.")


def main():
    parser = argparse.ArgumentParser(description="TriageAI Model Training")
    parser.add_argument('--data', default='data/triage_data.csv', help='Path to CSV dataset')
    parser.add_argument('--output', default='backend/ml/artifacts', help='Output directory for model artifacts')
    parser.add_argument('--trials', type=int, default=30, help='Number of Optuna trials')
    args = parser.parse_args()

    # Optional MLflow tracking
    mlflow_available = False
    try:
        import mlflow
        import mlflow.sklearn
        mlflow_available = True
    except ImportError:
        print("  MLflow not installed — experiment tracking disabled")

    print("=" * 70)
    print("  TRIAGEAI — ML TRAINING PIPELINE")
    print(f"  Feature contract hash: {get_contract_hash()}")
    print(f"  Expected features:     {EXPECTED_FEATURE_COUNT}")
    print("=" * 70)

    os.makedirs(args.output, exist_ok=True)

    try:
        if mlflow_available:
            mlflow.set_experiment("TriageAI_Model_Training")
            try:
                mlflow.start_run(run_name=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            except Exception as mlflow_err:
                print(f"  MLflow start_run failed: {mlflow_err}. Continuing without tracking.")
                mlflow_available = False

        # 1. Load
        df = load_and_explore(args.data)

        # 2. Standardise column names
        df = standardise_columns(df)

        # 3. Preprocess (contract-aligned)
        target_col = 'esi_target' if 'esi_target' in df.columns else 'acuity'
        X, y, le = preprocess(df, target_col=target_col)

        # 4. Train/test split — SMOTE is applied ONLY to training data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        print(f"\nTrain: {len(X_train)}  |  Test: {len(X_test)}")

        # 5. SMOTE — balance training data ONLY (prevents data leakage)
        X_train, y_train = apply_smote(X_train, y_train)

        # 6. Hyperparameter tuning
        best_params = tune_hyperparameters(X_train, y_train, n_trials=args.trials)

        # 7. Train + evaluate
        pipeline, auc, report, avg_brier, ece = train_evaluate(
            X_train, X_test, y_train, y_test, best_params, le, args.output
        )

        # 8. SHAP
        generate_shap(pipeline, X_test, args.output)

        # 9. Save
        save_artifacts(pipeline, le, auc, report, avg_brier, ece, args.output)

        # 9b. Drift-detection baseline (training feature distribution)
        baseline_df = pd.DataFrame(X_train, columns=FEATURE_NAMES)
        baseline = build_baseline(baseline_df, FEATURE_NAMES)
        baseline_path = save_baseline(baseline, args.output)
        print(f"  Drift baseline: {baseline_path}")

        # 10. MLflow logging
        if mlflow_available:
            mlflow.log_params({
                'dataset': args.data,
                'n_trials': args.trials,
                'feature_count': EXPECTED_FEATURE_COUNT,
                'contract_hash': get_contract_hash(),
                **best_params
            })
            mlflow.log_metrics({
                'auc_roc': auc,
                'weighted_f1': report['weighted avg']['f1-score'],
                'brier_score': avg_brier,
                'expected_calibration_error': ece,
                'train_size': len(X_train),
                'test_size': len(X_test),
            })
            mlflow.sklearn.log_model(pipeline, "triage_pipeline")
            mlflow.log_artifacts(args.output, artifact_path="model_artifacts")
            mlflow.end_run()
            print("\n  MLflow run logged successfully.")

    except FileNotFoundError:
        print(f"\nERROR: Dataset '{args.data}' not found.")
        print("Download from: kaggle.com/datasets/maalona/hospital-triage-and-patient-history-data")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        if mlflow_available:
            mlflow.end_run(status='FAILED')


if __name__ == "__main__":
    main()
