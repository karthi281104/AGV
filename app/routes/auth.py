from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from app import oauth, db, csrf
from app.models.user import User
from app.utils.auth import check_session_timeout
import os
from datetime import datetime

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


@auth_bp.before_request
def check_auth_session():
    """Check for session timeout before each auth request"""
    if current_user.is_authenticated and check_session_timeout():
        logout_user()
        flash('Your session has expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))


@auth_bp.route('/login')
def login():
    """Display login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('auth/login.html')


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
                # Create new user
                user = User(
                    auth0_id=user_info['sub'],
                    email=user_info['email'],
                    name=user_info['name']
                )
                db.session.add(user)
                
                # Set default preferences for new user
                default_prefs = {
                    'theme': 'light',
                    'notifications': True,
                    'language': 'en'
                }
                user.set_preferences(default_prefs)
                
                flash(f'Welcome {user.name}! Your account has been created.', 'success')
            else:
                flash(f'Welcome back, {user.name}!', 'success')

            # Update user information from Auth0
            user.email = user_info.get('email', user.email)
            user.name = user_info.get('name', user.name)
            user.update_last_login()
            
            db.session.commit()

            login_user(user, remember=True)
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Authentication failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))

    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user and redirect to Auth0 logout"""
    user_name = current_user.name
    logout_user()
    flash(f'Goodbye {user_name}! You have been logged out.', 'success')

    # Auth0 logout URL
    auth0_logout_url = f"https://{os.environ.get('AUTH0_DOMAIN')}/v2/logout"
    return_to = url_for('main.index', _external=True)

    return redirect(f"{auth0_logout_url}?returnTo={return_to}&client_id={os.environ.get('AUTH0_CLIENT_ID')}")


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        # Update basic info
        current_user.name = request.form.get('name', current_user.name)
        current_user.department = request.form.get('department', current_user.department)
        current_user.phone = request.form.get('phone', current_user.phone)
        
        # Update preferences
        preferences = current_user.get_preferences()
        preferences.update({
            'theme': request.form.get('theme', 'light'),
            'notifications': request.form.get('notifications') == 'on',
            'language': request.form.get('language', 'en')
        })
        current_user.set_preferences(preferences)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/api/user-info')
@login_required
def api_user_info():
    """API endpoint for current user information"""
    return jsonify(current_user.to_dict())


@auth_bp.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    return render_template('errors/403.html'), 403


@auth_bp.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('auth.login'))