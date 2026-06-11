"""
TriageAI — Inference Benchmark
===============================
Measures single-record and batch inference latency for the joblib pipeline
(and the ONNX model if it has been exported). Useful for capacity planning
and for quantifying the benefit of the ONNX optimization.

Usage:
    python scripts/benchmark_inference.py --n 1000
"""
import argparse
import os
import sys
import time

import joblib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from ml.feature_contract import EXPECTED_FEATURE_COUNT  # noqa: E402

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'ml', 'artifacts')


def _bench(fn, n):
    start = time.perf_counter()
    for _ in range(n):
        fn()
    elapsed = time.perf_counter() - start
    return elapsed, (elapsed / n) * 1000  # total s, per-call ms


def main():
    parser = argparse.ArgumentParser(description="TriageAI inference benchmark")
    parser.add_argument('--n', type=int, default=1000, help='Number of iterations')
    args = parser.parse_args()

    pipeline_path = os.path.join(ARTIFACTS_DIR, 'triage_pipeline.joblib')
    if not os.path.exists(pipeline_path):
        print("ERROR: trained pipeline not found. Train the model first.")
        return 2

    pipeline = joblib.load(pipeline_path)
    rng = np.random.default_rng(42)
    single = rng.random((1, EXPECTED_FEATURE_COUNT)).astype(np.float32)
    batch = rng.random((100, EXPECTED_FEATURE_COUNT)).astype(np.float32)

    print("=" * 60)
    print("  TriageAI Inference Benchmark (joblib pipeline)")
    print("=" * 60)

    total, per = _bench(lambda: pipeline.predict_proba(single), args.n)
    print(f"  Single record : {per:.3f} ms/call  ({args.n} calls, {total:.2f}s)")

    n_batch = max(1, args.n // 100)
    total_b, per_b = _bench(lambda: pipeline.predict_proba(batch), n_batch)
    print(f"  Batch (100)   : {per_b:.3f} ms/batch ({per_b / 100:.4f} ms/record)")

    # Compare against ONNX if available.
    onnx_path = os.path.join(ARTIFACTS_DIR, 'triage_pipeline.onnx')
    if os.path.exists(onnx_path):
        try:
            import onnxruntime as ort
            sess = ort.InferenceSession(onnx_path)
            total_o, per_o = _bench(lambda: sess.run(None, {'input': single}), args.n)
            print(f"  ONNX single   : {per_o:.3f} ms/call")
        except ImportError:
            print("  ONNX model present but onnxruntime not installed.")
    else:
        print("  ONNX model not exported (run scripts/export_onnx.py).")

    return 0


if __name__ == '__main__':
    sys.exit(main())
