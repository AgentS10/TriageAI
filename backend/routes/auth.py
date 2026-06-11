from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Simple in-memory rate limiter for login attempts
_login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


def _check_rate_limit(identifier):
    """Check if identifier (IP) has exceeded login attempts."""
    now = datetime.utcnow()
    # Clean old attempts
    _login_attempts[identifier] = [t for t in _login_attempts[identifier] if now - t < LOCKOUT_DURATION]
    if len(_login_attempts[identifier]) >= MAX_LOGIN_ATTEMPTS:
        remaining = LOCKOUT_DURATION - (now - _login_attempts[identifier][0])
        return False, int(remaining.total_seconds())
    return True, 0


def _record_failed_attempt(identifier):
    """Record a failed login attempt."""
    _login_attempts[identifier].append(datetime.utcnow())

auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    """Register a new user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        admin = db.session.get(User, current_user_id)
        if not admin or admin.role != 'admin':
            return jsonify({'error': 'Only administrators can create users'}), 403

        data = request.get_json()
        required_fields = ['username', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        if data['role'] not in ['clinician', 'admin']:
            return jsonify({'error': 'Invalid role. Must be "clinician" or "admin"'}), 400

        is_valid, password_msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': password_msg}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409

        user = User(
            username=data['username'],
            password_hash=generate_password_hash(data['password']),
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'message': f'User {user.username} created successfully',
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change own password (any authenticated user)"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'current_password and new_password are required'}), 400

        if not check_password_hash(user.password_hash, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401

        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': msg}), 400

        if data['current_password'] == data['new_password']:
            return jsonify({'error': 'New password must be different from current password'}), 400

        user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()

        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password change failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        allowed, lockout_remaining = _check_rate_limit(client_ip)
        if not allowed:
            return jsonify({
                'error': f'Too many login attempts. Try again in {lockout_remaining // 60} minutes.',
                'locked_until_seconds': lockout_remaining
            }), 429

        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            _record_failed_attempt(client_ip)
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Create tokens
        access_token = create_access_token(identity=user.user_id)
        refresh_token = create_refresh_token(identity=user.user_id)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 404
        
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({'access_token': new_access_token}), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'created_at': user.created_at.isoformat(),
            'is_active': user.is_active
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500


@auth_bp.route('/profile/activity', methods=['GET'])
@jwt_required()
def get_profile_activity():
    """Get own activity log, stats, and recent assessments."""
    try:
        from extensions import db
        from models import TriageAssessment
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        recent = TriageAssessment.query.filter_by(
            clinician_id=current_user_id
        ).order_by(TriageAssessment.assessed_at.desc()).limit(10).all()

        total = TriageAssessment.query.filter_by(clinician_id=current_user_id).count()
        confirmed = TriageAssessment.query.filter_by(
            clinician_id=current_user_id, is_override=False
        ).filter(TriageAssessment.clinician_priority.isnot(None)).count()
        overridden = TriageAssessment.query.filter_by(
            clinician_id=current_user_id, is_override=True
        ).count()
        pending = TriageAssessment.query.filter_by(
            clinician_id=current_user_id
        ).filter(TriageAssessment.clinician_priority.is_(None)).count()

        return jsonify({
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at.isoformat(),
                'is_active': user.is_active
            },
            'stats': {
                'total_assessments': total,
                'confirmed': confirmed,
                'overridden': overridden,
                'pending': pending
            },
            'recent_activity': [
                {
                    'assessment_id': a.assessment_id,
                    'ai_priority': a.ai_priority,
                    'clinician_priority': a.clinician_priority,
                    'is_override': a.is_override,
                    'status': 'resolved' if a.clinician_priority else 'pending',
                    'assessed_at': a.assessed_at.isoformat()
                } for a in recent
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get activity', 'details': str(e)}), 500
