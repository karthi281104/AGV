from functools import wraps
from flask import request, current_app
from app.models.auth import UserSession
from app import db
from datetime import datetime, timedelta
import uuid


def create_user_session(user_id, device_info=None):
    """Create a new user session"""
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


def get_device_info():
    """Extract device information from request headers"""
    user_agent = request.headers.get('User-Agent', '')
    return {
        'user_agent': user_agent,
        'ip_address': request.remote_addr,
        'timestamp': datetime.utcnow().isoformat()
    }


def cleanup_expired_sessions():
    """Remove expired user sessions"""
    expired_sessions = UserSession.query.filter(
        UserSession.expires_at < datetime.utcnow()
    ).all()
    
    for session_obj in expired_sessions:
        db.session.delete(session_obj)
    
    db.session.commit()