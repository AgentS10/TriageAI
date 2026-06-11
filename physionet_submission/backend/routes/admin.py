from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, TriageAssessment, AuditLog, Patient
from security import require_roles, log_phi_access
from datetime import datetime, timedelta
import pandas as pd

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        users = User.query.all()
        users_data = []
        
        for u in users:
            users_data.append({
                'user_id': u.user_id,
                'username': u.username,
                'role': u.role,
                'created_at': u.created_at.isoformat(),
                'is_active': u.is_active
            })
        
        return jsonify({'users': users_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users', 'details': str(e)}), 500

@admin_bp.route('/users/<user_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_user_status(user_id):
    """Activate/deactivate user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        target_user = db.session.get(User, user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        target_user.is_active = not target_user.is_active
        db.session.commit()
        
        status = 'activated' if target_user.is_active else 'deactivated'
        return jsonify({
            'message': f'User {target_user.username} {status} successfully',
            'user_id': target_user.user_id,
            'is_active': target_user.is_active
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle user status', 'details': str(e)}), 500


@admin_bp.route('/users/<user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    """Reset a user's password (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        admin = db.session.get(User, current_user_id)
        if not admin or admin.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

        target_user = db.session.get(User, user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        new_password = data.get('new_password')
        if not new_password:
            return jsonify({'error': 'new_password is required'}), 400

        from routes.auth import validate_password
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': msg}), 400

        from werkzeug.security import generate_password_hash
        target_user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({
            'message': f'Password for {target_user.username} reset successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password reset failed', 'details': str(e)}), 500


@admin_bp.route('/users/<user_id>/update', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user details - username and/or role (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        admin = db.session.get(User, current_user_id)
        if not admin or admin.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

        target_user = db.session.get(User, user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        if 'username' in data:
            new_username = data['username'].strip()
            if len(new_username) < 3:
                return jsonify({'error': 'Username must be at least 3 characters'}), 400
            existing = User.query.filter_by(username=new_username).first()
            if existing and existing.user_id != user_id:
                return jsonify({'error': 'Username already taken'}), 409
            target_user.username = new_username

        if 'role' in data:
            if data['role'] not in ['clinician', 'admin']:
                return jsonify({'error': 'Invalid role'}), 400
            target_user.role = data['role']

        db.session.commit()

        return jsonify({
            'message': f'User {target_user.username} updated successfully',
            'user': {
                'user_id': target_user.user_id,
                'username': target_user.username,
                'role': target_user.role,
                'is_active': target_user.is_active
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'User update failed', 'details': str(e)}), 500


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only) — only if they have no assessments"""
    try:
        current_user_id = get_jwt_identity()
        admin = db.session.get(User, current_user_id)
        if not admin or admin.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

        if user_id == current_user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400

        target_user = db.session.get(User, user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        assessment_count = TriageAssessment.query.filter_by(clinician_id=user_id).count()
        if assessment_count > 0:
            return jsonify({
                'error': f'Cannot delete user with {assessment_count} assessments. Deactivate instead.'
            }), 409

        db.session.delete(target_user)
        db.session.commit()

        return jsonify({'message': f'User {target_user.username} deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'User deletion failed', 'details': str(e)}), 500


@admin_bp.route('/patients/search', methods=['GET'])
@require_roles('clinician', 'admin')
def search_patients():
    """Search patient assessments by various criteria (PHI access — audited)"""
    try:
        query_param = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 50)

        query = db.session.query(TriageAssessment, Patient).join(
            Patient, TriageAssessment.patient_id == Patient.patient_id
        )

        query = query.order_by(TriageAssessment.assessed_at.desc())
        results = query.all()

        # Client-side filter because chief_complaint is encrypted at rest
        if query_param:
            qp = query_param.lower()
            results = [
                (a, p) for a, p in results
                if qp in p.chief_complaint.lower() or qp in p.patient_id.lower()
            ]

        total = len(results)
        start = (page - 1) * per_page
        paginated = results[start:start + per_page]

        patients_data = []
        for assessment, patient in paginated:
            patients_data.append({
                'assessment_id': assessment.assessment_id,
                'patient_id': patient.patient_id,
                'age': patient.age,
                'sex': patient.sex,
                'chief_complaint': patient.chief_complaint,
                'pain_score': patient.pain_score,
                'ai_priority': assessment.ai_priority,
                'clinician_priority': assessment.clinician_priority,
                'is_override': assessment.is_override,
                'assessed_at': assessment.assessed_at.isoformat(),
                'status': 'resolved' if assessment.clinician_priority else 'pending'
            })

        log_phi_access('phi_search', f'Patient search: q="{query_param}" ({total} matches)')

        return jsonify({
            'results': patients_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page if per_page else 1
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500


@admin_bp.route('/audit-log', methods=['GET'])
@jwt_required()
def get_audit_log():
    """Get audit log with filtering options (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        event_type = request.args.get('event_type')
        clinician_id = request.args.get('clinician_id')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Build query
        query = AuditLog.query.join(User, AuditLog.clinician_id == User.user_id)
        
        # Apply filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.timestamp >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.timestamp <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        if clinician_id:
            query = query.filter(AuditLog.clinician_id == clinician_id)
        
        # Order by timestamp descending
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Paginate
        total = query.count()
        logs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'log_id': log.log_id,
                'assessment_id': log.assessment_id,
                'clinician_id': log.clinician_id,
                'clinician_name': log.clinician.username,
                'event_type': log.event_type,
                'event_detail': log.event_detail,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp.isoformat()
            })
        
        return jsonify({
            'audit_log': logs_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get audit log', 'details': str(e)}), 500

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get system analytics and statistics (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        # Time range
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic statistics
        total_assessments = TriageAssessment.query.filter(
            TriageAssessment.assessed_at >= start_date
        ).count()
        
        confirmed_assessments = TriageAssessment.query.filter(
            TriageAssessment.assessed_at >= start_date,
            TriageAssessment.clinician_priority.isnot(None)
        ).count()
        
        overridden_assessments = TriageAssessment.query.filter(
            TriageAssessment.assessed_at >= start_date,
            TriageAssessment.is_override == True
        ).count()
        
        # AI vs Clinician agreement rate
        agreements = TriageAssessment.query.filter(
            TriageAssessment.assessed_at >= start_date,
            TriageAssessment.clinician_priority == TriageAssessment.ai_priority,
            TriageAssessment.clinician_priority.isnot(None)
        ).count()
        
        agreement_rate = (agreements / confirmed_assessments * 100) if confirmed_assessments > 0 else 0
        
        # ESI level distribution
        esi_distribution = db.session.query(
            TriageAssessment.ai_priority,
            db.func.count(TriageAssessment.assessment_id)
        ).filter(
            TriageAssessment.assessed_at >= start_date
        ).group_by(TriageAssessment.ai_priority).all()
        
        # Override reasons
        override_reasons = db.session.query(
            TriageAssessment.override_reason,
            db.func.count(TriageAssessment.assessment_id)
        ).filter(
            TriageAssessment.assessed_at >= start_date,
            TriageAssessment.is_override == True
        ).group_by(TriageAssessment.override_reason).all()
        
        # Clinician performance
        clinician_stats = db.session.query(
            User.username,
            db.func.count(TriageAssessment.assessment_id).label('total_assessments'),
            db.func.sum(
                db.case(
                    (TriageAssessment.is_override == True, 1),
                    else_=0
                )
            ).label('overrides'),
            db.func.avg(
                db.case(
                    (TriageAssessment.clinician_priority == TriageAssessment.ai_priority, 1),
                    (TriageAssessment.clinician_priority.isnot(None), 0),
                    else_=None
                )
            ).label('agreement_rate')
        ).join(
            TriageAssessment, User.user_id == TriageAssessment.clinician_id
        ).filter(
            TriageAssessment.assessed_at >= start_date
        ).group_by(User.user_id, User.username).all()
        
        # Daily assessment volume
        daily_volume = db.session.query(
            db.func.date(TriageAssessment.assessed_at).label('date'),
            db.func.count(TriageAssessment.assessment_id).label('count')
        ).filter(
            TriageAssessment.assessed_at >= start_date
        ).group_by(db.func.date(TriageAssessment.assessed_at)).all()
        
        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'days': days
            },
            'overview': {
                'total_assessments': total_assessments,
                'confirmed_assessments': confirmed_assessments,
                'overridden_assessments': overridden_assessments,
                'override_rate': (overridden_assessments / confirmed_assessments * 100) if confirmed_assessments > 0 else 0,
                'ai_clinician_agreement_rate': round(agreement_rate, 2)
            },
            'esi_distribution': [
                {'level': level, 'count': count} for level, count in esi_distribution
            ],
            'override_reasons': [
                {'reason': reason, 'count': count} for reason, count in override_reasons if reason
            ],
            'clinician_performance': [
                {
                    'username': username,
                    'total_assessments': total_assessments,
                    'overrides': overrides,
                    'agreement_rate': round(float(agreement_rate) * 100, 2) if agreement_rate else 0
                } for username, total_assessments, overrides, agreement_rate in clinician_stats
            ],
            'daily_volume': [
                {'date': str(date), 'count': count} for date, count in daily_volume
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get analytics', 'details': str(e)}), 500

@admin_bp.route('/export/audit-log', methods=['GET'])
@jwt_required()
def export_audit_log():
    """Export audit log as CSV (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = AuditLog.query.join(User, AuditLog.clinician_id == User.user_id)
        
        # Apply filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp <= end_dt)
        
        # Get all logs
        logs = query.order_by(AuditLog.timestamp.desc()).all()
        
        # Convert to DataFrame
        data = []
        for log in logs:
            data.append({
                'Timestamp': log.timestamp.isoformat(),
                'Clinician': log.clinician.username,
                'Event Type': log.event_type,
                'Event Detail': log.event_detail,
                'IP Address': log.ip_address,
                'Assessment ID': log.assessment_id
            })
        
        df = pd.DataFrame(data)
        
        # Convert to CSV
        csv_data = df.to_csv(index=False)
        
        from flask import Response
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=audit_log_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': 'Failed to export audit log', 'details': str(e)}), 500


@admin_bp.route('/settings', methods=['GET', 'PUT'])
@jwt_required()
def system_settings():
    """Get or update system settings (admin only)."""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

        # Simple in-memory defaults (in production, persist to a settings table)
        defaults = {
            'session_timeout_minutes': 15,
            'rate_limit_attempts': 5,
            'rate_limit_window_minutes': 15,
            'app_name': 'TriageAI',
            'version': '1.0.0'
        }

        if request.method == 'GET':
            return jsonify({'settings': defaults}), 200

        data = request.get_json() or {}
        # Merge incoming settings with defaults
        updated = {**defaults, **{k: v for k, v in data.items() if k in defaults}}
        return jsonify({'message': 'Settings updated', 'settings': updated}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to process settings', 'details': str(e)}), 500
