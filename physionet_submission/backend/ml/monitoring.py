"""
TriageAI — Model Monitoring & Drift Detection
==============================================
Detects when the distribution of incoming features (or the model's output
priorities) drifts away from the training baseline. Without this, a deployed
model silently degrades as the patient population, season, or data pipeline
changes.

Primary metric: Population Stability Index (PSI), the industry standard for
tabular drift. A complementary symmetric KL-divergence (Jensen-Shannon) is
also provided.

PSI interpretation (widely adopted convention):
    PSI < 0.10            -> no significant drift
    0.10 <= PSI < 0.25    -> moderate drift (investigate)
    PSI >= 0.25           -> significant drift (retrain / alert)

Workflow:
    1. After training, call build_baseline(df, features) and persist it as
       drift_baseline.json next to the model artifacts.
    2. In production, periodically call detect_drift(baseline, current_df)
       (via scripts/check_drift.py or the /api/v1/monitoring/drift endpoint)
       to compare recent traffic against the baseline.
"""
from __future__ import annotations

import json
import os
import numpy as np

# PSI thresholds
PSI_NO_DRIFT = 0.10
PSI_MODERATE = 0.25

DEFAULT_BINS = 10
_EPS = 1e-6  # avoids div-by-zero / log(0)


def _bin_edges(values, bins=DEFAULT_BINS):
    """Quantile-based bin edges from the baseline distribution."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if values.size == 0:
        return np.array([0.0, 1.0])
    # Quantile edges; fall back to linear if the feature is near-constant.
    quantiles = np.linspace(0, 1, bins + 1)
    edges = np.unique(np.quantile(values, quantiles))
    if edges.size < 2:
        edges = np.array([values.min() - _EPS, values.max() + _EPS])
    return edges


def _proportions(values, edges):
    """Fraction of values falling into each bin defined by `edges`."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    counts, _ = np.histogram(values, bins=edges)
    total = counts.sum()
    if total == 0:
        return np.full(len(counts), _EPS)
    props = counts / total
    return np.clip(props, _EPS, None)


def population_stability_index(expected_props, actual_props):
    """
    PSI = sum( (actual - expected) * ln(actual / expected) ).
    Both inputs are arrays of bin proportions that sum (approximately) to 1.
    """
    expected = np.clip(np.asarray(expected_props, dtype=float), _EPS, None)
    actual = np.clip(np.asarray(actual_props, dtype=float), _EPS, None)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


def jensen_shannon_divergence(expected_props, actual_props):
    """Symmetric, bounded [0, ln2] divergence — complements PSI."""
    p = np.clip(np.asarray(expected_props, dtype=float), _EPS, None)
    q = np.clip(np.asarray(actual_props, dtype=float), _EPS, None)
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    return float(0.5 * kl_pm + 0.5 * kl_qm)


def classify_psi(psi):
    """Map a PSI value to a human-readable drift severity."""
    if psi < PSI_NO_DRIFT:
        return "none"
    if psi < PSI_MODERATE:
        return "moderate"
    return "significant"


def build_baseline(df, features, bins=DEFAULT_BINS):
    """
    Build a drift baseline from a training DataFrame.

    Returns a JSON-serialisable dict mapping each feature to its bin edges
    and expected proportions, plus summary statistics for reference.
    """
    baseline = {"bins": bins, "n_rows": int(len(df)), "features": {}}
    for feat in features:
        if feat not in df.columns:
            continue
        values = df[feat].to_numpy(dtype=float)
        edges = _bin_edges(values, bins=bins)
        props = _proportions(values, edges)
        baseline["features"][feat] = {
            "edges": edges.tolist(),
            "expected_props": props.tolist(),
            "mean": float(np.nanmean(values)) if values.size else 0.0,
            "std": float(np.nanstd(values)) if values.size else 0.0,
        }
    return baseline


def detect_drift(baseline, current_df):
    """
    Compare a current DataFrame against a persisted baseline.

    Returns:
        {
          "overall_drift": "none|moderate|significant",
          "max_psi": float,
          "n_current": int,
          "features": {feat: {"psi": float, "jsd": float, "severity": str}},
        }
    """
    results = {}
    max_psi = 0.0
    for feat, spec in baseline.get("features", {}).items():
        if feat not in current_df.columns:
            continue
        edges = np.asarray(spec["edges"], dtype=float)
        expected = np.asarray(spec["expected_props"], dtype=float)
        actual = _proportions(current_df[feat].to_numpy(dtype=float), edges)
        psi = population_stability_index(expected, actual)
        jsd = jensen_shannon_divergence(expected, actual)
        results[feat] = {
            "psi": round(psi, 4),
            "jsd": round(jsd, 4),
            "severity": classify_psi(psi),
        }
        max_psi = max(max_psi, psi)

    return {
        "overall_drift": classify_psi(max_psi),
        "max_psi": round(max_psi, 4),
        "n_current": int(len(current_df)),
        "features": results,
    }


def save_baseline(baseline, output_dir):
    """Persist the baseline next to the model artifacts."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "drift_baseline.json")
    with open(path, "w") as f:
        json.dump(baseline, f, indent=2)
    return path


def load_baseline(artifacts_dir):
    """Load a persisted baseline, or return None if not present."""
    path = os.path.join(artifacts_dir, "drift_baseline.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)
