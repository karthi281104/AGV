from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from app import oauth, db
from app.models.user import User
from app.utils.auth import create_user_session, get_device_info
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
    """Display professional login page and handle demo login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Handle both email/username login methods
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Determine login identifier
        login_identifier = email or username
        
        # Demo login for testing (remove in production)
        if ((login_identifier == 'demo@agvfinance.com' or login_identifier == 'demo') and 
            password == 'demo123'):
            
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
            
            # Update last login
            from datetime import datetime
            demo_user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create user session
            if remember:
                device_info = get_device_info()
                create_user_session(demo_user.id, device_info)
            
            login_user(demo_user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Invalid credentials. Use demo@agvfinance.com/demo123 for testing or try Auth0 login.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/auth0-login')
def auth0_login():
    """Redirect to Auth0 for authentication"""
    redirect_uri = url_for('auth.callback', _external=True)
    connection = request.args.get('connection')  # Support for social providers
    
    if connection:
        return auth0.authorize_redirect(redirect_uri, connection=connection)
    else:
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

            # Create user session
            device_info = get_device_info()
            create_user_session(user.id, device_info)

            login_user(user)
            flash(f'Welcome, {user.name}!', 'success')
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
    # Clean up user sessions
    if current_user.is_authenticated:
        # Mark current sessions as inactive
        from app.models.user import UserSession
        user_sessions = UserSession.query.filter_by(user_id=current_user.id, is_active=True).all()
        for user_session in user_sessions:
            user_session.is_active = False
        db.session.commit()
    
    logout_user()

    # Auth0 logout URL
    auth0_logout_url = f"https://{os.environ.get('AUTH0_DOMAIN')}/v2/logout"
    return_to = url_for('main.index', _external=True)

    return redirect(f"{auth0_logout_url}?returnTo={return_to}&client_id={os.environ.get('AUTH0_CLIENT_ID')}")


@auth_bp.route('/webauthn/begin')
@login_required
def webauthn_begin():
    """Begin WebAuthn authentication process"""
    # Placeholder for WebAuthn implementation
    return jsonify({
        'error': 'WebAuthn authentication is not yet implemented',
        'message': 'This feature will be available in the next update'
    }), 501


@auth_bp.route('/webauthn/complete', methods=['POST'])
@login_required
def webauthn_complete():
    """Complete WebAuthn authentication process"""
    # Placeholder for WebAuthn implementation
    return jsonify({
        'error': 'WebAuthn authentication is not yet implemented',
        'message': 'This feature will be available in the next update'
    }), 501


@auth_bp.route('/reset-password')
def reset_password():
    """Password reset functionality"""
    # Redirect to Auth0 password reset
    auth0_domain = os.environ.get('AUTH0_DOMAIN')
    if auth0_domain:
        reset_url = f"https://{auth0_domain}/login?screen_hint=password_reset"
        return redirect(reset_url)
    else:
        flash('Password reset is not configured. Please contact support.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/verify')
def verify():
    """Account verification endpoint"""
    # Placeholder for account verification
    flash('Account verification will be implemented with full Auth0 integration.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/help')
def help():
    """Help and support page"""
    flash('Help system will be implemented with full support portal.', 'info')
    return redirect(url_for('auth.login'))