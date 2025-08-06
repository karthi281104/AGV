from functools import wraps
from flask import session, redirect, url_for, request, current_app, abort
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.auth import UserSession
from app import db
import jwt
from datetime import datetime, timedelta
import uuid


def hash_password(password):
    return generate_password_hash(password)


def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role != role and current_user.role != 'admin':
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def verify_auth0_token(token):
    try:
        payload = jwt.decode(
            token,
            current_app.config['AUTH0_CLIENT_SECRET'],
            algorithms=['HS256'],
            audience=current_app.config['AUTH0_CLIENT_ID']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_user_session(user_id, device_info=None):
    session_id = str(uuid.uuid4())
    user_session = UserSession(
        id=session_id,
        user_id=user_id,
        device_info=device_info,
        ip_address=request.remote_addr,
        expires_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.session.add(user_session)
    db.session.commit()
    return session_id


def cleanup_expired_sessions():
    """Remove expired user sessions"""
    expired_sessions = UserSession.query.filter(
        UserSession.expires_at < datetime.utcnow()
    ).all()
    
    for session_obj in expired_sessions:
        db.session.delete(session_obj)
    
    db.session.commit()


def get_device_info():
    """Extract device information from request headers"""
    user_agent = request.headers.get('User-Agent', '')
    return {
        'user_agent': user_agent,
        'ip_address': request.remote_addr,
        'timestamp': datetime.utcnow().isoformat()
    }