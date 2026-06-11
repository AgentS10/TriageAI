"""
Shared Flask extension instances.
Prevents circular imports between app.py, models.py, and routes.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Optional rate limiter — degrades to a no-op if flask-limiter is absent
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=[])
    LIMITER_AVAILABLE = True
except ImportError:  # pragma: no cover
    LIMITER_AVAILABLE = False

    class _NoopLimiter:
        """Fallback so routes can use @limiter.limit even without the package."""
        def init_app(self, app):
            pass

        def limit(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    limiter = _NoopLimiter()
