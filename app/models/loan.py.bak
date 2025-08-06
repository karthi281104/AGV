from app import db
from datetime import datetime
from decimal import Decimal


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    loan_type = db.Column(db.String(20), nullable=False)  # gold, bond
    principal_amount = db.Column(db.Numeric(15, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # Annual percentage
    loan_term_months = db.Column(db.Integer, nullable=False)
    disbursed_amount = db.Column(db.Numeric(15, 2), nullable=False)
    outstanding_principal = db.Column(db.Numeric(15, 2), nullable=False)
    total_interest_accrued = db.Column(db.Numeric(15, 2), default=0)

    # Document paths
    loan_document_path = db.Column(db.String(200))
    surety_document_path = db.Column(db.String(200))
    collateral_document_path = db.Column(db.String(200))

    # Surety person details
    surety_name = db.Column(db.String(100))
    surety_phone = db.Column(db.String(15))
    surety_address = db.Column(db.Text)
    surety_id_proof = db.Column(db.String(50))

    # Status and dates
    status = db.Column(db.String(20), default='active')  # active, closed, overdue
    disbursed_date = db.Column(db.DateTime, default=datetime.utcnow)
    maturity_date = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='loan', lazy=True)

    def __repr__(self):
        return f'<Loan {self.loan_id}: ₹{self.principal_amount}>'

    def calculate_monthly_emi(self):
        """Calculate monthly EMI based on principal, rate, and term"""
        p = float(self.principal_amount)
        r = float(self.interest_rate) / 100 / 12  # Monthly rate
        n = self.loan_term_months

        if r == 0:
            return p / n

        emi = p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(emi, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'loan_type': self.loan_type,
            'principal_amount': float(self.principal_amount),
            'interest_rate': float(self.interest_rate),
            'outstanding_principal': float(self.outstanding_principal),
            'status': self.status,
            'disbursed_date': self.disbursed_date.isoformat() if self.disbursed_date else None
        }