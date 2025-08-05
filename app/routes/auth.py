from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from app import oauth, db
from app.models.user import User
import os

auth_bp = Blueprint('auth', __name__)

# Auth0 configuration
auth0 = oauth.register(
    'auth0',
    client_id=os.environ.get('AUTH0_CLIENT_ID'),
    client_secret=os.environ.get('AUTH0_CLIENT_SECRET'),
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid profile email'
    }
)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display login page and handle demo login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Demo login for testing (remove in production)
        if username == 'demo' and password == 'demo123':
            # Create or get demo user
            demo_user = User.query.filter_by(email='demo@agvfinance.com').first()
            if not demo_user:
                demo_user = User(
                    auth0_id='demo_user',
                    email='demo@agvfinance.com',
                    name='Demo User',
                    role='admin'
                )
                db.session.add(demo_user)
                db.session.commit()
            
            login_user(demo_user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Invalid credentials. Use demo/demo123 for testing.', 'error')
    
    return render_template('login.html')


@auth_bp.route('/auth0-login')
def auth0_login():
    """Redirect to Auth0 for authentication"""
    redirect_uri = url_for('auth.callback', _external=True)
    return auth0.authorize_redirect(redirect_uri)


@auth_bp.route('/callback')
def callback():
    """Handle Auth0 callback"""
    try:
        token = auth0.authorize_access_token()
        user_info = token.get('userinfo')

        if user_info:
            # Find or create user
            user = User.query.filter_by(auth0_id=user_info['sub']).first()

            if not user:
                user = User(
                    auth0_id=user_info['sub'],
                    email=user_info['email'],
                    name=user_info['name']
                )
                db.session.add(user)
                db.session.commit()

            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()

            login_user(user)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Authentication failed', 'error')
            return redirect(url_for('auth.login'))

    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user and redirect to Auth0 logout"""
    logout_user()

    # Auth0 logout URL
    auth0_logout_url = f"https://{os.environ.get('AUTH0_DOMAIN')}/v2/logout"
    return_to = url_for('main.index', _external=True)

    return redirect(f"{auth0_logout_url}?returnTo={return_to}&client_id={os.environ.get('AUTH0_CLIENT_ID')}")