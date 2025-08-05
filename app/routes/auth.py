from flask import Blueprint, render_template, redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlencode
from app import db, oauth
from app.models.user import User
import requests

bp = Blueprint('auth', __name__)

@bp.route('/login')
def login():
    """Login page and Auth0 redirect."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # If Auth0 is configured, redirect to Auth0
    if current_app.config.get('AUTH0_CLIENT_ID'):
        redirect_uri = url_for('auth.callback', _external=True)
        return oauth.auth0.authorize_redirect(redirect_uri)
    
    # Otherwise show local login form
    return render_template('auth/login.html')

@bp.route('/callback')
def callback():
    """Auth0 callback handler."""
    try:
        token = oauth.auth0.authorize_access_token()
        session['jwt_payload'] = token
        
        # Get user info from Auth0
        resp = oauth.auth0.get('userinfo')
        userinfo = resp.json()
        
        # Find or create user
        user = User.query.filter_by(auth0_id=userinfo['sub']).first()
        
        if not user:
            # Create new user
            user = User.create_from_auth0(userinfo)
            db.session.add(user)
            db.session.commit()
            flash('Welcome! Your account has been created.', 'success')
        else:
            # Update user info if needed
            user.email = userinfo.get('email', user.email)
            user.name = userinfo.get('name', user.name)
            db.session.commit()
        
        # Log in the user
        login_user(user, remember=True)
        flash(f'Welcome back, {user.name}!', 'success')
        
        # Redirect to intended page or dashboard
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        
    except Exception as e:
        current_app.logger.error(f'Auth callback error: {str(e)}')
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@bp.route('/logout')
@login_required
def logout():
    """Logout user and clear session."""
    session.clear()
    logout_user()
    
    # If Auth0 is configured, redirect to Auth0 logout
    if current_app.config.get('AUTH0_DOMAIN'):
        params = {
            'returnTo': url_for('main.index', _external=True),
            'client_id': current_app.config['AUTH0_CLIENT_ID']
        }
        return redirect(f"https://{current_app.config['AUTH0_DOMAIN']}/v2/logout?" + urlencode(params))
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/login-local', methods=['GET', 'POST'])
def login_local():
    """Local login for development/testing."""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required.', 'error')
            return render_template('auth/login_local.html')
        
        # Find or create local user (for development only)
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create a local development user
            user = User(
                auth0_id=f'local|{email}',
                email=email,
                name=email.split('@')[0].title(),
                role='admin'  # Make first user admin
            )
            db.session.add(user)
            db.session.commit()
            flash('Development account created.', 'success')
        
        login_user(user, remember=True)
        flash(f'Welcome, {user.name}!', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
    
    return render_template('auth/login_local.html')

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        current_user.name = request.form.get('name', current_user.name)
        
        # Only admins can change roles
        if current_user.has_role('admin'):
            new_role = request.form.get('role')
            if new_role in ['admin', 'manager', 'employee']:
                current_user.role = new_role
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update profile.', 'error')
        current_app.logger.error(f'Profile update error: {str(e)}')
    
    return redirect(url_for('auth.profile'))

@bp.route('/users')
@login_required
def manage_users():
    """User management page (admin only)."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/manage_users.html', users=users)

@bp.route('/users/<int:user_id>/update-role', methods=['POST'])
@login_required
def update_user_role(user_id):
    """Update user role (admin only)."""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        user = User.query.get_or_404(user_id)
        new_role = request.form.get('role')
        
        if new_role in ['admin', 'manager', 'employee']:
            user.role = new_role
            db.session.commit()
            flash(f'User role updated to {new_role}.', 'success')
        else:
            flash('Invalid role selected.', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash('Failed to update user role.', 'error')
        current_app.logger.error(f'User role update error: {str(e)}')
    
    return redirect(url_for('auth.manage_users'))

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)."""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow disabling the last admin
        if user.role == 'admin' and user.is_active:
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                flash('Cannot disable the last active admin user.', 'error')
                return redirect(url_for('auth.manage_users'))
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User has been {status}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update user status.', 'error')
        current_app.logger.error(f'User status toggle error: {str(e)}')
    
    return redirect(url_for('auth.manage_users'))