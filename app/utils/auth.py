"""
Enhanced Authentication Utilities
Provides decorators, session management, and security functions
"""
from functools import wraps
from datetime import datetime, timedelta
import secrets
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, request, current_app, redirect, url_for, flash, jsonify, abort
from flask_login import current_user, login_required
from app.models.user import User, UserSession, AuditLog
from app import db


def hash_password(password):
    """Hash password using Werkzeug"""
    return generate_password_hash(password)


def verify_password(stored_password, provided_password):
    """Verify password using Werkzeug"""
    return check_password_hash(stored_password, provided_password)


def requires_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                AuditLog.log_event(
                    user_id=current_user.id,
                    event_type='access_denied',
                    description=f'Permission denied: {permission}',
                    resource=request.endpoint,
                    action='access',
                    success=False,
                    ip_address=get_client_ip(),
                    user_agent=request.user_agent.string,
                    session_id=session.get('session_id')
                )
                db.session.commit()
                
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash('You do not have permission to access this resource.', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_role(role_name):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(role_name):
                AuditLog.log_event(
                    user_id=current_user.id,
                    event_type='access_denied',
                    description=f'Role required: {role_name}',
                    resource=request.endpoint,
                    action='access',
                    success=False,
                    ip_address=get_client_ip(),
                    user_agent=request.user_agent.string,
                    session_id=session.get('session_id')
                )
                db.session.commit()
                
                if request.is_json:
                    return jsonify({'error': 'Access denied'}), 403
                flash('You do not have the required role to access this resource.', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    return requires_role('admin')(f)


def employee_required(f):
    """Decorator to require employee or admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.has_role('admin') or current_user.has_role('employee')):
            AuditLog.log_event(
                user_id=current_user.id,
                event_type='access_denied',
                description='Employee access required',
                resource=request.endpoint,
                action='access',
                success=False,
                ip_address=get_client_ip(),
                user_agent=request.user_agent.string,
                session_id=session.get('session_id')
            )
            db.session.commit()
            
            if request.is_json:
                return jsonify({'error': 'Access denied'}), 403
            flash('Employee access required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def check_session_validity():
    """Check if current session is valid"""
    session_id = session.get('session_id')
    if not session_id:
        return False
    
    user_session = UserSession.query.filter_by(
        session_id=session_id,
        is_active=True
    ).first()
    
    if not user_session or not user_session.is_valid():
        # Session invalid or expired
        if user_session:
            user_session.terminate('timeout')
            db.session.commit()
        
        session.clear()
        return False
    
    # Extend session activity
    user_session.last_activity = datetime.utcnow()
    db.session.commit()
    
    return True


def create_user_session(user, ip_address=None, user_agent=None):
    """Create a new user session"""
    from app.config.auth0 import SessionConfig
    
    # Generate unique session ID
    session_id = secrets.token_urlsafe(32)
    
    # Check concurrent session limit
    active_sessions = UserSession.query.filter_by(
        user_id=user.id,
        is_active=True
    ).count()
    
    if active_sessions >= SessionConfig.MAX_SESSIONS_PER_USER:
        # Terminate oldest session
        oldest_session = UserSession.query.filter_by(
            user_id=user.id,
            is_active=True
        ).order_by(UserSession.last_activity.asc()).first()
        
        if oldest_session:
            oldest_session.terminate('concurrent_limit')
    
    # Create new session
    user_session = UserSession(
        user_id=user.id,
        session_id=session_id,
        ip_address=ip_address or get_client_ip(),
        user_agent=user_agent or request.user_agent.string,
        expires_at=datetime.utcnow() + SessionConfig.PERMANENT_SESSION_LIFETIME
    )
    
    db.session.add(user_session)
    db.session.commit()
    
    # Store session ID in Flask session
    session['session_id'] = session_id
    session.permanent = True
    
    return user_session


def terminate_user_session(session_id=None, reason='manual'):
    """Terminate user session"""
    if not session_id:
        session_id = session.get('session_id')
    
    if session_id:
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        if user_session:
            user_session.terminate(reason)
            db.session.commit()
    
    session.clear()


def terminate_all_user_sessions(user_id, reason='security'):
    """Terminate all sessions for a user"""
    UserSession.query.filter_by(
        user_id=user_id,
        is_active=True
    ).update({
        'is_active': False,
        'logout_reason': reason
    })
    db.session.commit()


def get_client_ip():
    """Get client IP address from request"""
    # Check for forwarded IP (proxy/load balancer)
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    else:
        return request.remote_addr


def detect_suspicious_activity(user, ip_address=None, user_agent=None):
    """Detect suspicious login activity"""
    anomalies = []
    risk_score = 0
    
    # Check for new IP address
    recent_sessions = UserSession.query.filter_by(user_id=user.id).filter(
        UserSession.created_at > datetime.utcnow() - timedelta(days=30)
    ).all()
    
    recent_ips = {s.ip_address for s in recent_sessions}
    current_ip = ip_address or get_client_ip()
    
    if current_ip not in recent_ips and recent_ips:
        anomalies.append('new_ip_address')
        risk_score += 30
    
    # Check for new user agent
    recent_agents = {s.user_agent for s in recent_sessions}
    current_agent = user_agent or request.user_agent.string
    
    if current_agent not in recent_agents and recent_agents:
        anomalies.append('new_user_agent')
        risk_score += 20
    
    # Check login frequency
    recent_logins = AuditLog.query.filter_by(
        user_id=user.id,
        event_type='login'
    ).filter(
        AuditLog.created_at > datetime.utcnow() - timedelta(hours=1)
    ).count()
    
    if recent_logins > 5:
        anomalies.append('high_login_frequency')
        risk_score += 40
    
    # Check for failed attempts before success
    recent_failures = AuditLog.query.filter_by(
        user_id=user.id,
        event_type='login_failed'
    ).filter(
        AuditLog.created_at > datetime.utcnow() - timedelta(minutes=15)
    ).count()
    
    if recent_failures > 2:
        anomalies.append('recent_failed_attempts')
        risk_score += 25
    
    return anomalies, min(risk_score, 100)


def log_security_event(event_type, user_id=None, description=None, 
                      resource=None, action=None, success=True, 
                      error_message=None, risk_score=0):
    """Log security event with audit trail"""
    user_id = user_id or (current_user.id if current_user.is_authenticated else None)
    
    AuditLog.log_event(
        user_id=user_id,
        event_type=event_type,
        description=description,
        resource=resource,
        action=action,
        success=success,
        error_message=error_message,
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string,
        session_id=session.get('session_id'),
        risk_score=risk_score
    )
    db.session.commit()


def generate_csrf_token():
    """Generate CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']


def validate_csrf_token(token):
    """Validate CSRF token"""
    return token and token == session.get('csrf_token')


def rate_limit_key(identifier, endpoint):
    """Generate rate limit key"""
    return f"rate_limit:{endpoint}:{identifier}"


def is_rate_limited(identifier, endpoint, limit_string):
    """Check if identifier is rate limited for endpoint"""
    # This would integrate with Redis in a real implementation
    # For now, we'll use a simple in-memory approach
    
    # Parse limit string (e.g., "5 per 15 minutes")
    parts = limit_string.split()
    count = int(parts[0])
    
    if 'minute' in limit_string:
        if 'per minute' in limit_string:
            window = 60
        else:
            window = int(parts[2]) * 60
    elif 'hour' in limit_string:
        window = int(parts[2]) * 3600 if len(parts) > 2 else 3600
    else:
        window = 60  # default to 1 minute
    
    # In a real implementation, this would use Redis
    # For now, we'll just return False to not block functionality
    return False


def require_2fa_setup(f):
    """Decorator to require 2FA setup for sensitive operations"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.webauthn_enabled:
            flash('Two-factor authentication is required for this operation.', 'warning')
            return redirect(url_for('auth.setup_2fa', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def enhanced_login_required(f):
    """Enhanced login required with session validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login', next=request.url))
        
        if not check_session_validity():
            if request.is_json:
                return jsonify({'error': 'Session expired'}), 401
            flash('Your session has expired. Please log in again.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        # Update user activity
        current_user.update_last_activity()
        db.session.commit()
        
        return f(*args, **kwargs)
    return decorated_function