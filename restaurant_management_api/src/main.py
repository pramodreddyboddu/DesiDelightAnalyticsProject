import os
import sys
from flask import Flask, jsonify, request, session, g
from flask_cors import CORS
from flask_session import Session
import logging
from datetime import timedelta, datetime
import uuid
from sqlalchemy import text
from tempfile import gettempdir

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

def create_app(config_name='default'):
    """Create and configure the Flask application with enhanced security."""
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Add Flask configuration to prevent redirects
    app.config['STRICT_SLASHES'] = False  # Don't redirect for trailing slashes
    app.config['PREFERRED_URL_SCHEME'] = 'http'  # For local development
    
    # Setup enhanced logging
    logger = setup_logger(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Session
    Session(app)
    
    # Configure session explicitly
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_COOKIE_SECURE'] = False  # For local development
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = None  # Allow cross-site requests
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_NAME'] = 'plateiq_session'
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'plateiq_'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(gettempdir(), 'plateiq_sessions')
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Create database tables and admin user
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
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
            # Update admin password if it exists
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.commit()
            logger.info('Admin user password updated')
    
    # Enhanced CORS configuration
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": app.config['CORS_ORIGINS'],
                 "methods": app.config['CORS_METHODS'],
                 "allow_headers": app.config['CORS_ALLOW_HEADERS'],
                 "expose_headers": app.config['CORS_EXPOSE_HEADERS'],
                 "supports_credentials": app.config['CORS_SUPPORTS_CREDENTIALS'],
                 "max_age": app.config['CORS_MAX_AGE']
             }
         },
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS']
    )
    
    # Enhanced request logging middleware
    @app.before_request
    def before_request():
        try:
            # Generate unique request ID for tracking
            g.request_id = str(uuid.uuid4())
            
            # Load user object if logged in
            g.user = None
            if 'user_id' in session:
                g.user = User.query.get(session['user_id'])
            
            # Log all requests for debugging
            logger.info(f"Request: {request.method} {request.path} - Origin: {request.headers.get('Origin', 'None')}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Session: {dict(session)}")
            
            # Log request information
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
    app.register_blueprint(tenant_bp, url_prefix='/api/tenant')
    logger.info("Blueprints registered successfully")
    
    # Health check endpoint
    @app.route('/')
    def index():
        return jsonify({
            'status': 'healthy',
            'message': 'PlateIQ Analytics API is running!',
            'version': '1.0.0'
        }), 200
    
    # Health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        try:
            # Check database connection using SQLAlchemy 2.0 compatible syntax
            db.session.execute(text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': str(datetime.now())
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
