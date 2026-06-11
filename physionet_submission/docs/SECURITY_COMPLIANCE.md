# TriageAI — Security & Compliance Control Mapping

This document maps the TriageAI prototype's implemented controls to the relevant
healthcare and security standards. It is intended for the dissertation's
**Security, Privacy & Standards** chapter.

> **Scope disclaimer.** TriageAI is an **academic research prototype**, not a
> certified medical device or a HIPAA "covered entity" system. Code-level
> technical safeguards are implemented as described below. Organizational
> safeguards (Business Associate Agreements, breach-notification procedures,
> workforce training, formal risk assessments) are **out of scope** for an
> academic project and are noted as such.

---

## 1. HL7 / FHIR Interoperability

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| **HL7 FHIR R4** | Standard resource representation | `backend/routes/fhir.py` serves `Patient`, `DiagnosticReport`, and `Observation` resources |
| **FHIR CapabilityStatement** | Server self-description | `GET /api/fhir/metadata` (public), declares `fhirVersion 4.0.1` and supported interactions |
| **FHIR Bundle** | Multi-resource responses | `GET /api/fhir/Patient/<id>/$everything` and `GET /api/fhir/Observation?patient=<id>` return `searchset` Bundles |
| **FHIR content negotiation** | `application/fhir+json` media type | All FHIR responses use the `application/fhir+json` MIME type |
| **LOINC** | Coded vital signs | `Observation` resources carry LOINC codes (HR `8867-4`, SBP `8480-6`, DBP `8462-4`, RR `9279-1`, SpO2 `2708-6`, Temp `8310-5`, GCS `9269-2`, Pain `72514-3`) |
| **HL7 Administrative Gender** | Coded sex | `M/F/O/U` → `male/female/other/unknown` mapping |
| **ICD-10 / SNOMED CT** | Coded chief complaints | `backend/ml/clinical_standards.py` registry |
| **FHIR OperationOutcome** | Standard error envelope | 404/400 responses return `OperationOutcome` resources |

**Known limitations (future work):** no SMART-on-FHIR / OAuth2 authorization
server (internal JWT is used instead), Observations are `contained` within the
DiagnosticReport rather than independently persisted, and the server is
read-only (no create/update interactions).

---

## 2. HIPAA Security Rule — Technical Safeguards (45 CFR §164.312)

| Citation | Safeguard | Implementation |
|----------|-----------|----------------|
| §164.312(a)(1) | **Access control** | JWT authentication on all protected routes; RBAC via `backend/security.py` `require_roles()` (admin vs clinician) |
| §164.312(a)(2)(i) | **Unique user identification** | Each `User` has a UUID `user_id`; all actions attributed to it |
| §164.312(a)(2)(iii) | **Automatic logoff** | 15-minute JWT access-token expiry + frontend idle session timeout |
| §164.312(a)(2)(iv) | **Encryption at rest** | Fernet (AES-128-CBC + HMAC-SHA256) on PII; key from `PII_ENCRYPTION_KEY` or PBKDF2-derived from `JWT_SECRET_KEY` + `PII_ENCRYPTION_SALT`; `MultiFernet` key rotation via `PII_ENCRYPTION_KEYS_RETIRED` |
| §164.312(b) | **Audit controls** | Immutable `audit_log` table (INSERT-only, `ON DELETE RESTRICT`); **every PHI read** (FHIR Patient/DiagnosticReport/Observation, admin search) is logged via `log_phi_access()` with user id, event, and IP |
| §164.312(c)(1) | **Integrity** | Audit log immutability + ML feature-contract SHA-256 hash verification |
| §164.312(d) | **Authentication** | `werkzeug` password hashing, password-complexity policy, login rate-limiting (5 attempts / 15 min lockout) |
| §164.312(e)(1) | **Transmission security** | HSTS header; production `FORCE_HTTPS` redirect (`X-Forwarded-Proto` aware); TLS terminated at the deployment proxy |

---

## 3. HIPAA Privacy Rule

| Citation | Principle | Implementation |
|----------|-----------|----------------|
| §164.502(b) | **Minimum necessary** | FHIR & search endpoints restricted to `clinician`/`admin` roles; data model stores **no name, DOB, or MRN** (data minimization by design) |
| §164.514 | **De-identification posture** | Patient records hold only age, sex, coded complaint, vitals — reducing re-identification risk |

---

## 4. OWASP / Web Application Security

| Control | Implementation (`backend/app.py`) |
|---------|-----------------------------------|
| Security headers | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`, `Cache-Control: no-store` |
| CORS | Origin whitelist via `CORS_ORIGINS` env (defaults to localhost) |
| Rate limiting | `flask-limiter` throttles `/api/predict` (`RATELIMIT_PREDICT`, default 60/min); custom login limiter |
| Input validation | Vital-sign range validation (LOINC), coded override reasons (no free-text), JSON schema checks |
| Secrets management | `JWT_SECRET_KEY` mandatory in production (startup fails if unset); `.env` for config |
| SQL injection | SQLAlchemy ORM parameterised queries throughout |

---

## 5. Configuration Reference (environment variables)

| Variable | Purpose | Default |
|----------|---------|---------|
| `JWT_SECRET_KEY` | Token signing + PII key derivation | dev fallback (must be set in prod) |
| `PII_ENCRYPTION_KEY` | Explicit Fernet key for PII (preferred) | unset → derived key used |
| `PII_ENCRYPTION_SALT` | PBKDF2 salt for derived key | `triageai-pii-salt-v1` (legacy) |
| `PII_ENCRYPTION_KEYS_RETIRED` | Comma-separated old keys (decrypt-only) | unset |
| `CORS_ORIGINS` | Allowed front-end origins | `http://localhost:3000` |
| `DATABASE_URL` | Production PostgreSQL DSN | local Postgres |
| `FLASK_ENV` | `development` / `testing` / `production` | `development` |

> **Production migration note.** `audit_log.assessment_id` was made nullable to
> support PHI-access events that are not tied to a single assessment. Run
> `flask db migrate` / `flask db upgrade` against existing databases.

---

## 6. Out-of-scope (organizational controls)

The following HIPAA Administrative/Physical safeguards require organizational
processes beyond an academic prototype and are **not** implemented in code:

- Business Associate Agreements (BAAs)
- Formal risk analysis & risk management (§164.308(a)(1))
- Breach notification procedures (§164.400–414)
- Workforce security training & sanctions
- Physical facility access controls & device/media controls (§164.310)
- Contingency / disaster-recovery plan
