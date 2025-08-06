from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import uuid


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    auth0_id = db.Column(db.String(100), unique=True, nullable=True)  # Made nullable for demo users
    username = db.Column(db.String(80), unique=True, nullable=True)  # Added username field
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin, employee, manager
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    webauthn_credentials = db.relationship('WebAuthnCredential', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    device_info = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<UserSession {self.id}>'


class WebAuthnCredential(db.Model):
    __tablename__ = 'webauthn_credentials'

    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    credential_id = db.Column(db.LargeBinary, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, default=0)
    device_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WebAuthnCredential {self.id}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)