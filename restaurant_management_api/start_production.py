#!/usr/bin/env python3
"""
Production startup script for PlateIQ Analytics API
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_environment():
    """Setup environment variables and directories"""
    # Create necessary directories
    directories = ['logs', 'uploads', 'models', 'instance']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Set default environment variables if not set
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'production'
    
    if not os.environ.get('FLASK_APP'):
        os.environ['FLASK_APP'] = 'src.main:create_app()'
    
    # Check required environment variables for production
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before starting the application.")
        sys.exit(1)
    
    # Check optional Clover credentials
    clover_vars = ['CLOVER_MERCHANT_ID', 'CLOVER_ACCESS_TOKEN']
    missing_clover = [var for var in clover_vars if not os.environ.get(var)]
    
    if missing_clover:
        print(f"WARNING: Missing Clover credentials: {', '.join(missing_clover)}")
        print("Clover integration will be disabled. Set these variables to enable Clover features.")
    
    # Check admin credentials
    admin_vars = ['ADMIN_USERNAME', 'ADMIN_PASSWORD']
    missing_admin = [var for var in admin_vars if not os.environ.get(var)]
    
    if missing_admin:
        print(f"WARNING: Missing admin credentials: {', '.join(missing_admin)}")
        print("Using default admin credentials. Set these variables for production security.")

def setup_logging():
    """Setup production logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import flask
        import sqlalchemy
        import pandas
        import requests
        print("✅ All required dependencies are available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install all requirements: pip install -r requirements.txt")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🚀 Starting PlateIQ Analytics API in production mode...")
    
    # Setup environment
    setup_environment()
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    check_dependencies()
    
    # Import and create app
    try:
        from src.main import create_app
        app = create_app('production')
        
        # Get configuration
        config = app.config
        
        print(f"✅ Application configured successfully")
        print(f"📊 Database: {config['SQLALCHEMY_DATABASE_URI']}")
        print(f"🔐 Admin user: {config['ADMIN_USERNAME']}")
        print(f"🌐 CORS origins: {config['CORS_ORIGINS']}")
        
        # Start the application
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        
        print(f"🌍 Starting server on {host}:{port}")
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        logging.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 