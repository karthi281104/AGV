from app import db
from datetime import datetime


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text, nullable=False)
    aadhar_number = db.Column(db.String(12), unique=True, nullable=False)
    pan_number = db.Column(db.String(10), unique=True)
    fingerprint_data = db.Column(db.Text)  # Biometric data storage
    photo_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    loans = db.relationship('Loan', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.customer_id}: {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }