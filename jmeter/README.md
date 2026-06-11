# TriageAI — Load Testing

Two complementary load-testing tools are provided:

| Tool | File | Best for |
| --- | --- | --- |
| **JMeter** | `jmeter/triageai_load_test.jmx` | GUI-driven, detailed reports, CI artifacts |
| **Locust** | `scripts/locustfile.py` | Python-native, quick local runs, scripting |

---

## 1. Prerequisites

Start the backend (and ideally a production-like DB):

```bash
# from project root
$env:FLASK_ENV = "development"
python backend/app.py        # serves on http://localhost:5000
```

Ensure a clinician account exists (the seeder creates `clinician`/`Clinician123!`):

```bash
python backend/seed_db.py
```

---

## 2. JMeter

```bash
# GUI (authoring)
jmeter -t jmeter/triageai_load_test.jmx

# Headless (CI / reproducible runs)
jmeter -n -t jmeter/triageai_load_test.jmx \
       -l results.jtl -e -o report/
```

The plan exercises `/api/auth/login` then loops `/api/predict` and
`/api/queue` under a configurable thread group.

---

## 3. Locust

```bash
pip install locust

# Headless: 50 concurrent users, spawn 5/s, run for 1 minute
locust -f scripts/locustfile.py --headless -u 50 -r 5 -t 1m \
       --host http://localhost:5000

# Interactive web UI
locust -f scripts/locustfile.py --host http://localhost:5000
# then open http://localhost:8089
```

Task mix (weights): `/api/predict` (3), `/api/queue` (2),
`/api/predict/batch` (1), `/api/clinical-standards` (1).

---

## 4. Target SLOs

| Metric | Target |
| --- | --- |
| p95 latency `/api/predict` | < 500 ms |
| p95 latency `/api/predict/batch` (10 records) | < 1500 ms |
| Error rate | < 1% |
| Throughput | ≥ 50 req/s on a single instance |

Single-record vs. batched inference cost is quantified by
`scripts/benchmark_inference.py` (batching is ~13× cheaper per record).

---

## 5. CI note

Load tests are **not** run on every PR (they need a live server and are
time-consuming). Run them before releases or after performance-sensitive
changes. The functional smoke tests in `tests/` cover correctness in CI.
