"""
TriageAI Clinical Standards Registry
=====================================
Maps all clinical terms to internationally recognised codes:
  - Chief complaints  -> ICD-10-CM codes
  - Vital signs       -> LOINC codes
  - Override reasons  -> Standardised coded vocabulary

This module eliminates arbitrary/free-text terms throughout the system
and provides the single source of truth for categorical mapping used
by both the ML training pipeline and the inference endpoint.

References:
  ICD-10-CM: https://www.who.int/standards/classifications/classification-of-diseases
  LOINC:     https://loinc.org/
  SNOMED CT: https://www.snomed.org/
"""

# ────────────────────────────────────────────────────────────────────
# CHIEF COMPLAINT REGISTRY
# Each entry: code -> {icd10, snomed_ct, display_en, category_index}
# category_index is the deterministic integer used by the ML pipeline.
# ────────────────────────────────────────────────────────────────────
CHIEF_COMPLAINT_REGISTRY = {
    "chest_pain":            {"icd10": "R07.9",  "snomed": "29857009",  "display_en": "Chest Pain",               "category_index": 0},
    "shortness_of_breath":   {"icd10": "R06.0",  "snomed": "267036007", "display_en": "Shortness of Breath",      "category_index": 1},
    "abdominal_pain":        {"icd10": "R10.9",  "snomed": "21522001",  "display_en": "Abdominal Pain",           "category_index": 2},
    "headache":              {"icd10": "R51",     "snomed": "25064002",  "display_en": "Headache",                 "category_index": 3},
    "fever":                 {"icd10": "R50.9",  "snomed": "386661006", "display_en": "Fever",                    "category_index": 4},
    "trauma_injury":         {"icd10": "T14.90", "snomed": "417163006", "display_en": "Trauma / Injury",          "category_index": 5},
    "dizziness_syncope":     {"icd10": "R42",    "snomed": "404640003", "display_en": "Dizziness / Syncope",      "category_index": 6},
    "weakness_numbness":     {"icd10": "R53.1",  "snomed": "13791008",  "display_en": "Weakness / Numbness",      "category_index": 7},
    "back_pain":             {"icd10": "M54.9",  "snomed": "161891005", "display_en": "Back Pain",                "category_index": 8},
    "altered_mental_status": {"icd10": "R41.82", "snomed": "419284004", "display_en": "Altered Mental Status",    "category_index": 9},
    "seizure":               {"icd10": "R56.9",  "snomed": "91175000",  "display_en": "Seizure",                  "category_index": 10},
    "allergic_reaction":     {"icd10": "T78.40", "snomed": "419076005", "display_en": "Allergic Reaction",        "category_index": 11},
    "other":                 {"icd10": "R68.89", "snomed": "404684003", "display_en": "Other",                    "category_index": 12},
}

# ────────────────────────────────────────────────────────────────────
# VITAL SIGNS — LOINC CODES
# Each entry maps the internal field name to its LOINC code, unit,
# and clinically valid range used for input validation.
# ────────────────────────────────────────────────────────────────────
VITAL_SIGN_STANDARDS = {
    "heart_rate":        {"loinc": "8867-4",  "unit": "bpm",          "min": 0,   "max": 300,  "display_en": "Heart Rate"},
    "sbp":               {"loinc": "8480-6",  "unit": "mmHg",         "min": 0,   "max": 300,  "display_en": "Systolic Blood Pressure"},
    "dbp":               {"loinc": "8462-4",  "unit": "mmHg",         "min": 0,   "max": 200,  "display_en": "Diastolic Blood Pressure"},
    "respiratory_rate":  {"loinc": "9279-1",  "unit": "breaths/min",  "min": 0,   "max": 60,   "display_en": "Respiratory Rate"},
    "spo2":              {"loinc": "2708-6",  "unit": "%",            "min": 0,   "max": 100,  "display_en": "Oxygen Saturation (SpO2)"},
    "temperature":       {"loinc": "8310-5",  "unit": "°C",           "min": 20.0,"max": 45.0, "display_en": "Body Temperature"},
    "gcs":               {"loinc": "9269-2",  "unit": "score",        "min": 3,   "max": 15,   "display_en": "Glasgow Coma Scale"},
    "pain_score":        {"loinc": "72514-3", "unit": "score",        "min": 0,   "max": 10,   "display_en": "Pain Severity (0-10 NRS)"},
}

# ────────────────────────────────────────────────────────────────────
# OVERRIDE REASON CODES
# Deterministic coded set — no free-text in audit log.
# ────────────────────────────────────────────────────────────────────
OVERRIDE_REASON_CODES = {
    "OVR-01": "Clinical instinct based on patient presentation",
    "OVR-02": "Additional history not captured in vitals",
    "OVR-03": "Known patient with relevant medical history",
    "OVR-04": "Patient showing signs of rapid deterioration",
    "OVR-05": "Communication barrier affecting assessment",
    "OVR-06": "Concern about vital sign measurement accuracy",
    "OVR-07": "Other (documented in notes)",
}

# ────────────────────────────────────────────────────────────────────
# SEX / GENDER MAPPING (HL7 Administrative Gender)
# ────────────────────────────────────────────────────────────────────
SEX_CODES = {
    "M": {"hl7": "male",    "display_en": "Male",    "category_index": 0},
    "F": {"hl7": "female",  "display_en": "Female",  "category_index": 1},
    "O": {"hl7": "other",   "display_en": "Other",   "category_index": 2},
    "U": {"hl7": "unknown", "display_en": "Unknown", "category_index": 3},
}

# ────────────────────────────────────────────────────────────────────
# ESI LEVEL DEFINITIONS (Emergency Severity Index v4)
# ────────────────────────────────────────────────────────────────────
ESI_LEVELS = {
    1: {"label": "Immediate",   "color": "#d32f2f", "hex": "red"},
    2: {"label": "Emergent",    "color": "#f57c00", "hex": "orange"},
    3: {"label": "Urgent",      "color": "#fbc02d", "hex": "yellow"},
    4: {"label": "Less Urgent", "color": "#388e3c", "hex": "green"},
    5: {"label": "Non-Urgent",  "color": "#1976d2", "hex": "blue"},
}


def validate_vital_sign(field_name, value):
    """Validate a vital sign value against clinical range."""
    std = VITAL_SIGN_STANDARDS.get(field_name)
    if std is None:
        return False, f"Unknown vital sign: {field_name}"
    if value < std["min"] or value > std["max"]:
        return False, f"{std['display_en']} must be between {std['min']} and {std['max']} {std['unit']}"
    return True, None


# ────────────────────────────────────────────────────────────────────
# TEXT TOKEN STRATEGY — free-text → registry code normalisation
# ====================================================================
# Clinicians and upstream systems often submit free-text chief complaints
# (e.g. "SOB", "can't breathe", "chest tightness"). To keep the model's
# categorical input deterministic, all free text is normalised to a single
# registered code via a controlled synonym map BEFORE tokenisation.
#
# Strategy (documented in docs/TEXT_TOKEN_STRATEGY.md):
#   1. Lower-case, strip, collapse whitespace/punctuation.
#   2. Exact match against a registered code -> use it.
#   3. Match against the curated synonym lexicon -> mapped code.
#   4. Substring/keyword match against the lexicon -> mapped code.
#   5. No confident match -> "other" (never an arbitrary new category).
#
# This guarantees the inference vocabulary == the training vocabulary,
# eliminating out-of-vocabulary tokens that would silently degrade the model.
# ────────────────────────────────────────────────────────────────────
COMPLAINT_SYNONYMS = {
    "chest_pain":            ["chest pain", "chest tightness", "chest pressure", "angina", "chest discomfort"],
    "shortness_of_breath":   ["sob", "shortness of breath", "dyspnea", "dyspnoea", "cant breathe", "can't breathe", "breathing difficulty", "short of breath"],
    "abdominal_pain":        ["abdominal pain", "stomach pain", "belly pain", "tummy ache", "abdo pain", "stomach ache"],
    "headache":              ["headache", "head ache", "migraine", "cephalalgia"],
    "fever":                 ["fever", "pyrexia", "high temperature", "febrile", "temperature"],
    "trauma_injury":         ["trauma", "injury", "fall", "fracture", "wound", "laceration", "rta", "accident"],
    "dizziness_syncope":     ["dizziness", "dizzy", "syncope", "fainting", "faint", "lightheaded", "vertigo", "collapse"],
    "weakness_numbness":     ["weakness", "numbness", "tingling", "paresthesia", "limb weakness"],
    "back_pain":             ["back pain", "lower back pain", "lumbar pain", "backache"],
    "altered_mental_status": ["altered mental status", "confusion", "confused", "ams", "disoriented", "delirium"],
    "seizure":               ["seizure", "fit", "convulsion", "epilepsy", "fitting"],
    "allergic_reaction":     ["allergic reaction", "allergy", "anaphylaxis", "hives", "urticaria", "swelling"],
    "other":                 ["other", "unspecified", "unknown"],
}


def normalize_complaint_text(text):
    """
    Normalise a free-text chief complaint to a registered code.

    Returns a (code, matched_via) tuple where matched_via is one of:
      'exact_code' | 'synonym_exact' | 'synonym_keyword' | 'fallback_other'.
    Deterministic and case/punctuation-insensitive.
    """
    if text is None:
        return "other", "fallback_other"

    raw = str(text).strip().lower()
    # Collapse punctuation to spaces, then squeeze whitespace.
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in raw)
    cleaned = " ".join(cleaned.split())

    if not cleaned:
        return "other", "fallback_other"

    # 2. Already a registered code (e.g. "chest_pain").
    code_form = cleaned.replace(" ", "_")
    if code_form in CHIEF_COMPLAINT_REGISTRY:
        return code_form, "exact_code"

    # 3. Exact synonym match.
    for code, synonyms in COMPLAINT_SYNONYMS.items():
        if cleaned in synonyms:
            return code, "synonym_exact"

    # 4. Keyword / substring match (longest synonyms first for specificity).
    for code, synonyms in COMPLAINT_SYNONYMS.items():
        for syn in sorted(synonyms, key=len, reverse=True):
            if syn in cleaned or cleaned in syn:
                return code, "synonym_keyword"

    # 5. No confident match.
    return "other", "fallback_other"


def get_complaint_index(complaint_code):
    """Convert chief complaint code to deterministic integer for ML input."""
    entry = CHIEF_COMPLAINT_REGISTRY.get(complaint_code)
    if entry is None:
        return CHIEF_COMPLAINT_REGISTRY["other"]["category_index"]
    return entry["category_index"]


def get_sex_index(sex_code):
    """Convert sex code to deterministic integer for ML input."""
    entry = SEX_CODES.get(sex_code, SEX_CODES["U"])
    return entry["category_index"]
