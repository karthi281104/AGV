from app import db
from datetime import datetime
import uuid

class Customer(db.Model):
    """Customer model for storing customer information and biometric data."""
    
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=False)
    aadhar_number = db.Column(db.String(12), nullable=False, unique=True)
    pan_number = db.Column(db.String(10), nullable=True)
    biometric_data = db.Column(db.Text, nullable=True)  # JSON string for biometric data
    photo_path = db.Column(db.String(500), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    annual_income = db.Column(db.Decimal(15, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    loans = db.relationship('Loan', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Customer, self).__init__(**kwargs)
        if not self.customer_id:
            self.customer_id = self.generate_customer_id()
    
    def __repr__(self):
        return f'<Customer {self.customer_id}: {self.name}>'
    
    @staticmethod
    def generate_customer_id():
        """Generate a unique customer ID."""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f'CUS{timestamp}{unique_suffix}'
    
    def get_total_loan_amount(self):
        """Get total loan amount for this customer."""
        return sum(loan.principal_amount for loan in self.loans if loan.status in ['approved', 'disbursed'])
    
    def get_outstanding_amount(self):
        """Get total outstanding amount for this customer."""
        return sum(loan.get_outstanding_balance() for loan in self.loans if loan.status == 'disbursed')
    
    def has_active_loans(self):
        """Check if customer has any active loans."""
        return self.loans.filter_by(status='disbursed').count() > 0
    
    def get_loan_history(self):
        """Get loan history for this customer."""
        return self.loans.order_by(db.desc('created_at')).all()
    
    def to_dict(self):
        """Convert customer object to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'aadhar_number': self.aadhar_number,
            'pan_number': self.pan_number,
            'photo_path': self.photo_path,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'occupation': self.occupation,
            'annual_income': float(self.annual_income) if self.annual_income else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_loan_amount': self.get_total_loan_amount(),
            'outstanding_amount': self.get_outstanding_amount(),
            'has_active_loans': self.has_active_loans()
        }
    
    def search_customers(query):
        """Search customers by name, phone, or customer ID."""
        return Customer.query.filter(
            db.or_(
                Customer.name.contains(query),
                Customer.phone.contains(query),
                Customer.customer_id.contains(query),
                Customer.email.contains(query) if query else False
            )
        ).all()