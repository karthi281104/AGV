from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.user import User
from app.models.loan import Loan
from app.models.customer import Customer

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    user_id = request.args.get('user_id')  # Assuming user_id is passed as a query parameter
    user = User.get_user_by_id(user_id)  # Fetch user details
    loans = Loan.get_loans_by_user_id(user_id)  # Fetch loans for the user
    customers = Customer.get_customers_by_user_id(user_id)  # Fetch customers related to the user
    return render_template('dashboard.html', user=user, loans=loans, customers=customers)

@dashboard_bp.route('/dashboard/stats')
def stats():
    user_id = request.args.get('user_id')
    # Logic to calculate and display user-specific statistics
    return render_template('dashboard_stats.html', user_id=user_id)

@dashboard_bp.route('/dashboard/settings', methods=['GET', 'POST'])
def settings():
    user_id = request.args.get('user_id')
    if request.method == 'POST':
        # Logic to update user settings
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('dashboard.dashboard', user_id=user_id))
    return render_template('dashboard_settings.html', user_id=user_id)