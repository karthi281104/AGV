import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration with fallback
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # SQLite fallback for development
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///agv_finance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Auth0 Configuration with proper defaults
    AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN', 'agv-loans-dev.auth0.com')
    AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID', 'your-client-id')
    AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET', 'your-client-secret')
    AUTH0_CALLBACK_URL = os.environ.get('AUTH0_CALLBACK_URL', 'http://localhost:5000/auth/callback')
    AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE', f'https://{AUTH0_DOMAIN}/api/v2/')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # WebAuthn configuration
    WEBAUTHN_RP_ID = os.environ.get('WEBAUTHN_RP_ID', 'localhost')
    WEBAUTHN_RP_NAME = 'AGV Finance & Loans'
    
    # Development mode settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}


class DevelopmentConfig(Config):
    DEBUG = True
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///agv_finance_dev.db'

class ProductionConfig(Config):
    DEBUG = False
    # Use environment DATABASE_URL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///agv_finance.db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}