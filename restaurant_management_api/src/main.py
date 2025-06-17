import os
import sys
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
import logging
from datetime import timedelta
import shutil
import pickle

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
from src.config import Config

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config.from_object(Config)
    
    # Initialize extensions first
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Admin user created successfully')
        else:
            # Update admin password if it exists
            admin.set_password('admin123')
            db.session.commit()
            app.logger.info('Admin user password updated')
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(app.instance_path, 'flask_session')
    app.config['SESSION_FILE_THRESHOLD'] = 500
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow cookies to be sent to any subdomain
    app.config['SESSION_COOKIE_NAME'] = 'session'
    app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # Don't refresh session on each request
    app.config['SESSION_USE_SIGNER'] = True  # Enable session signing
    app.config['SESSION_KEY_PREFIX'] = 'desi_delight_'  # Add a prefix to session keys
    
    # Ensure the session directory exists
    session_dir = app.config['SESSION_FILE_DIR']
    os.makedirs(session_dir, exist_ok=True)
    
    # Initialize Flask-Session
    Session(app)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    app.logger.setLevel(logging.WARNING)
    
    # Add request logging middleware
    @app.before_request
    def log_request_info():
        try:
            # Only log errors and warnings
            if request.method in ['POST', 'PUT', 'DELETE']:
                app.logger.warning(f'{request.method} {request.path}')
        except Exception as e:
            app.logger.error(f"Error in request logging: {str(e)}")
    
    # Configure CORS with credentials
    CORS(app, resources={r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Set-Cookie"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "max_age": 3600
    }})
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        if request.method == 'OPTIONS':
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    
    # Add a root route for health check or landing page
    @app.route('/')
    def index():
        return "Desi Delight Analytics API is running!", 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
