"""
Customer Model for AGV Finance and Loans
Stores customer personal details, biometric data, and documents
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from app import db

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # Male, Female, Other
    marital_status = db.Column(db.String(20))  # Single, Married, Divorced, Widowed
    
    # Contact Information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    
    # Address Information
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False, default='India')
    
    # Identification Documents
    id_type = db.Column(db.String(50), nullable=False)  # Aadhaar, PAN, Passport, etc.
    id_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    id_document_path = db.Column(db.String(500))
    
    # Employment Information
    employment_status = db.Column(db.String(50))  # Employed, Self-Employed, Unemployed, Retired
    employer_name = db.Column(db.String(200))
    job_title = db.Column(db.String(100))
    monthly_income = db.Column(Numeric(15, 2))
    employment_duration_years = db.Column(db.Integer)
    
    # Financial Information
    bank_name = db.Column(db.String(100))
    bank_account_number = db.Column(db.String(50))
    bank_ifsc = db.Column(db.String(20))
    credit_score = db.Column(db.Integer)
    existing_loans_count = db.Column(db.Integer, default=0)
    existing_loans_emi = db.Column(Numeric(15, 2), default=0)
    
    # Biometric Data
    fingerprint_data = db.Column(db.Text)  # Encrypted fingerprint template
    face_recognition_data = db.Column(db.Text)  # Encrypted face template
    biometric_enrolled = db.Column(db.Boolean, default=False)
    biometric_enrollment_date = db.Column(db.DateTime)
    
    # Documents and Verification
    documents_uploaded = db.Column(db.Text)  # JSON list of uploaded document paths
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    verification_notes = db.Column(db.Text)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    # Customer Status
    status = db.Column(db.String(20), default='active')  # active, inactive, blacklisted
    risk_category = db.Column(db.String(20), default='medium')  # low, medium, high
    kyc_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    loans = db.relationship('Loan', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='customer', lazy='dynamic')
    verified_by_user = db.relationship('User', foreign_keys=[verified_by])
    
    def __repr__(self):
        return f'<Customer {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """Get customer's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate customer's age"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = [self.address_line1]
        if self.address_line2:
            address_parts.append(self.address_line2)
        address_parts.extend([self.city, self.state, self.postal_code, self.country])
        return ", ".join(address_parts)
    
    def can_apply_for_loan(self):
        """Check if customer is eligible to apply for a loan"""
        return (
            self.status == 'active' and
            self.verification_status == 'verified' and
            self.kyc_status == 'completed' and
            self.risk_category != 'high'
        )
    
    def get_active_loans(self):
        """Get customer's active loans"""
        return self.loans.filter_by(status='active').all()
    
    def get_total_outstanding_amount(self):
        """Calculate total outstanding loan amount"""
        active_loans = self.get_active_loans()
        return sum(loan.outstanding_balance for loan in active_loans)
    
    def get_monthly_emi_total(self):
        """Calculate total monthly EMI for all active loans"""
        active_loans = self.get_active_loans()
        return sum(loan.emi_amount for loan in active_loans)
    
    def to_dict(self):
        """Convert customer to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone_primary': self.phone_primary,
            'age': self.age,
            'gender': self.gender,
            'marital_status': self.marital_status,
            'employment_status': self.employment_status,
            'monthly_income': float(self.monthly_income) if self.monthly_income else None,
            'credit_score': self.credit_score,
            'verification_status': self.verification_status,
            'kyc_status': self.kyc_status,
            'status': self.status,
            'risk_category': self.risk_category,
            'biometric_enrolled': self.biometric_enrolled,
            'total_loans': self.loans.count(),
            'active_loans': len(self.get_active_loans()),
            'total_outstanding': float(self.get_total_outstanding_amount()),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }