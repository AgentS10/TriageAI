"""
TriageAI PII Encryption at Rest
=================================
Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) for patient PII.

Key management (HIPAA 164.312(a)(2)(iv) — encryption at rest):
  - Primary key precedence:
      1. PII_ENCRYPTION_KEY    — an explicit urlsafe-base64 Fernet key (preferred;
                                 lets ops manage/rotate keys outside source code)
      2. Derived key           — PBKDF2-HMAC-SHA256 over JWT_SECRET_KEY + salt
  - Salt is configurable via PII_ENCRYPTION_SALT (defaults to the legacy salt so
    previously-encrypted data still decrypts).
  - Key rotation: set PII_ENCRYPTION_KEYS_RETIRED to a comma-separated list of
    old Fernet keys. MultiFernet encrypts with the primary key but can still
    decrypt data written under any retired key, enabling zero-downtime rotation.

Encrypted fields: chief_complaint (and any future free-text PII fields).
"""
import os
import base64
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_fernet_instance = None


def _derive_key():
    """Derive a Fernet key from JWT_SECRET_KEY + configurable salt."""
    secret = os.getenv('JWT_SECRET_KEY', 'dev-only-secret-change-in-production')
    salt = os.getenv('PII_ENCRYPTION_SALT', 'triageai-pii-salt-v1').encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def _get_fernet():
    """Build (and cache) a MultiFernet supporting an explicit key + rotation."""
    global _fernet_instance
    if _fernet_instance is None:
        keys = []
        # 1. Explicit primary key (used for new encryptions if present)
        explicit = os.getenv('PII_ENCRYPTION_KEY')
        if explicit:
            keys.append(Fernet(explicit.encode()))
        # 2. Derived key (also kept so legacy/derived-encrypted data decrypts)
        keys.append(Fernet(_derive_key()))
        # 3. Retired keys — decrypt-only, for rotation windows
        retired = os.getenv('PII_ENCRYPTION_KEYS_RETIRED', '')
        for k in (x.strip() for x in retired.split(',') if x.strip()):
            keys.append(Fernet(k.encode()))
        _fernet_instance = MultiFernet(keys)
    return _fernet_instance


def reset_cipher_cache():
    """Clear cached cipher (used in tests after changing key env vars)."""
    global _fernet_instance
    _fernet_instance = None


def encrypt_field(plaintext):
    """Encrypt a string field for database storage."""
    if plaintext is None:
        return None
    f = _get_fernet()
    return f.encrypt(str(plaintext).encode()).decode()


def decrypt_field(ciphertext):
    """Decrypt a string field from database storage."""
    if ciphertext is None:
        return None
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext
