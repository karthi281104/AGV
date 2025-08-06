from app import db
from app.models.core import Customer, Loan, Payment
from app.models.dashboard import DashboardMetrics, RealtimeData, DashboardActivity
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from decimal import Decimal
import json


class DashboardCalculations:
    """Utility class for dashboard metric calculations and data aggregation"""

    @staticmethod
    def calculate_total_customers():
        """Calculate total active customers with growth indicators"""
        total_customers = Customer.query.filter_by(is_active=True).count()
        
        # Calculate month-over-month growth
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        new_customers_this_month = Customer.query.filter(
            Customer.created_at >= current_month_start,
            Customer.is_active == True
        ).count()
        
        new_customers_last_month = Customer.query.filter(
            and_(
                Customer.created_at >= last_month_start,
                Customer.created_at < current_month_start,
                Customer.is_active == True
            )
        ).count()
        
        growth_rate = 0
        if new_customers_last_month > 0:
            growth_rate = ((new_customers_this_month - new_customers_last_month) / new_customers_last_month) * 100
        
        return {
            'total': total_customers,
            'new_this_month': new_customers_this_month,
            'new_last_month': new_customers_last_month,
            'growth_rate': round(growth_rate, 2),
            'trend': 'up' if growth_rate > 0 else 'down' if growth_rate < 0 else 'stable'
        }

    @staticmethod
    def calculate_loan_portfolio():
        """Calculate comprehensive loan portfolio metrics"""
        active_loans = Loan.query.filter_by(status='active').all()
        
        total_disbursed = sum(float(loan.disbursed_amount) for loan in active_loans)
        total_outstanding = sum(float(loan.outstanding_principal) for loan in active_loans)
        total_interest_accrued = sum(float(loan.total_interest_accrued) for loan in active_loans)
        
        # Calculate average loan size
        avg_loan_size = total_disbursed / len(active_loans) if active_loans else 0
        
        # Portfolio breakdown by loan type
        gold_loans = [loan for loan in active_loans if loan.loan_type == 'gold']
        bond_loans = [loan for loan in active_loans if loan.loan_type == 'bond']
        
        portfolio_breakdown = {
            'gold': {
                'count': len(gold_loans),
                'amount': sum(float(loan.disbursed_amount) for loan in gold_loans),
                'percentage': (len(gold_loans) / len(active_loans) * 100) if active_loans else 0
            },
            'bond': {
                'count': len(bond_loans),
                'amount': sum(float(loan.disbursed_amount) for loan in bond_loans),
                'percentage': (len(bond_loans) / len(active_loans) * 100) if active_loans else 0
            }
        }
        
        return {
            'total_active_loans': len(active_loans),
            'total_disbursed': round(total_disbursed, 2),
            'total_outstanding': round(total_outstanding, 2),
            'total_interest_accrued': round(total_interest_accrued, 2),
            'average_loan_size': round(avg_loan_size, 2),
            'portfolio_breakdown': portfolio_breakdown
        }

    @staticmethod
    def calculate_overdue_metrics():
        """Calculate overdue loan metrics and risk indicators"""
        current_date = datetime.utcnow()
        
        # Overdue loans (past maturity date with outstanding balance)
        overdue_loans = Loan.query.filter(
            and_(
                Loan.status == 'active',
                Loan.maturity_date < current_date,
                Loan.outstanding_principal > 0
            )
        ).all()
        
        overdue_amount = sum(float(loan.outstanding_principal) for loan in overdue_loans)
        
        # Categorize by overdue duration
        thirty_days_ago = current_date - timedelta(days=30)
        sixty_days_ago = current_date - timedelta(days=60)
        ninety_days_ago = current_date - timedelta(days=90)
        
        overdue_categories = {
            '0-30': {'count': 0, 'amount': 0},
            '30-60': {'count': 0, 'amount': 0},
            '60-90': {'count': 0, 'amount': 0},
            '90+': {'count': 0, 'amount': 0}
        }
        
        for loan in overdue_loans:
            overdue_days = (current_date - loan.maturity_date).days
            amount = float(loan.outstanding_principal)
            
            if overdue_days <= 30:
                overdue_categories['0-30']['count'] += 1
                overdue_categories['0-30']['amount'] += amount
            elif overdue_days <= 60:
                overdue_categories['30-60']['count'] += 1
                overdue_categories['30-60']['amount'] += amount
            elif overdue_days <= 90:
                overdue_categories['60-90']['count'] += 1
                overdue_categories['60-90']['amount'] += amount
            else:
                overdue_categories['90+']['count'] += 1
                overdue_categories['90+']['amount'] += amount
        
        # Calculate default rate (90+ days overdue)
        total_active_loans = Loan.query.filter_by(status='active').count()
        default_rate = (overdue_categories['90+']['count'] / total_active_loans * 100) if total_active_loans > 0 else 0
        
        return {
            'total_overdue_loans': len(overdue_loans),
            'total_overdue_amount': round(overdue_amount, 2),
            'default_rate': round(default_rate, 2),
            'overdue_categories': overdue_categories,
            'risk_level': 'high' if default_rate > 10 else 'medium' if default_rate > 5 else 'low'
        }

    @staticmethod
    def calculate_collection_metrics():
        """Calculate collection efficiency and payment trends"""
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Current month collections
        current_month_payments = Payment.query.filter(
            Payment.payment_date >= current_month_start
        ).all()
        
        current_month_collections = sum(float(payment.payment_amount) for payment in current_month_payments)
        
        # Last month collections
        last_month_payments = Payment.query.filter(
            and_(
                Payment.payment_date >= last_month_start,
                Payment.payment_date < current_month_start
            )
        ).all()
        
        last_month_collections = sum(float(payment.payment_amount) for payment in last_month_payments)
        
        # Collection efficiency (collected vs due)
        # For simplicity, using total outstanding as "due" amount
        total_outstanding = db.session.query(
            func.sum(Loan.outstanding_principal)
        ).filter_by(status='active').scalar() or 0
        
        collection_efficiency = 0
        if total_outstanding > 0:
            collection_efficiency = (current_month_collections / float(total_outstanding)) * 100
        
        # Payment method breakdown
        payment_methods = {}
        for payment in current_month_payments:
            method = payment.payment_method
            if method not in payment_methods:
                payment_methods[method] = {'count': 0, 'amount': 0}
            payment_methods[method]['count'] += 1
            payment_methods[method]['amount'] += float(payment.payment_amount)
        
        return {
            'current_month_collections': round(current_month_collections, 2),
            'last_month_collections': round(last_month_collections, 2),
            'collection_efficiency': round(collection_efficiency, 2),
            'payment_count_current_month': len(current_month_payments),
            'payment_methods': payment_methods,
            'trend': 'up' if current_month_collections > last_month_collections else 'down'
        }

    @staticmethod
    def calculate_financial_ratios():
        """Calculate key financial ratios and performance indicators"""
        # Get all active loans
        active_loans = Loan.query.filter_by(status='active').all()
        
        if not active_loans:
            return {
                'interest_yield': 0,
                'loan_to_value': 0,
                'portfolio_growth': 0,
                'customer_acquisition_cost': 0
            }
        
        total_principal = sum(float(loan.principal_amount) for loan in active_loans)
        total_interest = sum(float(loan.total_interest_accrued) for loan in active_loans)
        
        # Interest yield calculation
        interest_yield = (total_interest / total_principal * 100) if total_principal > 0 else 0
        
        # Portfolio growth (month-over-month)
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_month_disbursed = db.session.query(
            func.sum(Loan.disbursed_amount)
        ).filter(Loan.disbursed_date >= current_month_start).scalar() or 0
        
        last_month_disbursed = db.session.query(
            func.sum(Loan.disbursed_amount)
        ).filter(
            and_(
                Loan.disbursed_date >= last_month_start,
                Loan.disbursed_date < current_month_start
            )
        ).scalar() or 0
        
        portfolio_growth = 0
        if last_month_disbursed > 0:
            portfolio_growth = ((float(current_month_disbursed) - float(last_month_disbursed)) / float(last_month_disbursed)) * 100
        
        return {
            'interest_yield': round(interest_yield, 2),
            'portfolio_growth': round(portfolio_growth, 2),
            'total_principal': round(total_principal, 2),
            'total_interest': round(total_interest, 2)
        }

    @staticmethod
    def get_recent_activities(limit=10):
        """Get recent dashboard activities"""
        activities = DashboardActivity.query.order_by(
            desc(DashboardActivity.created_at)
        ).limit(limit).all()
        
        return [activity.to_dict() for activity in activities]

    @staticmethod
    def get_chart_data():
        """Generate data for dashboard charts"""
        # Monthly disbursement trend (last 12 months)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        monthly_disbursements = db.session.query(
            func.date_trunc('month', Loan.disbursed_date).label('month'),
            func.sum(Loan.disbursed_amount).label('total'),
            func.count(Loan.id).label('count')
        ).filter(
            Loan.disbursed_date >= twelve_months_ago
        ).group_by(
            func.date_trunc('month', Loan.disbursed_date)
        ).order_by('month').all()
        
        # Portfolio breakdown for pie chart
        portfolio_data = DashboardCalculations.calculate_loan_portfolio()
        
        # Payment trends (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        monthly_collections = db.session.query(
            func.date_trunc('month', Payment.payment_date).label('month'),
            func.sum(Payment.payment_amount).label('total'),
            func.count(Payment.id).label('count')
        ).filter(
            Payment.payment_date >= six_months_ago
        ).group_by(
            func.date_trunc('month', Payment.payment_date)
        ).order_by('month').all()
        
        return {
            'monthly_disbursements': [
                {
                    'month': result.month.strftime('%Y-%m') if result.month else '',
                    'amount': float(result.total) if result.total else 0,
                    'count': result.count
                } for result in monthly_disbursements
            ],
            'portfolio_breakdown': portfolio_data['portfolio_breakdown'],
            'monthly_collections': [
                {
                    'month': result.month.strftime('%Y-%m') if result.month else '',
                    'amount': float(result.total) if result.total else 0,
                    'count': result.count
                } for result in monthly_collections
            ]
        }

    @staticmethod
    def update_cached_metrics():
        """Update all cached dashboard metrics for performance"""
        try:
            # Update customer metrics
            customer_data = DashboardCalculations.calculate_total_customers()
            DashboardMetrics.update_metric('total_customers', customer_data['total'], customer_data)
            
            # Update portfolio metrics
            portfolio_data = DashboardCalculations.calculate_loan_portfolio()
            DashboardMetrics.update_metric('total_disbursed', portfolio_data['total_disbursed'], portfolio_data)
            DashboardMetrics.update_metric('total_outstanding', portfolio_data['total_outstanding'])
            DashboardMetrics.update_metric('active_loans', portfolio_data['total_active_loans'])
            
            # Update overdue metrics
            overdue_data = DashboardCalculations.calculate_overdue_metrics()
            DashboardMetrics.update_metric('overdue_amount', overdue_data['total_overdue_amount'], overdue_data)
            
            # Update collection metrics
            collection_data = DashboardCalculations.calculate_collection_metrics()
            DashboardMetrics.update_metric('monthly_collections', collection_data['current_month_collections'], collection_data)
            
            # Update financial ratios
            ratio_data = DashboardCalculations.calculate_financial_ratios()
            DashboardMetrics.update_metric('interest_yield', ratio_data['interest_yield'], ratio_data)
            
            return True
        except Exception as e:
            print(f"Error updating cached metrics: {str(e)}")
            return False


class DashboardNotifications:
    """Utility class for dashboard notifications and alerts"""
    
    @staticmethod
    def check_overdue_alerts():
        """Check for overdue payment alerts"""
        overdue_data = DashboardCalculations.calculate_overdue_metrics()
        
        alerts = []
        if overdue_data['default_rate'] > 10:
            alerts.append({
                'type': 'critical',
                'message': f"High default rate: {overdue_data['default_rate']}%",
                'action': 'review_overdue_loans'
            })
        elif overdue_data['default_rate'] > 5:
            alerts.append({
                'type': 'warning',
                'message': f"Moderate default rate: {overdue_data['default_rate']}%",
                'action': 'monitor_collections'
            })
        
        return alerts
    
    @staticmethod
    def check_portfolio_alerts():
        """Check for portfolio-related alerts"""
        portfolio_data = DashboardCalculations.calculate_loan_portfolio()
        
        alerts = []
        if portfolio_data['total_outstanding'] > 10000000:  # 1 crore
            alerts.append({
                'type': 'info',
                'message': f"Portfolio milestone: ₹{portfolio_data['total_outstanding']:,.0f} outstanding",
                'action': 'celebrate_milestone'
            })
        
        return alerts
    
    @staticmethod
    def get_all_notifications():
        """Get all current notifications for dashboard"""
        notifications = []
        notifications.extend(DashboardNotifications.check_overdue_alerts())
        notifications.extend(DashboardNotifications.check_portfolio_alerts())
        
        return notifications