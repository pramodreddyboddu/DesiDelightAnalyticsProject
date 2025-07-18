import os
import sys
from flask import Flask, jsonify, request, session, g
from flask_cors import CORS
from flask_session import Session
import logging
from datetime import timedelta, datetime
import uuid
from sqlalchemy import text

# Add Flask-Migrate for migrations
from flask_migrate import Migrate

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.upload import upload_bp
from src.routes.dashboard import dashboard_bp
from src.routes.reports import reports_bp
from src.routes.admin import admin_bp
from src.routes.inventory import inventory_bp
from src.routes.ai import ai_bp
from src.routes.tenant import tenant_bp
from src.routes.tenant_data import tenant_data_bp
from src.routes.clover import clover_bp
from src.models import db
from src.models.user import User
from src.models.item import Item
from src.models.sale import Sale
from src.models.chef import Chef
from src.models.chef_dish_mapping import ChefDishMapping
from src.models.expense import Expense
from src.models.category import Category
from src.models.uncategorized_item import UncategorizedItem
from src.models.file_upload import FileUpload
from src.models.tenant import Tenant
from src.config import config
from src.utils.logger import setup_logger, log_request_info
from src.utils.error_handlers import setup_error_handlers, log_request_error

def create_app(config_name=None):
    """Create and configure the Flask application with enhanced security."""
    
    if not config_name:
        config_name = os.environ.get('FLASK_CONFIG', 'production')
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Setup enhanced logging first
    logger = setup_logger(app)
    
    # Debug print for CORS origins
    print("CORS_ORIGINS at startup:", app.config['CORS_ORIGINS'])
    
    # Add Flask configuration to prevent redirects
    app.config['STRICT_SLASHES'] = False  # Don't redirect for trailing slashes
    app.config['PREFERRED_URL_SCHEME'] = 'http'  # For local development
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Initialize extensions
    db.init_app(app)
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    # Initialize Flask-Session (config-driven)
    Session(app)
    
    # Create database tables and admin user
    with app.app_context():
        logger.info('Ensuring all database tables exist...')
        db.create_all()
        logger.info('Database tables created or already exist')
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin:
            admin = User(
                username=app.config['ADMIN_USERNAME'], 
                role='admin', 
                is_admin=True
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            logger.info('Admin user created successfully')
        else:
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.commit()
            logger.info('Admin user password updated')

    # Robust CORS setup: allow all backend endpoints for the Vercel frontend and Heroku
    # NOTE: If you change your frontend domain, update this list!
    CORS(
        app,
        resources={r"/*": {"origins": [
            "https://desi-delight-analytics-project.vercel.app",
            "https://desi-delight-analytics-project-pkhf.vercel.app",
            "https://desi-delight-analytics-project-usvt.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000"
        ]}},
        supports_credentials=True,
        allow_headers=app.config['CORS_ALLOW_HEADERS'] + ['Cookie', 'Set-Cookie'],
        expose_headers=app.config['CORS_EXPOSE_HEADERS'] + ['Set-Cookie'],
        methods=app.config['CORS_METHODS'],
        max_age=app.config['CORS_MAX_AGE']
    )

    # Enhanced request logging middleware
    @app.before_request
    def before_request():
        try:
            g.request_id = str(uuid.uuid4())
            g.user = None
            if 'user_id' in session:
                g.user = User.query.get(session['user_id'])
            logger.info(f"Request: {request.method} {request.path} - Origin: {request.headers.get('Origin', 'None')}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Session: {dict(session)}")
            if request.method in ['POST', 'PUT', 'DELETE']:
                log_request_info()
        except Exception as e:
            logger.error(f"Error in before_request: {str(e)}")

    # Register blueprints
    logger.info("Registering blueprints...")
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(clover_bp, url_prefix='/api/clover')
    app.register_blueprint(tenant_bp, url_prefix='/api/tenant')
    app.register_blueprint(tenant_data_bp, url_prefix='/api/tenant-data')
    logger.info("Blueprints registered successfully")

    # Global after_request CORS handler
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        allowed_origins = app.config['CORS_ORIGINS']
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cookie, Set-Cookie'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Expose-Headers'] = 'Set-Cookie'
        return response

    # Global OPTIONS handler for CORS preflight
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        response = app.make_response('')
        origin = request.headers.get('Origin')
        if origin in app.config['CORS_ORIGINS']:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cookie, Set-Cookie'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response, 200

    # Health check endpoint
    @app.route('/')
    def index():
        return jsonify({
            'status': 'healthy',
            'message': 'PlateIQ Analytics API is running!',
            'version': '1.0.0'
        }), 200

    # Health check endpoint for monitoring
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'version': '1.0.0'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'disconnected',
                'error': str(e)
            }), 500

    # Test endpoint for CORS debugging
    @app.route('/api/test-cors', methods=['GET', 'OPTIONS'])
    def test_cors():
        if request.method == 'OPTIONS':
            response = app.make_response('')
            response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cookie'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 200
        return jsonify({
            'message': 'CORS test successful',
            'session': dict(session),
            'cookies': dict(request.cookies)
        }), 200

    # Debug endpoint for authentication status
    @app.route('/api/debug/auth', methods=['GET'])
    def debug_auth():
        """Debug endpoint to check authentication status"""
        return jsonify({
            'session_exists': 'user_id' in session,
            'user_id': session.get('user_id'),
            'session_data': dict(session),
            'cookies': dict(request.cookies),
            'headers': dict(request.headers),
            'origin': request.headers.get('Origin'),
            'referer': request.headers.get('Referer')
        }), 200

    # Debug endpoint for cookie testing
    @app.route('/api/debug/cookies', methods=['GET', 'POST'])
    def debug_cookies():
        """Debug endpoint to test cookie handling"""
        if request.method == 'POST':
            # Set a test cookie
            response = jsonify({
                'message': 'Test cookie set',
                'cookies_received': dict(request.cookies),
                'session_data': dict(session)
            })
            response.set_cookie(
                'test_cookie',
                'test_value',
                secure=True,
                httponly=False,  # Allow JavaScript access for testing
                samesite='None',
                path='/',
                max_age=3600
            )
            return response, 200
        else:
            # Check cookies
            return jsonify({
                'cookies_received': dict(request.cookies),
                'session_data': dict(session),
                'headers': {k: v for k, v in request.headers.items() if k.lower() in ['cookie', 'origin', 'referer']}
            }), 200

    return app

# Expose app for Gunicorn/Heroku
app = create_app()

if __name__ == '__main__':
    # Only runs for local development
    app.run(
        debug=False,
        host=os.environ.get('FLASK_RUN_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_RUN_PORT', 5000))
    )
