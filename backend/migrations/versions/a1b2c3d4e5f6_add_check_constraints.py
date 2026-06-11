"""add CHECK constraints for data integrity & audit security

Adds database-level CHECK constraints so invalid clinical data and malformed
audit entries are rejected by the database itself (defence in depth), not just
the application layer.

Revision ID: a1b2c3d4e5f6
Revises: 7d43822ad7ad
Create Date: 2026-06-06 04:20:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7d43822ad7ad'
branch_labels = None
depends_on = None


PATIENT_CHECKS = [
    ('ck_patient_age_range', 'age >= 0 AND age <= 120'),
    ('ck_patient_pain_range', 'pain_score >= 0 AND pain_score <= 10'),
    ('ck_patient_sex_hl7', "sex IN ('M', 'F', 'O', 'U')"),
]

VITALS_CHECKS = [
    ('ck_vitals_hr_range', 'heart_rate >= 0 AND heart_rate <= 300'),
    ('ck_vitals_sbp_range', 'sbp >= 0 AND sbp <= 300'),
    ('ck_vitals_dbp_range', 'dbp >= 0 AND dbp <= 200'),
    ('ck_vitals_rr_range', 'respiratory_rate >= 0 AND respiratory_rate <= 60'),
    ('ck_vitals_spo2_range', 'spo2 >= 0 AND spo2 <= 100'),
    ('ck_vitals_temp_range', 'temperature >= 20 AND temperature <= 45'),
    ('ck_vitals_gcs_range', 'gcs >= 3 AND gcs <= 15'),
]

ASSESSMENT_CHECKS = [
    ('ck_assessment_ai_priority', 'ai_priority >= 1 AND ai_priority <= 5'),
    ('ck_assessment_confidence', 'ai_confidence >= 0 AND ai_confidence <= 1'),
    ('ck_assessment_clinician_priority',
     'clinician_priority IS NULL OR (clinician_priority >= 1 AND clinician_priority <= 5)'),
]

AUDIT_CHECKS = [
    ('ck_audit_event_type_nonempty', "event_type <> ''"),
    ('ck_audit_clinician_required', 'clinician_id IS NOT NULL'),
]

TABLES = [
    ('patients', PATIENT_CHECKS),
    ('vitals', VITALS_CHECKS),
    ('triage_assessments', ASSESSMENT_CHECKS),
    ('audit_log', AUDIT_CHECKS),
]


def upgrade():
    for table, checks in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            for name, condition in checks:
                batch_op.create_check_constraint(name, condition)


def downgrade():
    for table, checks in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            for name, _condition in checks:
                batch_op.drop_constraint(name, type_='check')
