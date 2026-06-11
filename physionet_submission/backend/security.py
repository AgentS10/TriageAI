"""
TriageAI — Security & Access Control Helpers
=============================================
Centralises Role-Based Access Control (RBAC) and PHI access auditing so
that every protected route enforces the same rules.

Compliance references:
  - HIPAA Security Rule 164.312(a)(1) — Access control (RBAC)
  - HIPAA Security Rule 164.312(b)    — Audit controls (log PHI access)
  - HIPAA Privacy Rule  164.502(b)    — Minimum necessary (role scoping)
"""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from extensions import db
from models import User, AuditLog


def get_current_user():
    """Return the authenticated User row, or None."""
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def require_roles(*roles):
    """
    Decorator: require a valid JWT AND that the user holds one of `roles`.
    Usage: @require_roles('clinician', 'admin')
    Returns 401 if unauthenticated/inactive, 403 if role not permitted.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user or not user.is_active:
                return jsonify({'error': 'Unauthorized'}), 401
            if roles and user.role not in roles:
                return jsonify({'error': 'Forbidden: insufficient privileges'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def log_phi_access(event_type, event_detail, assessment_id=None):
    """
    Write an immutable PHI-access entry to the audit trail (HIPAA 164.312(b)).
    Records WHO accessed WHAT and from WHERE. Safe to call inside a request
    that has a valid JWT; failures are swallowed so auditing never breaks the
    primary response, but they are surfaced via the return value.
    """
    try:
        user_id = get_jwt_identity()
        entry = AuditLog(
            assessment_id=assessment_id,
            clinician_id=user_id,
            event_type=event_type,
            event_detail=event_detail,
            ip_address=request.remote_addr,
        )
        db.session.add(entry)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
