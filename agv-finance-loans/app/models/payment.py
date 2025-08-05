"""
Payment Model for AGV Finance and Loans
Tracks all payment transactions with principal/interest breakdown
"""

from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from app import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Related Records
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Payment Details
    payment_amount = db.Column(Numeric(15, 2), nullable=False)
    principal_amount = db.Column(Numeric(15, 2), nullable=False, default=0)
    interest_amount = db.Column(Numeric(15, 2), nullable=False, default=0)
    penalty_amount = db.Column(Numeric(15, 2), default=0)
    processing_fee = db.Column(Numeric(10, 2), default=0)
    
    # Payment Information
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    payment_type = db.Column(db.String(20), nullable=False)  # EMI, Prepayment, Penalty, Closure
    payment_method = db.Column(db.String(30), nullable=False)  # Cash, Cheque, Bank Transfer, UPI, Card
    
    # Transaction Details
    transaction_reference = db.Column(db.String(100))  # Bank transaction ID, cheque number, etc.
    bank_name = db.Column(db.String(100))
    cheque_number = db.Column(db.String(50))
    cheque_date = db.Column(db.Date)
    upi_transaction_id = db.Column(db.String(100))
    
    # Payment Status
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed, cancelled, bounced
    payment_gateway_response = db.Column(db.Text)  # JSON response from payment gateway
    failure_reason = db.Column(db.Text)
    
    # EMI Information
    emi_number = db.Column(db.Integer)  # Which EMI number this payment is for
    due_date = db.Column(db.Date)  # Original due date for this EMI
    late_fee = db.Column(Numeric(10, 2), default=0)
    days_late = db.Column(db.Integer, default=0)
    
    # Advance Payment Information
    advance_amount = db.Column(Numeric(15, 2), default=0)  # Amount paid in advance
    advance_adjusted = db.Column(db.Boolean, default=False)  # Whether advance has been adjusted
    
    # Receipt Information
    receipt_number = db.Column(db.String(50), unique=True)
    receipt_generated = db.Column(db.Boolean, default=False)
    receipt_sent = db.Column(db.Boolean, default=False)
    receipt_email_sent = db.Column(db.Boolean, default=False)
    
    # Processing Information
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    processed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verification_status = db.Column(db.String(20), default='verified')  # pending, verified, disputed
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    # Additional Information
    remarks = db.Column(db.Text)
    internal_notes = db.Column(db.Text)  # Internal notes not visible to customer
    
    # Reversal Information
    is_reversed = db.Column(db.Boolean, default=False)
    reversed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reversed_at = db.Column(db.DateTime)
    reversal_reason = db.Column(db.Text)
    reversal_payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'))  # Links to reversal payment
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verified_by_user = db.relationship('User', foreign_keys=[verified_by])
    reversed_by_user = db.relationship('User', foreign_keys=[reversed_by])
    reversal_payment = db.relationship('Payment', remote_side=[id])
    
    def __repr__(self):
        return f'<Payment {self.payment_id}>'
    
    def calculate_breakdown(self, loan):
        """Calculate principal and interest breakdown for this payment"""
        if not loan:
            return
        
        # Get current outstanding balance
        remaining_balance = loan.outstanding_balance
        monthly_interest_rate = float(loan.interest_rate) / 100 / 12
        
        # Calculate interest on outstanding balance
        interest_due = remaining_balance * Decimal(str(monthly_interest_rate))
        
        # Payment breakdown
        payment_for_interest = min(self.payment_amount, interest_due)
        payment_for_principal = max(Decimal('0'), self.payment_amount - payment_for_interest)
        
        self.interest_amount = payment_for_interest
        self.principal_amount = payment_for_principal
    
    def apply_to_loan(self):
        """Apply this payment to the associated loan"""
        if self.status != 'completed' or self.is_reversed:
            return
        
        loan = self.loan
        if not loan:
            return
        
        # Update loan balances
        loan.outstanding_balance = max(Decimal('0'), loan.outstanding_balance - self.principal_amount)
        loan.principal_paid += self.principal_amount
        loan.interest_paid += self.interest_amount
        loan.last_payment_date = self.payment_date
        
        # Update EMI count if this is an EMI payment
        if self.payment_type == 'EMI' and self.emi_number:
            loan.paid_emis = max(loan.paid_emis, self.emi_number)
            
            # Calculate next EMI date
            if loan.paid_emis < loan.total_emis:
                from dateutil.relativedelta import relativedelta
                loan.next_emi_date = loan.first_emi_date + relativedelta(months=loan.paid_emis)
            else:
                loan.next_emi_date = None
                loan.status = 'closed'
        
        # Check if loan is fully paid
        if loan.outstanding_balance <= Decimal('0.01'):  # Allow for rounding differences
            loan.status = 'closed'
            loan.next_emi_date = None
        
        db.session.commit()
    
    def generate_receipt_number(self):
        """Generate a unique receipt number"""
        prefix = "RCP"
        year = datetime.now().year
        month = datetime.now().month
        
        # Count payments in this month
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)
        
        count = Payment.query.filter(
            Payment.created_at >= month_start,
            Payment.created_at < month_end
        ).count() + 1
        
        return f"{prefix}{year}{month:02d}{count:06d}"
    
    def reverse_payment(self, reversed_by_user_id, reason):
        """Reverse this payment"""
        if self.is_reversed:
            raise ValueError("Payment is already reversed")
        
        if self.status != 'completed':
            raise ValueError("Only completed payments can be reversed")
        
        # Create reversal payment
        reversal = Payment(
            payment_id=f"REV_{self.payment_id}",
            loan_id=self.loan_id,
            customer_id=self.customer_id,
            payment_amount=-self.payment_amount,
            principal_amount=-self.principal_amount,
            interest_amount=-self.interest_amount,
            penalty_amount=-self.penalty_amount,
            payment_type='Reversal',
            payment_method=self.payment_method,
            status='completed',
            processed_by=reversed_by_user_id,
            remarks=f"Reversal of payment {self.payment_id}: {reason}"
        )
        
        # Mark original payment as reversed
        self.is_reversed = True
        self.reversed_by = reversed_by_user_id
        self.reversed_at = datetime.utcnow()
        self.reversal_reason = reason
        self.reversal_payment_id = reversal.id
        
        # Update loan balances
        loan = self.loan
        loan.outstanding_balance += self.principal_amount
        loan.principal_paid -= self.principal_amount
        loan.interest_paid -= self.interest_amount
        
        # Adjust EMI count if necessary
        if self.payment_type == 'EMI' and self.emi_number:
            loan.paid_emis = max(0, loan.paid_emis - 1)
            # Recalculate next EMI date
            if loan.paid_emis < loan.total_emis:
                from dateutil.relativedelta import relativedelta
                loan.next_emi_date = loan.first_emi_date + relativedelta(months=loan.paid_emis)
            
            # Reopen loan if it was closed
            if loan.status == 'closed':
                loan.status = 'active'
        
        db.session.add(reversal)
        db.session.commit()
        
        return reversal
    
    def is_late_payment(self):
        """Check if this payment was made after the due date"""
        if self.due_date and self.payment_date:
            return self.payment_date > self.due_date
        return False
    
    def calculate_late_days(self):
        """Calculate number of days late"""
        if self.is_late_payment():
            return (self.payment_date - self.due_date).days
        return 0
    
    def to_dict(self):
        """Convert payment to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'loan_id': self.loan_id,
            'customer_id': self.customer_id,
            'payment_amount': float(self.payment_amount),
            'principal_amount': float(self.principal_amount),
            'interest_amount': float(self.interest_amount),
            'penalty_amount': float(self.penalty_amount),
            'payment_date': self.payment_date.isoformat(),
            'payment_type': self.payment_type,
            'payment_method': self.payment_method,
            'status': self.status,
            'emi_number': self.emi_number,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'late_fee': float(self.late_fee),
            'days_late': self.days_late,
            'receipt_number': self.receipt_number,
            'receipt_generated': self.receipt_generated,
            'transaction_reference': self.transaction_reference,
            'is_reversed': self.is_reversed,
            'verification_status': self.verification_status,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def generate_payment_id():
        """Generate a unique payment ID"""
        prefix = "PAY"
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day
        
        # Count payments today
        today_start = datetime(year, month, day)
        today_end = datetime(year, month, day, 23, 59, 59)
        
        count = Payment.query.filter(
            Payment.created_at >= today_start,
            Payment.created_at <= today_end
        ).count() + 1
        
        return f"{prefix}{year}{month:02d}{day:02d}{count:05d}"