"""
Dashboard utility functions for AGV Finance
Provides helper functions for dashboard calculations and data processing
"""

from app import db
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from decimal import Decimal
import calendar


class DashboardCalculator:
    """Helper class for dashboard calculations"""

    @staticmethod
    def get_date_ranges():
        """Get current and previous month date ranges"""
        current_date = datetime.utcnow()
        current_month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Previous month range
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        
        return {
            'current_month_start': current_month_start,
            'previous_month_start': previous_month_start,
            'previous_month_end': previous_month_end,
            'current_date': current_date
        }

    @staticmethod
    def calculate_portfolio_metrics():
        """Calculate portfolio-level metrics"""
        try:
            # Basic counts
            total_customers = Customer.query.filter_by(is_active=True).count()
            active_loans = Loan.query.filter_by(status='active').count()
            
            # Financial aggregations
            disbursed_amount = db.session.query(
                func.coalesce(func.sum(Loan.disbursed_amount), 0)
            ).filter_by(status='active').scalar()
            
            outstanding_principal = db.session.query(
                func.coalesce(func.sum(Loan.outstanding_principal), 0)
            ).filter_by(status='active').scalar()
            
            total_interest = db.session.query(
                func.coalesce(func.sum(Loan.total_interest_accrued), 0)
            ).filter_by(status='active').scalar()
            
            return {
                'total_customers': total_customers,
                'active_loans': active_loans,
                'total_disbursed': float(disbursed_amount),
                'total_outstanding': float(outstanding_principal),
                'total_interest': float(total_interest)
            }
        except Exception as e:
            print(f"Error calculating portfolio metrics: {e}")
            return {
                'total_customers': 0,
                'active_loans': 0,
                'total_disbursed': 0.0,
                'total_outstanding': 0.0,
                'total_interest': 0.0
            }

    @staticmethod
    def calculate_overdue_metrics():
        """Calculate overdue loan metrics"""
        try:
            current_date = datetime.utcnow()
            
            overdue_loans = Loan.query.filter(
                and_(
                    Loan.status == 'active',
                    Loan.maturity_date < current_date,
                    Loan.outstanding_principal > 0
                )
            ).all()
            
            overdue_count = len(overdue_loans)
            overdue_amount = sum(float(loan.outstanding_principal) for loan in overdue_loans)
            
            return {
                'overdue_count': overdue_count,
                'overdue_amount': overdue_amount,
                'overdue_loans': overdue_loans
            }
        except Exception as e:
            print(f"Error calculating overdue metrics: {e}")
            return {
                'overdue_count': 0,
                'overdue_amount': 0.0,
                'overdue_loans': []
            }

    @staticmethod
    def calculate_monthly_metrics():
        """Calculate current month performance metrics"""
        try:
            date_ranges = DashboardCalculator.get_date_ranges()
            current_month_start = date_ranges['current_month_start']
            
            # Monthly collections
            monthly_collections = 0
            try:
                monthly_collections = db.session.query(
                    func.coalesce(func.sum(Payment.payment_amount), 0)
                ).filter(
                    Payment.payment_date >= current_month_start
                ).scalar()
            except Exception:
                # If Payment table doesn't exist or has issues, set to 0
                monthly_collections = 0
            
            # New customers this month
            new_customers = Customer.query.filter(
                Customer.created_at >= current_month_start
            ).count()
            
            # Loans disbursed this month
            loans_disbursed = Loan.query.filter(
                Loan.disbursed_date >= current_month_start
            ).count()
            
            return {
                'monthly_collections': float(monthly_collections),
                'new_customers_month': new_customers,
                'loans_disbursed_month': loans_disbursed
            }
        except Exception as e:
            print(f"Error calculating monthly metrics: {e}")
            return {
                'monthly_collections': 0.0,
                'new_customers_month': 0,
                'loans_disbursed_month': 0
            }

    @staticmethod
    def get_recent_activities(limit=10):
        """Get recent activities for dashboard display"""
        try:
            # Recent loans with customer info
            recent_loans = db.session.query(Loan, Customer).join(
                Customer, Loan.customer_id == Customer.id
            ).order_by(Loan.created_at.desc()).limit(limit).all()
            
            # Recent customers
            recent_customers = Customer.query.order_by(
                Customer.created_at.desc()
            ).limit(limit).all()
            
            return {
                'recent_loans': recent_loans,
                'recent_customers': recent_customers
            }
        except Exception as e:
            print(f"Error getting recent activities: {e}")
            return {
                'recent_loans': [],
                'recent_customers': []
            }

    @staticmethod
    def calculate_growth_percentage(current, previous):
        """Calculate growth percentage between two values"""
        if not previous or previous == 0:
            return 0 if current == 0 else 100
        return round(((current - previous) / previous) * 100, 1)

    @staticmethod
    def calculate_loan_portfolio_health():
        """Calculate loan portfolio health indicators"""
        try:
            total_loans = Loan.query.filter_by(status='active').count()
            if total_loans == 0:
                return {
                    'healthy_loans_percentage': 100,
                    'at_risk_loans_percentage': 0,
                    'default_risk_score': 0
                }
            
            # Get overdue metrics
            overdue_metrics = DashboardCalculator.calculate_overdue_metrics()
            overdue_count = overdue_metrics['overdue_count']
            
            # Calculate percentages
            healthy_percentage = ((total_loans - overdue_count) / total_loans) * 100
            at_risk_percentage = (overdue_count / total_loans) * 100
            
            # Simple risk score (0-100, where 0 is best)
            risk_score = min(at_risk_percentage * 2, 100)
            
            return {
                'healthy_loans_percentage': round(healthy_percentage, 1),
                'at_risk_loans_percentage': round(at_risk_percentage, 1),
                'default_risk_score': round(risk_score, 1)
            }
        except Exception as e:
            print(f"Error calculating portfolio health: {e}")
            return {
                'healthy_loans_percentage': 100,
                'at_risk_loans_percentage': 0,
                'default_risk_score': 0
            }

    @staticmethod
    def format_currency(amount, currency='INR'):
        """Format amount as currency"""
        try:
            if currency == 'INR':
                # Indian Rupee formatting
                if amount >= 10000000:  # 1 Crore
                    return f"₹{amount/10000000:.1f}Cr"
                elif amount >= 100000:  # 1 Lakh
                    return f"₹{amount/100000:.1f}L"
                elif amount >= 1000:  # 1 Thousand
                    return f"₹{amount/1000:.1f}K"
                else:
                    return f"₹{amount:,.0f}"
            else:
                return f"${amount:,.2f}"
        except Exception:
            return "₹0"

    @staticmethod
    def get_payment_alerts(limit=5):
        """Get payment alerts for overdue accounts"""
        try:
            current_date = datetime.utcnow()
            
            # Get overdue loans with customer info
            overdue_loans = db.session.query(Loan, Customer).join(
                Customer, Loan.customer_id == Customer.id
            ).filter(
                and_(
                    Loan.status == 'active',
                    Loan.maturity_date < current_date,
                    Loan.outstanding_principal > 0
                )
            ).order_by(
                (current_date - Loan.maturity_date).desc()
            ).limit(limit).all()
            
            alerts = []
            for loan, customer in overdue_loans:
                days_overdue = (current_date - loan.maturity_date).days
                severity = 'danger' if days_overdue > 30 else 'warning'
                
                alerts.append({
                    'id': f'overdue-{loan.id}',
                    'title': f'Overdue Payment - {customer.full_name}',
                    'message': f'Loan {loan.loan_id} is {days_overdue} days overdue. Amount: ₹{loan.outstanding_principal:,.0f}',
                    'severity': severity,
                    'customer_name': customer.full_name,
                    'loan_id': loan.loan_id,
                    'amount': float(loan.outstanding_principal),
                    'days_overdue': days_overdue,
                    'customer_phone': customer.phone
                })
            
            # If no overdue loans, add a positive message
            if not alerts:
                alerts.append({
                    'id': 'no-overdue',
                    'title': 'All Payments Current',
                    'message': 'No overdue payments at this time.',
                    'severity': 'success'
                })
            
            return alerts
        except Exception as e:
            print(f"Error getting payment alerts: {e}")
            return [{
                'id': 'error',
                'title': 'Unable to load alerts',
                'message': 'Please refresh the page.',
                'severity': 'warning'
            }]