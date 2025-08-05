"""
Loan Model for AGV Finance and Loans
Handles loan management with principal, interest, terms, and documentation
"""

from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from app import db
import math

class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Customer Information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Loan Details
    loan_type = db.Column(db.String(50), nullable=False)  # Personal, Home, Vehicle, Business, etc.
    principal_amount = db.Column(Numeric(15, 2), nullable=False)
    interest_rate = db.Column(Numeric(5, 2), nullable=False)  # Annual interest rate percentage
    loan_term_months = db.Column(db.Integer, nullable=False)
    
    # Calculated Fields
    emi_amount = db.Column(Numeric(15, 2), nullable=False)
    total_amount = db.Column(Numeric(15, 2), nullable=False)
    total_interest = db.Column(Numeric(15, 2), nullable=False)
    
    # Loan Status and Dates
    status = db.Column(db.String(20), default='pending')  # pending, approved, disbursed, active, closed, defaulted
    application_date = db.Column(db.Date, nullable=False, default=date.today)
    approval_date = db.Column(db.Date)
    disbursement_date = db.Column(db.Date)
    first_emi_date = db.Column(db.Date)
    maturity_date = db.Column(db.Date)
    
    # Financial Tracking
    disbursed_amount = db.Column(Numeric(15, 2), default=0)
    outstanding_balance = db.Column(Numeric(15, 2), default=0)
    principal_paid = db.Column(Numeric(15, 2), default=0)
    interest_paid = db.Column(Numeric(15, 2), default=0)
    penalty_amount = db.Column(Numeric(15, 2), default=0)
    
    # EMI Tracking
    total_emis = db.Column(db.Integer, default=0)
    paid_emis = db.Column(db.Integer, default=0)
    overdue_emis = db.Column(db.Integer, default=0)
    next_emi_date = db.Column(db.Date)
    last_payment_date = db.Column(db.Date)
    
    # Surety and Guarantor Information
    surety_type = db.Column(db.String(50))  # personal, property, gold, fd, etc.
    surety_value = db.Column(Numeric(15, 2))
    guarantor_name = db.Column(db.String(200))
    guarantor_phone = db.Column(db.String(20))
    guarantor_relationship = db.Column(db.String(50))
    guarantor_income = db.Column(Numeric(15, 2))
    
    # Documents and Verification
    documents_required = db.Column(db.Text)  # JSON list of required documents
    documents_uploaded = db.Column(db.Text)  # JSON list of uploaded document paths
    documents_verified = db.Column(db.Boolean, default=False)
    
    # Approval Information
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    
    # Risk Assessment
    risk_score = db.Column(db.Integer)
    ltv_ratio = db.Column(Numeric(5, 2))  # Loan to Value ratio
    debt_to_income_ratio = db.Column(Numeric(5, 2))
    
    # Processing Information
    processing_fee = db.Column(Numeric(10, 2), default=0)
    insurance_amount = db.Column(Numeric(10, 2), default=0)
    other_charges = db.Column(Numeric(10, 2), default=0)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='loan', lazy='dynamic', cascade='all, delete-orphan')
    approved_by_user = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<Loan {self.loan_number}>'
    
    def calculate_emi(self):
        """Calculate EMI using the formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)"""
        if self.principal_amount and self.interest_rate and self.loan_term_months:
            principal = float(self.principal_amount)
            rate = float(self.interest_rate) / 100 / 12  # Monthly interest rate
            months = self.loan_term_months
            
            if rate == 0:  # No interest case
                return Decimal(str(principal / months))
            
            emi = principal * rate * (1 + rate) ** months / ((1 + rate) ** months - 1)
            return Decimal(str(round(emi, 2)))
        return Decimal('0')
    
    def calculate_total_amount(self):
        """Calculate total amount to be paid"""
        if self.emi_amount and self.loan_term_months:
            return self.emi_amount * self.loan_term_months
        return Decimal('0')
    
    def calculate_total_interest(self):
        """Calculate total interest to be paid"""
        total = self.calculate_total_amount()
        if total and self.principal_amount:
            return total - self.principal_amount
        return Decimal('0')
    
    def update_calculations(self):
        """Update all calculated fields"""
        self.emi_amount = self.calculate_emi()
        self.total_amount = self.calculate_total_amount()
        self.total_interest = self.calculate_total_interest()
        self.total_emis = self.loan_term_months
        self.outstanding_balance = self.principal_amount
    
    def get_current_emi_number(self):
        """Get the current EMI number based on disbursement date"""
        if not self.disbursement_date or not self.first_emi_date:
            return 0
        
        today = date.today()
        if today < self.first_emi_date:
            return 0
        
        months_passed = (today.year - self.first_emi_date.year) * 12 + \
                       (today.month - self.first_emi_date.month)
        return min(months_passed + 1, self.total_emis)
    
    def get_overdue_amount(self):
        """Calculate overdue amount"""
        current_emi = self.get_current_emi_number()
        expected_paid_emis = max(0, current_emi - 1)
        overdue_emis = max(0, expected_paid_emis - self.paid_emis)
        return overdue_emis * self.emi_amount
    
    def is_overdue(self):
        """Check if loan has overdue payments"""
        return self.get_overdue_amount() > 0
    
    def get_remaining_balance(self):
        """Get remaining principal balance"""
        return max(Decimal('0'), self.outstanding_balance)
    
    def get_completion_percentage(self):
        """Get loan completion percentage"""
        if self.total_amount and self.total_amount > 0:
            paid_amount = self.principal_paid + self.interest_paid
            return min(100, (float(paid_amount) / float(self.total_amount)) * 100)
        return 0
    
    def approve_loan(self, approved_by_user_id, notes=None):
        """Approve the loan"""
        self.status = 'approved'
        self.approval_date = date.today()
        self.approved_by = approved_by_user_id
        self.approval_notes = notes
        
    def disburse_loan(self, disbursement_amount=None):
        """Disburse the loan"""
        if self.status != 'approved':
            raise ValueError("Loan must be approved before disbursement")
        
        amount = disbursement_amount or self.principal_amount
        self.disbursed_amount = amount
        self.outstanding_balance = amount
        self.status = 'active'
        self.disbursement_date = date.today()
        
        # Calculate first EMI date (usually 30 days after disbursement)
        from datetime import timedelta
        self.first_emi_date = self.disbursement_date + timedelta(days=30)
        
        # Calculate maturity date
        months = self.loan_term_months
        maturity_year = self.first_emi_date.year + (self.first_emi_date.month + months - 1) // 12
        maturity_month = (self.first_emi_date.month + months - 1) % 12 + 1
        self.maturity_date = date(maturity_year, maturity_month, self.first_emi_date.day)
        
        self.next_emi_date = self.first_emi_date
    
    def to_dict(self):
        """Convert loan to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'loan_number': self.loan_number,
            'customer_id': self.customer_id,
            'loan_type': self.loan_type,
            'principal_amount': float(self.principal_amount),
            'interest_rate': float(self.interest_rate),
            'loan_term_months': self.loan_term_months,
            'emi_amount': float(self.emi_amount),
            'total_amount': float(self.total_amount),
            'total_interest': float(self.total_interest),
            'status': self.status,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'disbursement_date': self.disbursement_date.isoformat() if self.disbursement_date else None,
            'outstanding_balance': float(self.outstanding_balance),
            'principal_paid': float(self.principal_paid),
            'interest_paid': float(self.interest_paid),
            'paid_emis': self.paid_emis,
            'total_emis': self.total_emis,
            'overdue_emis': self.overdue_emis,
            'next_emi_date': self.next_emi_date.isoformat() if self.next_emi_date else None,
            'completion_percentage': self.get_completion_percentage(),
            'is_overdue': self.is_overdue(),
            'overdue_amount': float(self.get_overdue_amount()),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def generate_loan_number():
        """Generate a unique loan number"""
        from datetime import datetime
        prefix = "AGV"
        year = datetime.now().year
        
        # Count loans created this year
        year_start = datetime(year, 1, 1)
        count = Loan.query.filter(Loan.created_at >= year_start).count() + 1
        
        return f"{prefix}{year}{count:06d}"