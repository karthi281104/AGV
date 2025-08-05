from flask_login import UserMixin
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='employee')  # admin, manager, employee
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def has_role(self, role):
        """Check if user has a specific role."""
        return self.role == role
    
    def can_access_admin(self):
        """Check if user can access admin functions."""
        return self.role in ['admin', 'manager']
    
    def can_manage_loans(self):
        """Check if user can manage loans."""
        return self.role in ['admin', 'manager', 'employee']
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'auth0_id': self.auth0_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_from_auth0(auth0_user):
        """Create a new user from Auth0 user data."""
        user = User(
            auth0_id=auth0_user['sub'],
            email=auth0_user['email'],
            name=auth0_user.get('name', auth0_user['email']),
            role='employee'  # Default role
        )
        return user