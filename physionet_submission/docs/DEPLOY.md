# TriageAI Deployment Guide

> **Student:** M.S.M.Sajidh (CL/BSCSD/34/01)  
> **Institution:** Cardiff Metropolitan University  
> **Project:** TriageAI — Clinical Decision Support System for Emergency Department Triage

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Flask backend |
| Node.js | 18+ | React frontend |
| Docker Desktop | 4.0+ | Containerised deployment |
| Git | 2.30+ | Version control |

## Quick Start (Development)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd triageai
```

### 2. Backend

```bash
cd backend
python -m venv ../triageai_venv
. ../triageai_venv/Scripts/activate  # Windows
# source ../triageai_venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`.

### 3. Frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`.

### 4. Database (SQLite — Development)

The SQLite database `triageai_dev.db` is auto-created on first run.
Default seeded accounts:

| Username | Password | Role |
|----------|----------|------|
| admin | Admin123! | admin |
| nurse_amara | Nurse123! | clinician |
| dr_kemal | Doctor123! | clinician |

### 5. ML Model

Model artifacts must be present in `backend/ml/artifacts/`:
- `triage_pipeline.joblib` — trained XGBoost pipeline
- `feature_contract.json` — 13-feature contract with SHA-256 hash
- `label_encoder.joblib` — ESI level encoder
- `categorical_registry.json` — deterministic mappings
- `model_metrics.json` — performance metrics
- `shap_summary.png` — global explainability plot

If missing, train the model:

```bash
# From project root
python prepare_real_data.py
python train_model.py --data triage_data_real.csv --output backend/ml/artifacts --trials 20
```

## Docker Compose (Production-like)

```bash
docker-compose up --build
```

This starts three services:
- **PostgreSQL** on port 5432
- **Flask API** on port 5000
- **React Frontend** on port 3000

## Testing

```bash
# Unit + Integration tests with coverage
python -m pytest tests/ -v --cov=backend --cov-report=term-missing

# Performance test (requires Apache JMeter)
# 1. Download JMeter from https://jmeter.apache.org/
# 2. Open jmeter/triageai_load_test.jmx
# 3. Run with 10 threads, 20 loops
# 4. Check 95th percentile in Aggregate Report
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | development / testing / production |
| `JWT_SECRET_KEY` | (required in prod) | 64+ character secret for token signing |
| `DATABASE_URL` | `sqlite:///triageai_dev.db` | PostgreSQL in production |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

## Security Checklist

- [ ] Change default `JWT_SECRET_KEY` in production
- [ ] Use HTTPS with valid SSL certificate
- [ ] Restrict `CORS_ORIGINS` to deployed domain
- [ ] Enable `SESSION_COOKIE_SECURE` in production config
- [ ] Run OWASP ZAP scan on all endpoints
- [ ] Review rate limit settings per deployment scale

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "Feature contract not found" | Model not trained | Run `train_model.py` first |
| "Model loading failed" | Python/shap version mismatch | Use exact versions in `requirements.txt` |
| "Port 5000 in use" | Another Flask instance running | `taskkill /F /IM python.exe` (Windows) |
| "CORS error" | Frontend origin not whitelisted | Add origin to `CORS_ORIGINS` env var |
| "npm run build fails" | Node modules outdated | `rm -rf node_modules && npm install` |

## Architecture Diagram

```
+-----------+      HTTP/JSON       +-------------------+      SQLAlchemy      +----------+
|  React    | <-------------------> |   Flask Backend   | <-------------------> |  SQLite  |
|  Frontend |    (CORS whitelist)   |   (Port 5000)     |    (dev) / PG (prod)  |  / PG    |
+-----------+                     +-------------------+                       +----------+
                                         |     |     |
                                         v     v     v
                                   +-----------+-----------+-----------+
                                   |  JWT Auth |  ML Model | Audit Log |
                                   |  + RBAC  |  + SHAP   |  (Immutable)
                                   +-----------+-----------+-----------+
```

## Contact

For issues with deployment, contact:  
M.S.M.Sajidh — CL/BSCSD/34/01  
Cardiff School of Technologies, Cardiff Metropolitan University
