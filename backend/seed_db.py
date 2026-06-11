"""
Seed the database with initial admin and clinician users.
Run once: python seed_db.py

WARNING: This script generates random secure passwords for demo users.
These credentials must be changed immediately via /change-password in production.
Default seed credentials should NEVER be used in a live deployment.
"""
import secrets
import string
from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


def generate_random_password(length=14):
    """Generate a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


app = create_app('development')

with app.app_context():
    db.create_all()

    # Check if users already exist
    if User.query.count() > 0:
        print("Database already seeded. Skipping.")
    else:
        admin_pw = generate_random_password()
        nurse_pw = generate_random_password()
        doctor_pw = generate_random_password()

        admin = User(
            username='admin',
            password_hash=generate_password_hash(admin_pw),
            role='admin'
        )
        clinician = User(
            username='nurse_amara',
            password_hash=generate_password_hash(nurse_pw),
            role='clinician'
        )
        clinician2 = User(
            username='dr_kemal',
            password_hash=generate_password_hash(doctor_pw),
            role='clinician'
        )

        db.session.add_all([admin, clinician, clinician2])
        db.session.commit()

        print("=" * 60)
        print("  DATABASE SEEDED — SECURE CREDENTIALS")
        print("=" * 60)
        print(f"  Admin:     admin     / {admin_pw}")
        print(f"  Clinician: nurse_amara / {nurse_pw}")
        print(f"  Clinician: dr_kemal  / {doctor_pw}")
        print("=" * 60)
        print("  WARNING: Change these passwords via /change-password immediately!")
        print("=" * 60)

    print(f"\nTotal users: {User.query.count()}")
