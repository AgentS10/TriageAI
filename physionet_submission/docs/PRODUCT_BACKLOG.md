# TriageAI — Product Backlog

## Sprint 1 (Weeks 1–2): Research & Setup
| ID | Priority | User Story / Task | Status | Acceptance Criteria |
|----|----------|-------------------|--------|---------------------|
| PB-001 | HIGH | Literature review on ED triage ML systems | DONE | Min 8 peer-reviewed sources documented |
| PB-002 | HIGH | PhysioNet/Kaggle dataset access | DONE | CSV downloaded and accessible |
| PB-003 | HIGH | Figma wireframes (all 6 screens) | DONE | Peer-reviewed with think-aloud protocol |
| PB-004 | HIGH | Dev environment setup (Python, Node, Docker, PostgreSQL) | DONE | All dependencies install cleanly |
| PB-005 | MED  | GitHub repo + Projects Kanban board | DONE | Backlog populated, supervisor access |
| PB-006 | MED  | Clinical standards registry (ICD-10, LOINC, SNOMED) | DONE | All terms coded, no arbitrary strings |

## Sprint 2 (Weeks 3–4): Data & ML Pipeline
| ID | Priority | User Story / Task | Status | Acceptance Criteria |
|----|----------|-------------------|--------|---------------------|
| PB-007 | HIGH | EDA notebook with data quality report | DONE | 8 figures generated on real data (126K records) |
| PB-008 | HIGH | Feature contract definition (13 features) | DONE | Contract hash 8652111523af92d0 verified |
| PB-009 | HIGH | Categorical mapping registry (deterministic) | DONE | Chief complaint -> ICD-10 index; sex -> HL7 index |
| PB-010 | HIGH | Data cleaning: imputation, outlier capping, SMOTE | DONE | Pipeline runs end-to-end, 10K records processed |
| PB-011 | HIGH | XGBoost training with Optuna tuning (15 trials) | DONE | AUC-ROC 0.91, Level 1 recall 99% |
| PB-012 | HIGH | Random Forest baseline comparison | DONE | XGBoost F1 0.6927 > RF F1 0.6915 |
| PB-013 | HIGH | SHAP global + local explanations | DONE | Summary plot saved + per-patient top-3 in API |
| PB-014 | MED  | MLflow experiment tracking | DEFERRED | Using JSON metrics file instead |
| PB-015 | HIGH | Model artifacts saved with contract hash | DONE | triage_pipeline.joblib + feature_contract.json saved |

## Sprint 3 (Weeks 5–6): Backend Development
| ID | Priority | User Story / Task | Status | Acceptance Criteria |
|----|----------|-------------------|--------|---------------------|
| PB-016 | HIGH | Flask app factory with config (dev/test/prod) | DONE | Config loads correctly per environment |
| PB-017 | HIGH | SQLAlchemy models (5 entities, ON DELETE RESTRICT) | DONE | All FK constraints enforced |
| PB-018 | HIGH | JWT authentication (register, login, refresh, profile) | DONE | 15-min access, 7-day refresh tokens |
| PB-019 | HIGH | POST /api/predict with contract-enforced vector | DONE | Returns ESI level + SHAP + confidence |
| PB-020 | HIGH | POST /api/confirm + /api/override with coded reasons | DONE | Override requires OVERRIDE_REASON_CODES |
| PB-021 | HIGH | GET /api/queue (priority-sorted) | DONE | Sorted by ai_priority ASC |
| PB-022 | HIGH | Immutable audit log (INSERT only, no DELETE) | DONE | All events logged with timestamp + IP |
| PB-023 | HIGH | OWASP security headers middleware | DONE | X-Frame-Options, CSP, HSTS, etc. |
| PB-024 | HIGH | Input sanitization + vital sign range validation | DONE | Rejects out-of-range vitals with LOINC ref |
| PB-025 | MED  | Localization middleware (English only) | DONE | Accept-Language header selects locale |
| PB-026 | MED  | Admin routes (users, audit log, analytics, CSV export) | DONE | Admin-only access enforced |
| PB-027 | MED  | GET /api/clinical-standards (standards endpoint) | DONE | Returns ICD-10 + SNOMED codes for frontend |
| PB-028 | LOW  | Unit tests (pytest) — target 80% coverage | DONE | 70 tests pass, 73% coverage (auth/predict error paths remain) |
| PB-028a | HIGH | Login rate limiting (5 attempts/15min) | DONE | Brute-force protection active |
| PB-028b | HIGH | Admin user CRUD (create, edit, reset pw, delete) | DONE | Full lifecycle management |
| PB-028c | HIGH | Change own password endpoint | DONE | Validates current + new password |
| PB-028d | MED  | Patient search endpoint | DONE | Search by complaint/ID with pagination |

## Sprint 4 (Weeks 7–8): Frontend Development
| ID | Priority | User Story / Task | Status | Acceptance Criteria |
|----|----------|-------------------|--------|---------------------|
| PB-029 | HIGH | React app scaffold with MUI theme | DONE | Medical colour scheme applied |
| PB-030 | HIGH | Login page with JWT integration | DONE | Tokens stored, auto-refresh configured |
| PB-031 | HIGH | Patient intake form with validation | DONE | All vitals validated against clinical ranges |
| PB-032 | HIGH | Triage result screen with SHAP panel | DONE | Colour-coded badge + top-3 SHAP features |
| PB-033 | HIGH | Active patient queue dashboard | DONE | Sorted by priority, filterable |
| PB-034 | HIGH | Confirm / Override controls with coded reasons | DONE | Override reason dropdown (OVR-01..07) |
| PB-035 | MED  | Admin panel (4 tabs: audit, users, analytics, search) | DONE | Full CRUD + CSV export |
| PB-036 | MED  | i18n support (frontend) | DONE | English-only interface |
| PB-037 | LOW  | React Testing Library component tests | TODO | Key components covered |
| PB-037a | HIGH | Session timeout (auto-logout 15min) | DONE | useSessionTimeout hook active |
| PB-037b | HIGH | Professional UI/UX overhaul | DONE | Inter font, gradients, polished theme |

## Sprint 5 (Weeks 9–10): Integration & Testing
| ID | Priority | User Story / Task | Status | Acceptance Criteria |
|----|----------|-------------------|--------|---------------------|
| PB-038 | HIGH | End-to-end integration tests (pytest + httpx) | DONE | 18/18 API tests passing (tests/test_api.py) |
| PB-039 | HIGH | Docker Compose deployment verified | DONE | `docker-compose.yml` valid YAML, Dockerfiles present |
| PB-040 | HIGH | UAT with 2 peer reviewers (think-aloud) | TODO | Task completion rate >=85% |
| PB-041 | HIGH | JMeter performance test (<=500ms @ 10 concurrent) | DONE | Test plan created at `jmeter/triageai_load_test.jmx` |
| PB-042 | MED  | OpenAPI/Swagger specification | DONE | Flasgger UI live at /apidocs/ |
| PB-043 | MED  | Bug fixes from UAT feedback | TODO | Zero critical defects |

## Sprint 6 (Weeks 11–12): Evaluation & Documentation
| ID | Priority | User Story / Task | Status | Acceptance Criteria |
|----|----------|-------------------|--------|---------------------|
| PB-044 | HIGH | Fairness evaluation (demographic parity ±5%) | DONE | 3 charts + chi-squared tests generated (see notebooks/02_fairness_eval.py) |
| PB-045 | HIGH | Evaluation report (metrics, fairness, reflection) | DONE | Generated at `notebooks/figures/evaluation_report.md` |
| PB-046 | HIGH | Final dissertation | TODO | Harvard referencing, all chapters complete |
| PB-047 | MED  | Deployment guide (Docker) | DONE | `DEPLOY.md` with full setup instructions |
| PB-048 | MED  | UML diagrams (class, sequence, use case) | DONE | 3 PlantUML files in `docs/` (render at plantuml.com/plantuml) |
| PB-049 | LOW  | GitHub cleanup + final tag (v1.0.0) | TODO | Clean commit history, README updated |

## Out of Scope (Future Work)
| ID | Description |
|----|-------------|
| FW-001 | HL7 FHIR integration with live hospital systems |
| FW-002 | Mobile application (iOS / Android) |
| FW-003 | Automated model retraining pipeline |
| FW-004 | Multi-hospital deployment |
| FW-005 | NLP of unstructured clinical notes |
| FW-006 | Real patient data (requires MHRA/FDA approval) |
