# TriageAI

**A Machine Learning-Powered Clinical Decision Support System for Emergency Department Patient Triage**

Student: M.S.M.Sajidh | ID: CL/BSCSD/34/01 | Cardiff Metropolitan University | 2025–2026

---

## Architecture

```
┌─────────────────┐     HTTPS/REST      ┌──────────────────┐     SQL     ┌─────────────┐
│   React.js v18  │ ◄─────────────────► │   Flask API      │ ◄──────────►│ PostgreSQL  │
│   (Port 3000)   │                     │   (Port 5000)    │             │ (Port 5432) │
│                 │                     │                  │             │             │
│ - Patient Form  │                     │ - JWT Auth       │             │ - users     │
│ - SHAP Panel    │                     │ - ML Inference   │             │ - patients  │
│ - Queue         │                     │ - Audit Logging  │             │ - vitals    │
│ - Admin Panel   │                     │ - OWASP Headers  │             │ - triage    │
└─────────────────┘                     └──────────────────┘             │ - audit_log │
                                               │                         └─────────────┘
                                        ┌──────┴──────┐
                                        │  XGBoost    │
                                        │  Pipeline   │
                                        │  (joblib)   │
                                        └─────────────┘
```

## Quick Start

### Option A: Docker Compose (Recommended)
```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- API: http://localhost:5000
- Database: localhost:5432

### Option B: Manual Setup

**1. Backend**
```bash
conda create -n triageai python=3.11
conda activate triageai
cd backend
pip install -r requirements.txt
python app.py
```

**2. Frontend**
```bash
cd frontend
npm install
npm start
```

**3. Train ML Model**
```bash
# Place datasets in the data/ directory
python scripts/train_model.py --data data/triage_data.csv --output backend/ml/artifacts
```

## Testing

```bash
# Backend (pytest — 108 tests: API, units, enhancements, resilience)
python -m pytest tests/ --tb=short

# Frontend unit (Jest + React Testing Library — 10 tests)
cd frontend
npm test -- --watchAll=false

# Frontend E2E (Playwright — login → intake → predict → override)
#   requires the backend running on :5000 (python backend/app.py)
cd frontend
npm run test:e2e:install   # one-time browser download
npm run test:e2e
```

Backend suites: `test_api.py`, `test_unit.py`,
`test_enhancements.py` (data quality, batch, GDPR erasure, monitoring,
versioning, caching, DB constraints), `test_resilience.py` (expired/malformed
JWT, unloaded model, malformed JSON, integrity rollback).

## CI/CD

Push/PR to `main`/`develop` triggers GitHub Actions:

- **Backend:** lint (flake8 syntax) + `pytest` with coverage
- **Frontend:** `npm ci` → `npm test` → `npm run build`
- **E2E (non-blocking):** seeds DB, starts backend, runs Playwright auth specs

## Load Testing

JMeter (`jmeter/triageai_load_test.jmx`) and Locust (`scripts/locustfile.py`)
plans are provided — see `jmeter/README.md`. Inference cost is quantified by
`scripts/benchmark_inference.py` (batched inference is ~13× cheaper per record).

## Model Monitoring

```bash
# Build/refresh the training baseline (also auto-generated during training)
python scripts/check_drift.py --build-baseline --data data/triage_data_real.csv

# Check new production data for PSI drift
python scripts/check_drift.py --data data/recent_traffic.csv
```

Live drift + AI/clinician agreement are exposed (admin-only) at
`/api/v1/monitoring/drift` and `/api/v1/monitoring/performance`.

## Model Performance

Trained on **126,420 real triage records** (Kaggle Hospital Triage dataset).

| Metric                      | Hold-out Test | 5-Fold CV (mean ± std) |
| --------------------------- | ------------- | ---------------------- |
| AUC-ROC                     | **0.894**     | **0.861 ± 0.001**      |
| Weighted F1                 | **0.637**     | **0.576 ± 0.001**      |
| Precision                   | —             | 0.586 ± 0.001          |
| Recall                      | —             | 0.589 ± 0.001          |
| Brier Score                 | **0.093**     | —                      |
| Expected Calibration Error  | **0.015**     | —                      |

*External-validation via `notebooks/04_external_validation.py` (SMOTE → stratified 5-fold).*

## Key Design Decisions (Supervisor Feedback)

| Concern | Solution |
| --- | --- |
| Localization | i18n via Accept-Language header + locale JSON files (English only) |
| Categorical mapping | Deterministic integer registry in `clinical_standards.py` |
| Arbitrary terms | ICD-10 + SNOMED CT + LOINC codes for all clinical terminology |
| Pipeline vector mismatch | `feature_contract.py` with SHA-256 hash verification |
| Audit logs | INSERT-only, ON DELETE RESTRICT on all foreign keys |
| Product backlog | `PRODUCT_BACKLOG.md` — 49 items across 6 sprints |
| Data security | OWASP headers, CORS whitelist, input validation, JWT, rate limiting, HTTPS redirect |
| PHI access audit | Immutable `audit_log` with `log_phi_access()` (HIPAA §164.312(b)) |
| RBAC | `@require_roles('clinician','admin')` decorator on all PHI routes |
| FHIR R4 | Full FHIR R4 server with Patient, DiagnosticReport, Observation, Bundle, CapabilityStatement, LOINC codes |
| Encryption at rest | Fernet + MultiFernet key rotation (PBKDF2 with env-configurable salt) |
| CI/CD | GitHub Actions: backend pytest + flake8, frontend npm test + build, E2E |
| Standard clinical data | LOINC-coded vitals, ICD-10 chief complaints |
| Drift monitoring | PSI/JSD baseline + `/api/v1/monitoring/drift` (see `scripts/check_drift.py`) |
| Data quality | Schema/range/null/categorical gate in `ml/data_quality.py` |
| Batch prediction | `/api/v1/predict/batch` (≤100 records, vectorised, per-row validation) |
| API versioning | `/api/v1/*` with legacy `/api/*` alias kept for compatibility |
| Caching | `cache.py` — in-process TTL, optional Redis via `REDIS_URL` |
| Text token strategy | `normalize_complaint_text()` synonym map (`docs/TEXT_TOKEN_STRATEGY.md`) |
| GDPR erasure | `DELETE /api/v1/patient/<id>/erase` scrubs PII, keeps audit |
| DB integrity | CHECK constraints on vitals/age/ESI/audit (`a1b2c3d4e5f6` migration) |
| E2E tests | Playwright login → intake → predict → override (`frontend/e2e/`) |
| Serving optimization | Optional ONNX export (`scripts/export_onnx.py`) + benchmark |
| Usability metrics | ISO 9241-11 KPIs mapped to wireframes (`docs/USABILITY_METRICS.md`) |

## Project Structure

```
├── .github/workflows/ci.yml    # GitHub Actions: backend pytest + frontend build/test
├── docker-compose.yml          # Full stack deployment
├── requirements.txt            # Top-level Python dependencies
├── .env.example                # Environment variable template
├── data/                       # Datasets (gitignored — not committed)
│   ├── triage_data.csv         # Synthetic dev dataset
│   ├── triage_data_real.csv    # Prepared Kaggle dataset
│   └── 5v_cleandf.csv          # Raw Kaggle source
├── scripts/                    # Training, data prep, monitoring, load-test utilities
│   ├── train_model.py          # ML training pipeline (contract-aligned, MLflow-tracked)
│   ├── generate_dataset.py     # Synthetic dataset generator
│   ├── prepare_real_data.py    # Kaggle → feature-contract mapper
│   ├── check_dataset.py        # Dataset sanity checker
│   ├── check_drift.py          # Build baseline / detect PSI drift
│   ├── export_onnx.py          # Optional ONNX export
│   ├── benchmark_inference.py  # Inference latency benchmark
│   ├── locustfile.py           # Locust load test
│   ├── smoke_test_api.py       # Live-server API smoke test
│   ├── smoke_test_features.py  # Live-server feature smoke test
│   └── generate_proposal.js    # Proposal document generator (Node.js)
├── jmeter/                     # Load testing (JMeter plan + README)
├── notebooks/                  # EDA, fairness, evaluation, external validation
│   ├── 01_eda.py
│   ├── 02_fairness_eval.py
│   ├── 03_evaluation_report.py
│   └── 04_external_validation.py
├── docs/                       # Specs, UML, wireframes, UAT/SUS, deploy guide, compliance
│   ├── TRIAGEAI_SYSTEM_SPEC.md
│   ├── DEPLOY.md
│   ├── PRODUCT_BACKLOG.md
│   ├── SECURITY_COMPLIANCE.md
│   ├── TEXT_TOKEN_STRATEGY.md
│   ├── USABILITY_METRICS.md
│   ├── UPDATED_PROPOSAL.md
│   ├── wireframes.md
│   ├── uat_script.md
│   └── sus_questionnaire.md
├── tests/                      # Pytest suite (unit + API + enhancements + resilience)
│   ├── test_unit.py
│   ├── test_api.py
│   ├── test_enhancements.py
│   └── test_resilience.py
├── backend/
│   ├── app.py                  # Flask app factory (limiter, HTTPS, OWASP headers)
│   ├── config.py               # Centralised configuration (dev/test/prod)
│   ├── models.py               # SQLAlchemy models (LOINC/ICD-10 aligned)
│   ├── extensions.py           # Shared db/jwt/limiter instances
│   ├── encryption.py           # Fernet PII encryption (MultiFernet rotation)
│   ├── security.py             # RBAC decorator + PHI audit logging
│   ├── seed_db.py              # Demo data seeder
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── migrations/             # Alembic — flask db migrate/upgrade
│   ├── locales/                # i18n locale files (English only)
│   ├── cache.py                # TTL cache (in-process / optional Redis)
│   ├── ml/
│   │   ├── clinical_standards.py   # ICD-10, LOINC, SNOMED registry + text tokens
│   │   ├── feature_contract.py     # 13-feature contract + hash
│   │   ├── data_quality.py         # Schema/range/null/categorical validation
│   │   ├── monitoring.py           # PSI/JSD drift detection
│   │   └── artifacts/              # Model files + drift_baseline.json
│   └── routes/
│       ├── auth.py             # JWT authentication
│       ├── predict.py          # ML inference, batch, GDPR erasure + SHAP
│       ├── admin.py            # Admin panel APIs (RBAC + PHI audit)
│       ├── monitoring.py       # Drift + live-performance endpoints
│       └── fhir.py             # FHIR R4 server (Patient/DiagnosticReport/Observation/Bundle)
└── frontend/
    ├── package.json
    ├── playwright.config.js
    ├── Dockerfile
    ├── public/index.html
    ├── e2e/                    # Playwright E2E (auth + triage flow)
    └── src/
        ├── App.js
        ├── index.js
        ├── contexts/           # AuthContext, ThemeContext, ToastContext
        ├── components/         # Layout, Navbar, ProtectedRoute, ErrorBoundary
        └── pages/              # Login, Dashboard, PatientIntake, TriageResult,
                                # PatientQueue, PatientDetail, AdminPanel,
                                # ClinicianProfile, ShiftHandover, SystemSettings,
                                # SystemAbout, NotFound
```

## Dataset

- **Primary:** Kaggle Hospital Triage dataset (immediate access)
- **Secondary:** MIMIC-IV-ED via PhysioNet (requires credentialing)

## Disclaimer

This is a **research prototype** for academic purposes only. It is NOT a certified medical device and MUST NOT be used for real clinical decisions without regulatory approval.
