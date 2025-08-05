"""
Payment processing routes for AGV Finance and Loans
Payment collection, processing, and history with automatic calculations
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from decimal import Decimal

from app import db
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from app.utils.auth import requires_auth, requires_role
from app.utils.helpers import format_currency, paginate_query
from app.routes.dashboard import trigger_metrics_update

bp = Blueprint('payment', __name__)

@bp.route('/')
@login_required
def list_payments():
    """List all payments with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PAYMENTS_PER_PAGE', 20)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    payment_type_filter = request.args.get('payment_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Build query
    query = Payment.query.join(Customer).join(Loan)
    
    if search:
        query = query.filter(
            db.or_(
                Payment.payment_id.ilike(f'%{search}%'),
                Payment.receipt_number.ilike(f'%{search}%'),
                Loan.loan_number.ilike(f'%{search}%'),
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    if payment_type_filter:
        query = query.filter(Payment.payment_type == payment_type_filter)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date <= to_date)
        except ValueError:
            pass
    
    # Order by payment date (newest first)
    query = query.order_by(Payment.payment_date.desc())
    
    # Paginate
    payments = paginate_query(query, page, per_page)
    
    # Calculate summary statistics for current filter
    total_amount = query.with_entities(db.func.sum(Payment.payment_amount)).scalar() or Decimal('0')
    count = query.count()
    
    summary = {
        'total_amount': float(total_amount),
        'count': count,
        'average_amount': float(total_amount / count) if count > 0 else 0
    }
    
    return render_template('payments/payment_list.html',
                         payments=payments,
                         summary=summary,
                         search=search,
                         status_filter=status_filter,
                         payment_type_filter=payment_type_filter,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/process', methods=['GET', 'POST'])
@bp.route('/process/<int:loan_id>', methods=['GET', 'POST'])
@login_required
def process_payment(loan_id=None):
    """Process new payment"""
    loan = None
    if loan_id:
        loan = Loan.query.get_or_404(loan_id)
        
        if loan.status != 'active':
            flash('Payments can only be processed for active loans.', 'error')
            return redirect(url_for('loan.detail', id=loan_id))
    
    if request.method == 'POST':
        try:
            # Get or validate loan
            if not loan_id:
                loan_id = request.form.get('loan_id')
                if not loan_id:
                    flash('Please select a loan.', 'error')
                    return render_template('payments/payment_form.html', loan=loan)
                loan = Loan.query.get_or_404(loan_id)
            
            # Validate required fields
            payment_amount = request.form.get('payment_amount')
            payment_method = request.form.get('payment_method')
            payment_type = request.form.get('payment_type', 'EMI')
            
            if not payment_amount or not payment_method:
                flash('Payment amount and method are required.', 'error')
                return render_template('payments/payment_form.html', loan=loan)
            
            try:
                payment_amount = Decimal(payment_amount)
                if payment_amount <= 0:
                    flash('Payment amount must be positive.', 'error')
                    return render_template('payments/payment_form.html', loan=loan)
            except (ValueError, TypeError):
                flash('Invalid payment amount.', 'error')
                return render_template('payments/payment_form.html', loan=loan)
            
            # Generate payment ID and receipt number
            payment_id = Payment.generate_payment_id()
            
            # Create payment
            payment = Payment(
                payment_id=payment_id,
                loan_id=loan.id,
                customer_id=loan.customer_id,
                payment_amount=payment_amount,
                payment_type=payment_type,
                payment_method=payment_method,
                transaction_reference=request.form.get('transaction_reference'),
                bank_name=request.form.get('bank_name'),
                cheque_number=request.form.get('cheque_number'),
                upi_transaction_id=request.form.get('upi_transaction_id'),
                remarks=request.form.get('remarks'),
                processed_by=current_user.id
            )
            
            # Set payment date
            payment_date_str = request.form.get('payment_date')
            if payment_date_str:
                try:
                    payment.payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                except ValueError:
                    payment.payment_date = date.today()
            else:
                payment.payment_date = date.today()
            
            # Set cheque date if applicable
            if payment_method == 'Cheque':
                cheque_date_str = request.form.get('cheque_date')
                if cheque_date_str:
                    try:
                        payment.cheque_date = datetime.strptime(cheque_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass
            
            # Calculate EMI number if this is an EMI payment
            if payment_type == 'EMI':
                current_emi_number = loan.get_current_emi_number()
                payment.emi_number = loan.paid_emis + 1
                
                # Set due date for this EMI
                if loan.first_emi_date and payment.emi_number <= loan.total_emis:
                    from dateutil.relativedelta import relativedelta
                    payment.due_date = loan.first_emi_date + relativedelta(months=payment.emi_number - 1)
                    
                    # Calculate late fee if payment is late
                    if payment.payment_date > payment.due_date:
                        days_late = (payment.payment_date - payment.due_date).days
                        payment.days_late = days_late
                        
                        # Calculate late fee (2% of EMI per month)
                        from app.utils.calculations import PaymentCalculator
                        payment.late_fee = PaymentCalculator.calculate_late_fee(
                            loan.emi_amount, days_late
                        )
            
            # Calculate principal and interest breakdown
            payment.calculate_breakdown(loan)
            
            # Generate receipt number
            payment.receipt_number = payment.generate_receipt_number()
            
            db.session.add(payment)
            
            # Apply payment to loan
            payment.apply_to_loan()
            
            db.session.commit()
            
            flash(f'Payment {payment.payment_id} processed successfully!', 'success')
            trigger_metrics_update()
            return redirect(url_for('payment.detail', id=payment.id))
            
        except Exception as e:
            current_app.logger.error(f"Error processing payment: {e}")
            flash('An error occurred while processing the payment.', 'error')
            db.session.rollback()
    
    # Get active loans for dropdown (if loan not pre-selected)
    loans = []
    if not loan:
        loans = Loan.query.filter_by(status='active')\
            .join(Customer)\
            .order_by(Customer.first_name).all()
    
    return render_template('payments/payment_form.html', 
                         loan=loan, 
                         loans=loans)

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Payment detail page"""
    payment = Payment.query.get_or_404(id)
    
    return render_template('payments/payment_detail.html', payment=payment)

@bp.route('/<int:id>/receipt')
@login_required
def receipt(id):
    """Generate payment receipt"""
    payment = Payment.query.get_or_404(id)
    
    if not payment.receipt_generated:
        payment.receipt_generated = True
        db.session.commit()
    
    return render_template('payments/receipt.html', payment=payment)

@bp.route('/<int:id>/reverse', methods=['POST'])
@login_required
@requires_role('manager')
def reverse_payment(id):
    """Reverse a payment"""
    payment = Payment.query.get_or_404(id)
    
    if payment.is_reversed:
        flash('Payment is already reversed.', 'error')
        return redirect(url_for('payment.detail', id=id))
    
    if payment.status != 'completed':
        flash('Only completed payments can be reversed.', 'error')
        return redirect(url_for('payment.detail', id=id))
    
    reversal_reason = request.form.get('reversal_reason')
    if not reversal_reason:
        flash('Reversal reason is required.', 'error')
        return redirect(url_for('payment.detail', id=id))
    
    try:
        reversal_payment = payment.reverse_payment(current_user.id, reversal_reason)
        
        flash(f'Payment {payment.payment_id} has been reversed. Reversal payment: {reversal_payment.payment_id}', 'warning')
        trigger_metrics_update()
        
    except Exception as e:
        current_app.logger.error(f"Error reversing payment: {e}")
        flash(f'Error reversing payment: {e}', 'error')
        db.session.rollback()
    
    return redirect(url_for('payment.detail', id=id))

@bp.route('/bulk-process', methods=['GET', 'POST'])
@login_required
@requires_role('manager')
def bulk_process():
    """Bulk payment processing (for bank file uploads)"""
    if request.method == 'POST':
        # This would handle CSV/Excel file upload and process multiple payments
        flash('Bulk payment processing will be implemented soon.', 'info')
        return redirect(url_for('payment.list_payments'))
    
    return render_template('payments/bulk_process.html')

@bp.route('/api/loan-details/<int:loan_id>')
@login_required
def api_loan_details(loan_id):
    """API endpoint to get loan details for payment processing"""
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.status != 'active':
        return jsonify({'error': 'Loan is not active'}), 400
    
    # Calculate next EMI details
    next_emi_amount = float(loan.emi_amount)
    overdue_amount = float(loan.get_overdue_amount())
    total_due = next_emi_amount + overdue_amount
    
    # Get payment history
    recent_payments = loan.payments.filter_by(status='completed')\
        .order_by(Payment.payment_date.desc()).limit(5).all()
    
    payment_history = []
    for payment in recent_payments:
        payment_history.append({
            'payment_id': payment.payment_id,
            'amount': float(payment.payment_amount),
            'date': payment.payment_date.isoformat(),
            'type': payment.payment_type,
            'emi_number': payment.emi_number
        })
    
    return jsonify({
        'loan_number': loan.loan_number,
        'customer_name': loan.customer.full_name,
        'outstanding_balance': float(loan.outstanding_balance),
        'emi_amount': next_emi_amount,
        'overdue_amount': overdue_amount,
        'total_due': total_due,
        'next_emi_date': loan.next_emi_date.isoformat() if loan.next_emi_date else None,
        'paid_emis': loan.paid_emis,
        'total_emis': loan.total_emis,
        'payment_history': payment_history
    })

@bp.route('/api/calculate-breakdown', methods=['POST'])
@login_required
def api_calculate_breakdown():
    """API endpoint to calculate payment breakdown"""
    try:
        data = request.get_json()
        loan_id = data.get('loan_id')
        payment_amount = Decimal(str(data.get('payment_amount', 0)))
        
        if payment_amount <= 0:
            return jsonify({'error': 'Payment amount must be positive'}), 400
        
        loan = Loan.query.get(loan_id)
        if not loan:
            return jsonify({'error': 'Loan not found'}), 404
        
        # Calculate interest on outstanding balance
        monthly_rate = float(loan.interest_rate) / 100 / 12
        interest_due = loan.outstanding_balance * Decimal(str(monthly_rate))
        
        # Split payment between interest and principal
        interest_payment = min(payment_amount, interest_due)
        principal_payment = max(Decimal('0'), payment_amount - interest_payment)
        
        # Calculate remaining balance after payment
        remaining_balance = max(Decimal('0'), loan.outstanding_balance - principal_payment)
        
        return jsonify({
            'payment_amount': float(payment_amount),
            'interest_payment': float(interest_payment),
            'principal_payment': float(principal_payment),
            'remaining_balance': float(remaining_balance),
            'current_outstanding': float(loan.outstanding_balance)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/reports/collection-summary')
@login_required
@requires_role('manager')
def collection_summary():
    """Collection summary report"""
    # Get date range from query params
    date_from = request.args.get('date_from', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', date.today().strftime('%Y-%m-%d'))
    
    try:
        from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('payment.list_payments'))
    
    # Get collection summary
    collections = Payment.query.filter(
        db.and_(
            Payment.payment_date >= from_date,
            Payment.payment_date <= to_date,
            Payment.status == 'completed'
        )
    ).all()
    
    # Calculate summaries
    total_collected = sum(float(p.payment_amount) for p in collections)
    total_principal = sum(float(p.principal_amount) for p in collections)
    total_interest = sum(float(p.interest_amount) for p in collections)
    
    # Group by payment method
    method_summary = {}
    for payment in collections:
        method = payment.payment_method
        if method not in method_summary:
            method_summary[method] = {'count': 0, 'amount': 0}
        method_summary[method]['count'] += 1
        method_summary[method]['amount'] += float(payment.payment_amount)
    
    # Group by payment type
    type_summary = {}
    for payment in collections:
        ptype = payment.payment_type
        if ptype not in type_summary:
            type_summary[ptype] = {'count': 0, 'amount': 0}
        type_summary[ptype]['count'] += 1
        type_summary[ptype]['amount'] += float(payment.payment_amount)
    
    summary_data = {
        'date_range': {
            'from': from_date,
            'to': to_date,
            'days': (to_date - from_date).days + 1
        },
        'totals': {
            'collected': total_collected,
            'principal': total_principal,
            'interest': total_interest,
            'count': len(collections)
        },
        'by_method': method_summary,
        'by_type': type_summary,
        'daily_collections': {}
    }
    
    # Calculate daily collections for chart
    current_date = from_date
    while current_date <= to_date:
        daily_amount = sum(
            float(p.payment_amount) for p in collections 
            if p.payment_date == current_date
        )
        summary_data['daily_collections'][current_date.strftime('%Y-%m-%d')] = daily_amount
        current_date += timedelta(days=1)
    
    return render_template('payments/collection_summary.html', 
                         summary=summary_data,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/reports/overdue-collections')
@login_required
@requires_role('manager')
def overdue_collections():
    """Overdue collections report"""
    # Get all active loans with overdue amounts
    active_loans = Loan.query.filter_by(status='active').all()
    overdue_loans = []
    
    total_overdue = Decimal('0')
    
    for loan in active_loans:
        overdue_amount = loan.get_overdue_amount()
        if overdue_amount > 0:
            overdue_loans.append({
                'loan': loan,
                'overdue_amount': overdue_amount,
                'days_overdue': (date.today() - loan.next_emi_date).days if loan.next_emi_date else 0
            })
            total_overdue += overdue_amount
    
    # Sort by overdue amount (highest first)
    overdue_loans.sort(key=lambda x: x['overdue_amount'], reverse=True)
    
    return render_template('payments/overdue_collections.html',
                         overdue_loans=overdue_loans,
                         total_overdue=float(total_overdue))

@bp.route('/api/pending-emis/<int:customer_id>')
@login_required
def api_pending_emis(customer_id):
    """Get pending EMIs for a customer"""
    customer = Customer.query.get_or_404(customer_id)
    active_loans = customer.get_active_loans()
    
    pending_emis = []
    total_pending = Decimal('0')
    
    for loan in active_loans:
        if loan.next_emi_date and loan.next_emi_date <= date.today():
            overdue_amount = loan.get_overdue_amount()
            pending_emis.append({
                'loan_id': loan.id,
                'loan_number': loan.loan_number,
                'emi_amount': float(loan.emi_amount),
                'next_emi_date': loan.next_emi_date.isoformat(),
                'overdue_amount': float(overdue_amount),
                'days_overdue': (date.today() - loan.next_emi_date).days
            })
            total_pending += loan.emi_amount + overdue_amount
    
    return jsonify({
        'pending_emis': pending_emis,
        'total_pending': float(total_pending),
        'customer_name': customer.full_name
    })