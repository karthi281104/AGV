from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from flask_socketio import emit
from app import db, socketio
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from app.models.dashboard import DashboardMetrics, UserPreferences, AlertSettings, DashboardActivity
from app.utils.dashboard import DashboardCalculations, DashboardNotifications
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from decimal import Decimal
import json

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page with comprehensive metrics"""
    # Log dashboard access
    DashboardActivity.log_activity(
        user_id=current_user.id,
        activity_type='dashboard_access',
        description=f'{current_user.username} accessed dashboard'
    )
    
    # Get user preferences for dashboard layout
    preferences = UserPreferences.query.filter_by(user_id=current_user.id).all()
    user_prefs = {pref.preference_key: json.loads(pref.preference_value) for pref in preferences}
    
    return render_template('dashboard/dashboard.html', user_preferences=user_prefs)


@dashboard_bp.route('/api/metrics')
@login_required
def get_dashboard_metrics():
    """Get comprehensive real-time dashboard metrics"""
    try:
        # Calculate all metrics using utility functions
        customer_metrics = DashboardCalculations.calculate_total_customers()
        portfolio_metrics = DashboardCalculations.calculate_loan_portfolio()
        overdue_metrics = DashboardCalculations.calculate_overdue_metrics()
        collection_metrics = DashboardCalculations.calculate_collection_metrics()
        financial_ratios = DashboardCalculations.calculate_financial_ratios()
        
        # Combine all metrics
        metrics = {
            'customers': customer_metrics,
            'portfolio': portfolio_metrics,
            'overdue': overdue_metrics,
            'collections': collection_metrics,
            'financial_ratios': financial_ratios,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Update cached metrics in background
        DashboardCalculations.update_cached_metrics()
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/charts')
@login_required
def get_chart_data():
    """Get data for dashboard charts and visualizations"""
    try:
        chart_data = DashboardCalculations.get_chart_data()
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get current notifications and alerts"""
    try:
        notifications = DashboardNotifications.get_all_notifications()
        return jsonify({'notifications': notifications})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/activities')
@login_required
def get_recent_activities():
    """Get recent dashboard activities"""
    try:
        limit = request.args.get('limit', 10, type=int)
        activities = DashboardCalculations.get_recent_activities(limit)
        return jsonify({'activities': activities})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    """Get or update user dashboard preferences"""
    try:
        if request.method == 'GET':
            preferences = UserPreferences.query.filter_by(user_id=current_user.id).all()
            prefs_dict = {pref.preference_key: json.loads(pref.preference_value) for pref in preferences}
            return jsonify(prefs_dict)
        
        elif request.method == 'POST':
            data = request.get_json()
            for key, value in data.items():
                UserPreferences.set_preference(current_user.id, key, value)
            
            return jsonify({'status': 'success', 'message': 'Preferences updated'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/export/<data_type>')
@login_required
def export_data(data_type):
    """Export dashboard data in various formats"""
    try:
        if data_type == 'metrics':
            # Get current metrics
            customer_metrics = DashboardCalculations.calculate_total_customers()
            portfolio_metrics = DashboardCalculations.calculate_loan_portfolio()
            overdue_metrics = DashboardCalculations.calculate_overdue_metrics()
            collection_metrics = DashboardCalculations.calculate_collection_metrics()
            
            export_data = {
                'export_date': datetime.utcnow().isoformat(),
                'metrics': {
                    'customers': customer_metrics,
                    'portfolio': portfolio_metrics,
                    'overdue': overdue_metrics,
                    'collections': collection_metrics
                }
            }
            
            # Log export activity
            DashboardActivity.log_activity(
                user_id=current_user.id,
                activity_type='data_export',
                description=f'Exported {data_type} data'
            )
            
            return jsonify(export_data)
            
        elif data_type == 'charts':
            chart_data = DashboardCalculations.get_chart_data()
            return jsonify({
                'export_date': datetime.utcnow().isoformat(),
                'chart_data': chart_data
            })
            
        else:
            return jsonify({'error': 'Invalid export type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/search')
@login_required
def search_data():
    """Search across customers, loans, and payments"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'results': []})
        
        results = {
            'customers': [],
            'loans': [],
            'payments': []
        }
        
        # Search customers
        customers = Customer.query.filter(
            or_(
                Customer.full_name.ilike(f'%{query}%'),
                Customer.customer_id.ilike(f'%{query}%'),
                Customer.phone.ilike(f'%{query}%')
            )
        ).limit(10).all()
        results['customers'] = [customer.to_dict() for customer in customers]
        
        # Search loans
        loans = Loan.query.filter(
            Loan.loan_id.ilike(f'%{query}%')
        ).limit(10).all()
        results['loans'] = [loan.to_dict() for loan in loans]
        
        # Search payments
        payments = Payment.query.filter(
            Payment.payment_id.ilike(f'%{query}%')
        ).limit(10).all()
        results['payments'] = [payment.to_dict() for payment in payments]
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        emit('status', {'msg': 'Connected to AGV Finance Dashboard'})
        # Send initial metrics
        emit('metrics_update', get_dashboard_metrics().get_json())


@socketio.on('request_metrics_update')
def handle_metrics_request():
    """Handle request for real-time metrics update"""
    if current_user.is_authenticated:
        try:
            # Get fresh metrics
            customer_metrics = DashboardCalculations.calculate_total_customers()
            portfolio_metrics = DashboardCalculations.calculate_loan_portfolio()
            overdue_metrics = DashboardCalculations.calculate_overdue_metrics()
            collection_metrics = DashboardCalculations.calculate_collection_metrics()
            
            metrics = {
                'customers': customer_metrics,
                'portfolio': portfolio_metrics,
                'overdue': overdue_metrics,
                'collections': collection_metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            emit('metrics_update', metrics)
        except Exception as e:
            emit('error', {'message': str(e)})


@socketio.on('request_chart_update')
def handle_chart_request():
    """Handle request for chart data update"""
    if current_user.is_authenticated:
        try:
            chart_data = DashboardCalculations.get_chart_data()
            emit('chart_update', chart_data)
        except Exception as e:
            emit('error', {'message': str(e)})


@socketio.on('request_notifications')
def handle_notifications_request():
    """Handle request for notifications update"""
    if current_user.is_authenticated:
        try:
            notifications = DashboardNotifications.get_all_notifications()
            emit('notifications_update', {'notifications': notifications})
        except Exception as e:
            emit('error', {'message': str(e)})


def broadcast_data_update(data_type, data):
    """Broadcast data updates to all connected clients"""
    socketio.emit('data_update', {
        'type': data_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    })