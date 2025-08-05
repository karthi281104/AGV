from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import json


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin, employee, manager
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    preferences = db.Column(db.Text)  # JSON string for user preferences
    department = db.Column(db.String(50))
    phone = db.Column(db.String(20))

    def __repr__(self):
        return f'<User {self.email}>'

    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role

    def has_any_role(self, roles):
        """Check if user has any of the specified roles"""
        return self.role in roles

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_manager(self):
        """Check if user is manager or admin"""
        return self.role in ['admin', 'manager']

    def get_preferences(self):
        """Get user preferences as dictionary"""
        if self.preferences:
            try:
                return json.loads(self.preferences)
            except:
                return {}
        return {}

    def set_preferences(self, prefs_dict):
        """Set user preferences from dictionary"""
        self.preferences = json.dumps(prefs_dict)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'department': self.department,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))