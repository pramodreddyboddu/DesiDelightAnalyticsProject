import os
from dotenv import load_dotenv
from datetime import timedelta
from tempfile import gettempdir

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class with enhanced security settings."""
    
    # Base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Database configuration
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    os.makedirs(DATABASE_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(DATABASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin Configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SESSION_COOKIE_SECURE = False  # For local development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = None  # Allow cross-site requests for development
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_DOMAIN = None  # Let Flask set domain automatically
    SESSION_COOKIE_NAME = 'desi_delight_session'  # Unique session name
    SESSION_REFRESH_EACH_REQUEST = True  # Keep session alive
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'desi_delight_'
    
    # CORS Configuration
    CORS_ORIGINS = ["http://localhost:5173"]  # Strict CORS origins
    CORS_SUPPORTS_CREDENTIALS = True  # Allow credentials
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "Cookie"]  # Added Cookie header
    CORS_EXPOSE_HEADERS = ["Content-Type", "Authorization", "Set-Cookie"]  # Added Set-Cookie header
    CORS_MAX_AGE = 600  # Cache preflight requests for 10 minutes
    
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
    SESSION_TYPE = 'filesystem'  # Use filesystem for development
    SESSION_FILE_DIR = os.path.join(gettempdir(), 'desi_delight_sessions')  # Dedicated session directory
    os.makedirs(SESSION_FILE_DIR, exist_ok=True)  # Ensure directory exists
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
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