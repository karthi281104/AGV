"""
AGV Finance and Loans Flask Application Factory
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    csrf.init_app(app)
    CORS(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
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
    upload_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(os.path.join(upload_dir, 'documents'), exist_ok=True)
    
    # Create .gitkeep files for empty directories
    gitkeep_path = os.path.join(upload_dir, 'documents', '.gitkeep')
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, 'w') as f:
            f.write('')
    
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
    
    # Context processors
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app import models