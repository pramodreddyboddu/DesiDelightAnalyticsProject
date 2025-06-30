import os
from dotenv import load_dotenv
from datetime import timedelta
from tempfile import gettempdir
import redis
import urllib.parse

# Load environment variables
# load_dotenv()  # Temporarily disabled due to .env file encoding issues

def get_database_uri():
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    return db_url or 'sqlite:///restaurant_management.db'

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Handle Heroku's DATABASE_URL format
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    
    # Redis configuration for Heroku
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration - Fixed for cross-origin and Redis
    SESSION_TYPE = 'redis'  # Use Redis by default for better performance
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        try:
            if redis_url.startswith('rediss://'):
                SESSION_REDIS = redis.from_url(redis_url, ssl_cert_reqs=None)
            else:
                SESSION_REDIS = redis.from_url(redis_url)
            SESSION_TYPE = 'redis'
            print(f"✅ Using Redis for sessions: {redis_url}")
        except Exception as e:
            print(f"⚠️ Redis connection failed, using filesystem sessions: {e}")
            SESSION_REDIS = None
            SESSION_TYPE = 'filesystem'
    else:
        SESSION_REDIS = None
        SESSION_TYPE = 'filesystem'
        print("⚠️ No REDIS_URL found, using filesystem sessions")
    
    # Session settings optimized for cross-origin requests
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True  # Always secure in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'  # Required for cross-origin
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_NAME = 'plateiq_session'
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'plateiq_'
    SESSION_COOKIE_DOMAIN = 'plateiq-analytics-api-f6a987ab13c5.herokuapp.com'
    
    # CORS configuration
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'https://desi-delight-analytics-project-usvt.vercel.app',
        'https://desi-delight-analytics-project-pkhf.vercel.app'
    ]
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With', 'X-API-KEY']
    CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_MAX_AGE = 3600
    
    # Admin configuration
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Clover API configuration
    CLOVER_MERCHANT_ID = os.environ.get('CLOVER_MERCHANT_ID') or ''
    CLOVER_ACCESS_TOKEN = os.environ.get('CLOVER_ACCESS_TOKEN') or ''
    CLOVER_API_BASE_URL = 'https://api.clover.com'
    CLOVER_API_VERSION = 'v3'
    
    # Data source configuration
    DEFAULT_SALES_SOURCE = os.environ.get('DEFAULT_SALES_SOURCE') or 'clover'
    DEFAULT_INVENTORY_SOURCE = os.environ.get('DEFAULT_INVENTORY_SOURCE') or 'clover'
    DEFAULT_EXPENSES_SOURCE = 'local'  # Always local
    DEFAULT_CHEF_MAPPING_SOURCE = 'local'  # Always local
    
    # Cache configuration
    CLOVER_CACHE_TTL = 600  # 10 minutes
    DASHBOARD_CACHE_TTL = 300  # 5 minutes
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = 'logs/app.log'
    ERROR_LOG_FILE = 'logs/error.log'
    
    # File upload configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # AI service configuration
    AI_MODEL_PATH = 'models/sales_forecast_model.pkl'
    AI_PREDICTION_DAYS = 7
    
    # Production settings
    DEBUG = False
    TESTING = False
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Rate limiting (if implemented)
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Database connection pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_LEVEL = 'DEBUG'
    
    # Development CORS settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173', 'http://127.0.0.1:3000', 'http://127.0.0.1:5173']
    
    # Development session settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = None

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Production CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Production Clover settings
    CLOVER_MERCHANT_ID = os.environ.get('CLOVER_MERCHANT_ID')
    CLOVER_ACCESS_TOKEN = os.environ.get('CLOVER_ACCESS_TOKEN')
    
    # Production admin settings
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    def __init__(self):
        super().__init__()
        print(f"[DEBUG] SESSION_COOKIE_DOMAIN at startup: {self.SESSION_COOKIE_DOMAIN}")
        print(f"[DEBUG] SESSION_COOKIE_SAMESITE at startup: {self.SESSION_COOKIE_SAMESITE}")
        print(f"[DEBUG] SESSION_COOKIE_SECURE at startup: {self.SESSION_COOKIE_SECURE}")
        # Validate required environment variables only when config is used
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required in production")
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable is required in production")
        if not self.ADMIN_USERNAME or not self.ADMIN_PASSWORD:
            raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required in production")
        if not self.CLOVER_MERCHANT_ID or not self.CLOVER_ACCESS_TOKEN:
            print("WARNING: Clover credentials not set. Clover integration will be disabled.")
        
        # Override CORS origins if needed
        if not self.CORS_ORIGINS:
            print("WARNING: No CORS_ORIGINS set, using default origins")
            self.CORS_ORIGINS = [
                'https://desi-delight-analytics-project-pkhf.vercel.app',
                'https://desi-delight-analytics-project-usvt.vercel.app'
            ]
        
        # Log session configuration for debugging
        print(f"🔧 Production Session Config: TYPE={self.SESSION_TYPE}, SECURE={self.SESSION_COOKIE_SECURE}, SAMESITE={self.SESSION_COOKIE_SAMESITE}, DOMAIN={self.SESSION_COOKIE_DOMAIN}")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Test CORS settings
    CORS_ORIGINS = ['http://localhost:3000']
    
    # Test session settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = None

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Environment-based configuration selection
def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 