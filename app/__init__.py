from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
oauth = OAuth()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name=None):
    app = Flask(__name__)

    # Load configuration
    if config_name:
        app.config.from_object(f'config.{config_name}')
    else:
        app.config.from_object('config.DevelopmentConfig')

    # Enhanced security configuration
    from app.config.auth0 import SessionConfig, SecurityConfig, apply_security_headers
    
    # Session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = SessionConfig.PERMANENT_SESSION_LIFETIME
    app.config['SESSION_COOKIE_SECURE'] = SessionConfig.SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_HTTPONLY'] = SessionConfig.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = SessionConfig.SESSION_COOKIE_SAMESITE
    
    # CSRF configuration
    app.config['WTF_CSRF_ENABLED'] = SecurityConfig.WTF_CSRF_ENABLED
    app.config['WTF_CSRF_TIME_LIMIT'] = SecurityConfig.WTF_CSRF_TIME_LIMIT
    app.config['WTF_CSRF_SSL_STRICT'] = SecurityConfig.WTF_CSRF_SSL_STRICT

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    oauth.init_app(app)
    csrf.init_app(app)
    
    # Initialize rate limiter (would use Redis in production)
    try:
        limiter.init_app(app)
    except:
        # Fallback if Redis is not available
        pass

    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'Please log in again to access this page.'

    # Apply security headers
    apply_security_headers(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.customer import customer_bp
    from app.routes.loan import loan_bp
    from app.routes.payment import payment_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(customer_bp, url_prefix='/customers')
    app.register_blueprint(loan_bp, url_prefix='/loans')
    app.register_blueprint(payment_bp, url_prefix='/payments')

    # Create default roles after app context is available
    with app.app_context():
        try:
            from app.models.user import init_default_roles
            init_default_roles()
        except:
            # Skip if database tables don't exist yet
            pass

    return app