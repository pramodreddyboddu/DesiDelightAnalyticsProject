import os
from datetime import timedelta

class Config:
    # Base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Database configuration
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    os.makedirs(DATABASE_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(DATABASE_DIR, "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_TYPE = 'filesystem'
    
    # CORS configuration
    CORS_ORIGINS = ['http://localhost:5173']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Flask settings
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_DOMAIN = 'localhost'
    SESSION_COOKIE_PATH = '/'
    
    # Logging configuration
    LOG_LEVEL = 'INFO' 