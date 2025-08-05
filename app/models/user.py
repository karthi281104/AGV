from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta
import json


class Role(db.Model):
    """User roles for access control"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.Text)  # JSON string of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='user_role', lazy='dynamic')
    
    def get_permissions(self):
        """Get role permissions as list"""
        return json.loads(self.permissions) if self.permissions else []
    
    def set_permissions(self, permissions):
        """Set role permissions from list"""
        self.permissions = json.dumps(permissions)
    
    def has_permission(self, permission):
        """Check if role has specific permission"""
        return permission in self.get_permissions()
    
    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """Enhanced user model with RBAC and preferences"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Role-based access control
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=1)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)
    
    # WebAuthn/Biometric fields
    webauthn_enabled = db.Column(db.Boolean, default=False)
    webauthn_credentials = db.Column(db.Text)  # JSON string of credential data
    
    # User preferences
    preferences = db.Column(db.Text)  # JSON string of user preferences
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    @property
    def role(self):
        """Get user role name for backward compatibility"""
        return self.user_role.name if self.user_role else 'employee'
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        return self.user_role and self.user_role.name == role_name
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        return self.user_role and self.user_role.has_permission(permission)
    
    def get_preferences(self):
        """Get user preferences as dictionary"""
        return json.loads(self.preferences) if self.preferences else {}
    
    def set_preferences(self, prefs):
        """Set user preferences from dictionary"""
        self.preferences = json.dumps(prefs)
    
    def get_webauthn_credentials(self):
        """Get WebAuthn credentials as list"""
        return json.loads(self.webauthn_credentials) if self.webauthn_credentials else []
    
    def set_webauthn_credentials(self, credentials):
        """Set WebAuthn credentials from list"""
        self.webauthn_credentials = json.dumps(credentials)
    
    def add_webauthn_credential(self, credential):
        """Add a new WebAuthn credential"""
        credentials = self.get_webauthn_credentials()
        credentials.append(credential)
        self.set_webauthn_credentials(credentials)
        self.webauthn_enabled = True
    
    def is_account_locked(self):
        """Check if account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def lock_account(self, duration=timedelta(hours=24)):
        """Lock user account for specified duration"""
        self.locked_until = datetime.utcnow() + duration
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        
        # Lock account after too many failed attempts
        from app.config.auth0 import RateLimitConfig
        if self.failed_login_attempts >= RateLimitConfig.ACCOUNT_LOCKOUT_THRESHOLD:
            self.lock_account(RateLimitConfig.ACCOUNT_LOCKOUT_DURATION)
    
    def reset_failed_login(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self):
        return f'<User {self.email}>'


class UserSession(db.Model):
    """Track user sessions for security and concurrency control"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    
    # Session metadata
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    country = db.Column(db.String(2))
    city = db.Column(db.String(100))
    
    # Session timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Session status
    is_active = db.Column(db.Boolean, default=True)
    logout_reason = db.Column(db.String(50))  # 'manual', 'timeout', 'security'
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid and active"""
        return self.is_active and not self.is_expired()
    
    def extend_session(self, duration=timedelta(minutes=30)):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + duration
        self.last_activity = datetime.utcnow()
    
    def terminate(self, reason='manual'):
        """Terminate session"""
        self.is_active = False
        self.logout_reason = reason
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'


class AuditLog(db.Model):
    """Audit log for security and compliance tracking"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Event details
    event_type = db.Column(db.String(50), nullable=False)  # login, logout, access_denied, etc.
    event_description = db.Column(db.Text)
    resource = db.Column(db.String(100))  # Resource accessed
    action = db.Column(db.String(50))     # Action attempted
    
    # Request metadata
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    session_id = db.Column(db.String(255))
    
    # Security metadata
    risk_score = db.Column(db.Integer, default=0)  # 0-100 risk score
    anomaly_flags = db.Column(db.Text)  # JSON array of anomaly indicators
    
    # Result
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_anomaly_flags(self):
        """Get anomaly flags as list"""
        return json.loads(self.anomaly_flags) if self.anomaly_flags else []
    
    def set_anomaly_flags(self, flags):
        """Set anomaly flags from list"""
        self.anomaly_flags = json.dumps(flags)
    
    def add_anomaly_flag(self, flag):
        """Add an anomaly flag"""
        flags = self.get_anomaly_flags()
        if flag not in flags:
            flags.append(flag)
            self.set_anomaly_flags(flags)
    
    @classmethod
    def log_event(cls, user_id, event_type, description=None, resource=None, 
                  action=None, success=True, error_message=None, ip_address=None,
                  user_agent=None, session_id=None, risk_score=0):
        """Helper method to create audit log entry"""
        log_entry = cls(
            user_id=user_id,
            event_type=event_type,
            event_description=description,
            resource=resource,
            action=action,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            risk_score=risk_score
        )
        db.session.add(log_entry)
        return log_entry
    
    def __repr__(self):
        return f'<AuditLog {self.event_type} for User {self.user_id}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))


def init_default_roles():
    """Initialize default roles if they don't exist"""
    # Admin role
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_permissions = [
            'user.create', 'user.read', 'user.update', 'user.delete',
            'role.create', 'role.read', 'role.update', 'role.delete',
            'audit.read', 'system.configure', 'reports.generate'
        ]
        admin_role = Role(
            name='admin',
            description='Full administrative access',
            permissions=json.dumps(admin_permissions)
        )
        db.session.add(admin_role)
    
    # Employee role
    employee_role = Role.query.filter_by(name='employee').first()
    if not employee_role:
        employee_permissions = [
            'customer.create', 'customer.read', 'customer.update',
            'loan.create', 'loan.read', 'loan.update',
            'payment.create', 'payment.read', 'dashboard.view'
        ]
        employee_role = Role(
            name='employee',
            description='Standard employee access',
            permissions=json.dumps(employee_permissions)
        )
        db.session.add(employee_role)
    
    # Viewer role
    viewer_role = Role.query.filter_by(name='viewer').first()
    if not viewer_role:
        viewer_permissions = [
            'customer.read', 'loan.read', 'payment.read', 'dashboard.view'
        ]
        viewer_role = Role(
            name='viewer',
            description='Read-only access',
            permissions=json.dumps(viewer_permissions)
        )
        db.session.add(viewer_role)
    
    db.session.commit()