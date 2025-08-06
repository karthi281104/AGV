from app import db
from datetime import datetime
import uuid


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    identity_type = db.Column(db.String(20), nullable=False)  # aadhaar, passport, etc.
    identity_number = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    loans = db.relationship('Loan', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'identity_type': self.identity_type,
            'identity_number': self.identity_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(100), db.ForeignKey('customers.id'), nullable=False)
    principal_amount = db.Column(db.Numeric(15, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # Annual percentage
    tenure_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, closed, overdue
    collateral_type = db.Column(db.String(50))  # gold, bonds, etc.
    collateral_description = db.Column(db.Text)
    disbursed_amount = db.Column(db.Numeric(15, 2), nullable=False)
    outstanding_principal = db.Column(db.Numeric(15, 2), nullable=False)
    total_interest_accrued = db.Column(db.Numeric(15, 2), default=0)
    created_by = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    disbursed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='loan', lazy=True)

    def __repr__(self):
        return f'<Loan {self.id}: ₹{self.principal_amount}>'

    def calculate_monthly_emi(self):
        """Calculate monthly EMI based on principal, rate, and term"""
        p = float(self.principal_amount)
        r = float(self.interest_rate) / 100 / 12  # Monthly rate
        n = self.tenure_months

        if r == 0:
            return p / n

        emi = p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(emi, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'principal_amount': float(self.principal_amount),
            'interest_rate': float(self.interest_rate),
            'outstanding_principal': float(self.outstanding_principal),
            'status': self.status,
            'collateral_type': self.collateral_type,
            'disbursed_at': self.disbursed_at.isoformat() if self.disbursed_at else None
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id = db.Column(db.String(100), db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    principal_amount = db.Column(db.Numeric(15, 2), nullable=False)
    interest_amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), default='cash')  # cash, bank_transfer, cheque
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}: ₹{self.amount}>'

    def to_dict(self):
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'amount': float(self.amount),
            'principal_amount': float(self.principal_amount),
            'interest_amount': float(self.interest_amount),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number
        }


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = db.Column(db.String(20), nullable=False)  # customer, loan, payment
    entity_id = db.Column(db.String(100), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_by = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.file_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'document_type': self.document_type,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }