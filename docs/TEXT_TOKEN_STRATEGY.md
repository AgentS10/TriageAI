# TriageAI — Text Token Strategy

**Purpose:** Formalise how free-text and abbreviated chief complaints are
converted into the deterministic categorical token the ML model consumes.
This guarantees the **inference vocabulary is identical to the training
vocabulary**, eliminating out-of-vocabulary (OOV) inputs that silently
degrade model quality.

Implemented in `backend/ml/clinical_standards.py`
(`normalize_complaint_text()` + `COMPLAINT_SYNONYMS`) and exercised by the
single and batch prediction endpoints.

---

## 1. Why not free-text embeddings?

A full NLP embedding (e.g. BioBERT) was considered and rejected for this
prototype because:

- **Determinism & auditability.** Triage decisions must be reproducible and
  explainable to clinicians and regulators. A controlled vocabulary maps
  every input to one of 13 ICD-10-coded categories with a traceable reason.
- **Vector contract integrity.** The model expects a single integer
  `chief_complaint_code`. A controlled mapping keeps the feature contract
  hash stable (see `docs/SECURITY_COMPLIANCE.md`).
- **Safety.** An embedding could map an unseen phrase to an arbitrary point
  in latent space; the controlled map fails safe to `other`.

---

## 2. Normalisation pipeline

`normalize_complaint_text(text)` applies five deterministic stages and
returns `(code, matched_via)`:

| Stage | Rule | `matched_via` |
| --- | --- | --- |
| 1 | Lower-case, strip, replace punctuation with spaces, squeeze whitespace | — |
| 2 | Exact match against a registered code (e.g. `chest_pain`) | `exact_code` |
| 3 | Exact match against the curated synonym lexicon (e.g. `"sob"`) | `synonym_exact` |
| 4 | Keyword / substring match, longest synonym first | `synonym_keyword` |
| 5 | No confident match | `fallback_other` |

The mapping is **case- and punctuation-insensitive** and never invents a new
category.

---

## 3. Synonym lexicon (excerpt)

| Registry code | ICD-10 | Example synonyms |
| --- | --- | --- |
| `chest_pain` | R07.9 | chest pain, chest tightness, angina, chest pressure |
| `shortness_of_breath` | R06.0 | sob, dyspnea, can't breathe, short of breath |
| `abdominal_pain` | R10.9 | stomach pain, belly pain, abdo pain |
| `dizziness_syncope` | R42 | dizzy, syncope, fainting, vertigo, collapse |
| `altered_mental_status` | R41.82 | confusion, ams, disoriented, delirium |
| `seizure` | R56.9 | fit, convulsion, epilepsy |
| `allergic_reaction` | T78.40 | allergy, anaphylaxis, hives, urticaria |

Full lexicon: `COMPLAINT_SYNONYMS` in `backend/ml/clinical_standards.py`.

---

## 4. Governance

- **Adding a synonym** is a safe, backward-compatible change (no retraining
  required) because it maps to an existing code.
- **Adding a new category** is a breaking change: it alters
  `CHIEF_COMPLAINT_REGISTRY`, changes the feature-contract hash, and requires
  model retraining.
- Every normalisation outcome is testable and unit-tested in
  `tests/test_enhancements.py::TestTextNormalisation`.

---

## 5. Worked examples

| Input | Output code | Matched via |
| --- | --- | --- |
| `"SOB"` | `shortness_of_breath` | synonym_exact |
| `"Chest Tightness!!"` | `chest_pain` | synonym_keyword |
| `"chest_pain"` | `chest_pain` | exact_code |
| `"qqqq wwww"` | `other` | fallback_other |
