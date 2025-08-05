from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit
from app import db, socketio
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from decimal import Decimal

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/stats')
@login_required
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        # Total customers
        total_customers = Customer.query.filter_by(is_active=True).count()

        # Total active loans
        active_loans = Loan.query.filter_by(status='active').count()

        # Total disbursed amount
        total_disbursed = db.session.query(
            func.sum(Loan.disbursed_amount)
        ).filter_by(status='active').scalar() or 0

        # Total outstanding principal
        total_outstanding = db.session.query(
            func.sum(Loan.outstanding_principal)
        ).filter_by(status='active').scalar() or 0

        # Total interest accrued
        total_interest = db.session.query(
            func.sum(Loan.total_interest_accrued)
        ).filter_by(status='active').scalar() or 0

        # Overdue loans (past maturity date)
        overdue_loans = Loan.query.filter(
            and_(
                Loan.status == 'active',
                Loan.maturity_date < datetime.utcnow(),
                Loan.outstanding_principal > 0
            )
        ).count()

        # Monthly collections (current month)
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_collections = db.session.query(
            func.sum(Payment.payment_amount)
        ).filter(
            Payment.payment_date >= current_month_start
        ).scalar() or 0

        # New customers this month
        new_customers_month = Customer.query.filter(
            Customer.created_at >= current_month_start
        ).count()

        # Loans disbursed this month
        loans_disbursed_month = Loan.query.filter(
            Loan.disbursed_date >= current_month_start
        ).count()

        stats = {
            'total_customers': total_customers,
            'active_loans': active_loans,
            'total_disbursed': float(total_disbursed),
            'total_outstanding': float(total_outstanding),
            'total_interest': float(total_interest),
            'overdue_loans': overdue_loans,
            'monthly_collections': float(monthly_collections),
            'new_customers_month': new_customers_month,
            'loans_disbursed_month': loans_disbursed_month,
            'last_updated': datetime.utcnow().isoformat()
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/recent-activities')
@login_required
def get_recent_activities():
    """Get recent activities for dashboard"""
    try:
        # Recent loans (last 10)
        recent_loans = Loan.query.order_by(
            Loan.created_at.desc()
        ).limit(10).all()

        # Recent payments (last 10)
        recent_payments = Payment.query.order_by(
            Payment.created_at.desc()
        ).limit(10).all()

        # Recent customers (last 10)
        recent_customers = Customer.query.order_by(
            Customer.created_at.desc()
        ).limit(10).all()

        activities = {
            'recent_loans': [loan.to_dict() for loan in recent_loans],
            'recent_payments': [payment.to_dict() for payment in recent_payments],
            'recent_customers': [customer.to_dict() for customer in recent_customers]
        }

        return jsonify(activities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        emit('status', {'msg': 'Connected to dashboard updates'})


@socketio.on('request_stats_update')
def handle_stats_request():
    """Handle request for stats update"""
    if current_user.is_authenticated:
        # This would be called when data changes
        # You can emit updated stats to all connected clients
        pass