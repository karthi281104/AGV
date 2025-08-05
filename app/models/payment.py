from app import db
from datetime import datetime
import uuid
from sqlalchemy import Numeric

class Payment(db.Model):
    """Payment model for tracking loan payments and history."""
    
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(Numeric(15, 2), nullable=False)
    principal_paid = db.Column(Numeric(15, 2), nullable=False, default=0)
    interest_paid = db.Column(Numeric(15, 2), nullable=False, default=0)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, cheque, bank_transfer, upi
    receipt_number = db.Column(db.String(100), nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)  # Bank transaction ID, cheque number, etc.
    notes = db.Column(db.Text, nullable=True)
    
    # Payment processing details
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='completed')  # pending, completed, failed, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Payment, self).__init__(**kwargs)
        if not self.payment_id:
            self.payment_id = self.generate_payment_id()
        
        # Auto-calculate principal and interest breakdown if not provided
        if self.amount and not (self.principal_paid or self.interest_paid):
            self.calculate_payment_breakdown()
    
    def __repr__(self):
        return f'<Payment {self.payment_id}: {self.amount}>'
    
    @staticmethod
    def generate_payment_id():
        """Generate a unique payment ID."""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f'PAY{timestamp}{unique_suffix}'
    
    def calculate_payment_breakdown(self):
        """Calculate principal and interest breakdown for the payment."""
        if not self.loan:
            return
        
        # Get current outstanding balances
        outstanding_principal = self.loan.get_outstanding_principal()
        outstanding_interest = self.loan.get_outstanding_balance() - outstanding_principal
        
        payment_amount = float(self.amount)
        
        # First pay interest, then principal
        if outstanding_interest > 0:
            interest_payment = min(payment_amount, outstanding_interest)
            self.interest_paid = interest_payment
            self.principal_paid = payment_amount - interest_payment
        else:
            self.interest_paid = 0
            self.principal_paid = payment_amount
    
    def get_remaining_balance_after_payment(self):
        """Get remaining loan balance after this payment."""
        if not self.loan:
            return 0
        
        # Calculate outstanding before this payment
        previous_payments = Payment.query.filter(
            Payment.loan_id == self.loan_id,
            Payment.id < self.id,
            Payment.status == 'completed'
        ).all()
        
        previous_paid = sum(float(p.amount) for p in previous_payments)
        total_loan_amount = self.loan.get_total_amount()
        
        return total_loan_amount - previous_paid - float(self.amount)
    
    def is_emi_payment(self):
        """Check if this is a regular EMI payment."""
        if not self.loan:
            return False
        
        expected_emi = self.loan.calculate_emi()
        payment_amount = float(self.amount)
        
        # Consider it EMI if within 10% of expected EMI
        return abs(payment_amount - expected_emi) <= (expected_emi * 0.1)
    
    def is_prepayment(self):
        """Check if this is a prepayment (more than EMI)."""
        if not self.loan:
            return False
        
        expected_emi = self.loan.calculate_emi()
        payment_amount = float(self.amount)
        
        return payment_amount > (expected_emi * 1.1)
    
    def get_payment_type(self):
        """Get the type of payment."""
        if self.is_prepayment():
            return 'prepayment'
        elif self.is_emi_payment():
            return 'emi'
        else:
            return 'partial'
    
    def to_dict(self):
        """Convert payment object to dictionary."""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'loan_id': self.loan_id,
            'loan_number': self.loan.loan_id if self.loan else None,
            'customer_name': self.loan.customer.name if self.loan and self.loan.customer else None,
            'amount': float(self.amount),
            'principal_paid': float(self.principal_paid),
            'interest_paid': float(self.interest_paid),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'receipt_number': self.receipt_number,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'status': self.status,
            'payment_type': self.get_payment_type(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'remaining_balance': self.get_remaining_balance_after_payment()
        }
    
    @staticmethod
    def get_payment_summary_for_loan(loan_id):
        """Get payment summary for a specific loan."""
        payments = Payment.query.filter_by(loan_id=loan_id, status='completed').all()
        
        if not payments:
            return {
                'total_paid': 0,
                'principal_paid': 0,
                'interest_paid': 0,
                'payment_count': 0,
                'last_payment_date': None
            }
        
        total_paid = sum(float(p.amount) for p in payments)
        principal_paid = sum(float(p.principal_paid) for p in payments)
        interest_paid = sum(float(p.interest_paid) for p in payments)
        last_payment = max(payments, key=lambda p: p.payment_date)
        
        return {
            'total_paid': total_paid,
            'principal_paid': principal_paid,
            'interest_paid': interest_paid,
            'payment_count': len(payments),
            'last_payment_date': last_payment.payment_date.isoformat()
        }
    
    @staticmethod
    def get_payments_by_date_range(start_date, end_date):
        """Get payments within a date range."""
        return Payment.query.filter(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
            Payment.status == 'completed'
        ).order_by(Payment.payment_date.desc()).all()
    
    @staticmethod
    def get_daily_collection_summary(date):
        """Get daily collection summary for a specific date."""
        payments = Payment.query.filter(
            Payment.payment_date == date,
            Payment.status == 'completed'
        ).all()
        
        return {
            'date': date.isoformat(),
            'total_collection': sum(float(p.amount) for p in payments),
            'payment_count': len(payments),
            'payment_methods': {
                method: sum(float(p.amount) for p in payments if p.payment_method == method)
                for method in set(p.payment_method for p in payments)
            }
        }