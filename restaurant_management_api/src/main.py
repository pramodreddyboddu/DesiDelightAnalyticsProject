import os
import sys
from flask import Flask, jsonify, request, send_from_directory, session, g
from flask_cors import CORS
from flask_session import Session
import logging
from datetime import timedelta, datetime
import shutil
import pickle
import uuid

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.upload import upload_bp
from src.routes.dashboard import dashboard_bp
from src.routes.reports import reports_bp
from src.routes.admin import admin_bp
from src.routes.inventory import inventory_bp
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
from src.config import config
from src.utils.logger import setup_logger, log_request_info
from src.utils.error_handlers import setup_error_handlers, log_request_error

def create_app(config_name='default'):
    """Create and configure the Flask application with enhanced security."""
    
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Setup enhanced logging
    logger = setup_logger(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Initialize extensions
    db.init_app(app)
    
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
    
    # Configure session with enhanced security
    session_dir = os.path.join(app.instance_path, 'flask_session')
    os.makedirs(session_dir, exist_ok=True)
    
    app.config['SESSION_FILE_DIR'] = session_dir
    app.config['SESSION_FILE_THRESHOLD'] = app.config.get('SESSION_FILE_THRESHOLD', 500)
    app.config['SESSION_PERMANENT'] = app.config.get('SESSION_PERMANENT', True)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=app.config.get('PERMANENT_SESSION_LIFETIME', 86400))
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', False)
    app.config['SESSION_COOKIE_HTTPONLY'] = app.config.get('SESSION_COOKIE_HTTPONLY', True)
    app.config['SESSION_COOKIE_SAMESITE'] = app.config.get('SESSION_COOKIE_SAMESITE', 'Lax')
    app.config['SESSION_COOKIE_PATH'] = app.config.get('SESSION_COOKIE_PATH', '/')
    app.config['SESSION_COOKIE_DOMAIN'] = app.config.get('SESSION_COOKIE_DOMAIN', None)
    app.config['SESSION_COOKIE_NAME'] = app.config.get('SESSION_COOKIE_NAME', 'session')
    app.config['SESSION_REFRESH_EACH_REQUEST'] = app.config.get('SESSION_REFRESH_EACH_REQUEST', False)
    app.config['SESSION_USE_SIGNER'] = app.config.get('SESSION_USE_SIGNER', True)
    app.config['SESSION_KEY_PREFIX'] = app.config.get('SESSION_KEY_PREFIX', 'desi_delight_')
    
    # Initialize Flask-Session
    Session(app)
    
    # Enhanced request logging middleware
    @app.before_request
    def before_request():
        try:
            # Generate unique request ID for tracking
            g.request_id = str(uuid.uuid4())
            
            # Log request information
            if request.method in ['POST', 'PUT', 'DELETE']:
                log_request_info()
                
        except Exception as e:
            logger.error(f"Error in before_request: {str(e)}")
    
    # Enhanced CORS configuration
    CORS(app, resources={r"/api/*": {
        "origins": app.config.get('ALLOWED_ORIGINS', ["http://localhost:5173"]),
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Set-Cookie"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "max_age": 3600
    }})
    
    # Add security headers
    @app.after_request
    def after_request(response):
        try:
            # Add CORS headers
            if request.method == 'OPTIONS':
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
            
        except Exception as e:
            logger.error(f"Error in after_request: {str(e)}")
            return response
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    
    # Health check endpoint
    @app.route('/')
    def index():
        return jsonify({
            'status': 'healthy',
            'message': 'Desi Delight Analytics API is running!',
            'version': '1.0.0'
        }), 200
    
    # Health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        try:
            # Check database connection
            db.session.execute('SELECT 1')
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
