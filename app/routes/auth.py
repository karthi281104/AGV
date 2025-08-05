"""
Enhanced Authentication Routes
Provides comprehensive Auth0 integration with WebAuthn, session management,
and advanced security features
"""
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import validate_csrf
from wtforms import StringField, EmailField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length
from authlib.integrations.flask_client import OAuth
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential
from webauthn.helpers.cose import COSEAlgorithmIdentifier
import secrets
import base64
import json
from datetime import datetime

from app import oauth, db
from app.models.user import User, Role, UserSession, AuditLog, init_default_roles
from app.utils.auth import (
    create_user_session, terminate_user_session, terminate_all_user_sessions,
    get_client_ip, detect_suspicious_activity, log_security_event,
    admin_required, enhanced_login_required, generate_csrf_token
)
from app.config.auth0 import get_auth0_client_config, get_webauthn_config

auth_bp = Blueprint('auth', __name__)

# Auth0 configuration
auth0 = oauth.register('auth0', **get_auth0_client_config())


class RegistrationForm(FlaskForm):
    """Admin user registration form"""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.name.title()) for r in Role.query.all()]


class ProfileForm(FlaskForm):
    """User profile management form"""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time'),
        ('America/Chicago', 'Central Time'),
        ('America/Denver', 'Mountain Time'),
        ('America/Los_Angeles', 'Pacific Time'),
    ])
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
    ])
    email_notifications = BooleanField('Email Notifications')
    security_notifications = BooleanField('Security Notifications')


@auth_bp.route('/login')
def login():
    """Display enhanced login page with Auth0 and WebAuthn options"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # Generate CSRF token for forms
    csrf_token = generate_csrf_token()
    
    return render_template('auth/login.html', csrf_token=csrf_token)


@auth_bp.route('/auth0-login')
def auth0_login():
    """Redirect to Auth0 for authentication"""
    # Store return URL in session
    next_url = request.args.get('next', url_for('dashboard.index'))
    session['next_url'] = next_url
    
    # Generate and store state for security
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build redirect URI
    redirect_uri = url_for('auth.callback', _external=True)
    
    # Log authentication attempt
    log_security_event(
        event_type='auth0_login_attempt',
        description='Auth0 authentication initiated',
        action='authenticate'
    )
    
    return auth0.authorize_redirect(redirect_uri, state=state)


@auth_bp.route('/callback')
def callback():
    """Handle Auth0 OAuth callback with enhanced security"""
    try:
        # Verify state parameter
        received_state = request.args.get('state')
        stored_state = session.pop('oauth_state', None)
        
        if not received_state or received_state != stored_state:
            log_security_event(
                event_type='auth0_callback_error',
                description='Invalid OAuth state parameter',
                success=False,
                error_message='State parameter mismatch'
            )
            flash('Authentication failed: Invalid state parameter', 'error')
            return redirect(url_for('auth.login'))
        
        # Get access token
        token = auth0.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            log_security_event(
                event_type='auth0_callback_error',
                description='No user info received from Auth0',
                success=False,
                error_message='Missing user info'
            )
            flash('Authentication failed: No user information received', 'error')
            return redirect(url_for('auth.login'))
        
        # Find or create user
        user = User.query.filter_by(auth0_id=user_info['sub']).first()
        
        if not user:
            # Check if user registration is allowed
            if not current_app.config.get('ALLOW_SELF_REGISTRATION', False):
                log_security_event(
                    event_type='unauthorized_registration_attempt',
                    description=f'Unauthorized registration attempt for {user_info["email"]}',
                    success=False,
                    error_message='Self-registration not allowed'
                )
                flash('Account not found. Please contact an administrator.', 'error')
                return redirect(url_for('auth.login'))
            
            # Create new user with default employee role
            default_role = Role.query.filter_by(name='employee').first()
            user = User(
                auth0_id=user_info['sub'],
                email=user_info['email'],
                name=user_info['name'],
                role_id=default_role.id if default_role else 1,
                email_verified=user_info.get('email_verified', False)
            )
            db.session.add(user)
            db.session.commit()
            
            log_security_event(
                event_type='user_registration',
                user_id=user.id,
                description=f'New user registered: {user.email}',
                action='register'
            )
        
        # Check if account is locked
        if user.is_account_locked():
            log_security_event(
                event_type='login_failed',
                user_id=user.id,
                description='Login attempt on locked account',
                success=False,
                error_message='Account locked'
            )
            flash('Account is temporarily locked. Please try again later.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if account is active
        if not user.is_active:
            log_security_event(
                event_type='login_failed',
                user_id=user.id,
                description='Login attempt on inactive account',
                success=False,
                error_message='Account inactive'
            )
            flash('Account is inactive. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Detect suspicious activity
        anomalies, risk_score = detect_suspicious_activity(user)
        
        # Create user session
        ip_address = get_client_ip()
        user_agent = request.user_agent.string
        user_session = create_user_session(user, ip_address, user_agent)
        
        # Update user login info
        user.last_login = datetime.utcnow()
        user.reset_failed_login()
        user.update_last_activity()
        db.session.commit()
        
        # Login user
        login_user(user, remember=True)
        
        # Log successful login
        audit_log = log_security_event(
            event_type='login',
            user_id=user.id,
            description=f'Successful Auth0 login for {user.email}',
            action='authenticate',
            risk_score=risk_score
        )
        
        # Add anomaly flags if detected
        if anomalies:
            audit_log.set_anomaly_flags(anomalies)
            db.session.commit()
            
            # Flash warning for high-risk logins
            if risk_score > 50:
                flash('Unusual login activity detected. Please verify your account security.', 'warning')
        
        # Redirect to intended destination
        next_url = session.pop('next_url', url_for('dashboard.index'))
        return redirect(next_url)
        
    except Exception as e:
        log_security_event(
            event_type='auth0_callback_error',
            description=f'Auth0 callback error: {str(e)}',
            success=False,
            error_message=str(e)
        )
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@enhanced_login_required
def logout():
    """Enhanced logout with session cleanup and Auth0 logout"""
    user_id = current_user.id
    email = current_user.email
    session_id = session.get('session_id')
    
    # Terminate user session
    terminate_user_session(session_id, 'manual')
    
    # Log logout
    log_security_event(
        event_type='logout',
        user_id=user_id,
        description=f'Manual logout for {email}',
        action='logout'
    )
    
    # Logout from Flask-Login
    logout_user()
    
    # Build Auth0 logout URL
    from app.config.auth0 import Auth0Config
    logout_url = f"{Auth0Config.LOGOUT_URL}?returnTo={url_for('main.index', _external=True)}&client_id={Auth0Config.CLIENT_ID}"
    
    flash('You have been logged out successfully.', 'success')
    return redirect(logout_url)


@auth_bp.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    """Admin-only user registration"""
    # Initialize default roles if needed
    init_default_roles()
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('User with this email already exists.', 'error')
                return render_template('auth/register.html', form=form)
            
            # Create Auth0 user (this would require Auth0 Management API)
            # For now, we'll create a placeholder user that will be completed on first login
            auth0_id = f"pending_{secrets.token_urlsafe(16)}"
            
            # Create local user
            user = User(
                auth0_id=auth0_id,
                email=form.email.data,
                name=form.name.data,
                role_id=form.role_id.data,
                is_active=True,
                email_verified=False
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Log user creation
            log_security_event(
                event_type='user_created',
                user_id=user.id,
                description=f'User created by admin: {user.email}',
                action='create'
            )
            
            flash(f'User {user.email} has been created successfully. They can now log in with Auth0.', 'success')
            return redirect(url_for('auth.register'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@enhanced_login_required
def profile():
    """User profile management"""
    form = ProfileForm(obj=current_user)
    
    # Load user preferences
    prefs = current_user.get_preferences()
    form.email_notifications.data = prefs.get('email_notifications', True)
    form.security_notifications.data = prefs.get('security_notifications', True)
    
    if form.validate_on_submit():
        try:
            # Update user info
            current_user.name = form.name.data
            current_user.timezone = form.timezone.data
            current_user.language = form.language.data
            
            # Update preferences
            prefs = {
                'email_notifications': form.email_notifications.data,
                'security_notifications': form.security_notifications.data,
            }
            current_user.set_preferences(prefs)
            
            db.session.commit()
            
            log_security_event(
                event_type='profile_updated',
                user_id=current_user.id,
                description='User profile updated',
                action='update'
            )
            
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    # Get user sessions for display
    active_sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    return render_template('auth/profile.html', 
                         form=form, 
                         active_sessions=active_sessions,
                         webauthn_enabled=current_user.webauthn_enabled)


@auth_bp.route('/setup-2fa')
@enhanced_login_required
def setup_2fa():
    """Setup two-factor authentication (WebAuthn)"""
    next_url = request.args.get('next')
    return render_template('auth/setup_2fa.html', next_url=next_url)


@auth_bp.route('/webauthn/register/begin', methods=['POST'])
@enhanced_login_required
def webauthn_register_begin():
    """Begin WebAuthn registration"""
    try:
        # Validate CSRF token
        csrf_token = request.json.get('csrf_token')
        if not validate_csrf(csrf_token):
            return jsonify({'error': 'Invalid CSRF token'}), 400
        
        webauthn_config = get_webauthn_config()
        
        # Generate registration options
        options = generate_registration_options(
            rp_id=webauthn_config['rp_id'],
            rp_name=webauthn_config['rp_name'],
            user_id=str(current_user.id).encode(),
            user_name=current_user.email,
            user_display_name=current_user.name,
            exclude_credentials=[],  # Could exclude existing credentials
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
            timeout=webauthn_config['registration_timeout'],
            authenticator_selection_criteria_user_verification=webauthn_config['user_verification'],
            authenticator_selection_criteria_resident_key=webauthn_config['resident_key'],
        )
        
        # Store challenge in session
        session['webauthn_challenge'] = options.challenge
        
        return jsonify(options)
        
    except Exception as e:
        log_security_event(
            event_type='webauthn_register_error',
            user_id=current_user.id,
            description=f'WebAuthn registration begin error: {str(e)}',
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/webauthn/register/complete', methods=['POST'])
@enhanced_login_required
def webauthn_register_complete():
    """Complete WebAuthn registration"""
    try:
        # Validate CSRF token
        csrf_token = request.json.get('csrf_token')
        if not validate_csrf(csrf_token):
            return jsonify({'error': 'Invalid CSRF token'}), 400
        
        credential_data = request.json.get('credential')
        challenge = session.pop('webauthn_challenge', None)
        
        if not challenge or not credential_data:
            return jsonify({'error': 'Invalid request'}), 400
        
        webauthn_config = get_webauthn_config()
        
        # Verify registration response
        credential = RegistrationCredential.parse_raw(json.dumps(credential_data))
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_origin=webauthn_config['origin'],
            expected_rp_id=webauthn_config['rp_id'],
        )
        
        if verification.verified:
            # Save credential
            credential_info = {
                'id': credential.id,
                'public_key': base64.b64encode(verification.credential_public_key).decode(),
                'sign_count': verification.sign_count,
                'created_at': datetime.utcnow().isoformat(),
                'name': request.json.get('credential_name', 'Security Key')
            }
            
            current_user.add_webauthn_credential(credential_info)
            db.session.commit()
            
            log_security_event(
                event_type='webauthn_registered',
                user_id=current_user.id,
                description='WebAuthn credential registered',
                action='register'
            )
            
            return jsonify({'status': 'success', 'message': 'Security key registered successfully'})
        else:
            return jsonify({'error': 'Registration verification failed'}), 400
            
    except Exception as e:
        log_security_event(
            event_type='webauthn_register_error',
            user_id=current_user.id,
            description=f'WebAuthn registration complete error: {str(e)}',
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/webauthn/authenticate/begin', methods=['POST'])
def webauthn_authenticate_begin():
    """Begin WebAuthn authentication"""
    try:
        email = request.json.get('email')
        csrf_token = request.json.get('csrf_token')
        
        if not validate_csrf(csrf_token):
            return jsonify({'error': 'Invalid CSRF token'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.webauthn_enabled:
            return jsonify({'error': 'WebAuthn not available for this user'}), 400
        
        webauthn_config = get_webauthn_config()
        credentials = user.get_webauthn_credentials()
        
        # Generate authentication options
        options = generate_authentication_options(
            rp_id=webauthn_config['rp_id'],
            timeout=webauthn_config['authentication_timeout'],
            user_verification=webauthn_config['user_verification'],
            allow_credentials=[{
                'id': base64.b64decode(cred['id']),
                'type': 'public-key',
                'transports': ['usb', 'nfc', 'ble', 'internal']
            } for cred in credentials]
        )
        
        # Store challenge and user ID in session
        session['webauthn_challenge'] = options.challenge
        session['webauthn_user_id'] = user.id
        
        return jsonify(options)
        
    except Exception as e:
        log_security_event(
            event_type='webauthn_auth_error',
            description=f'WebAuthn authentication begin error: {str(e)}',
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Authentication failed'}), 500


@auth_bp.route('/webauthn/authenticate/complete', methods=['POST'])
def webauthn_authenticate_complete():
    """Complete WebAuthn authentication"""
    try:
        credential_data = request.json.get('credential')
        csrf_token = request.json.get('csrf_token')
        
        if not validate_csrf(csrf_token):
            return jsonify({'error': 'Invalid CSRF token'}), 400
        
        challenge = session.pop('webauthn_challenge', None)
        user_id = session.pop('webauthn_user_id', None)
        
        if not challenge or not user_id or not credential_data:
            return jsonify({'error': 'Invalid request'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        # Find matching credential
        credentials = user.get_webauthn_credentials()
        matching_credential = None
        
        for cred in credentials:
            if cred['id'] == credential_data['id']:
                matching_credential = cred
                break
        
        if not matching_credential:
            return jsonify({'error': 'Credential not found'}), 400
        
        webauthn_config = get_webauthn_config()
        
        # Verify authentication response
        credential = AuthenticationCredential.parse_raw(json.dumps(credential_data))
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_origin=webauthn_config['origin'],
            expected_rp_id=webauthn_config['rp_id'],
            credential_public_key=base64.b64decode(matching_credential['public_key']),
            credential_current_sign_count=matching_credential['sign_count'],
        )
        
        if verification.verified:
            # Update sign count
            matching_credential['sign_count'] = verification.new_sign_count
            user.set_webauthn_credentials(credentials)
            
            # Create session and login user
            user_session = create_user_session(user)
            user.last_login = datetime.utcnow()
            user.reset_failed_login()
            user.update_last_activity()
            db.session.commit()
            
            login_user(user, remember=True)
            
            log_security_event(
                event_type='webauthn_login',
                user_id=user.id,
                description='Successful WebAuthn authentication',
                action='authenticate'
            )
            
            return jsonify({
                'status': 'success', 
                'redirect': url_for('dashboard.index')
            })
        else:
            user.increment_failed_login()
            db.session.commit()
            
            log_security_event(
                event_type='webauthn_auth_failed',
                user_id=user.id,
                description='Failed WebAuthn authentication',
                success=False,
                error_message='Verification failed'
            )
            
            return jsonify({'error': 'Authentication verification failed'}), 400
            
    except Exception as e:
        log_security_event(
            event_type='webauthn_auth_error',
            description=f'WebAuthn authentication complete error: {str(e)}',
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Authentication failed'}), 500


@auth_bp.route('/terminate-session/<int:session_id>')
@enhanced_login_required
def terminate_session(session_id):
    """Terminate a specific user session"""
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()
    
    if user_session:
        user_session.terminate('manual')
        db.session.commit()
        
        log_security_event(
            event_type='session_terminated',
            user_id=current_user.id,
            description=f'Session {user_session.session_id} terminated manually',
            action='terminate'
        )
        
        flash('Session terminated successfully.', 'success')
    else:
        flash('Session not found.', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/terminate-all-sessions')
@enhanced_login_required
def terminate_all_sessions():
    """Terminate all user sessions except current"""
    current_session_id = session.get('session_id')
    
    # Terminate all other sessions
    other_sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).filter(UserSession.session_id != current_session_id).all()
    
    for user_session in other_sessions:
        user_session.terminate('manual')
    
    db.session.commit()
    
    log_security_event(
        event_type='all_sessions_terminated',
        user_id=current_user.id,
        description=f'All other sessions terminated (kept current session)',
        action='terminate'
    )
    
    flash(f'Terminated {len(other_sessions)} other sessions.', 'success')
    return redirect(url_for('auth.profile'))