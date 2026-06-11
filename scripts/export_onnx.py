"""
TriageAI — ONNX Export (optional model-serving optimization)
=============================================================
Converts the trained scikit-learn + XGBoost pipeline to ONNX for faster,
framework-independent inference in production (e.g. behind onnxruntime).

This is OPTIONAL tooling. The API runs fine on the joblib pipeline; ONNX is
an optimization for high-throughput deployments. The script degrades
gracefully if the conversion dependencies are not installed:

    pip install skl2onnx onnxmltools onnxruntime

Usage:
    python scripts/export_onnx.py
Produces backend/ml/artifacts/triage_pipeline.onnx on success.
"""
import os
import sys

import joblib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from ml.feature_contract import EXPECTED_FEATURE_COUNT  # noqa: E402

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'ml', 'artifacts')


def main():
    pipeline_path = os.path.join(ARTIFACTS_DIR, 'triage_pipeline.joblib')
    if not os.path.exists(pipeline_path):
        print("ERROR: trained pipeline not found. Train the model first.")
        return 2

    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        from onnxmltools.convert.xgboost.operator_converters.XGBoost import convert_xgboost  # noqa: F401
        import onnxmltools  # noqa: F401
    except ImportError:
        print("ONNX export dependencies not installed.")
        print("Install with: pip install skl2onnx onnxmltools onnxruntime")
        return 0

    pipeline = joblib.load(pipeline_path)
    initial_type = [('input', FloatTensorType([None, EXPECTED_FEATURE_COUNT]))]

    try:
        onnx_model = convert_sklearn(pipeline, initial_types=initial_type)
    except Exception as e:  # XGBoost inside a Pipeline may need custom registration
        print(f"Conversion failed: {e}")
        print("For XGBoost pipelines see onnxmltools XGBoost converter registration.")
        return 1

    out_path = os.path.join(ARTIFACTS_DIR, 'triage_pipeline.onnx')
    with open(out_path, 'wb') as f:
        f.write(onnx_model.SerializeToString())
    print(f"ONNX model written: {out_path}")

    # Smoke-test with onnxruntime if available.
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(out_path)
        dummy = np.zeros((1, EXPECTED_FEATURE_COUNT), dtype=np.float32)
        sess.run(None, {'input': dummy})
        print("onnxruntime smoke test passed.")
    except ImportError:
        print("onnxruntime not installed — skipped runtime smoke test.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
