from app import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(20), unique=True, nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    payment_amount = db.Column(db.Numeric(15, 2), nullable=False)
    principal_component = db.Column(db.Numeric(15, 2), nullable=False)
    interest_component = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), default='cash')  # cash, bank_transfer, cheque
    receipt_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.payment_id}: ₹{self.payment_amount}>'

    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'payment_amount': float(self.payment_amount),
            'principal_component': float(self.principal_component),
            'interest_component': float(self.interest_component),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method
        }