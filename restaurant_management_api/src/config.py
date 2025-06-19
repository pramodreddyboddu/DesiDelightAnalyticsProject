import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class with enhanced security settings."""
    
    # Base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Database configuration
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    os.makedirs(DATABASE_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(DATABASE_DIR, "app.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin Configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_NAME = 'session'
    SESSION_REFRESH_EACH_REQUEST = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'desi_delight_'
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '900'))  # 15 minutes
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'upload'
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_THRESHOLD = 500
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Flask settings
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_DOMAIN = 'localhost'
    SESSION_COOKIE_PATH = '/'
    
    # Logging configuration
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 