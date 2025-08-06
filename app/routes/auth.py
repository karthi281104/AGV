from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
import uuid

from app import db, oauth
from app.models.auth import User, UserSession
from app.utils.auth_helpers import create_user_session

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with fallback authentication"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')
        
        # Demo authentication for development
        if email == 'demo@agvfinance.com' and password == 'demo123':
            demo_user = User.query.filter_by(email=email).first()
            if not demo_user:
                # Create demo user if not exists
                demo_user = User(
                    id='demo_001',
                    auth0_id='auth0|demo001',
                    username='demo',
                    email=email,
                    name='Demo Employee',
                    role='employee',
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(demo_user)
                db.session.commit()
            
            # Update last login
            demo_user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create session
            session_id = create_user_session(demo_user.id)
            session['user_session_id'] = session_id
            
            # Login user
            login_user(demo_user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.index'))
        
        # Check for other demo users
        demo_users = {
            'admin@agvfinance.com': ('admin123', 'admin'),
            'manager@agvfinance.com': ('manager123', 'manager')
        }
        
        if email in demo_users:
            correct_password, role = demo_users[email]
            if password == correct_password:
                user = User.query.filter_by(email=email).first()
                if not user:
                    # Create user if not exists
                    user = User(
                        id=f'{role}_001',
                        auth0_id=f'auth0|{role}001',
                        username=role,
                        email=email,
                        name=f'{role.title()} User',
                        role=role,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(user)
                    db.session.commit()
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Create session
                session_id = create_user_session(user.id)
                session['user_session_id'] = session_id
                
                # Login user
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard.index'))
        
        flash('Invalid email or password.', 'error')
        return render_template('auth/login.html')
        
    except Exception as e:
        flash('An error occurred during login. Please try again.', 'error')
        print(f"Login error: {e}")
        return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user and clear session"""
    try:
        # Clear user session from database
        if 'user_session_id' in session:
            user_session = UserSession.query.filter_by(id=session['user_session_id']).first()
            if user_session:
                db.session.delete(user_session)
                db.session.commit()
        
        # Clear Flask session
        session.clear()
        
        # Logout user
        logout_user()
        
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Logout error: {e}")
        return redirect(url_for('main.index'))

@auth_bp.route('/auth0-login')
def auth0_login():
    """Auth0 OAuth login (when properly configured)"""
    try:
        connection = request.args.get('connection', '')
        redirect_uri = url_for('auth.auth0_callback', _external=True)
        
        # Check if Auth0 is properly configured
        if not oauth.auth0 or oauth.auth0.client_id == 'your-client-id':
            flash('Auth0 not configured. Using demo authentication.', 'warning')
            return redirect(url_for('auth.login'))
        
        return oauth.auth0.authorize_redirect(redirect_uri, connection=connection)
        
    except Exception as e:
        flash('OAuth login not available. Please use email/password.', 'warning')
        print(f"Auth0 login error: {e}")
        return redirect(url_for('auth.login'))

@auth_bp.route('/callback')
def auth0_callback():
    """Auth0 OAuth callback"""
    try:
        token = oauth.auth0.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            # Find or create user
            user = User.query.filter_by(auth0_id=user_info['sub']).first()
            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    auth0_id=user_info['sub'],
                    email=user_info['email'],
                    name=user_info['name'],
                    username=user_info.get('nickname', user_info['email'].split('@')[0]),
                    role='employee',
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(user)
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create session
            session_id = create_user_session(user.id)
            session['user_session_id'] = session_id
            
            login_user(user)
            return redirect(url_for('dashboard.index'))
        
        flash('Authentication failed.', 'error')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        flash('Authentication error. Please try again.', 'error')
        print(f"Auth0 callback error: {e}")
        return redirect(url_for('auth.login'))