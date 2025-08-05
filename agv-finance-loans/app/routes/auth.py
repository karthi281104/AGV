"""
Authentication routes for AGV Finance and Loans
Handles Auth0 OAuth flow and WebAuthn biometric authentication
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlencode
import json

from app import db
from app.models.user import User
from app.utils.auth import init_auth0, get_auth0_logout_url, WebAuthnHelper

bp = Blueprint('auth', __name__)

# Initialize Auth0 when the blueprint is created
auth0 = None

def initialize_auth0():
    global auth0
    auth0 = init_auth0(current_app)

@bp.route('/login')
def login():
    """Display login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')

@bp.route('/callback')
def callback():
    """Auth0 callback handler"""
    global auth0
    if auth0 is None:
        initialize_auth0()
    
    try:
        # Get the authorization code from callback
        token = auth0.authorize_access_token()
        
        # Get user info from Auth0
        user_info = token.get('userinfo')
        if not user_info:
            user_info = auth0.parse_id_token(token)
        
        # Find or create user
        user = User.query.filter_by(auth0_id=user_info['sub']).first()
        
        if not user:
            # Create new user
            user = User.create_from_auth0(user_info)
            flash('Welcome! Your account has been created successfully.', 'success')
        else:
            # Update existing user info
            user.email = user_info['email']
            user.name = user_info.get('name', user_info['email'])
            user.picture = user_info.get('picture')
            user.is_verified = user_info.get('email_verified', False)
            db.session.commit()
        
        # Record login
        user.record_login()
        
        # Log user in
        login_user(user, remember=True)
        
        # Check if user has WebAuthn enabled
        next_page = request.args.get('next')
        if user.webauthn_credentials and request.args.get('webauthn') != 'skip':
            session['pending_webauthn_user_id'] = user.id
            session['next_after_webauthn'] = next_page
            return redirect(url_for('auth.webauthn_verify'))
        
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        
    except Exception as e:
        current_app.logger.error(f"Auth0 callback error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@bp.route('/oauth-login')
def oauth_login():
    """Initiate Auth0 OAuth login"""
    global auth0
    if auth0 is None:
        initialize_auth0()
    
    redirect_uri = url_for('auth.callback', _external=True)
    return auth0.authorize_redirect(redirect_uri)

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    user_name = current_user.name
    logout_user()
    
    # Clear session
    session.clear()
    
    flash(f'Goodbye {user_name}! You have been logged out.', 'info')
    
    # Redirect to Auth0 logout URL
    return redirect(get_auth0_logout_url())

@bp.route('/webauthn/register')
@login_required
def webauthn_register():
    """WebAuthn biometric registration page"""
    if current_user.webauthn_credentials:
        flash('Biometric authentication is already enabled for your account.', 'info')
        return redirect(url_for('dashboard.profile'))
    
    return render_template('auth/webauthn_register.html')

@bp.route('/webauthn/verify')
def webauthn_verify():
    """WebAuthn biometric verification page"""
    user_id = session.get('pending_webauthn_user_id')
    if not user_id:
        flash('Invalid verification session.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user or not user.webauthn_credentials:
        flash('Biometric verification not available for this account.', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/webauthn_verify.html', user=user)

@bp.route('/api/webauthn/register/begin', methods=['POST'])
@login_required
def webauthn_register_begin():
    """Begin WebAuthn registration"""
    try:
        options = WebAuthnHelper.create_credential_creation_options(current_user)
        return jsonify(options)
    except Exception as e:
        current_app.logger.error(f"WebAuthn registration begin error: {e}")
        return jsonify({'error': 'Failed to begin registration'}), 500

@bp.route('/api/webauthn/register/finish', methods=['POST'])
@login_required
def webauthn_register_finish():
    """Finish WebAuthn registration"""
    try:
        credential_data = request.get_json()
        
        if WebAuthnHelper.verify_registration(current_user, credential_data):
            flash('Biometric authentication has been enabled successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Registration verification failed'}), 400
            
    except Exception as e:
        current_app.logger.error(f"WebAuthn registration finish error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@bp.route('/api/webauthn/authenticate/begin', methods=['POST'])
def webauthn_authenticate_begin():
    """Begin WebAuthn authentication"""
    try:
        user_id = session.get('pending_webauthn_user_id')
        if not user_id:
            return jsonify({'error': 'Invalid session'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        options = WebAuthnHelper.create_credential_request_options(user)
        return jsonify(options)
        
    except Exception as e:
        current_app.logger.error(f"WebAuthn authentication begin error: {e}")
        return jsonify({'error': 'Failed to begin authentication'}), 500

@bp.route('/api/webauthn/authenticate/finish', methods=['POST'])
def webauthn_authenticate_finish():
    """Finish WebAuthn authentication"""
    try:
        user_id = session.get('pending_webauthn_user_id')
        if not user_id:
            return jsonify({'error': 'Invalid session'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        assertion_data = request.get_json()
        
        if WebAuthnHelper.verify_authentication(user, assertion_data):
            # Complete login
            login_user(user, remember=True)
            
            # Clear WebAuthn session data
            next_page = session.pop('next_after_webauthn', None)
            session.pop('pending_webauthn_user_id', None)
            
            return jsonify({
                'success': True,
                'redirect': next_page or url_for('dashboard.index')
            })
        else:
            return jsonify({'error': 'Authentication verification failed'}), 400
            
    except Exception as e:
        current_app.logger.error(f"WebAuthn authentication finish error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@bp.route('/webauthn/disable', methods=['POST'])
@login_required
def webauthn_disable():
    """Disable WebAuthn for current user"""
    try:
        current_user.webauthn_credentials = None
        db.session.commit()
        flash('Biometric authentication has been disabled.', 'info')
    except Exception as e:
        current_app.logger.error(f"WebAuthn disable error: {e}")
        flash('Failed to disable biometric authentication.', 'error')
    
    return redirect(url_for('dashboard.profile'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        # Update basic profile information
        current_user.name = request.form.get('name', current_user.name)
        
        # Handle profile picture upload
        if 'picture' in request.files:
            picture_file = request.files['picture']
            if picture_file and picture_file.filename:
                from app.utils.helpers import save_uploaded_file
                picture_path = save_uploaded_file(picture_file, 'profiles')
                if picture_path:
                    current_user.picture = picture_path
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Profile update error: {e}")
        flash('Failed to update profile.', 'error')
        db.session.rollback()
    
    return redirect(url_for('auth.profile'))

@bp.route('/change-password')
@login_required
def change_password():
    """Change password page (redirects to Auth0)"""
    change_password_url = f"https://{current_app.config['AUTH0_DOMAIN']}/login?" + urlencode({
        'client_id': current_app.config['AUTH0_CLIENT_ID'],
        'response_type': 'code',
        'redirect_uri': url_for('auth.callback', _external=True),
        'scope': 'openid profile email',
        'prompt': 'login',
        'screen_hint': 'signup'
    })
    
    return redirect(change_password_url)

@bp.route('/api/user/permissions')
@login_required
def user_permissions():
    """Get current user permissions"""
    from app.utils.auth import get_user_permissions
    permissions = get_user_permissions(current_user)
    return jsonify(permissions)

@bp.route('/api/user/status')
@login_required
def user_status():
    """Get current user status and info"""
    return jsonify({
        'authenticated': True,
        'user': current_user.to_dict(),
        'permissions': get_user_permissions(current_user)
    })

# Skip WebAuthn for testing or accessibility
@bp.route('/skip-webauthn')
def skip_webauthn():
    """Skip WebAuthn verification"""
    user_id = session.get('pending_webauthn_user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            login_user(user, remember=True)
            next_page = session.pop('next_after_webauthn', None)
            session.pop('pending_webauthn_user_id', None)
            return redirect(next_page or url_for('dashboard.index'))
    
    flash('Unable to complete login.', 'error')
    return redirect(url_for('auth.login'))