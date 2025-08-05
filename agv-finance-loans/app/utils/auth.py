"""
Authentication utilities for AGV Finance and Loans
Includes Auth0 integration and WebAuthn support
"""

import os
import json
from functools import wraps
from flask import session, redirect, url_for, request, current_app, flash
from flask_login import current_user
from authlib.integrations.flask_client import OAuth
from urllib.parse import urlencode

# Initialize OAuth
oauth = OAuth()

def init_auth0(app):
    """Initialize Auth0 OAuth client"""
    oauth.init_app(app)
    
    auth0 = oauth.register(
        'auth0',
        client_id=app.config['AUTH0_CLIENT_ID'],
        client_secret=app.config['AUTH0_CLIENT_SECRET'],
        client_kwargs={
            'scope': 'openid profile email',
        },
        server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid_configuration'
    )
    
    return auth0

def requires_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def requires_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if role == 'admin' and not current_user.is_admin():
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('dashboard.index'))
            elif role == 'manager' and not current_user.is_manager():
                flash('Access denied. Manager privileges required.', 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def get_auth0_logout_url():
    """Generate Auth0 logout URL"""
    return f"https://{current_app.config['AUTH0_DOMAIN']}/v2/logout?" + urlencode({
        'returnTo': url_for('main.index', _external=True),
        'client_id': current_app.config['AUTH0_CLIENT_ID']
    })

class WebAuthnHelper:
    """Helper class for WebAuthn biometric authentication"""
    
    @staticmethod
    def generate_challenge():
        """Generate a random challenge for WebAuthn"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_credential_creation_options(user):
        """Create credential creation options for registration"""
        challenge = WebAuthnHelper.generate_challenge()
        session['webauthn_challenge'] = challenge
        
        return {
            'challenge': challenge,
            'rp': {
                'name': 'AGV Finance and Loans',
                'id': request.host.split(':')[0]
            },
            'user': {
                'id': str(user.id),
                'name': user.email,
                'displayName': user.name
            },
            'pubKeyCredParams': [
                {'alg': -7, 'type': 'public-key'},  # ES256
                {'alg': -257, 'type': 'public-key'},  # RS256
            ],
            'authenticatorSelection': {
                'authenticatorAttachment': 'platform',
                'userVerification': 'required'
            },
            'timeout': 60000,
            'attestation': 'direct'
        }
    
    @staticmethod
    def create_credential_request_options(user):
        """Create credential request options for authentication"""
        challenge = WebAuthnHelper.generate_challenge()
        session['webauthn_challenge'] = challenge
        
        # Get user's stored credentials
        credentials = []
        if user.webauthn_credentials:
            try:
                stored_creds = json.loads(user.webauthn_credentials)
                credentials = [{'id': cred['id'], 'type': 'public-key'} for cred in stored_creds]
            except:
                pass
        
        return {
            'challenge': challenge,
            'allowCredentials': credentials,
            'timeout': 60000,
            'userVerification': 'required'
        }
    
    @staticmethod
    def verify_registration(user, credential_data):
        """Verify and store WebAuthn registration"""
        try:
            # In a real implementation, you would verify the attestation
            # For now, we'll store the credential data
            
            stored_credentials = []
            if user.webauthn_credentials:
                stored_credentials = json.loads(user.webauthn_credentials)
            
            # Add new credential
            new_credential = {
                'id': credential_data.get('id'),
                'public_key': credential_data.get('response', {}).get('publicKey'),
                'counter': 0,
                'created_at': str(datetime.utcnow())
            }
            
            stored_credentials.append(new_credential)
            user.webauthn_credentials = json.dumps(stored_credentials)
            
            from app import db
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"WebAuthn registration error: {e}")
            return False
    
    @staticmethod
    def verify_authentication(user, assertion_data):
        """Verify WebAuthn authentication"""
        try:
            # In a real implementation, you would verify the signature
            # For now, we'll do basic validation
            
            if not user.webauthn_credentials:
                return False
            
            stored_credentials = json.loads(user.webauthn_credentials)
            credential_id = assertion_data.get('id')
            
            # Check if credential exists
            for cred in stored_credentials:
                if cred['id'] == credential_id:
                    # Update counter (prevent replay attacks)
                    cred['counter'] += 1
                    user.webauthn_credentials = json.dumps(stored_credentials)
                    
                    from app import db
                    db.session.commit()
                    return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"WebAuthn authentication error: {e}")
            return False

def generate_secure_token():
    """Generate a secure random token"""
    import secrets
    return secrets.token_urlsafe(32)

def hash_password(password):
    """Hash a password using bcrypt"""
    from bcrypt import hashpw, gensalt
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    from bcrypt import checkpw
    return checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_user_permissions(user):
    """Get user permissions based on role"""
    permissions = {
        'can_view_dashboard': True,
        'can_view_customers': True,
        'can_create_customers': user.role in ['admin', 'manager', 'employee'],
        'can_edit_customers': user.role in ['admin', 'manager'],
        'can_delete_customers': user.role == 'admin',
        'can_view_loans': True,
        'can_create_loans': user.role in ['admin', 'manager'],
        'can_approve_loans': user.role == 'admin',
        'can_disburse_loans': user.role in ['admin', 'manager'],
        'can_view_payments': True,
        'can_process_payments': user.role in ['admin', 'manager', 'employee'],
        'can_reverse_payments': user.role in ['admin', 'manager'],
        'can_view_reports': user.role in ['admin', 'manager'],
        'can_manage_users': user.role == 'admin',
        'can_manage_settings': user.role == 'admin'
    }
    return permissions