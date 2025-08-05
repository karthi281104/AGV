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


@auth_bp.route('/login')
def login():
    """Display login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('login.html')


@auth_bp.route('/dev-login', methods=['POST'])
def dev_login():
    """Development login route for testing without Auth0"""
    try:
        # Create or get a test user
        user = User.query.filter_by(email='admin@agvfinance.com').first()
        
        if not user:
            user = User(
                auth0_id='dev_user_123',
                email='admin@agvfinance.com',
                username='admin',
                name='AGV Admin'
            )
            db.session.add(user)
            try:
                db.session.commit()
            except Exception as db_error:
                db.session.rollback()
                flash(f'Database error creating user: {str(db_error)}', 'error')
                return redirect(url_for('auth.login'))

        # Update last login
        from datetime import datetime
        try:
            user.last_login = datetime.utcnow()
            db.session.commit()
        except Exception as db_error:
            # If we can't update login time, that's okay
            db.session.rollback()
            print(f"Warning: Could not update last login: {db_error}")

        login_user(user)
        flash('Logged in successfully (Development Mode)', 'success')
        return redirect(url_for('dashboard.index'))

    except Exception as e:
        flash(f'Development login error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


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
                    username=user_info.get('preferred_username', user_info['email']),
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