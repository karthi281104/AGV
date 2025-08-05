from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.payment import Payment
from app.models.loan import Loan
from app.models.customer import Customer
from datetime import datetime, timedelta
from sqlalchemy import func, and_

bp = Blueprint('payment', __name__)

@bp.route('/')
@login_required
def list_payments():
    """List all payments with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    method = request.args.get('method', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 20
    
    # Build query
    query = Payment.query.join(Loan).join(Customer)
    
    # Apply filters
    if status:
        query = query.filter(Payment.status == status)
    
    if method:
        query = query.filter(Payment.payment_method == method)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date >= from_date)
        except ValueError:
            flash('Invalid from date format.', 'error')
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date <= to_date)
        except ValueError:
            flash('Invalid to date format.', 'error')
    
    if search:
        query = query.filter(
            db.or_(
                Payment.payment_id.contains(search),
                Loan.loan_id.contains(search),
                Customer.name.contains(search),
                Payment.receipt_number.contains(search)
            )
        )
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    payment_methods = db.session.query(Payment.payment_method).distinct().all()
    payment_methods = [pm[0] for pm in payment_methods if pm[0]]
    
    return render_template('payments/payment_history.html', 
                         payments=payments,
                         status=status,
                         method=method,
                         date_from=date_from,
                         date_to=date_to,
                         search=search,
                         payment_methods=payment_methods)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_payment():
    """Add new payment."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('payment.list_payments'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['loan_id', 'amount', 'payment_method']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('payments/payment_form.html')
            
            # Validate loan exists and is disbursed
            loan = Loan.query.get(request.form.get('loan_id'))
            if not loan:
                flash('Selected loan does not exist.', 'error')
                return render_template('payments/payment_form.html')
            
            if loan.status != 'disbursed':
                flash('Can only add payments for disbursed loans.', 'error')
                return render_template('payments/payment_form.html')
            
            # Validate payment amount
            amount = float(request.form.get('amount'))
            if amount <= 0:
                flash('Payment amount must be greater than zero.', 'error')
                return render_template('payments/payment_form.html')
            
            outstanding_balance = loan.get_outstanding_balance()
            if amount > outstanding_balance:
                flash(f'Payment amount cannot exceed outstanding balance of ₹{outstanding_balance:.2f}', 'error')
                return render_template('payments/payment_form.html')
            
            # Parse payment date
            payment_date = datetime.now().date()
            if request.form.get('payment_date'):
                try:
                    payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid payment date format.', 'error')
                    return render_template('payments/payment_form.html')
            
            # Create payment
            payment = Payment(
                loan_id=int(request.form.get('loan_id')),
                amount=amount,
                payment_date=payment_date,
                payment_method=request.form.get('payment_method'),
                receipt_number=request.form.get('receipt_number') or None,
                reference_number=request.form.get('reference_number') or None,
                notes=request.form.get('notes') or None,
                processed_by=current_user.id
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # Check if loan is fully paid
            if loan.get_outstanding_balance() <= 0.01:  # Allow for small rounding differences
                loan.status = 'closed'
                db.session.commit()
                flash(f'Payment recorded successfully. Loan {loan.loan_id} is now fully paid and closed.', 'success')
            else:
                flash(f'Payment of ₹{amount:.2f} recorded successfully with ID: {payment.payment_id}', 'success')
            
            return redirect(url_for('payment.view_payment', id=payment.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to record payment. Please try again.', 'error')
            current_app.logger.error(f'Add payment error: {str(e)}')
    
    # Get active loans for dropdown
    active_loans = Loan.query.filter_by(status='disbursed').join(Customer).add_columns(
        Customer.name, Customer.customer_id
    ).order_by(Customer.name).all()
    
    return render_template('payments/payment_form.html', active_loans=active_loans)

@bp.route('/<int:id>')
@login_required
def view_payment(id):
    """View payment details."""
    payment = Payment.query.get_or_404(id)
    
    return render_template('payments/payment_detail.html', payment=payment)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payment(id):
    """Edit payment details (limited editing)."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('payment.view_payment', id=id))
    
    payment = Payment.query.get_or_404(id)
    
    if payment.status != 'completed':
        flash('Can only edit completed payments.', 'error')
        return redirect(url_for('payment.view_payment', id=id))
    
    if request.method == 'POST':
        try:
            # Only allow editing of non-critical fields
            payment.receipt_number = request.form.get('receipt_number') or None
            payment.reference_number = request.form.get('reference_number') or None
            payment.notes = request.form.get('notes') or None
            
            # Update payment method if needed
            new_method = request.form.get('payment_method')
            if new_method in ['cash', 'cheque', 'bank_transfer', 'upi']:
                payment.payment_method = new_method
            
            db.session.commit()
            
            flash('Payment details updated successfully.', 'success')
            return redirect(url_for('payment.view_payment', id=payment.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update payment.', 'error')
            current_app.logger.error(f'Edit payment error: {str(e)}')
    
    return render_template('payments/edit_payment.html', payment=payment)

@bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_payment(id):
    """Cancel payment (admin only)."""
    if not current_user.has_role('admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('payment.view_payment', id=id))
    
    payment = Payment.query.get_or_404(id)
    
    if payment.status != 'completed':
        flash('Can only cancel completed payments.', 'error')
        return redirect(url_for('payment.view_payment', id=id))
    
    try:
        # Check if this would affect loan closure status
        loan = payment.loan
        remaining_balance_after_cancellation = loan.get_outstanding_balance() + float(payment.amount)
        
        if loan.status == 'closed' and remaining_balance_after_cancellation > 0:
            loan.status = 'disbursed'  # Reopen the loan
        
        payment.status = 'cancelled'
        payment.notes = f"Cancelled by {current_user.name} on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        db.session.commit()
        
        flash('Payment cancelled successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel payment.', 'error')
        current_app.logger.error(f'Cancel payment error: {str(e)}')
    
    return redirect(url_for('payment.view_payment', id=id))

@bp.route('/api/loan-details/<int:loan_id>')
@login_required
def api_loan_details(loan_id):
    """API endpoint to get loan details for payment form."""
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.status != 'disbursed':
        return jsonify({'error': 'Loan is not disbursed'}), 400
    
    return jsonify({
        'loan_id': loan.loan_id,
        'customer_name': loan.customer.name,
        'customer_id': loan.customer.customer_id,
        'principal_amount': float(loan.principal_amount),
        'outstanding_balance': loan.get_outstanding_balance(),
        'outstanding_principal': loan.get_outstanding_principal(),
        'emi_amount': loan.calculate_emi(),
        'next_emi_date': loan.get_next_emi_date().isoformat() if loan.get_next_emi_date() else None,
        'overdue_amount': loan.get_overdue_amount(),
        'is_overdue': loan.is_overdue()
    })

@bp.route('/reports/daily')
@login_required
def daily_report():
    """Daily collection report."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('payment.list_payments'))
    
    # Get date from query parameter or use today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        report_date = datetime.now().date()
        flash('Invalid date format, showing today\'s report.', 'warning')
    
    # Get daily collections
    daily_collections = Payment.get_daily_collection_summary(report_date)
    
    # Get detailed payments for the day
    payments = Payment.query.filter(
        Payment.payment_date == report_date,
        Payment.status == 'completed'
    ).join(Loan).join(Customer).order_by(Payment.created_at.desc()).all()
    
    return render_template('payments/daily_report.html', 
                         report_date=report_date,
                         collections=daily_collections,
                         payments=payments)

@bp.route('/reports/monthly')
@login_required
def monthly_report():
    """Monthly collection report."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('payment.list_payments'))
    
    # Get month and year from query parameters
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Calculate date range
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get monthly payments
    payments = Payment.get_payments_by_date_range(start_date, end_date)
    
    # Calculate summary
    total_collections = sum(float(p.amount) for p in payments)
    payment_count = len(payments)
    
    # Group by payment method
    method_summary = {}
    for payment in payments:
        method = payment.payment_method
        if method not in method_summary:
            method_summary[method] = {'count': 0, 'amount': 0}
        method_summary[method]['count'] += 1
        method_summary[method]['amount'] += float(payment.amount)
    
    # Group by day for chart
    daily_collections = {}
    current_date = start_date
    while current_date <= end_date:
        daily_collections[current_date.isoformat()] = 0
        current_date += timedelta(days=1)
    
    for payment in payments:
        date_key = payment.payment_date.isoformat()
        if date_key in daily_collections:
            daily_collections[date_key] += float(payment.amount)
    
    report_data = {
        'year': year,
        'month': month,
        'month_name': start_date.strftime('%B'),
        'start_date': start_date,
        'end_date': end_date,
        'total_collections': total_collections,
        'payment_count': payment_count,
        'method_summary': method_summary,
        'daily_collections': daily_collections,
        'payments': payments
    }
    
    return render_template('payments/monthly_report.html', report=report_data)

@bp.route('/api/payment-summary')
@login_required
def api_payment_summary():
    """API endpoint for payment summary statistics."""
    # Today's collections
    today = datetime.now().date()
    today_collections = db.session.query(func.sum(Payment.amount)).filter(
        and_(Payment.payment_date == today, Payment.status == 'completed')
    ).scalar() or 0
    
    # This month's collections
    month_start = today.replace(day=1)
    month_collections = db.session.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.payment_date >= month_start,
            Payment.payment_date <= today,
            Payment.status == 'completed'
        )
    ).scalar() or 0
    
    # This year's collections
    year_start = today.replace(month=1, day=1)
    year_collections = db.session.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.payment_date >= year_start,
            Payment.payment_date <= today,
            Payment.status == 'completed'
        )
    ).scalar() or 0
    
    return jsonify({
        'today_collections': float(today_collections),
        'month_collections': float(month_collections),
        'year_collections': float(year_collections),
        'last_updated': datetime.now().isoformat()
    })