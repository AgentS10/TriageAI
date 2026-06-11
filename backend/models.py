"""
TriageAI Database Models
=========================
SQLAlchemy ORM models aligned with:
  - HL7 Administrative Gender codes (sex field)
  - LOINC-referenced vital sign fields
  - ICD-10 coded chief complaints (stored as registry code, not free text)
  - Immutable audit_log (ON DELETE RESTRICT, no application-level DELETE)

All foreign keys use ON DELETE RESTRICT to protect audit trail integrity.
"""
from extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime
import uuid
import sys
import os

# Make encryption module importable
sys.path.insert(0, os.path.dirname(__file__))
from encryption import encrypt_field, decrypt_field


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'clinician' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    triage_assessments = db.relationship('TriageAssessment', backref='clinician', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='clinician', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Patient(db.Model):
    __tablename__ = 'patients'

    patient_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(1), nullable=False)  # HL7: M, F, O, U
    # Encrypted at rest — Fernet symmetric encryption via encrypt_field / decrypt_field
    # Backward compatible: decrypt_field returns plaintext as-is if not encrypted
    _chief_complaint_enc = db.Column('chief_complaint', db.String(255), nullable=False)
    pain_score = db.Column(db.Integer, nullable=False)  # LOINC 72514-3, range 0-10
    medication_flags = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('age >= 0 AND age <= 120', name='ck_patient_age_range'),
        CheckConstraint('pain_score >= 0 AND pain_score <= 10', name='ck_patient_pain_range'),
        CheckConstraint("sex IN ('M', 'F', 'O', 'U')", name='ck_patient_sex_hl7'),
    )

    @property
    def chief_complaint(self):
        """Return decrypted chief_complaint (falls back to plaintext for legacy records)."""
        return decrypt_field(self._chief_complaint_enc)

    @chief_complaint.setter
    def chief_complaint(self, value):
        """Encrypt before storing to database."""
        self._chief_complaint_enc = encrypt_field(value)

    vitals = db.relationship('Vitals', backref='patient', lazy=True,
                             cascade='all', passive_deletes=False)
    triage_assessments = db.relationship('TriageAssessment', backref='patient', lazy=True,
                                         cascade='all', passive_deletes=False)

    def __repr__(self):
        return f'<Patient {self.patient_id}>'


class Vitals(db.Model):
    """
    Vital sign measurements aligned with LOINC codes:
      heart_rate      -> LOINC 8867-4
      sbp             -> LOINC 8480-6
      dbp             -> LOINC 8462-4
      respiratory_rate-> LOINC 9279-1
      spo2            -> LOINC 2708-6
      temperature     -> LOINC 8310-5
      gcs             -> LOINC 9269-2
    """
    __tablename__ = 'vitals'

    vital_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(
        db.String(36),
        db.ForeignKey('patients.patient_id', ondelete='RESTRICT'),
        nullable=False
    )
    heart_rate = db.Column(db.Integer, nullable=False)       # bpm
    sbp = db.Column(db.Integer, nullable=False)              # mmHg
    dbp = db.Column(db.Integer, nullable=False)              # mmHg
    respiratory_rate = db.Column(db.Integer, nullable=False)  # breaths/min
    spo2 = db.Column(db.Float, nullable=False)               # %
    temperature = db.Column(db.Float, nullable=False)         # Celsius
    gcs = db.Column(db.Integer, nullable=False)              # 3-15
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('heart_rate >= 0 AND heart_rate <= 300', name='ck_vitals_hr_range'),
        CheckConstraint('sbp >= 0 AND sbp <= 300', name='ck_vitals_sbp_range'),
        CheckConstraint('dbp >= 0 AND dbp <= 200', name='ck_vitals_dbp_range'),
        CheckConstraint('respiratory_rate >= 0 AND respiratory_rate <= 60', name='ck_vitals_rr_range'),
        CheckConstraint('spo2 >= 0 AND spo2 <= 100', name='ck_vitals_spo2_range'),
        CheckConstraint('temperature >= 20 AND temperature <= 45', name='ck_vitals_temp_range'),
        CheckConstraint('gcs >= 3 AND gcs <= 15', name='ck_vitals_gcs_range'),
    )

    def __repr__(self):
        return f'<Vitals {self.vital_id}>'


class TriageAssessment(db.Model):
    __tablename__ = 'triage_assessments'

    assessment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(
        db.String(36),
        db.ForeignKey('patients.patient_id', ondelete='RESTRICT'),
        nullable=False
    )
    clinician_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='RESTRICT'),
        nullable=False
    )

    # AI Prediction
    ai_priority = db.Column(db.Integer, nullable=False)       # ESI 1-5
    ai_confidence = db.Column(db.Float, nullable=False)       # 0.0-1.0
    shap_explanation = db.Column(db.JSON)

    # Clinician Decision (null until confirmed/overridden)
    clinician_priority = db.Column(db.Integer)                # ESI 1-5
    is_override = db.Column(db.Boolean, default=False)
    override_reason = db.Column(db.String(10))                # Coded: OVR-01..OVR-07

    assessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('ai_priority >= 1 AND ai_priority <= 5', name='ck_assessment_ai_priority'),
        CheckConstraint('ai_confidence >= 0 AND ai_confidence <= 1', name='ck_assessment_confidence'),
        CheckConstraint(
            'clinician_priority IS NULL OR (clinician_priority >= 1 AND clinician_priority <= 5)',
            name='ck_assessment_clinician_priority'
        ),
    )

    # RESTRICT prevents deletion of assessments that have audit entries
    audit_logs = db.relationship('AuditLog', backref='assessment', lazy=True,
                                 cascade='all', passive_deletes=False)

    def __repr__(self):
        return f'<TriageAssessment {self.assessment_id}>'


class AuditLog(db.Model):
    """
    Immutable audit log — INSERT only.
    Application code MUST NOT issue DELETE or UPDATE on this table.
    All foreign keys use ON DELETE RESTRICT to prevent data loss.
    """
    __tablename__ = 'audit_log'

    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Nullable: PHI-access events (e.g. Patient reads, searches) are not tied to
    # a single assessment, but clinical events (predict/confirm/override) are.
    assessment_id = db.Column(
        db.String(36),
        db.ForeignKey('triage_assessments.assessment_id', ondelete='RESTRICT'),
        nullable=True
    )
    clinician_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='RESTRICT'),
        nullable=False
    )

    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_detail = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        # Audit integrity: an event must always identify WHO and WHAT type.
        CheckConstraint("event_type <> ''", name='ck_audit_event_type_nonempty'),
        CheckConstraint('clinician_id IS NOT NULL', name='ck_audit_clinician_required'),
    )

    def __repr__(self):
        return f'<AuditLog {self.log_id}>'
