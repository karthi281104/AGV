from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.loan import Loan
from app.models.customer import Customer
from app.models.payment import Payment
from app.utils.helpers import allowed_file, save_uploaded_file
from app.utils.calculations import calculate_emi
import os
from datetime import datetime, timedelta
import json

bp = Blueprint('loan', __name__)

@bp.route('/')
@login_required
def list_loans():
    """List all loans with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    loan_type = request.args.get('type', '', type=str)
    search = request.args.get('search', '', type=str)
    per_page = 20
    
    # Build query
    query = Loan.query.join(Customer)
    
    # Apply filters
    if status:
        query = query.filter(Loan.status == status)
    
    if loan_type:
        query = query.filter(Loan.loan_type == loan_type)
    
    if search:
        query = query.filter(
            db.or_(
                Loan.loan_id.contains(search),
                Customer.name.contains(search),
                Customer.phone.contains(search)
            )
        )
    
    loans = query.order_by(Loan.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    loan_types = db.session.query(Loan.loan_type).distinct().all()
    loan_types = [lt[0] for lt in loan_types]
    
    return render_template('loans/loan_list.html', 
                         loans=loans,
                         status=status,
                         loan_type=loan_type,
                         search=search,
                         loan_types=loan_types)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_loan():
    """Add new loan application."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('loan.list_loans'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['customer_id', 'principal_amount', 'interest_rate', 'term_months', 'loan_type']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('loans/loan_form.html')
            
            # Validate customer exists
            customer = Customer.query.get(request.form.get('customer_id'))
            if not customer:
                flash('Selected customer does not exist.', 'error')
                return render_template('loans/loan_form.html')
            
            # Handle document uploads
            document_paths = []
            if 'documents' in request.files:
                files = request.files.getlist('documents')
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        file_path = save_uploaded_file(file, 'documents')
                        document_paths.append(file_path)
            
            # Create loan
            loan = Loan(
                customer_id=int(request.form.get('customer_id')),
                principal_amount=float(request.form.get('principal_amount')),
                interest_rate=float(request.form.get('interest_rate')),
                term_months=int(request.form.get('term_months')),
                loan_type=request.form.get('loan_type'),
                surety_name=request.form.get('surety_name') or None,
                surety_phone=request.form.get('surety_phone') or None,
                surety_address=request.form.get('surety_address') or None,
                collateral_details=request.form.get('collateral_details') or None,
                purpose=request.form.get('purpose') or None,
                created_by=current_user.id
            )
            
            # Set documents
            if document_paths:
                loan.set_documents(document_paths)
            
            # Calculate EMI
            loan.emi_amount = loan.calculate_emi()
            
            db.session.add(loan)
            db.session.commit()
            
            flash(f'Loan application created successfully with ID: {loan.loan_id}', 'success')
            return redirect(url_for('loan.view_loan', id=loan.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to create loan application. Please try again.', 'error')
            current_app.logger.error(f'Add loan error: {str(e)}')
    
    # Get customers for dropdown
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name).all()
    
    return render_template('loans/loan_form.html', customers=customers)

@bp.route('/<int:id>')
@login_required
def view_loan(id):
    """View loan details."""
    loan = Loan.query.get_or_404(id)
    
    # Get payment history
    payments = loan.payments.order_by(Payment.payment_date.desc()).all()
    
    # Calculate payment schedule
    payment_schedule = generate_payment_schedule(loan)
    
    return render_template('loans/loan_detail.html', 
                         loan=loan,
                         payments=payments,
                         payment_schedule=payment_schedule)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_loan(id):
    """Edit loan details (only before disbursement)."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'pending':
        flash('Can only edit pending loans.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    if request.method == 'POST':
        try:
            # Update loan details
            loan.principal_amount = float(request.form.get('principal_amount'))
            loan.interest_rate = float(request.form.get('interest_rate'))
            loan.term_months = int(request.form.get('term_months'))
            loan.loan_type = request.form.get('loan_type')
            loan.surety_name = request.form.get('surety_name') or None
            loan.surety_phone = request.form.get('surety_phone') or None
            loan.surety_address = request.form.get('surety_address') or None
            loan.collateral_details = request.form.get('collateral_details') or None
            loan.purpose = request.form.get('purpose') or None
            
            # Recalculate EMI
            loan.emi_amount = loan.calculate_emi()
            
            # Handle additional document uploads
            if 'documents' in request.files:
                files = request.files.getlist('documents')
                existing_docs = loan.get_documents()
                
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        file_path = save_uploaded_file(file, 'documents')
                        existing_docs.append(file_path)
                
                loan.set_documents(existing_docs)
            
            db.session.commit()
            
            flash('Loan details updated successfully.', 'success')
            return redirect(url_for('loan.view_loan', id=loan.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update loan. Please try again.', 'error')
            current_app.logger.error(f'Edit loan error: {str(e)}')
    
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name).all()
    return render_template('loans/edit_loan.html', loan=loan, customers=customers)

@bp.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve_loan(id):
    """Approve loan application."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'pending':
        flash('Can only approve pending loans.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    try:
        loan.status = 'approved'
        loan.approved_by = current_user.id
        
        db.session.commit()
        
        flash('Loan approved successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to approve loan.', 'error')
        current_app.logger.error(f'Approve loan error: {str(e)}')
    
    return redirect(url_for('loan.view_loan', id=id))

@bp.route('/<int:id>/disburse', methods=['GET', 'POST'])
@login_required
def disburse_loan(id):
    """Disburse approved loan."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'approved':
        flash('Can only disburse approved loans.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    if request.method == 'POST':
        try:
            disbursement_date = request.form.get('disbursement_date')
            if disbursement_date:
                loan.disbursed_date = datetime.strptime(disbursement_date, '%Y-%m-%d').date()
            else:
                loan.disbursed_date = datetime.now().date()
            
            # Calculate maturity date
            loan.maturity_date = loan.disbursed_date + timedelta(days=30 * loan.term_months)
            
            loan.status = 'disbursed'
            loan.disbursed_by = current_user.id
            
            db.session.commit()
            
            flash(f'Loan disbursed successfully on {loan.disbursed_date}.', 'success')
            return redirect(url_for('loan.view_loan', id=loan.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to disburse loan.', 'error')
            current_app.logger.error(f'Disburse loan error: {str(e)}')
    
    return render_template('loans/disburse_loan.html', loan=loan)

@bp.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject_loan(id):
    """Reject loan application."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    loan = Loan.query.get_or_404(id)
    
    if loan.status not in ['pending', 'approved']:
        flash('Can only reject pending or approved loans.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    try:
        loan.status = 'rejected'
        
        db.session.commit()
        
        flash('Loan rejected.', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to reject loan.', 'error')
        current_app.logger.error(f'Reject loan error: {str(e)}')
    
    return redirect(url_for('loan.view_loan', id=id))

@bp.route('/<int:id>/close', methods=['POST'])
@login_required
def close_loan(id):
    """Close loan (mark as fully paid)."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'disbursed':
        flash('Can only close disbursed loans.', 'error')
        return redirect(url_for('loan.view_loan', id=id))
    
    try:
        outstanding_balance = loan.get_outstanding_balance()
        
        if outstanding_balance > 0:
            flash(f'Cannot close loan with outstanding balance of ₹{outstanding_balance:.2f}', 'error')
            return redirect(url_for('loan.view_loan', id=id))
        
        loan.status = 'closed'
        
        db.session.commit()
        
        flash('Loan closed successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to close loan.', 'error')
        current_app.logger.error(f'Close loan error: {str(e)}')
    
    return redirect(url_for('loan.view_loan', id=id))

@bp.route('/api/calculate-emi', methods=['POST'])
@login_required
def api_calculate_emi():
    """API endpoint for EMI calculation."""
    try:
        data = request.get_json()
        principal = float(data.get('principal', 0))
        rate = float(data.get('rate', 0))
        tenure = int(data.get('tenure', 0))
        
        if principal <= 0 or rate <= 0 or tenure <= 0:
            return jsonify({'error': 'Invalid input values'}), 400
        
        emi_result = calculate_emi(principal, rate, tenure)
        
        return jsonify({
            'success': True,
            'emi': emi_result['emi'],
            'total_amount': emi_result['total_amount'],
            'total_interest': emi_result['total_interest']
        })
    
    except Exception as e:
        return jsonify({'error': 'Calculation failed'}), 500

def generate_payment_schedule(loan):
    """Generate payment schedule for a loan."""
    if not loan.disbursed_date:
        return []
    
    schedule = []
    balance = float(loan.principal_amount)
    monthly_rate = float(loan.interest_rate) / 100 / 12
    emi = loan.calculate_emi()
    
    for month in range(1, loan.term_months + 1):
        due_date = loan.disbursed_date + timedelta(days=30 * month)
        
        interest_payment = balance * monthly_rate
        principal_payment = emi - interest_payment
        balance -= principal_payment
        
        # Check if payment was made
        payment_made = Payment.query.filter(
            Payment.loan_id == loan.id,
            Payment.payment_date >= due_date - timedelta(days=15),
            Payment.payment_date <= due_date + timedelta(days=15)
        ).first()
        
        schedule.append({
            'month': month,
            'due_date': due_date,
            'emi': emi,
            'principal': max(0, principal_payment),
            'interest': interest_payment,
            'balance': max(0, balance),
            'payment_made': payment_made.to_dict() if payment_made else None,
            'status': 'paid' if payment_made else ('overdue' if due_date < datetime.now().date() else 'pending')
        })
    
    return schedule