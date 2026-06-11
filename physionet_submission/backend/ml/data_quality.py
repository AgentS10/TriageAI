"""
TriageAI — Data Quality Validation
===================================
Automated quality gates for data entering the system, whether through the
prediction API (single / batch) or the training pipeline (CSV).

Goes beyond the feature-contract hash check by verifying that VALUES are
clinically plausible, complete, and correctly typed before they reach the
model. This protects against silent data corruption, schema drift, and
out-of-range inputs that would otherwise produce garbage predictions.

Checks performed:
  1. Schema      — all required fields present (no missing columns)
  2. Type        — values coerce to the expected numeric/string type
  3. Range       — vitals / pain / age within clinically valid bounds
  4. Categorical — chief_complaint / sex are registered codes
  5. Nullness    — per-field null rate stays under a configurable threshold

Each check returns a structured result so callers can surface actionable
errors (single record) or quality reports (batch / training dataset).
"""
from __future__ import annotations

from ml.clinical_standards import (
    VITAL_SIGN_STANDARDS,
    CHIEF_COMPLAINT_REGISTRY,
    SEX_CODES,
)

# Required fields for a single triage record (matches the feature contract).
REQUIRED_PATIENT_FIELDS = ["age", "sex", "chief_complaint", "pain_score"]
REQUIRED_VITAL_FIELDS = [
    "heart_rate", "sbp", "dbp", "respiratory_rate", "spo2", "temperature", "gcs",
]

# Age is not in VITAL_SIGN_STANDARDS; define its plausible bounds here.
AGE_RANGE = {"min": 0, "max": 120}

# Default maximum acceptable per-column null rate for batch / dataset checks.
DEFAULT_MAX_NULL_RATE = 0.05


class DataQualityError(ValueError):
    """Raised when a record fails a hard data-quality gate."""


def _check_range(field, value):
    """Return an error string if value is outside the clinical range, else None."""
    if field == "age":
        lo, hi = AGE_RANGE["min"], AGE_RANGE["max"]
        unit = "years"
    else:
        std = VITAL_SIGN_STANDARDS.get(field)
        if std is None:
            return None  # not a range-checked field
        lo, hi, unit = std["min"], std["max"], std["unit"]
    try:
        v = float(value)
    except (TypeError, ValueError):
        return f"{field} must be numeric (got {value!r})"
    if v < lo or v > hi:
        return f"{field} out of range: {v} not in [{lo}, {hi}] {unit}"
    return None


def validate_record(patient_data, vitals_data):
    """
    Validate a single triage record (patient + vitals dictionaries).

    Returns a dict: {"valid": bool, "errors": [str, ...]}.
    Does not raise — callers decide whether to reject or collect errors.
    """
    errors = []

    # 1. Schema — required fields present
    for field in REQUIRED_PATIENT_FIELDS:
        if field not in patient_data or patient_data[field] is None:
            errors.append(f"Missing patient field: {field}")
    for field in REQUIRED_VITAL_FIELDS:
        if field not in vitals_data or vitals_data[field] is None:
            errors.append(f"Missing vital sign: {field}")

    # 4. Categorical validity
    cc = patient_data.get("chief_complaint")
    if cc is not None and cc not in CHIEF_COMPLAINT_REGISTRY:
        errors.append(f"Invalid chief_complaint code: {cc}")
    sex = patient_data.get("sex")
    if sex is not None and sex not in SEX_CODES:
        errors.append(f"Invalid sex code: {sex}")

    # 2 + 3. Type + range for numeric fields
    if patient_data.get("age") is not None:
        err = _check_range("age", patient_data["age"])
        if err:
            errors.append(err)
    if patient_data.get("pain_score") is not None:
        err = _check_range("pain_score", patient_data["pain_score"])
        if err:
            errors.append(err)
    for field in REQUIRED_VITAL_FIELDS:
        if vitals_data.get(field) is not None:
            err = _check_range(field, vitals_data[field])
            if err:
                errors.append(err)

    return {"valid": len(errors) == 0, "errors": errors}


def validate_dataframe(df, max_null_rate=DEFAULT_MAX_NULL_RATE):
    """
    Validate a pandas DataFrame (used by the training pipeline and batch
    ingestion of CSVs). Returns a structured quality report.

    The report contains:
      - schema_ok            : all expected columns present
      - missing_columns      : list of expected columns that are absent
      - null_rates           : {column: rate} for columns exceeding threshold
      - range_violations     : {column: count} of out-of-range values
      - invalid_categoricals : {column: count} of unregistered codes
      - n_rows               : total rows
      - passed               : overall pass/fail
    """
    import pandas as pd  # local import keeps API-only paths lightweight

    report = {
        "n_rows": int(len(df)),
        "schema_ok": True,
        "missing_columns": [],
        "null_rates": {},
        "range_violations": {},
        "invalid_categoricals": {},
        "passed": True,
    }

    # Expected columns (dataset uses 'acuity' or 'esi_target' for the label,
    # which we do not require here — only the feature columns).
    expected = REQUIRED_PATIENT_FIELDS + REQUIRED_VITAL_FIELDS
    for col in expected:
        if col not in df.columns:
            report["missing_columns"].append(col)
    if report["missing_columns"]:
        report["schema_ok"] = False
        report["passed"] = False

    # Null-rate check (only for present columns)
    for col in [c for c in expected if c in df.columns]:
        rate = float(df[col].isna().mean())
        if rate > max_null_rate:
            report["null_rates"][col] = round(rate, 4)
            report["passed"] = False

    # Range checks for numeric fields
    range_fields = REQUIRED_VITAL_FIELDS + ["age", "pain_score"]
    for col in [c for c in range_fields if c in df.columns]:
        if col == "age":
            lo, hi = AGE_RANGE["min"], AGE_RANGE["max"]
        else:
            std = VITAL_SIGN_STANDARDS.get(col)
            if std is None:
                continue
            lo, hi = std["min"], std["max"]
        numeric = pd.to_numeric(df[col], errors="coerce")
        violations = int(((numeric < lo) | (numeric > hi)).sum())
        if violations > 0:
            report["range_violations"][col] = violations
            report["passed"] = False

    # Categorical checks
    if "chief_complaint" in df.columns:
        invalid = int((~df["chief_complaint"].isin(CHIEF_COMPLAINT_REGISTRY)).sum())
        if invalid > 0:
            report["invalid_categoricals"]["chief_complaint"] = invalid
            report["passed"] = False
    if "sex" in df.columns:
        invalid = int((~df["sex"].isin(SEX_CODES)).sum())
        if invalid > 0:
            report["invalid_categoricals"]["sex"] = invalid
            report["passed"] = False

    return report
