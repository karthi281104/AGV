from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth
from config import config
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()
oauth = OAuth()

def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading'))
    csrf.init_app(app)
    oauth.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure Auth0
    if app.config.get('AUTH0_CLIENT_ID'):
        oauth.register(
            name='auth0',
            client_id=app.config['AUTH0_CLIENT_ID'],
            client_secret=app.config['AUTH0_CLIENT_SECRET'],
            server_metadata_url=f"https://{app.config['AUTH0_DOMAIN']}/.well-known/openid_configuration",
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    
    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    from app.routes.customer import bp as customer_bp
    app.register_blueprint(customer_bp, url_prefix='/customers')
    
    from app.routes.loan import bp as loan_bp
    app.register_blueprint(loan_bp, url_prefix='/loans')
    
    from app.routes.payment import bp as payment_bp
    app.register_blueprint(payment_bp, url_prefix='/payments')
    
    # Create upload directories
    upload_dir = os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])
    documents_dir = os.path.join(upload_dir, 'documents')
    os.makedirs(documents_dir, exist_ok=True)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Shell context processor
    @app.shell_context_processor
    def make_shell_context():
        from app.models.user import User
        from app.models.customer import Customer
        from app.models.loan import Loan
        from app.models.payment import Payment
        return {'db': db, 'User': User, 'Customer': Customer, 'Loan': Loan, 'Payment': Payment}
    
    return app