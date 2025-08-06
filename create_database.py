#!/usr/bin/env python3
"""
Database initialization script for AGV Finance & Loans
Creates all required tables and initial data
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models.auth import User, UserSession, WebAuthnCredential
from app.models.core import Customer, Loan, Payment, Document

def create_database():
    """Create all database tables and initial data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables (for fresh start)
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # Create demo users
            print("Creating demo users...")
            
            # Admin user
            admin_user = User(
                id='admin_001',
                auth0_id='auth0|admin001',
                username='admin',
                email='admin@agvfinance.com',
                name='Administrator',
                role='admin',
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Demo employee
            demo_user = User(
                id='demo_001',
                auth0_id='auth0|demo001',
                username='demo',
                email='demo@agvfinance.com',
                name='Demo Employee',
                role='employee',
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Manager user
            manager_user = User(
                id='manager_001',
                auth0_id='auth0|manager001',
                username='manager',
                email='manager@agvfinance.com',
                name='Branch Manager',
                role='manager',
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add_all([admin_user, demo_user, manager_user])
            
            # Create sample customers
            print("Creating sample customers...")
            
            customers = [
                Customer(
                    id='CUST001',
                    name='Rajesh Kumar',
                    email='rajesh.kumar@email.com',
                    phone='+91-9876543210',
                    address='123 MG Road, Bangalore, Karnataka 560001',
                    identity_type='aadhaar',
                    identity_number='1234-5678-9012',
                    created_by='demo_001',
                    created_at=datetime.utcnow()
                ),
                Customer(
                    id='CUST002',
                    name='Priya Sharma',
                    email='priya.sharma@email.com',
                    phone='+91-9876543211',
                    address='456 Brigade Road, Bangalore, Karnataka 560025',
                    identity_type='aadhaar',
                    identity_number='2345-6789-0123',
                    created_by='demo_001',
                    created_at=datetime.utcnow()
                ),
                Customer(
                    id='CUST003',
                    name='Amit Patel',
                    email='amit.patel@email.com',
                    phone='+91-9876543212',
                    address='789 Commercial Street, Bangalore, Karnataka 560001',
                    identity_type='passport',
                    identity_number='A1234567',
                    created_by='demo_001',
                    created_at=datetime.utcnow()
                )
            ]
            
            db.session.add_all(customers)
            
            # Create sample loans
            print("Creating sample loans...")
            
            loans = [
                Loan(
                    id='LOAN001',
                    customer_id='CUST001',
                    principal_amount=500000.00,
                    interest_rate=12.0,
                    tenure_months=24,
                    status='active',
                    collateral_type='gold',
                    collateral_description='22K Gold Ornaments - 50g',
                    disbursed_amount=500000.00,
                    outstanding_principal=450000.00,
                    total_interest_accrued=54000.00,
                    created_by='demo_001',
                    disbursed_at=datetime.utcnow(),
                    created_at=datetime.utcnow()
                ),
                Loan(
                    id='LOAN002',
                    customer_id='CUST002',
                    principal_amount=300000.00,
                    interest_rate=10.5,
                    tenure_months=18,
                    status='active',
                    collateral_type='bonds',
                    collateral_description='Government Bonds - ₹400,000 face value',
                    disbursed_amount=300000.00,
                    outstanding_principal=200000.00,
                    total_interest_accrued=28500.00,
                    created_by='demo_001',
                    disbursed_at=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
            ]
            
            db.session.add_all(loans)
            
            # Create sample payments
            print("Creating sample payments...")
            
            payments = [
                Payment(
                    id='PAY001',
                    loan_id='LOAN001',
                    amount=25000.00,
                    principal_amount=20000.00,
                    interest_amount=5000.00,
                    payment_date=datetime.utcnow(),
                    payment_method='cash',
                    reference_number='CASH001',
                    created_by='demo_001',
                    created_at=datetime.utcnow()
                ),
                Payment(
                    id='PAY002',
                    loan_id='LOAN001',
                    amount=25000.00,
                    principal_amount=20000.00,
                    interest_amount=5000.00,
                    payment_date=datetime.utcnow(),
                    payment_method='bank_transfer',
                    reference_number='TXN123456',
                    created_by='demo_001',
                    created_at=datetime.utcnow()
                )
            ]
            
            db.session.add_all(payments)
            
            # Commit all changes
            db.session.commit()
            
            print("\n✅ Database created successfully!")
            print(f"📊 Created {len([admin_user, demo_user, manager_user])} users")
            print(f"👥 Created {len(customers)} customers")
            print(f"💰 Created {len(loans)} loans")
            print(f"💳 Created {len(payments)} payments")
            
            # Print demo credentials
            print("\n🔐 Demo Login Credentials:")
            print("Admin: admin@agvfinance.com / admin123")
            print("Demo: demo@agvfinance.com / demo123")
            print("Manager: manager@agvfinance.com / manager123")
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_database()