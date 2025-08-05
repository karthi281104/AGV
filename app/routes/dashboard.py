from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from flask_socketio import emit
from app import db, socketio
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from decimal import Decimal
import calendar

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
        current_date = datetime.utcnow()
        current_month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)

        # Total customers
        total_customers = Customer.query.filter_by(is_active=True).count()

        # Total active loans
        active_loans = Loan.query.filter_by(status='active').count()

        # Total disbursed amount (all active loans)
        total_disbursed = db.session.query(
            func.coalesce(func.sum(Loan.disbursed_amount), 0)
        ).filter_by(status='active').scalar()

        # Total outstanding principal
        total_outstanding = db.session.query(
            func.coalesce(func.sum(Loan.outstanding_principal), 0)
        ).filter_by(status='active').scalar()

        # Total interest accrued (all active loans)
        total_interest = db.session.query(
            func.coalesce(func.sum(Loan.total_interest_accrued), 0)
        ).filter_by(status='active').scalar()

        # Overdue loans and amount
        overdue_loans_query = Loan.query.filter(
            and_(
                Loan.status == 'active',
                Loan.maturity_date < current_date,
                Loan.outstanding_principal > 0
            )
        )
        overdue_loans = overdue_loans_query.count()
        overdue_amount = db.session.query(
            func.coalesce(func.sum(Loan.outstanding_principal), 0)
        ).filter(
            and_(
                Loan.status == 'active',
                Loan.maturity_date < current_date,
                Loan.outstanding_principal > 0
            )
        ).scalar()

        # Monthly collections (current month)
        monthly_collections = db.session.query(
            func.coalesce(func.sum(Payment.payment_amount), 0)
        ).filter(
            Payment.payment_date >= current_month_start
        ).scalar()

        # Previous month collections for comparison
        prev_month_collections = db.session.query(
            func.coalesce(func.sum(Payment.payment_amount), 0)
        ).filter(
            and_(
                Payment.payment_date >= previous_month_start,
                Payment.payment_date <= previous_month_end
            )
        ).scalar()

        # New customers this month
        new_customers_month = Customer.query.filter(
            Customer.created_at >= current_month_start
        ).count()

        # Loans disbursed this month
        loans_disbursed_month = Loan.query.filter(
            Loan.disbursed_date >= current_month_start
        ).count()

        # Previous month data for growth calculations
        prev_month_disbursed = db.session.query(
            func.coalesce(func.sum(Loan.disbursed_amount), 0)
        ).filter(
            and_(
                Loan.disbursed_date >= previous_month_start,
                Loan.disbursed_date <= previous_month_end
            )
        ).scalar()

        prev_month_interest = db.session.query(
            func.coalesce(func.sum(Loan.total_interest_accrued), 0)
        ).filter(
            and_(
                Loan.created_at >= previous_month_start,
                Loan.created_at <= previous_month_end
            )
        ).scalar()

        # Monthly target (example: 80% of current month collections)
        monthly_target = float(monthly_collections) * 1.25 if monthly_collections > 0 else 1000000

        stats = {
            'total_customers': total_customers,
            'active_loans': active_loans,
            'total_disbursed': float(total_disbursed),
            'total_outstanding': float(total_outstanding),
            'total_interest': float(total_interest),
            'overdue_loans': overdue_loans,
            'overdue_amount': float(overdue_amount),
            'monthly_collections': float(monthly_collections),
            'new_customers_month': new_customers_month,
            'loans_disbursed_month': loans_disbursed_month,
            'prev_month_disbursed': float(prev_month_disbursed),
            'prev_month_interest': float(prev_month_interest),
            'prev_month_collections': float(prev_month_collections),
            'monthly_target': monthly_target,
            'last_updated': current_date.isoformat()
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
        recent_loans = db.session.query(Loan, Customer).join(
            Customer, Loan.customer_id == Customer.id
        ).order_by(Loan.created_at.desc()).limit(10).all()

        # Recent customers (last 10)
        recent_customers = Customer.query.order_by(
            Customer.created_at.desc()
        ).limit(10).all()

        # Generate payment alerts for overdue accounts
        overdue_loans = db.session.query(Loan, Customer).join(
            Customer, Loan.customer_id == Customer.id
        ).filter(
            and_(
                Loan.status == 'active',
                Loan.maturity_date < datetime.utcnow(),
                Loan.outstanding_principal > 0
            )
        ).limit(5).all()

        # Format recent loans data
        loans_data = []
        for loan, customer in recent_loans:
            loans_data.append({
                'id': loan.id,
                'loan_id': loan.loan_id,
                'customer_name': customer.full_name,
                'customer_id': customer.customer_id,
                'principal_amount': float(loan.principal_amount),
                'loan_type': loan.loan_type.title(),
                'status': loan.status,
                'disbursed_date': loan.disbursed_date.isoformat() if loan.disbursed_date else None
            })

        # Format recent customers data
        customers_data = []
        for customer in recent_customers:
            customers_data.append({
                'id': customer.id,
                'customer_id': customer.customer_id,
                'full_name': customer.full_name,
                'phone': customer.phone,
                'email': customer.email,
                'created_at': customer.created_at.isoformat() if customer.created_at else None
            })

        # Format payment alerts
        alerts_data = []
        for loan, customer in overdue_loans:
            days_overdue = (datetime.utcnow() - loan.maturity_date).days
            alerts_data.append({
                'id': loan.id,
                'title': f'Overdue Payment - {customer.full_name}',
                'message': f'Loan {loan.loan_id} is {days_overdue} days overdue. Amount: ₹{loan.outstanding_principal:,.0f}',
                'severity': 'danger' if days_overdue > 30 else 'warning',
                'customer_name': customer.full_name,
                'loan_id': loan.loan_id,
                'amount': float(loan.outstanding_principal),
                'days_overdue': days_overdue
            })

        # Add some general alerts if no overdue loans
        if not alerts_data:
            alerts_data = [
                {
                    'id': 'general-1',
                    'title': 'All Payments Current',
                    'message': 'No overdue payments at this time.',
                    'severity': 'success'
                }
            ]

        activities = {
            'recent_loans': loans_data,
            'recent_customers': customers_data,
            'payment_alerts': alerts_data
        }

        return jsonify(activities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/search')
@login_required
def search():
    """Search across customers and loans"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'error': 'Query too short'}), 400

        # Search customers
        customers = Customer.query.filter(
            Customer.full_name.ilike(f'%{query}%') |
            Customer.customer_id.ilike(f'%{query}%') |
            Customer.phone.ilike(f'%{query}%')
        ).limit(10).all()

        # Search loans
        loans = db.session.query(Loan, Customer).join(
            Customer, Loan.customer_id == Customer.id
        ).filter(
            Loan.loan_id.ilike(f'%{query}%') |
            Customer.full_name.ilike(f'%{query}%')
        ).limit(10).all()

        results = {
            'customers': [customer.to_dict() for customer in customers],
            'loans': [
                {
                    **loan.to_dict(),
                    'customer_name': customer.full_name
                }
                for loan, customer in loans
            ]
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get system notifications"""
    try:
        notifications = []
        
        # Check for overdue loans
        overdue_count = Loan.query.filter(
            and_(
                Loan.status == 'active',
                Loan.maturity_date < datetime.utcnow(),
                Loan.outstanding_principal > 0
            )
        ).count()

        if overdue_count > 0:
            notifications.append({
                'id': 'overdue-loans',
                'title': f'{overdue_count} Overdue Loans',
                'message': f'{overdue_count} loans require immediate attention',
                'type': 'warning',
                'icon': 'fa-exclamation-triangle',
                'created_at': datetime.utcnow().isoformat()
            })

        # Check for new customers today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_customers_today = Customer.query.filter(
            Customer.created_at >= today_start
        ).count()

        if new_customers_today > 0:
            notifications.append({
                'id': 'new-customers',
                'title': f'{new_customers_today} New Customer{"s" if new_customers_today > 1 else ""}',
                'message': f'{new_customers_today} new customer{"s" if new_customers_today > 1 else ""} registered today',
                'type': 'info',
                'icon': 'fa-user-plus',
                'created_at': datetime.utcnow().isoformat()
            })

        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        emit('status', {'msg': 'Connected to dashboard updates'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f'User {current_user.username} disconnected from dashboard')


@socketio.on('request_stats_update')
def handle_stats_request():
    """Handle request for stats update"""
    if current_user.is_authenticated:
        # You can emit updated stats to the requesting client
        # This would typically be called when data changes
        emit('dashboard_update', {
            'type': 'stats',
            'timestamp': datetime.utcnow().isoformat()
        })


def broadcast_dashboard_update(update_type, data):
    """Broadcast dashboard updates to all connected clients"""
    socketio.emit('dashboard_update', {
        'type': update_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    })