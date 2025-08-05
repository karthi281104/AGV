"""
User Model for AGV Finance and Loans
Integrates with Auth0 authentication and supports role-based access
"""

from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    picture = db.Column(db.String(500))
    
    # Role-based access control
    role = db.Column(db.String(50), nullable=False, default='employee')  # admin, manager, employee
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    
    # Biometric and authentication data
    webauthn_credentials = db.Column(db.Text)  # JSON string of WebAuthn credentials
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_customers = db.relationship('Customer', backref='created_by_user', lazy='dynamic', foreign_keys='Customer.created_by')
    created_loans = db.relationship('Loan', backref='created_by_user', lazy='dynamic', foreign_keys='Loan.created_by')
    processed_payments = db.relationship('Payment', backref='processed_by_user', lazy='dynamic', foreign_keys='Payment.processed_by')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_id(self):
        """Return the user ID for Flask-Login"""
        return str(self.id)
    
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.role == 'admin'
    
    def is_manager(self):
        """Check if user has manager privileges"""
        return self.role in ['admin', 'manager']
    
    def can_create_loans(self):
        """Check if user can create loans"""
        return self.role in ['admin', 'manager']
    
    def can_approve_loans(self):
        """Check if user can approve loans"""
        return self.role == 'admin'
    
    def can_process_payments(self):
        """Check if user can process payments"""
        return self.role in ['admin', 'manager', 'employee']
    
    def record_login(self):
        """Record a successful login"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'auth0_id': self.auth0_id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def create_from_auth0(auth0_user_info):
        """Create a new user from Auth0 user information"""
        user = User(
            auth0_id=auth0_user_info['sub'],
            email=auth0_user_info['email'],
            name=auth0_user_info.get('name', auth0_user_info['email']),
            picture=auth0_user_info.get('picture'),
            is_verified=auth0_user_info.get('email_verified', False)
        )
        db.session.add(user)
        db.session.commit()
        return user