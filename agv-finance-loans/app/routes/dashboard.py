"""
Dashboard routes for AGV Finance and Loans
Real-time dashboard with 6-metric display and analytics
"""

from flask import Blueprint, render_template, request, jsonify, current_app, url_for, flash, redirect
from flask_login import login_required, current_user
from flask_socketio import emit
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_
from decimal import Decimal

from app import db, socketio
from app.models.user import User
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from app.utils.auth import requires_auth
from app.utils.calculations import FinancialAnalyzer
from app.utils.helpers import format_currency, format_percentage

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Main dashboard with 6-metric grid"""
    metrics = get_dashboard_metrics()
    recent_activities = get_recent_activities()
    
    return render_template('dashboard/index.html', 
                         metrics=metrics, 
                         activities=recent_activities)

@bp.route('/analytics')
@login_required
def analytics():
    """Detailed analytics dashboard"""
    # Get period from query params (default last 30 days)
    period = request.args.get('period', '30')
    
    analytics_data = get_analytics_data(period)
    
    return render_template('dashboard/analytics.html', 
                         analytics=analytics_data, 
                         period=period)

@bp.route('/reports')
@login_required
def reports():
    """Reports dashboard"""
    if not current_user.is_manager():
        flash('Access denied. Manager privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/reports.html')

@bp.route('/api/metrics')
@login_required
def api_metrics():
    """API endpoint for real-time metrics"""
    metrics = get_dashboard_metrics()
    return jsonify(metrics)

@bp.route('/api/chart-data/<chart_type>')
@login_required
def chart_data(chart_type):
    """API endpoint for chart data"""
    period = request.args.get('period', '30')
    
    if chart_type == 'loan-disbursement':
        data = get_loan_disbursement_chart(period)
    elif chart_type == 'payment-collection':
        data = get_payment_collection_chart(period)
    elif chart_type == 'loan-status':
        data = get_loan_status_chart()
    elif chart_type == 'monthly-trends':
        data = get_monthly_trends_chart(period)
    elif chart_type == 'customer-growth':
        data = get_customer_growth_chart(period)
    elif chart_type == 'portfolio-analysis':
        data = get_portfolio_analysis_chart()
    else:
        return jsonify({'error': 'Invalid chart type'}), 400
    
    return jsonify(data)

def get_dashboard_metrics():
    """Calculate the 6 main dashboard metrics"""
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    
    # Calculate previous month
    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
        prev_month_end = date(today.year, 1, 1) - timedelta(days=1)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)
        prev_month_end = current_month_start - timedelta(days=1)
    
    # Metric 1: Total Active Loans
    active_loans_count = Loan.query.filter_by(status='active').count()
    prev_active_loans = Loan.query.filter(
        and_(Loan.status == 'active', Loan.created_at < current_month_start)
    ).count()
    
    # Metric 2: Outstanding Amount
    outstanding_amount = db.session.query(
        func.sum(Loan.outstanding_balance)
    ).filter_by(status='active').scalar() or Decimal('0')
    
    prev_outstanding = db.session.query(
        func.sum(Loan.outstanding_balance)
    ).filter(
        and_(Loan.status == 'active', Loan.created_at < current_month_start)
    ).scalar() or Decimal('0')
    
    # Metric 3: Monthly Collections
    monthly_collections = db.session.query(
        func.sum(Payment.payment_amount)
    ).filter(
        and_(
            Payment.payment_date >= current_month_start,
            Payment.payment_date <= today,
            Payment.status == 'completed'
        )
    ).scalar() or Decimal('0')
    
    prev_collections = db.session.query(
        func.sum(Payment.payment_amount)
    ).filter(
        and_(
            Payment.payment_date >= prev_month_start,
            Payment.payment_date <= prev_month_end,
            Payment.status == 'completed'
        )
    ).scalar() or Decimal('0')
    
    # Metric 4: New Customers This Month
    new_customers = Customer.query.filter(
        Customer.created_at >= current_month_start
    ).count()
    
    prev_new_customers = Customer.query.filter(
        and_(
            Customer.created_at >= prev_month_start,
            Customer.created_at <= prev_month_end
        )
    ).count()
    
    # Metric 5: Loan Approvals This Month
    loan_approvals = Loan.query.filter(
        and_(
            Loan.approval_date >= current_month_start,
            Loan.approval_date <= today,
            Loan.status.in_(['approved', 'disbursed', 'active'])
        )
    ).count()
    
    prev_approvals = Loan.query.filter(
        and_(
            Loan.approval_date >= prev_month_start,
            Loan.approval_date <= prev_month_end,
            Loan.status.in_(['approved', 'disbursed', 'active'])
        )
    ).count()
    
    # Metric 6: Overdue Amount
    overdue_amount = Decimal('0')
    active_loans = Loan.query.filter_by(status='active').all()
    for loan in active_loans:
        overdue_amount += loan.get_overdue_amount()
    
    # Calculate previous overdue (simplified)
    prev_overdue_amount = overdue_amount * Decimal('0.9')  # Estimate
    
    # Calculate percentage changes
    def calc_percentage_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
    
    metrics = {
        'active_loans': {
            'value': active_loans_count,
            'change': calc_percentage_change(active_loans_count, prev_active_loans),
            'formatted_value': f"{active_loans_count:,}"
        },
        'outstanding_amount': {
            'value': float(outstanding_amount),
            'change': calc_percentage_change(float(outstanding_amount), float(prev_outstanding)),
            'formatted_value': format_currency(outstanding_amount)
        },
        'monthly_collections': {
            'value': float(monthly_collections),
            'change': calc_percentage_change(float(monthly_collections), float(prev_collections)),
            'formatted_value': format_currency(monthly_collections)
        },
        'new_customers': {
            'value': new_customers,
            'change': calc_percentage_change(new_customers, prev_new_customers),
            'formatted_value': f"{new_customers:,}"
        },
        'loan_approvals': {
            'value': loan_approvals,
            'change': calc_percentage_change(loan_approvals, prev_approvals),
            'formatted_value': f"{loan_approvals:,}"
        },
        'overdue_amount': {
            'value': float(overdue_amount),
            'change': calc_percentage_change(float(overdue_amount), float(prev_overdue_amount)),
            'formatted_value': format_currency(overdue_amount)
        }
    }
    
    return metrics

def get_recent_activities(limit=10):
    """Get recent activities for dashboard"""
    activities = []
    
    # Recent payments
    recent_payments = Payment.query.filter_by(status='completed')\
        .order_by(Payment.created_at.desc()).limit(5).all()
    
    for payment in recent_payments:
        activities.append({
            'type': 'payment',
            'icon': 'fas fa-money-bill-wave',
            'title': f'Payment of {format_currency(payment.payment_amount)} received',
            'subtitle': f'From {payment.customer.full_name} for Loan #{payment.loan.loan_number}',
            'time': payment.created_at,
            'url': url_for('payment.detail', id=payment.id)
        })
    
    # Recent loan approvals
    recent_approvals = Loan.query.filter(Loan.approval_date.isnot(None))\
        .order_by(Loan.approval_date.desc()).limit(3).all()
    
    for loan in recent_approvals:
        activities.append({
            'type': 'approval',
            'icon': 'fas fa-check-circle',
            'title': f'Loan #{loan.loan_number} approved',
            'subtitle': f'Amount: {format_currency(loan.principal_amount)} for {loan.customer.full_name}',
            'time': datetime.combine(loan.approval_date, datetime.min.time()),
            'url': url_for('loan.detail', id=loan.id)
        })
    
    # Recent customer registrations
    recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(3).all()
    
    for customer in recent_customers:
        activities.append({
            'type': 'customer',
            'icon': 'fas fa-user-plus',
            'title': f'New customer registered',
            'subtitle': f'{customer.full_name} - {customer.email}',
            'time': customer.created_at,
            'url': url_for('customer.detail', id=customer.id)
        })
    
    # Sort activities by time and limit
    activities.sort(key=lambda x: x['time'], reverse=True)
    return activities[:limit]

def get_loan_disbursement_chart(period):
    """Get loan disbursement chart data"""
    days = int(period)
    start_date = date.today() - timedelta(days=days)
    
    disbursements = db.session.query(
        func.date(Loan.disbursement_date).label('date'),
        func.sum(Loan.disbursed_amount).label('amount'),
        func.count(Loan.id).label('count')
    ).filter(
        and_(
            Loan.disbursement_date >= start_date,
            Loan.status.in_(['disbursed', 'active', 'closed'])
        )
    ).group_by(func.date(Loan.disbursement_date)).all()
    
    data = {
        'labels': [d.date.strftime('%d %b') for d in disbursements],
        'amounts': [float(d.amount) for d in disbursements],
        'counts': [d.count for d in disbursements]
    }
    
    return data

def get_payment_collection_chart(period):
    """Get payment collection chart data"""
    days = int(period)
    start_date = date.today() - timedelta(days=days)
    
    collections = db.session.query(
        func.date(Payment.payment_date).label('date'),
        func.sum(Payment.payment_amount).label('amount'),
        func.count(Payment.id).label('count')
    ).filter(
        and_(
            Payment.payment_date >= start_date,
            Payment.status == 'completed'
        )
    ).group_by(func.date(Payment.payment_date)).all()
    
    data = {
        'labels': [c.date.strftime('%d %b') for c in collections],
        'amounts': [float(c.amount) for c in collections],
        'counts': [c.count for c in collections]
    }
    
    return data

def get_loan_status_chart():
    """Get loan status distribution chart"""
    status_counts = db.session.query(
        Loan.status,
        func.count(Loan.id).label('count'),
        func.sum(Loan.principal_amount).label('amount')
    ).group_by(Loan.status).all()
    
    data = {
        'labels': [s.status.title() for s in status_counts],
        'counts': [s.count for s in status_counts],
        'amounts': [float(s.amount or 0) for s in status_counts]
    }
    
    return data

def get_analytics_data(period):
    """Get comprehensive analytics data"""
    days = int(period)
    start_date = date.today() - timedelta(days=days)
    
    # Portfolio metrics
    all_loans = Loan.query.all()
    portfolio_metrics = FinancialAnalyzer.calculate_portfolio_metrics(all_loans)
    
    # Performance metrics
    total_customers = Customer.query.count()
    verified_customers = Customer.query.filter_by(verification_status='verified').count()
    
    analytics = {
        'portfolio': portfolio_metrics,
        'customer_metrics': {
            'total_customers': total_customers,
            'verified_customers': verified_customers,
            'verification_rate': (verified_customers / total_customers * 100) if total_customers > 0 else 0
        },
        'period_summary': {
            'start_date': start_date.strftime('%d %b %Y'),
            'end_date': date.today().strftime('%d %b %Y'),
            'days': days
        }
    }
    
    return analytics

# Real-time updates with SocketIO
@socketio.on('connect', namespace='/dashboard')
@requires_auth
def handle_dashboard_connect():
    """Handle dashboard WebSocket connection"""
    emit('connected', {'message': 'Connected to dashboard updates'})

@socketio.on('request_metrics', namespace='/dashboard')
@requires_auth
def handle_metrics_request():
    """Handle request for updated metrics"""
    metrics = get_dashboard_metrics()
    emit('metrics_update', metrics)

# Background task to emit real-time updates
def emit_dashboard_update():
    """Emit dashboard updates to connected clients"""
    try:
        metrics = get_dashboard_metrics()
        socketio.emit('metrics_update', metrics, namespace='/dashboard')
    except Exception as e:
        current_app.logger.error(f"Dashboard update error: {e}")

# Helper functions for other modules to trigger updates
def trigger_metrics_update():
    """Trigger metrics update for all connected dashboards"""
    socketio.emit('dashboard_refresh', namespace='/dashboard')