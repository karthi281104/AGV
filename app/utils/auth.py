from functools import wraps
from flask import flash, redirect, url_for, abort, current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta


def hash_password(password):
    """Hash a password for storing"""
    return generate_password_hash(password)


def verify_password(stored_password, provided_password):
    """Verify a stored password against provided password"""
    return check_password_hash(stored_password, provided_password)


def login_required(f):
    """Enhanced login required decorator with better error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user is still active
        if not current_user.is_active:
            flash('Your account has been deactivated.', 'error')
            return redirect(url_for('auth.logout'))
            
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Decorator to require specific roles for access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_any_role(roles):
                flash('You do not have permission to access this page.', 'error')
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Administrator access required.', 'error')
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """Decorator to require manager or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_manager():
            flash('Manager or Administrator access required.', 'error')
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function


def validate_auth0_token(token):
    """Validate Auth0 JWT token"""
    try:
        # This would need proper Auth0 public key validation in production
        # For now, we'll do basic JWT validation
        decoded = jwt.decode(
            token, 
            current_app.config['SECRET_KEY'], 
            algorithms=['HS256'],
            options={"verify_signature": False}  # Would verify with Auth0 public key in production
        )
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def check_session_timeout():
    """Check if user session has timed out"""
    if current_user.is_authenticated and current_user.last_login:
        timeout_duration = current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=8))
        if datetime.utcnow() - current_user.last_login > timeout_duration:
            return True
    return False