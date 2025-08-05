from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from flask_socketio import emit
from app import db, socketio
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from datetime import datetime, timedelta
from sqlalchemy import func, and_

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Main dashboard with 6 metric blocks."""
    # Get dashboard metrics
    metrics = get_dashboard_metrics()
    
    # Get recent activities
    recent_loans = Loan.query.order_by(Loan.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                         metrics=metrics,
                         recent_loans=recent_loans,
                         recent_payments=recent_payments)

@bp.route('/api/metrics')
@login_required
def api_metrics():
    """API endpoint for dashboard metrics."""
    return jsonify(get_dashboard_metrics())

@bp.route('/api/chart-data')
@login_required
def api_chart_data():
    """API endpoint for dashboard charts."""
    chart_type = request.args.get('type', 'monthly_collections')
    
    if chart_type == 'monthly_collections':
        return jsonify(get_monthly_collections_data())
    elif chart_type == 'loan_distribution':
        return jsonify(get_loan_distribution_data())
    elif chart_type == 'payment_trends':
        return jsonify(get_payment_trends_data())
    else:
        return jsonify({'error': 'Invalid chart type'}), 400

@bp.route('/reports')
@login_required
def reports():
    """Reports dashboard."""
    if not current_user.can_access_admin():
        return redirect(url_for('dashboard.index'))
    
    # Get report data
    report_data = {
        'daily_collections': get_daily_collections_report(),
        'overdue_loans': get_overdue_loans_report(),
        'loan_portfolio': get_loan_portfolio_report()
    }
    
    return render_template('dashboard/reports.html', report_data=report_data)

@bp.route('/analytics')
@login_required
def analytics():
    """Advanced analytics dashboard."""
    if not current_user.can_access_admin():
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/analytics.html')

# SocketIO events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        emit('connected', {'status': 'Connected to AGV Finance Dashboard'})

@socketio.on('request_metrics_update')
def handle_metrics_request():
    """Handle request for metrics update."""
    if current_user.is_authenticated:
        metrics = get_dashboard_metrics()
        emit('metrics_update', metrics)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass

def get_dashboard_metrics():
    """Calculate and return dashboard metrics."""
    try:
        # 1. Total customers with loans
        customers_with_loans = db.session.query(Customer.id).join(Loan).distinct().count()
        
        # 2. Total disbursed loan amount
        total_disbursed = db.session.query(func.sum(Loan.principal_amount)).filter(
            Loan.status == 'disbursed'
        ).scalar() or 0
        
        # 3. Total interest accrued
        total_interest_accrued = 0
        disbursed_loans = Loan.query.filter_by(status='disbursed').all()
        for loan in disbursed_loans:
            if loan.disbursed_date:
                days_elapsed = (datetime.now().date() - loan.disbursed_date).days
                months_elapsed = days_elapsed / 30
                monthly_interest = float(loan.principal_amount) * (float(loan.interest_rate) / 100 / 12)
                total_interest_accrued += monthly_interest * months_elapsed
        
        # 4. Outstanding principal amounts
        outstanding_principal = 0
        for loan in disbursed_loans:
            outstanding_principal += loan.get_outstanding_principal()
        
        # 5. Overdue loans count
        overdue_loans_count = 0
        for loan in disbursed_loans:
            if loan.is_overdue():
                overdue_loans_count += 1
        
        # 6. Monthly collections (current month)
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_collections = db.session.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.payment_date >= current_month_start.date(),
                Payment.status == 'completed'
            )
        ).scalar() or 0
        
        return {
            'customers_with_loans': customers_with_loans,
            'total_disbursed': float(total_disbursed),
            'total_interest_accrued': round(total_interest_accrued, 2),
            'outstanding_principal': round(outstanding_principal, 2),
            'overdue_loans_count': overdue_loans_count,
            'monthly_collections': float(monthly_collections),
            'last_updated': datetime.now().isoformat()
        }
    
    except Exception as e:
        current_app.logger.error(f'Dashboard metrics error: {str(e)}')
        return {
            'customers_with_loans': 0,
            'total_disbursed': 0,
            'total_interest_accrued': 0,
            'outstanding_principal': 0,
            'overdue_loans_count': 0,
            'monthly_collections': 0,
            'last_updated': datetime.now().isoformat(),
            'error': 'Failed to load metrics'
        }

def get_monthly_collections_data():
    """Get monthly collections data for charts."""
    try:
        # Get last 12 months data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            
            collections = db.session.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.payment_date >= current_date.date(),
                    Payment.payment_date < next_month.date(),
                    Payment.status == 'completed'
                )
            ).scalar() or 0
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'collections': float(collections)
            })
            
            current_date = next_month
        
        return {'monthly_collections': monthly_data}
    
    except Exception as e:
        return {'error': str(e)}

def get_loan_distribution_data():
    """Get loan distribution by type."""
    try:
        loan_types = db.session.query(
            Loan.loan_type,
            func.count(Loan.id).label('count'),
            func.sum(Loan.principal_amount).label('amount')
        ).filter(Loan.status == 'disbursed').group_by(Loan.loan_type).all()
        
        distribution = []
        for loan_type, count, amount in loan_types:
            distribution.append({
                'type': loan_type,
                'count': count,
                'amount': float(amount or 0)
            })
        
        return {'loan_distribution': distribution}
    
    except Exception as e:
        return {'error': str(e)}

def get_payment_trends_data():
    """Get payment trends data."""
    try:
        # Get last 30 days payment data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        daily_payments = db.session.query(
            Payment.payment_date,
            func.sum(Payment.amount).label('total'),
            func.count(Payment.id).label('count')
        ).filter(
            and_(
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == 'completed'
            )
        ).group_by(Payment.payment_date).order_by(Payment.payment_date).all()
        
        trends = []
        for payment_date, total, count in daily_payments:
            trends.append({
                'date': payment_date.isoformat(),
                'amount': float(total),
                'count': count
            })
        
        return {'payment_trends': trends}
    
    except Exception as e:
        return {'error': str(e)}

def get_daily_collections_report():
    """Get daily collections report."""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_collections = db.session.query(func.sum(Payment.amount)).filter(
        and_(Payment.payment_date == today, Payment.status == 'completed')
    ).scalar() or 0
    
    yesterday_collections = db.session.query(func.sum(Payment.amount)).filter(
        and_(Payment.payment_date == yesterday, Payment.status == 'completed')
    ).scalar() or 0
    
    return {
        'today': float(today_collections),
        'yesterday': float(yesterday_collections),
        'change': float(today_collections - yesterday_collections)
    }

def get_overdue_loans_report():
    """Get overdue loans report."""
    overdue_loans = []
    disbursed_loans = Loan.query.filter_by(status='disbursed').all()
    
    for loan in disbursed_loans:
        if loan.is_overdue():
            overdue_amount = loan.get_overdue_amount()
            overdue_loans.append({
                'loan_id': loan.loan_id,
                'customer_name': loan.customer.name,
                'overdue_amount': overdue_amount,
                'days_overdue': (datetime.now().date() - loan.disbursed_date).days
            })
    
    return sorted(overdue_loans, key=lambda x: x['overdue_amount'], reverse=True)

def get_loan_portfolio_report():
    """Get loan portfolio summary."""
    portfolio = {
        'total_loans': Loan.query.filter_by(status='disbursed').count(),
        'total_amount': 0,
        'by_type': {}
    }
    
    loans_by_type = db.session.query(
        Loan.loan_type,
        func.count(Loan.id).label('count'),
        func.sum(Loan.principal_amount).label('amount')
    ).filter(Loan.status == 'disbursed').group_by(Loan.loan_type).all()
    
    for loan_type, count, amount in loans_by_type:
        portfolio['by_type'][loan_type] = {
            'count': count,
            'amount': float(amount or 0)
        }
        portfolio['total_amount'] += float(amount or 0)
    
    return portfolio