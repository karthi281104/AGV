from app import db
from datetime import datetime, timedelta
import uuid
import json

class Loan(db.Model):
    """Loan model for managing loan information and calculations."""
    
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    principal_amount = db.Column(db.Decimal(15, 2), nullable=False)
    interest_rate = db.Column(db.Decimal(5, 2), nullable=False)  # Annual interest rate
    term_months = db.Column(db.Integer, nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)  # personal, gold, vehicle, home
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, disbursed, closed, defaulted
    disbursed_date = db.Column(db.Date, nullable=True)
    maturity_date = db.Column(db.Date, nullable=True)
    emi_amount = db.Column(db.Decimal(15, 2), nullable=True)
    
    # Surety information
    surety_name = db.Column(db.String(255), nullable=True)
    surety_phone = db.Column(db.String(15), nullable=True)
    surety_address = db.Column(db.Text, nullable=True)
    
    # Document paths (JSON string)
    document_paths = db.Column(db.Text, nullable=True)
    
    # Loan specific details
    collateral_details = db.Column(db.Text, nullable=True)  # For secured loans
    purpose = db.Column(db.String(255), nullable=True)
    
    # Tracking
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    disbursed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='loan', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Loan, self).__init__(**kwargs)
        if not self.loan_id:
            self.loan_id = self.generate_loan_id()
        if self.disbursed_date and not self.maturity_date:
            self.maturity_date = self.disbursed_date + timedelta(days=30 * self.term_months)
    
    def __repr__(self):
        return f'<Loan {self.loan_id}: {self.principal_amount}>'
    
    @staticmethod
    def generate_loan_id():
        """Generate a unique loan ID."""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f'LN{timestamp}{unique_suffix}'
    
    def calculate_emi(self):
        """Calculate EMI using reducing balance method."""
        if self.term_months == 0:
            return 0
        
        principal = float(self.principal_amount)
        rate = float(self.interest_rate) / 100 / 12  # Monthly interest rate
        months = self.term_months
        
        if rate == 0:
            return principal / months
        
        emi = principal * (rate * (1 + rate) ** months) / ((1 + rate) ** months - 1)
        return round(emi, 2)
    
    def get_total_interest(self):
        """Calculate total interest to be paid."""
        emi = self.calculate_emi()
        return round((emi * self.term_months) - float(self.principal_amount), 2)
    
    def get_total_amount(self):
        """Get total amount to be paid (principal + interest)."""
        return float(self.principal_amount) + self.get_total_interest()
    
    def get_paid_amount(self):
        """Get total amount paid so far."""
        return sum(float(payment.amount) for payment in self.payments)
    
    def get_outstanding_balance(self):
        """Get outstanding balance."""
        return self.get_total_amount() - self.get_paid_amount()
    
    def get_principal_paid(self):
        """Get total principal paid."""
        return sum(float(payment.principal_paid) for payment in self.payments)
    
    def get_interest_paid(self):
        """Get total interest paid."""
        return sum(float(payment.interest_paid) for payment in self.payments)
    
    def get_outstanding_principal(self):
        """Get outstanding principal amount."""
        return float(self.principal_amount) - self.get_principal_paid()
    
    def get_overdue_amount(self):
        """Calculate overdue amount based on EMI schedule."""
        if not self.disbursed_date or self.status != 'disbursed':
            return 0
        
        months_elapsed = (datetime.now().date() - self.disbursed_date).days // 30
        expected_payment = self.calculate_emi() * months_elapsed
        paid_amount = self.get_paid_amount()
        
        return max(0, expected_payment - paid_amount)
    
    def is_overdue(self):
        """Check if loan is overdue."""
        return self.get_overdue_amount() > 0
    
    def get_next_emi_date(self):
        """Get next EMI due date."""
        if not self.disbursed_date:
            return None
        
        payments_made = self.payments.count()
        next_emi_date = self.disbursed_date + timedelta(days=30 * (payments_made + 1))
        
        return next_emi_date if next_emi_date <= self.maturity_date else None
    
    def get_documents(self):
        """Get list of document paths."""
        if not self.document_paths:
            return []
        try:
            return json.loads(self.document_paths)
        except:
            return []
    
    def set_documents(self, document_list):
        """Set document paths as JSON string."""
        self.document_paths = json.dumps(document_list)
    
    def to_dict(self):
        """Convert loan object to dictionary."""
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'principal_amount': float(self.principal_amount),
            'interest_rate': float(self.interest_rate),
            'term_months': self.term_months,
            'loan_type': self.loan_type,
            'status': self.status,
            'disbursed_date': self.disbursed_date.isoformat() if self.disbursed_date else None,
            'maturity_date': self.maturity_date.isoformat() if self.maturity_date else None,
            'emi_amount': float(self.emi_amount) if self.emi_amount else self.calculate_emi(),
            'surety_name': self.surety_name,
            'surety_phone': self.surety_phone,
            'purpose': self.purpose,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_amount': self.get_total_amount(),
            'paid_amount': self.get_paid_amount(),
            'outstanding_balance': self.get_outstanding_balance(),
            'outstanding_principal': self.get_outstanding_principal(),
            'overdue_amount': self.get_overdue_amount(),
            'is_overdue': self.is_overdue(),
            'next_emi_date': self.get_next_emi_date().isoformat() if self.get_next_emi_date() else None,
            'documents': self.get_documents()
        }