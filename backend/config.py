"""
TriageAI Configuration Module
Centralised configuration for all environments with security best practices.
"""
import os
from datetime import timedelta


class BaseConfig:
    """Base configuration shared across all environments."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Security headers
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True

    # Rate limiting (flask-limiter)
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "200 per hour"
    RATELIMIT_PREDICT = "60 per minute"

    # Force HTTPS redirect (enabled in production)
    FORCE_HTTPS = False

    # Model artifact paths (relative to backend/)
    MODEL_PIPELINE_PATH = os.path.join(os.path.dirname(__file__), 'ml', 'artifacts', 'triage_pipeline.joblib')
    FEATURE_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), 'ml', 'artifacts', 'feature_contract.json')
    LABEL_ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'ml', 'artifacts', 'label_encoder.joblib')
    CATEGORICAL_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), 'ml', 'artifacts', 'categorical_registry.json')

    # Locale (English only)
    DEFAULT_LOCALE = 'en'
    SUPPORTED_LOCALES = ['en']


class DevelopmentConfig(BaseConfig):
    """Development configuration using SQLite."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///triageai_dev.db')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-only-secret-change-in-production')


class TestingConfig(BaseConfig):
    """Testing configuration using in-memory SQLite."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-secret-key-must-be-at-least-32-characters-long'
    # Disable global rate limiting during tests for deterministic runs
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production configuration using PostgreSQL."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://triageai_user:triageai_password@localhost:5432/triageai'
    )
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    FORCE_HTTPS = True

    @classmethod
    def init_app(cls, app):
        if not cls.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable must be set in production.")


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
