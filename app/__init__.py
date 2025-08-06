from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from authlib.integrations.flask_client import OAuth
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
oauth = OAuth()


def create_app(config_name=None):
    app = Flask(__name__)

    # Load configuration
    from config import config
    config_class = config.get(config_name or 'development')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    oauth.init_app(app)

    # Configure Auth0 if credentials are provided
    with app.app_context():
        try:
            auth0_domain = app.config.get('AUTH0_DOMAIN')
            auth0_client_id = app.config.get('AUTH0_CLIENT_ID')
            auth0_client_secret = app.config.get('AUTH0_CLIENT_SECRET')
            
            if (auth0_domain and auth0_client_id and auth0_client_secret and 
                auth0_domain != 'your-domain.auth0.com' and 
                auth0_client_id != 'your-client-id'):
                
                oauth.register(
                    'auth0',
                    client_id=auth0_client_id,
                    client_secret=auth0_client_secret,
                    server_metadata_url=f'https://{auth0_domain}/.well-known/openid_configuration',
                    client_kwargs={
                        'scope': 'openid profile email'
                    }
                )
                print("✅ Auth0 configured successfully")
            else:
                print("⚠️  Auth0 not configured - using demo authentication")
        except Exception as e:
            print(f"⚠️  Auth0 configuration failed: {e}")

    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Import models to ensure they are registered
    from app.models import auth, core
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.customer import customer_bp
    from app.routes.loan import loan_bp
    from app.routes.payment import payment_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(customer_bp, url_prefix='/customers')
    app.register_blueprint(loan_bp, url_prefix='/loans')
    app.register_blueprint(payment_bp, url_prefix='/payments')

    return app