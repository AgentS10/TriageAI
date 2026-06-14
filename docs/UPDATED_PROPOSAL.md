# UPDATED FINAL YEAR PROJECT PROPOSAL

## TriageAI: A Machine Learning-Powered Clinical Decision Support System for Emergency Department Patient Triage

**Student:** M.S.M. Sajidh | **Student ID:** CL/BSCSD/34/01  
**Module:** CIS6002 Software Engineering Dissertation Project | **Academic Year:** 2025 / 2026  
**Last Updated:** 11 June 2026

---

## Executive Summary of Changes

This updated proposal reflects significant progress since initial submission:
- **Dual-dataset strategy:** Kaggle Hospital Triage Data (development) + MIMIC-IV-ED (external validation pending PhysioNet credentialing)
- **CITI training completed:** "Data or Specimens Only Research" (92%) and "Conflicts of Interest" (100%)
- **PhysioNet project submitted:** Software resource, MIT License, 11 June 2026
- **GitHub repository published:** https://github.com/Agent510/TriageAI
- **Security audit completed:** Grade A — all identified issues resolved (SMOTE data leakage, input validation, random passwords, MLflow timeout, rate limiting)
- **Feature contract implemented:** Deterministic 13-feature vector with SHA-256 integrity checking

---

## 1. Title

TriageAI: A Machine Learning-Powered Clinical Decision Support System for Emergency Department Patient Triage

---

## 2. Introduction

### 2.1 Background and Context

Emergency departments globally face escalating pressure from rising patient volumes, ageing populations, and constrained clinical resources. Current triage systems (MTS, ESI) are manual, subjective, and dependent on individual clinician expertise — introducing inter-rater variability, cognitive bias, and systematic underutilisation of EHR data. With AI/ML proven on large-scale clinical datasets, there is a compelling opportunity to augment triage decision-making in real time, subject to EU AI Act high-risk AI requirements for transparency, explainability, and human oversight.

### 2.2 Proposed Solution — Overview

**TriageAI** is a full-stack web application embedding a self-developed XGBoost classification model:
- **Frontend:** React.js SPA with structured patient intake, SHAP explainability panel, and active queue dashboard
- **Backend:** Python Flask REST API with JWT authentication, ML inference endpoint (≤500ms latency), and immutable audit logging
- **Database:** PostgreSQL 15 with ACID-compliant audit trail
- **ML Pipeline:** XGBoost with scikit-learn Pipeline, Optuna hyperparameter tuning, MLflow tracking, and SHAP explanations
- **Deployment:** Docker Compose single-command deployment
- **Open Source:** MIT License, GitHub: https://github.com/Agent510/TriageAI
- **PhysioNet:** Submitted as Software resource (11 June 2026)

**Datasets:**
- **Development/Internal Validation:** Kaggle Hospital Triage Data (immediately available, no credentialing)
- **External Validation (Pending):** MIMIC-IV-ED v2.2 via PhysioNet (credentialing in progress)

### 2.3 SMART Objectives

1. Train and validate XGBoost model achieving ≥85% accuracy and ≥90% recall for ESI Levels 1–2 *(achieved on Kaggle dataset; MIMIC-IV-ED validation pending)*
2. Develop Flask REST API with ≤500ms inference latency *(verified via JMeter benchmarking)*
3. Implement React.js dashboard with RBAC and zero critical defects *(integration testing complete)*
4. Conduct fairness evaluation with demographic parity within ±5% *(pending MIMIC-IV-ED demographic data)*
5. Produce complete technical documentation and dissertation *(in progress)*

### 2.4 Research Questions

**Primary:** To what extent can a self-developed XGBoost model embedded in a full-stack web application accurately and fairly classify five-level ED triage priority?

**Secondary:**
- Which intake features are most predictive of triage classification?
- How does SHAP explainability affect clinician trust in AI recommendations?
- To what extent does post-split SMOTE improve high-acuity recall vs baseline?
- How does the model perform across demographic subgroups?

---

## 3. Current Situation and Problem Identification

### 3.1 Triage Inconsistency
Garbez et al. (2011) identified nurse experience, communication barriers, and decision fatigue as primary contributors, with 20–35% of ED patients incorrectly categorised.

### 3.2 Data Underutilisation
Structured EHR data (vitals, GCS, medication history) remains systematically unexploited in real-time triage decisions.

### 3.3 Absence of Open-Source Solutions
Fernandes et al. (2020) found no open-source, end-to-end AI triage system for practical deployment. **TriageAI addresses this gap** — fully open-source with Docker Compose deployment.

### 3.4 Algorithmic Bias
Obermeyer et al. (2019) demonstrated that clinical algorithms can perpetuate demographic biases. Fairness evaluation is a **design requirement**, not optional.

### 3.5 Ethical and Regulatory Context
EU AI Act (high-risk AI), HIPAA, GDPR, and Floridi et al.'s AI4People framework inform TriageAI's architecture:
- FHIR R4 interoperability
- LOINC-coded vitals
- ICD-10 chief complaints
- Immutable audit logging
- GDPR data erasure
- SHAP explainability for transparency

---

## 4. Proposed Technique

### 4.1 Self-Developed AI/ML Model

#### 4.1.1 Datasets

**Development:** Kaggle Hospital Triage and Patient History Data — publicly available, de-identified, no credentialing required.

**External Validation (Pending):** MIMIC-IV-ED v2.2 (Johnson et al., 2023) — 425,000+ ED visits. Access requirements:
- ✅ CITI "Data or Specimens Only Research" — 92% (11 June 2026)
- ✅ CITI "Conflicts of Interest" — 100% (11 June 2026)
- ✅ PhysioNet project submitted (11 June 2026)
- ⏳ Credentialing approval (3–7 business days)
- ⏳ Data Use Agreement signature

#### 4.1.2 Data Preparation

- Missing value imputation (median/mode)
- Outlier capping at 1st/99th percentiles
- **SMOTE applied AFTER train_test_split() — ONLY to training fold** *(post-audit fix)*
- Feature scaling via StandardScaler in scikit-learn Pipeline
- Deterministic feature contract with SHA-256 hash verification

> **Audit Fix:** SMOTE was originally applied before `train_test_split()`, causing data leakage. Identified in comprehensive security/quality audit and corrected. Test set now remains untouched.

#### 4.1.3 Feature Contract (13 Features)

| # | Feature | Type |
|---|---------|------|
| 1 | age | continuous |
| 2 | heart_rate | continuous |
| 3 | sbp | continuous |
| 4 | dbp | continuous |
| 5 | respiratory_rate | continuous |
| 6 | spo2 | continuous |
| 7 | temperature | continuous |
| 8 | gcs | continuous |
| 9 | pain_score | continuous (0–10) |
| 10 | chief_complaint | categorical |
| 11 | arrival_mode | categorical |
| 12 | has_medication | binary |
| 13 | previous_attendance | binary |

Target: five-level ESI acuity (1–5)

#### 4.1.4 Model Architecture

**XGBoost** selected for:
- Structured tabular data (CNN/RNN architecturally inappropriate)
- Native missing value handling
- L1/L2 regularisation
- SHAP compatibility
- Fast CPU training

**Pipeline:**
- Baseline: Random Forest comparison
- Optimisation: Optuna Bayesian search
- Tracking: MLflow with graceful degradation (continues training if MLflow server unreachable)
- Serialisation: joblib for reproducible inference

### 4.2 System Architecture

```
┌─────────────────┐     HTTPS REST      ┌─────────────────┐     SQL      ┌─────────────┐
│  React.js v18   │ ◄──────────────────► │  Flask REST API │ ◄──────────► │ PostgreSQL  │
│   (Frontend)    │       (Axios)        │   (Backend)     │  (SQLAlchemy)│  (Database) │
└─────────────────┘                      └─────────────────┘              └─────────────┘
                                                │
                                                │ joblib Pipeline
                                                ▼
                                        ┌─────────────────┐
                                        │  XGBoost Model  │
                                        │  + SHAP + Optuna│
                                        └─────────────────┘
```

**Deployment:** Docker Compose (flask-api, react-frontend, postgres-db)

### 4.3 Technology Stack

| Technology | Role | Justification |
|------------|------|---------------|
| Python 3.11 + scikit-learn | ML Pipeline | Industry standard; reproducible Pipeline |
| XGBoost 2.0 | Classification | Best-in-class tabular; SHAP-compatible; CPU-trainable |
| SHAP | Explainability | EU AI Act transparency; global + local explanations |
| Optuna + MLflow | Tuning / Tracking | Bayesian search; graceful error handling |
| Flask + Flask-JWT-Extended | REST API / Auth | Lightweight; stateless JWT; role-based access |
| React.js v18 | Frontend | Component-based; Recharts for SHAP viz |
| PostgreSQL 15 | Database | ACID audit log integrity |
| Docker Compose | Deployment | Single-command; platform-independent |
| Flask-Limiter | Rate Limiting | DoS protection on health endpoints |
| Fernet | Encryption | HIPAA-compliant at-rest encryption |

### 4.4 Security and Quality Hardening

Following comprehensive audit (documented in `AUDIT_REPORT.md`, Grade A):

| Issue | Fix |
|-------|-----|
| **SMOTE data leakage** | Moved `train_test_split()` before `apply_smote()` — SMOTE only on training fold |
| **Missing input validation** | Added `try/except` around vital sign `float()` — returns 400 error |
| **Missing `datetime` import** | Added `from datetime import datetime` |
| **Hardcoded credentials** | Replaced with `secrets.choice()` 14-char random passwords + warnings |
| **MLflow hang** | Nested `try/except` around `mlflow.start_run()` — graceful fallback |
| **No health rate limiting** | Added `@limiter.limit()` decorators (60/min and 30/min) |

---

## 5. Feasibility

### 5.1 Technical
All technologies open-source and documented. Kaggle dataset immediately available. XGBoost trains on 8GB RAM laptop without GPU. Docker Compose eliminates environment issues.

### 5.2 Operational
MVP scoped for 12-week Agile sprint. Secondary features deferred. Weekly supervisor reviews provide accountability. GitHub Projects Kanban visible to supervisor.

### 5.3 Economic
**Total cost: £0.** All software, frameworks, and datasets freely available. No subscriptions or hardware procurement.

---

## 6. Project Description

### 6.1 System Overview
Clinician enters patient vitals/chief complaint → Flask backend preprocesses via scikit-learn Pipeline → XGBoost returns ESI priority (1–5), confidence, and SHAP explanation → Clinician confirms or overrides → All decisions logged to PostgreSQL audit trail.

### 6.2 Key Features
- Patient intake form with LOINC-compliant validation
- XGBoost inference (≤500ms) via `/api/predict`
- SHAP explainability panel (top 3 features in plain English)
- Colour-coded priority badges (Red→Green)
- Active queue dashboard sorted by AI priority
- Confirm/Override with mandatory reason code
- RBAC (Clinician / Administrator)
- Immutable audit log (timestamp, clinician ID, IP address)
- FHIR R4 endpoints (`/fhir/*`)
- Model drift monitoring (`/api/v1/monitoring/drift`)

### 6.3 User Personas
**Amara (Triage Nurse, 34):** Needs rapid tool, colour-coded output, trusts AI. Key: result in <60 seconds.

**Dr. Kemal (ED Lead, 47):** Needs audit trail, override patterns, user management. Key: exportable filtered audit log.

### 6.4 Use Cases
| ID | User | Action | Purpose |
|----|------|--------|---------|
| UC1 | Nurse | Enter vitals + complaint | Generate AI triage priority |
| UC2 | Nurse | View priority + SHAP factors | Make informed decision |
| UC3 | Nurse | Confirm or override with reason | Maintain clinical authority |
| UC4 | Nurse | View queue by priority | Attend to critical patients first |
| UC5 | Admin | Access audit log | Review compliance |
| UC6 | Admin | Manage accounts | Control access |

### 6.5 Scope

**In Scope:** XGBoost model, React/Flask/PostgreSQL stack, RBAC, Docker, SHAP, testing, fairness eval, documentation, PhysioNet submission, GitHub repo.

**Out of Scope:** Live HIS integration, mobile app, regulatory certification, auto-retraining, multi-hospital deployment, NLP of notes.

### 6.6 Data Model

| Entity | PK | Key Attributes |
|--------|-----|---------------|
| users | user_id UUID | username, password_hash, role, is_active |
| patients | patient_id UUID | age, sex, chief_complaint, pain_score, medication_flags |
| vitals | vital_id UUID | patient_id FK, heart_rate, sbp, dbp, rr, spo2, temp, gcs |
| triage_assessments | assessment_id UUID | patient_id FK, clinician_id FK, ai_priority, ai_confidence, shap JSON, clinician_priority, is_override, override_reason |
| audit_log | log_id UUID | assessment_id FK, event_type, event_detail, clinician_id FK, ip_address, timestamp |

All FKs use `ON DELETE RESTRICT` to protect audit integrity.

### 6.7 UI/UX Design
- **Speed:** <60 seconds intake→result
- **Clarity:** Colour-coded badges (international ED conventions)
- **Trust:** Confidence % + plain-English SHAP + permanent advisory disclaimer

Wireframes in Figma; peer usability review before implementation.

### 6.8 Development Methodology
**Agile Scrum** (2-week sprints). Adapted for solo development: sprint planning, written daily stand-up logs, supervisor sprint reviews, written retrospectives. GitHub Projects Kanban.

---

## 7. Deliverables

| Ref | Deliverable | Success Criteria |
|-----|-------------|-----------------|
| D1 | Working TriageAI application | UC1–UC6 pass system testing; zero critical defects |
| D2 | Trained XGBoost model | ≥85% accuracy, ≥90% recall ESI 1–2 on Kaggle dataset |
| D3 | Technical documentation | UML, ERD, OpenAPI, test reports, Docker guide |
| D4 | Evaluation report | Quantitative metrics, fairness analysis, reflective critique |
| D5 | Project dissertation | Full academic report with Harvard referencing |
| D6 | PhysioNet submission | Published software project; approved for MIMIC-IV-ED access |

### 7.1 Evaluation Plan
- **Unit Testing (pytest):** ≥80% coverage (pytest-cov)
- **Integration Testing (pytest + httpx):** E2E against test PostgreSQL
- **System Testing:** Docker Compose stack
- **Frontend (React Testing Library):** Component tests
- **UAT:** 2 BSc peers as simulated clinicians
- **Performance (JMeter):** ≤500ms under 10 concurrent requests
- **Security Audit:** Comprehensive code review (`AUDIT_REPORT.md`)

---

## 8. Resources Required

### 8.1 Software
Python 3.11, scikit-learn, XGBoost, pandas, NumPy, SHAP, Optuna, MLflow, imbalanced-learn, joblib, pytest, React.js v18, Flask, PostgreSQL 15, Docker, Git/GitHub, Jupyter, Figma, JMeter, VS Code.

### 8.2 Data
- **Kaggle Hospital Triage Data** — development (available immediately)
- **MIMIC-IV-ED v2.2** — external validation (PhysioNet credentialing in progress)

### 8.3 Hardware
Student laptop: 8GB RAM, 50GB storage, modern multi-core CPU. No GPU required.

### 8.4 Human Resources
- M.S.M. Sajidh (sole developer)
- Academic supervisor (reviews, feedback)
- 2 BSc peers (UAT volunteers)

---

## 9. Expected Output and Outcome

### 9.1 Outputs
- Deployed TriageAI web application (D1)
- Validated XGBoost model with reproducible pipeline (D2)
- Technical documentation suite (D3)
- Evaluation report with fairness analysis (D4)
- Project dissertation (D5)
- Published PhysioNet software project (D6)
- Public GitHub repository

### 9.2 Measurable Outcomes
- ~40% reduction in simulated triage decision time (UAT)
- API latency ≤500ms at 95th percentile (JMeter)
- Demographic parity within ±5% (pending MIMIC-IV-ED)

### 9.3 Cardiff Met Criteria Mapping
| Criterion | Evidence |
|-----------|----------|
| Practical/analytical skills | Self-developed ML pipeline, full-stack dev, containerisation |
| Innovation/creativity | SHAP in real-time triage; fairness-aware ML; open-source deployable system |
| Quality + evaluation | Quantitative eval, fairness analysis, UAT, security audit |
| Real need | Addresses documented triage inconsistency globally |
| Self-management | 12-week Agile, GitHub Kanban, daily logs, supervisor reviews |
| Critical self-evaluation | Sprint retrospectives, documented decisions, limitations section |

---

## 10. Time Plan

| Phase | Weeks | Focus | Output |
|-------|-------|-------|--------|
| 1 | 1–2 | Research, setup, wireframes, Docker env, GitHub backlog | Research notes; wireframes |
| 2 | 3–4 | Kaggle EDA, data cleaning, feature engineering, SMOTE (post-split), XGBoost training, Optuna, SHAP | Trained model (D2) |
| 3 | 5–6 | Flask API, JWT auth, /api/predict, PostgreSQL schema, unit tests | Backend API |
| 4 | 7–8 | React SPA, intake form, SHAP panel, queue dashboard, component tests | Frontend UI |
| 5 | 9–10 | E2E integration, system tests, UAT, JMeter benchmarking, security audit | Test reports; AUDIT_REPORT.md (D3) |
| 6 | 11–12 | Fairness eval, dissertation, deployment guide, PhysioNet submission, GitHub release | D1, D4, D5, D6 |

**Post-Week 12:**
- ✅ CITI training completed (11 June 2026)
- ✅ PhysioNet project submitted (11 June 2026)
- ✅ GitHub repo published: https://github.com/Agent510/TriageAI
- ⏳ PhysioNet credentialing approval (3–7 days)
- ⏳ MIMIC-IV-ED Data Use Agreement

---

## 11. Limitations

1. **Single-site datasets:** Kaggle and MIMIC-IV-ED reflect specific institutions. Multi-site validation is future work.
2. **Prototype only:** NOT a certified medical device. Permanent advisory disclaimers on all interfaces. MHRA/FDA approval required for clinical use.
3. **Residual algorithmic bias:** Fairness evaluation conducted but cannot fully eliminate all bias sources in a single student project.
4. **Solo developer scope:** Real-time HIS integration, mobile app, auto-retraining, multi-hospital deployment deferred.
5. **No real clinical validation:** UAT with BSc peers as simulated clinicians — indicative but not a substitute for qualified ED staff validation.

---

## 12. Post-Submission Milestones

### 12.1 CITI Training (Completed 11 June 2026)
| Course | Score | Passing |
|--------|-------|---------|
| Human Research — Data or Specimens Only Research | 92% | 90% |
| CITI Conflicts of Interest | 100% | 80% |

### 12.2 PhysioNet Submission (Completed 11 June 2026)
- Resource Type: Software
- License: MIT License
- Project Home: https://github.com/Agent510/TriageAI
- Status: Submitted for editorial review

### 12.3 GitHub Repository (Published 11 June 2026)
- URL: https://github.com/Agent510/TriageAI
- Visibility: Public
- Contents: Full source code, docs, audit report, Docker config

### 12.4 Security Audit (Completed 11 June 2026)
- Report: `physionet_submission/AUDIT_REPORT.md`
- Grade: A (all issues resolved)

### 12.5 External Validation Pending
Awaiting PhysioNet credentialing approval and MIMIC-IV-ED Data Use Agreement.

---

## 13. References

1. Fernandes, M. et al. (2020) 'Clinical Decision Support Systems for Triage in the Emergency Department using Intelligent Systems: A Review', *Artificial Intelligence in Medicine*, 102, p.101762.
2. Floridi, L. et al. (2018) 'AI4People — An Ethical Framework for a Good AI Society', *Minds and Machines*, 28(4), pp.689–707.
3. Garbez, R. et al. (2011) 'Factors influencing patient assignment to triage category', *Emergency Medicine Journal*, 28(3), pp.234–238.
4. Johnson, A. et al. (2023) 'MIMIC-IV (version 2.2)', *PhysioNet*. doi:10.13026/6mm1-ek67.
5. Obermeyer, Z. et al. (2019) 'Dissecting racial bias in an algorithm used to manage the health of populations', *Science*, 366(6464), pp.447–453.
6. Lundberg, S.M. and Lee, S.I. (2017) 'A unified approach to interpreting model predictions', *Advances in Neural Information Processing Systems*, 30.
7. European Commission (2024) *Regulation on Artificial Intelligence (AI Act)*. Available at: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
8. World Health Organization (2023) *Emergency Care Systems: Improving Access, Quality and Safety in Emergency Care*. Geneva: WHO.
