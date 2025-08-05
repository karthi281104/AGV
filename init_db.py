#!/usr/bin/env python3
"""
Database initialization script for AGV Finance & Loans
Creates all tables and sample data for testing
"""

from app import create_app, db
from app.models.user import User
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from app.models.dashboard import DashboardMetrics, UserPreferences, AlertSettings, DashboardActivity, RealtimeData
from datetime import datetime, timedelta
from decimal import Decimal
import random

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()
        
        # Create sample users
        print("Creating sample users...")
        demo_user = User(
            auth0_id='demo_user',
            username='demo',
            email='demo@agvfinance.com',
            name='Demo User',
            role='admin',
            is_active=True
        )
        
        admin_user = User(
            auth0_id='admin_user',
            username='admin',
            email='admin@agvfinance.com',
            name='Admin User',
            role='admin',
            is_active=True
        )
        
        db.session.add(demo_user)
        db.session.add(admin_user)
        db.session.commit()
        
        # Create sample customers
        print("Creating sample customers...")
        customers_data = [
            {
                'customer_id': 'CUST001',
                'full_name': 'Rajesh Kumar',
                'phone': '9876543210',
                'email': 'rajesh@example.com',
                'address': '123 Main Street, Chennai, Tamil Nadu',
                'aadhar_number': '123456789012',
                'pan_number': 'ABCDE1234F',
                'created_by': demo_user.id
            },
            {
                'customer_id': 'CUST002',
                'full_name': 'Priya Sharma',
                'phone': '9876543211',
                'email': 'priya@example.com',
                'address': '456 Oak Avenue, Bangalore, Karnataka',
                'aadhar_number': '123456789013',
                'pan_number': 'FGHIJ5678K',
                'created_by': demo_user.id
            },
            {
                'customer_id': 'CUST003',
                'full_name': 'Amit Patel',
                'phone': '9876543212',
                'email': 'amit@example.com',
                'address': '789 Pine Road, Mumbai, Maharashtra',
                'aadhar_number': '123456789014',
                'pan_number': 'LMNOP9012Q',
                'created_by': demo_user.id
            },
            {
                'customer_id': 'CUST004',
                'full_name': 'Sunita Reddy',
                'phone': '9876543213',
                'email': 'sunita@example.com',
                'address': '321 Cedar Lane, Hyderabad, Telangana',
                'aadhar_number': '123456789015',
                'pan_number': 'RSTUV3456W',
                'created_by': demo_user.id
            },
            {
                'customer_id': 'CUST005',
                'full_name': 'Vikram Singh',
                'phone': '9876543214',
                'email': 'vikram@example.com',
                'address': '654 Elm Street, Delhi, Delhi',
                'aadhar_number': '123456789016',
                'pan_number': 'XYZAB7890C',
                'created_by': demo_user.id
            }
        ]
        
        customers = []
        for data in customers_data:
            customer = Customer(**data)
            customers.append(customer)
            db.session.add(customer)
        
        db.session.commit()
        
        # Create sample loans
        print("Creating sample loans...")
        loan_types = ['gold', 'bond']
        
        for i, customer in enumerate(customers):
            # Create 1-3 loans per customer
            num_loans = random.randint(1, 3)
            
            for j in range(num_loans):
                loan_id = f'LOAN{(i*3+j+1):03d}'
                loan_type = random.choice(loan_types)
                principal = Decimal(random.randint(50000, 500000))
                interest_rate = Decimal(random.uniform(12.0, 18.0))
                term_months = random.choice([6, 12, 18, 24, 36])
                
                # Some loans are disbursed in the past
                disbursed_date = datetime.utcnow() - timedelta(days=random.randint(0, 365))
                maturity_date = disbursed_date + timedelta(days=term_months * 30)
                
                # Calculate outstanding principal (some payments may have been made)
                outstanding = principal * Decimal(random.uniform(0.3, 1.0))
                interest_accrued = principal * (interest_rate / 100) * Decimal(term_months / 12) * Decimal(random.uniform(0.1, 0.8))
                
                # Some loans might be overdue
                status = 'active'
                if maturity_date < datetime.utcnow() and outstanding > 0:
                    status = 'active'  # Keep as active but overdue
                
                loan = Loan(
                    loan_id=loan_id,
                    customer_id=customer.id,
                    loan_type=loan_type,
                    principal_amount=principal,
                    interest_rate=interest_rate,
                    loan_term_months=term_months,
                    disbursed_amount=principal,
                    outstanding_principal=outstanding,
                    total_interest_accrued=interest_accrued,
                    status=status,
                    disbursed_date=disbursed_date,
                    maturity_date=maturity_date,
                    created_by=demo_user.id,
                    surety_name=f'Surety for {customer.full_name}',
                    surety_phone='9999999999',
                    surety_address='Surety Address'
                )
                
                db.session.add(loan)
        
        db.session.commit()
        
        # Create sample payments
        print("Creating sample payments...")
        loans = Loan.query.all()
        
        for loan in loans:
            # Create 0-5 payments per loan
            num_payments = random.randint(0, 5)
            
            for k in range(num_payments):
                payment_id = f'PAY{loan.id:03d}{k+1:02d}'
                payment_amount = Decimal(random.randint(5000, 50000))
                principal_component = payment_amount * Decimal(random.uniform(0.6, 0.9))
                interest_component = payment_amount - principal_component
                
                # Payment date between loan disbursement and now
                payment_date = loan.disbursed_date + timedelta(
                    days=random.randint(0, min(365, (datetime.utcnow() - loan.disbursed_date).days))
                )
                
                payment = Payment(
                    payment_id=payment_id,
                    loan_id=loan.id,
                    payment_amount=payment_amount,
                    principal_component=principal_component,
                    interest_component=interest_component,
                    payment_date=payment_date,
                    payment_method=random.choice(['cash', 'bank_transfer', 'cheque']),
                    receipt_number=f'RCP{payment_id}',
                    processed_by=demo_user.id
                )
                
                db.session.add(payment)
        
        db.session.commit()
        
        # Create sample dashboard activities
        print("Creating sample dashboard activities...")
        activities = [
            'customer_created', 'loan_disbursed', 'payment_received',
            'loan_approved', 'customer_updated', 'payment_processed'
        ]
        
        for i in range(20):
            activity = DashboardActivity(
                user_id=demo_user.id,
                activity_type=random.choice(activities),
                activity_description=f'Sample activity {i+1} - {random.choice(activities).replace("_", " ").title()}',
                related_entity_type=random.choice(['customer', 'loan', 'payment']),
                related_entity_id=random.randint(1, 10),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 168))  # Last week
            )
            db.session.add(activity)
        
        db.session.commit()
        
        # Create sample alert settings
        print("Creating sample alert settings...")
        alert_types = ['overdue_payment', 'new_loan_application', 'large_payment', 'portfolio_milestone']
        
        for alert_type in alert_types:
            alert_setting = AlertSettings(
                user_id=demo_user.id,
                alert_type=alert_type,
                is_enabled=True,
                threshold_value=Decimal(100000) if 'payment' in alert_type else None,
                notification_method='dashboard'
            )
            db.session.add(alert_setting)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print(f"Created {len(customers)} customers")
        print(f"Created {Loan.query.count()} loans")
        print(f"Created {Payment.query.count()} payments")
        print(f"Created {DashboardActivity.query.count()} activities")
        print(f"Demo login: username='demo', password='demo123'")

if __name__ == '__main__':
    init_database()