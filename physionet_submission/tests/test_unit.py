"""
TriageAI Unit Tests
====================
Tests individual functions in isolation — no HTTP, no database.
Run: pytest tests/ -v --tb=short
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
import numpy as np

# ── CLINICAL STANDARDS ──────────────────────────────────────────

from ml.clinical_standards import (
    validate_vital_sign, get_complaint_index, get_sex_index,
    CHIEF_COMPLAINT_REGISTRY, SEX_CODES, VITAL_SIGN_STANDARDS,
    OVERRIDE_REASON_CODES, ESI_LEVELS
)

class TestVitalSignValidation:
    def test_valid_heart_rate(self):
        ok, msg = validate_vital_sign('heart_rate', 80)
        assert ok is True
        assert msg is None

    def test_heart_rate_too_high(self):
        ok, msg = validate_vital_sign('heart_rate', 999)
        assert ok is False
        assert 'Heart Rate' in msg

    def test_heart_rate_boundary_low(self):
        ok, _ = validate_vital_sign('heart_rate', 0)
        assert ok is True

    def test_heart_rate_boundary_high(self):
        ok, _ = validate_vital_sign('heart_rate', 300)
        assert ok is True

    def test_heart_rate_over_max(self):
        ok, _ = validate_vital_sign('heart_rate', 301)
        assert ok is False

    def test_spo2_valid(self):
        ok, _ = validate_vital_sign('spo2', 95)
        assert ok is True

    def test_spo2_over_100(self):
        ok, _ = validate_vital_sign('spo2', 101)
        assert ok is False

    def test_temperature_valid(self):
        ok, _ = validate_vital_sign('temperature', 37.5)
        assert ok is True

    def test_temperature_hypothermia(self):
        ok, _ = validate_vital_sign('temperature', 19.9)
        assert ok is False

    def test_gcs_valid_range(self):
        ok, _ = validate_vital_sign('gcs', 15)
        assert ok is True
        ok2, _ = validate_vital_sign('gcs', 3)
        assert ok2 is True

    def test_gcs_below_min(self):
        ok, _ = validate_vital_sign('gcs', 2)
        assert ok is False

    def test_unknown_vital_sign(self):
        ok, msg = validate_vital_sign('blood_sugar', 120)
        assert ok is False
        assert 'Unknown' in msg

    def test_all_vitals_have_loinc_code(self):
        for name, spec in VITAL_SIGN_STANDARDS.items():
            assert 'loinc' in spec, f"{name} missing LOINC code"
            assert spec['loinc'], f"{name} has empty LOINC code"


class TestComplaintMapping:
    def test_known_complaint(self):
        idx = get_complaint_index('chest_pain')
        assert idx == 0

    def test_another_complaint(self):
        idx = get_complaint_index('fever')
        assert idx == 4

    def test_unknown_defaults_to_other(self):
        idx = get_complaint_index('alien_abduction')
        other_idx = CHIEF_COMPLAINT_REGISTRY['other']['category_index']
        assert idx == other_idx

    def test_all_complaints_have_icd10(self):
        for code, entry in CHIEF_COMPLAINT_REGISTRY.items():
            assert 'icd10' in entry, f"{code} missing ICD-10"
            assert 'snomed' in entry, f"{code} missing SNOMED"
            assert 'category_index' in entry, f"{code} missing index"

    def test_category_indices_unique(self):
        indices = [e['category_index'] for e in CHIEF_COMPLAINT_REGISTRY.values()]
        assert len(indices) == len(set(indices)), "Duplicate category indices"


class TestSexMapping:
    def test_male(self):
        assert get_sex_index('M') == 0

    def test_female(self):
        assert get_sex_index('F') == 1

    def test_other(self):
        assert get_sex_index('O') == 2

    def test_unknown_defaults(self):
        idx = get_sex_index('X')
        assert idx == SEX_CODES['U']['category_index']


class TestOverrideReasons:
    def test_all_codes_exist(self):
        for code in ['OVR-01', 'OVR-02', 'OVR-03', 'OVR-04', 'OVR-05', 'OVR-06', 'OVR-07']:
            assert code in OVERRIDE_REASON_CODES

    def test_codes_have_descriptions(self):
        for code, desc in OVERRIDE_REASON_CODES.items():
            assert len(desc) > 10, f"{code} has too short description"


class TestESILevels:
    def test_five_levels(self):
        assert len(ESI_LEVELS) == 5

    def test_each_has_color(self):
        for level, info in ESI_LEVELS.items():
            assert 'color' in info
            assert info['color'].startswith('#')


# ── FEATURE CONTRACT ────────────────────────────────────────────

from ml.feature_contract import (
    FEATURE_NAMES, EXPECTED_FEATURE_COUNT, FEATURE_VECTOR_SPEC,
    get_contract_hash, build_feature_vector
)

class TestFeatureContract:
    def test_feature_count(self):
        assert EXPECTED_FEATURE_COUNT == 13

    def test_feature_names_match_spec(self):
        assert len(FEATURE_NAMES) == len(FEATURE_VECTOR_SPEC)
        for name, spec in zip(FEATURE_NAMES, FEATURE_VECTOR_SPEC):
            assert name == spec['name']

    def test_hash_deterministic(self):
        h1 = get_contract_hash()
        h2 = get_contract_hash()
        assert h1 == h2
        assert len(h1) == 16

    def test_build_vector_valid(self):
        patient = {'age': 45, 'sex': 'M', 'chief_complaint': 'chest_pain',
                   'pain_score': 8, 'medication_flags': {'anticoagulant': True, 'diabetic': False}}
        vitals = {'heart_rate': 110, 'sbp': 90, 'dbp': 60, 'respiratory_rate': 24,
                  'spo2': 92, 'temperature': 37.5, 'gcs': 15}
        vector = build_feature_vector(patient, vitals)
        assert len(vector) == EXPECTED_FEATURE_COUNT
        assert vector[0] == 110.0  # heart_rate first
        assert vector[7] == 45.0   # age
        assert vector[11] == 1.0   # anticoagulant flag

    def test_build_vector_missing_field_raises(self):
        with pytest.raises(ValueError, match="Missing required feature"):
            build_feature_vector({'age': 45}, {})

    def test_build_vector_default_complaint(self):
        patient = {'age': 30, 'sex': 'F', 'chief_complaint': 'unknown_thing',
                   'pain_score': 3, 'medication_flags': {}}
        vitals = {'heart_rate': 72, 'sbp': 120, 'dbp': 80, 'respiratory_rate': 16,
                  'spo2': 98, 'temperature': 36.8, 'gcs': 15}
        vector = build_feature_vector(patient, vitals)
        # Unknown complaint maps to 'other' index (12)
        assert vector[9] == 12.0

    def test_all_features_have_type(self):
        valid_types = {'continuous', 'categorical_int', 'binary'}
        for spec in FEATURE_VECTOR_SPEC:
            assert spec['type'] in valid_types, f"{spec['name']} has invalid type"


# ── PASSWORD VALIDATION ─────────────────────────────────────────

from routes.auth import validate_password

class TestPasswordValidation:
    def test_valid_password(self):
        ok, _ = validate_password('Test1234')
        assert ok is True

    def test_too_short(self):
        ok, msg = validate_password('Ab1')
        assert ok is False
        assert '8 characters' in msg

    def test_no_uppercase(self):
        ok, msg = validate_password('test1234')
        assert ok is False
        assert 'uppercase' in msg

    def test_no_lowercase(self):
        ok, msg = validate_password('TEST1234')
        assert ok is False
        assert 'lowercase' in msg

    def test_no_digit(self):
        ok, msg = validate_password('TestTest')
        assert ok is False
        assert 'digit' in msg

    def test_exactly_8_chars(self):
        ok, _ = validate_password('Abcdefg1')
        assert ok is True


# ── ENCRYPTION ─────────────────────────────────────────────────

from encryption import encrypt_field, decrypt_field

class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        original = 'sensitive_patient_data_123'
        encrypted = encrypt_field(original)
        decrypted = decrypt_field(encrypted)
        assert decrypted == original
        assert encrypted != original

    def test_encrypt_none_returns_none(self):
        assert encrypt_field(None) is None

    def test_decrypt_none_returns_none(self):
        assert decrypt_field(None) is None

    def test_decrypt_plaintext_passes_through(self):
        """If value wasn't encrypted, decrypt_field returns it as-is."""
        plaintext = 'not_encrypted_value'
        assert decrypt_field(plaintext) == plaintext

    def test_encrypt_different_outputs(self):
        """Fernet produces different ciphertexts for same plaintext."""
        original = 'test_value'
        enc1 = encrypt_field(original)
        enc2 = encrypt_field(original)
        assert enc1 != enc2  # Fernet includes timestamp
        assert decrypt_field(enc1) == original
        assert decrypt_field(enc2) == original
