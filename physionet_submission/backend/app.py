"""
TriageAI Flask Application Factory
====================================
Addresses:
  - Data security (OWASP headers, CORS whitelist, input sanitization)
  - Localization (Accept-Language header → locale selection)
  - Immutable audit logging (no DELETE/UPDATE on audit_log)
  - Feature contract validation at startup
"""
from flask import Flask, request, g, jsonify, redirect
from flask_cors import CORS
from extensions import db, migrate, jwt, limiter
from datetime import datetime
import os
import json
import logging

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('triageai')


def load_locale(locale_code):
    """Load a locale JSON file from backend/locales/."""
    locale_dir = os.path.join(os.path.dirname(__file__), 'locales')
    path = os.path.join(locale_dir, f'{locale_code}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Fallback to English
    with open(os.path.join(locale_dir, 'en.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)

    # Load configuration
    from config import CONFIG_MAP
    config_class = CONFIG_MAP.get(config_name)
    if config_class is None:
        raise ValueError(f"Unknown config: {config_name}")
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # CORS — restrict origins in production
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # ── FORCE HTTPS (production) ───────────────────────────────────
    @app.before_request
    def enforce_https():
        if app.config.get('FORCE_HTTPS'):
            proto = request.headers.get('X-Forwarded-Proto', 'http')
            if proto != 'https':
                return redirect(request.url.replace('http://', 'https://', 1), code=301)

    # ── SECURITY HEADERS (OWASP) ──────────────────────────────────
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response

    # ── LOCALIZATION MIDDLEWARE (English only) ─────────────────────
    @app.before_request
    def set_locale():
        g.locale = 'en'
        g.translations = load_locale('en')

    # ── INPUT SANITIZATION ────────────────────────────────────────
    @app.before_request
    def sanitize_json_input():
        if request.is_json and request.data:
            try:
                data = request.get_json(silent=True)
                if data is None:
                    return jsonify({'error': 'Invalid JSON payload'}), 400
            except Exception:
                return jsonify({'error': 'Malformed request body'}), 400

    # ── FEATURE CONTRACT VALIDATION AT STARTUP ────────────────────
    with app.app_context():
        try:
            from ml.feature_contract import validate_contract_against_model
            contract_path = app.config.get('FEATURE_CONTRACT_PATH')
            if contract_path and os.path.exists(contract_path):
                validate_contract_against_model(contract_path)
                logger.info("Feature contract validated successfully.")
            else:
                logger.warning("Feature contract not found — model not yet trained.")
        except RuntimeError as e:
            logger.error(f"FEATURE CONTRACT MISMATCH: {e}")
        except Exception as e:
            logger.warning(f"Contract validation skipped: {e}")

    # ── REGISTER BLUEPRINTS ───────────────────────────────────────
    # Every blueprint is mounted twice: at the legacy unversioned prefix
    # (kept for backward compatibility) and at the versioned /api/v1 prefix.
    # Versioning lets us ship breaking changes (v2) without disrupting
    # existing clients. The unique `name=` avoids Flask registration clashes.
    from routes.auth import auth_bp
    from routes.predict import predict_bp
    from routes.admin import admin_bp
    from routes.fhir import fhir_bp
    from routes.monitoring import monitoring_bp

    blueprint_mounts = [
        (auth_bp, 'auth'),
        (predict_bp, ''),
        (admin_bp, 'admin'),
        (fhir_bp, 'fhir'),
        (monitoring_bp, 'monitoring'),
    ]

    for bp, suffix in blueprint_mounts:
        sub = f'/{suffix}' if suffix else ''
        # Legacy unversioned mount (original behaviour).
        app.register_blueprint(bp, url_prefix=f'/api{sub}')
        # Versioned mount (distinct endpoint name to satisfy Flask).
        app.register_blueprint(bp, url_prefix=f'/api/v1{sub}', name=f'{bp.name}_v1')

    # ── SWAGGER / OPENAPI ───────────────────────────────────────
    try:
        from flasgger import Swagger
        swagger_config = {
            'headers': [],
            'specs': [{
                'endpoint': 'apispec',
                'route': '/apispec.json',
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True,
            }],
            'static_url_path': '/flasgger_static',
            'swagger_ui': True,
            'specs_route': '/apidocs/'
        }
        swagger_template = {
            'info': {
                'title': 'TriageAI API',
                'description': 'Clinical Decision Support System for Emergency Department Patient Triage',
                'version': '1.0.0',
                'contact': {'name': 'M.S.M.Sajidh', 'email': 'CL/BSCSD/34/01'}
            },
            'securityDefinitions': {
                'Bearer': {
                    'type': 'apiKey',
                    'name': 'Authorization',
                    'in': 'header',
                    'description': 'JWT token: Bearer {token}'
                }
            }
        }
        Swagger(app, config=swagger_config, template=swagger_template)
        logger.info("Swagger UI available at /apidocs/")
    except ImportError:
        logger.warning("Flasgger not installed — Swagger UI disabled")

    # ── HEALTH CHECK ──────────────────────────────────────────────
    @app.route('/api/health', methods=['GET'])
    @limiter.limit("60 per minute")
    def health_check():
        """System health check
        ---
        responses:
          200:
            description: System is healthy
        """
        return jsonify({
            'status': 'healthy',
            'locale': g.get('locale', 'en'),
            'version': '1.0.0'
        }), 200

    # ── MODEL METRICS ─────────────────────────────────────────────
    @app.route('/api/model-metrics', methods=['GET'])
    def model_metrics():
        """Get current ML model performance metrics
        ---
        responses:
          200:
            description: Model metrics
        """
        import cache
        cached = cache.get('model_metrics')
        if cached is not None:
            return jsonify(cached), 200

        metrics_path = os.path.join(os.path.dirname(__file__), 'ml', 'artifacts', 'model_metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                data = json.load(f)
            cache.set('model_metrics', data, ttl=3600)
            return jsonify(data), 200
        return jsonify({'error': 'Model metrics not available'}), 404

    # ── DETAILED HEALTH CHECK ─────────────────────────────────────
    app_start_time = datetime.utcnow().timestamp()

    @app.route('/api/health/detailed', methods=['GET'])
    @limiter.limit("30 per minute")
    def health_detailed():
        """Detailed system health: DB, model, uptime, contract hash."""
        from sqlalchemy import text
        status = {'status': 'healthy', 'components': {}, 'timestamp': datetime.utcnow().isoformat()}

        # Database check
        try:
            db.session.execute(text('SELECT 1'))
            status['components']['database'] = 'connected'
        except Exception as e:
            status['components']['database'] = f'error: {str(e)}'
            status['status'] = 'degraded'

        # Model check
        artifacts_dir = os.path.join(os.path.dirname(__file__), 'ml', 'artifacts')
        pipeline_path = os.path.join(artifacts_dir, 'triage_pipeline.joblib')
        contract_path = os.path.join(artifacts_dir, 'feature_contract.json')
        if os.path.exists(pipeline_path) and os.path.exists(contract_path):
            status['components']['model'] = 'loaded'
            try:
                from ml.feature_contract import get_contract_hash
                status['model_contract_hash'] = get_contract_hash()
            except Exception:
                pass
        else:
            status['components']['model'] = 'not_loaded'
            status['status'] = 'degraded'

        status['uptime_seconds'] = int(datetime.utcnow().timestamp() - app_start_time)
        return jsonify(status), 200 if status['status'] == 'healthy' else 503

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
