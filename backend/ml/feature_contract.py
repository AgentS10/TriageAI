"""
TriageAI Feature Contract
==========================
Defines the EXACT ordered feature vector expected by the ML pipeline.
This contract is enforced at both:
  1. Training time  — train_model.py reads this to build X
  2. Inference time — predict.py reads this to build the input vector

If the contract changes (e.g. a feature is added/removed), the model
MUST be retrained. The contract is version-stamped and serialised
alongside the model artifacts to detect drift.

This eliminates "silent pipeline vector mismatches" where the training
and inference pipelines silently disagree on feature order or count.
"""
import json
import os
import hashlib
from datetime import datetime

# ────────────────────────────────────────────────────────────────────
# FEATURE CONTRACT v1.0
# The EXACT ordered list of features the model expects.
# Changing this list invalidates all existing model artifacts.
# ────────────────────────────────────────────────────────────────────
FEATURE_VECTOR_SPEC = [
    # Continuous vital signs (scaled by StandardScaler in pipeline)
    {"name": "heart_rate",        "type": "continuous", "source": "vitals",  "nullable": False},
    {"name": "sbp",               "type": "continuous", "source": "vitals",  "nullable": False},
    {"name": "dbp",               "type": "continuous", "source": "vitals",  "nullable": False},
    {"name": "respiratory_rate",  "type": "continuous", "source": "vitals",  "nullable": False},
    {"name": "spo2",              "type": "continuous", "source": "vitals",  "nullable": False},
    {"name": "temperature",       "type": "continuous", "source": "vitals",  "nullable": False},
    {"name": "gcs",               "type": "continuous", "source": "vitals",  "nullable": False},

    # Patient demographics (continuous)
    {"name": "age",               "type": "continuous", "source": "patient", "nullable": False},
    {"name": "pain_score",        "type": "continuous", "source": "patient", "nullable": False},

    # Categorical features (integer-encoded via clinical_standards registry)
    {"name": "chief_complaint_code", "type": "categorical_int", "source": "patient", "nullable": False},
    {"name": "sex_code",             "type": "categorical_int", "source": "patient", "nullable": False},

    # Binary medication flags
    {"name": "med_anticoagulant", "type": "binary", "source": "patient", "nullable": False},
    {"name": "med_diabetic",      "type": "binary", "source": "patient", "nullable": False},
]

CONTRACT_VERSION = "1.0.0"
EXPECTED_FEATURE_COUNT = len(FEATURE_VECTOR_SPEC)
FEATURE_NAMES = [f["name"] for f in FEATURE_VECTOR_SPEC]


def get_contract_hash():
    """Generate a SHA-256 hash of the feature contract for integrity checking."""
    contract_str = json.dumps(FEATURE_VECTOR_SPEC, sort_keys=True)
    return hashlib.sha256(contract_str.encode()).hexdigest()[:16]


def build_feature_vector(patient_data, vitals_data):
    """
    Build a feature vector from patient + vitals data dictionaries.
    Returns a list in the EXACT order defined by FEATURE_VECTOR_SPEC.
    Raises ValueError if any required feature is missing.
    """
    from ml.clinical_standards import get_complaint_index, get_sex_index

    vector = []
    for spec in FEATURE_VECTOR_SPEC:
        name = spec["name"]
        source = spec["source"]

        if source == "vitals":
            value = vitals_data.get(name)
        elif source == "patient":
            if name == "chief_complaint_code":
                raw = patient_data.get("chief_complaint", "other")
                value = get_complaint_index(raw)
            elif name == "sex_code":
                raw = patient_data.get("sex", "U")
                value = get_sex_index(raw)
            elif name == "med_anticoagulant":
                flags = patient_data.get("medication_flags", {})
                value = 1 if flags.get("anticoagulant", False) else 0
            elif name == "med_diabetic":
                flags = patient_data.get("medication_flags", {})
                value = 1 if flags.get("diabetic", False) else 0
            else:
                value = patient_data.get(name)
        else:
            value = None

        if value is None and not spec["nullable"]:
            raise ValueError(f"Missing required feature: {name} (source: {source})")

        vector.append(float(value) if value is not None else 0.0)

    if len(vector) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Feature vector length mismatch: got {len(vector)}, "
            f"expected {EXPECTED_FEATURE_COUNT}. "
            f"Contract hash: {get_contract_hash()}"
        )

    return vector


def save_contract(output_dir):
    """Save the feature contract as a JSON file alongside model artifacts."""
    contract = {
        "version": CONTRACT_VERSION,
        "hash": get_contract_hash(),
        "created_at": datetime.utcnow().isoformat(),
        "feature_count": EXPECTED_FEATURE_COUNT,
        "features": FEATURE_VECTOR_SPEC,
        "feature_names": FEATURE_NAMES,
    }
    path = os.path.join(output_dir, "feature_contract.json")
    with open(path, "w") as f:
        json.dump(contract, f, indent=2)
    return path


def validate_contract_against_model(contract_path):
    """
    Check that the current code contract matches the saved contract
    that was used to train the model. Raises if they differ.
    """
    if not os.path.exists(contract_path):
        raise FileNotFoundError(f"Feature contract not found at {contract_path}")

    with open(contract_path, "r") as f:
        saved = json.load(f)

    saved_hash = saved.get("hash")
    current_hash = get_contract_hash()

    if saved_hash != current_hash:
        raise RuntimeError(
            f"FEATURE CONTRACT MISMATCH detected!\n"
            f"  Saved contract hash:   {saved_hash}\n"
            f"  Current contract hash: {current_hash}\n"
            f"The model was trained with a different feature set. "
            f"Retrain the model or revert the contract change."
        )
    return True
