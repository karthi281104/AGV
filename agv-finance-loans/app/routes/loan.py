"""
Loan management routes for AGV Finance and Loans
Loan application, approval, disbursement workflow with document uploads
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
import json
from datetime import datetime, date, timedelta
from decimal import Decimal

from app import db
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from app.utils.auth import requires_auth, requires_role
from app.utils.calculations import LoanCalculator, LoanEligibilityCalculator
from app.utils.helpers import (save_uploaded_file, allowed_file, format_currency, 
                              paginate_query, flash_form_errors)
from app.routes.dashboard import trigger_metrics_update

bp = Blueprint('loan', __name__)

@bp.route('/')
@login_required
def list_loans():
    """List all loans with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('LOANS_PER_PAGE', 10)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    loan_type_filter = request.args.get('loan_type', '')
    
    # Build query
    query = Loan.query
    
    if search:
        query = query.join(Customer).filter(
            db.or_(
                Loan.loan_number.ilike(f'%{search}%'),
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if loan_type_filter:
        query = query.filter_by(loan_type=loan_type_filter)
    
    # Order by creation date (newest first)
    query = query.order_by(Loan.created_at.desc())
    
    # Paginate
    loans = paginate_query(query, page, per_page)
    
    return render_template('loans/loan_list.html',
                         loans=loans,
                         search=search,
                         status_filter=status_filter,
                         loan_type_filter=loan_type_filter)

@bp.route('/apply', methods=['GET', 'POST'])
@bp.route('/apply/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def apply(customer_id=None):
    """Loan application form"""
    customer = None
    if customer_id:
        customer = Customer.query.get_or_404(customer_id)
        
        # Check if customer is eligible for loans
        if not customer.can_apply_for_loan():
            flash('Customer is not eligible for loans. Please complete verification and KYC first.', 'error')
            return redirect(url_for('customer.detail', id=customer_id))
    
    if request.method == 'POST':
        try:
            # Get or validate customer
            if not customer_id:
                customer_id = request.form.get('customer_id')
                if not customer_id:
                    flash('Please select a customer.', 'error')
                    return render_template('loans/loan_form.html', customer=customer)
                customer = Customer.query.get_or_404(customer_id)
            
            # Validate required fields
            required_fields = ['loan_type', 'principal_amount', 'interest_rate', 
                             'loan_term_months', 'surety_type']
            
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('loans/loan_form.html', customer=customer)
            
            # Validate amounts
            try:
                principal_amount = Decimal(request.form.get('principal_amount'))
                interest_rate = Decimal(request.form.get('interest_rate'))
                loan_term_months = int(request.form.get('loan_term_months'))
                
                if principal_amount <= 0:
                    flash('Principal amount must be positive.', 'error')
                    return render_template('loans/loan_form.html', customer=customer)
                
                if interest_rate < 0:
                    flash('Interest rate cannot be negative.', 'error')
                    return render_template('loans/loan_form.html', customer=customer)
                
                if loan_term_months <= 0:
                    flash('Loan term must be positive.', 'error')
                    return render_template('loans/loan_form.html', customer=customer)
                
            except (ValueError, TypeError):
                flash('Invalid amount or term values.', 'error')
                return render_template('loans/loan_form.html', customer=customer)
            
            # Check loan eligibility
            if customer.monthly_income:
                existing_emi = customer.get_monthly_emi_total()
                max_eligible = LoanEligibilityCalculator.calculate_max_loan_amount(
                    float(customer.monthly_income), float(existing_emi), 
                    float(interest_rate), loan_term_months
                )
                
                if float(principal_amount) > max_eligible:
                    flash(f'Loan amount exceeds eligibility. Maximum eligible: {format_currency(max_eligible)}', 'warning')
            
            # Generate loan number
            loan_number = Loan.generate_loan_number()
            
            # Create loan
            loan = Loan(
                loan_number=loan_number,
                customer_id=customer.id,
                loan_type=request.form.get('loan_type'),
                principal_amount=principal_amount,
                interest_rate=interest_rate,
                loan_term_months=loan_term_months,
                surety_type=request.form.get('surety_type'),
                surety_value=request.form.get('surety_value') or None,
                guarantor_name=request.form.get('guarantor_name'),
                guarantor_phone=request.form.get('guarantor_phone'),
                guarantor_relationship=request.form.get('guarantor_relationship'),
                guarantor_income=request.form.get('guarantor_income') or None,
                processing_fee=request.form.get('processing_fee') or 0,
                insurance_amount=request.form.get('insurance_amount') or 0,
                other_charges=request.form.get('other_charges') or 0,
                created_by=current_user.id
            )
            
            # Calculate EMI and other amounts
            loan.update_calculations()
            
            # Handle document uploads
            uploaded_documents = []
            document_fields = ['income_proof', 'address_proof', 'bank_statement', 
                             'property_document', 'guarantor_document']
            
            for field in document_fields:
                if field in request.files:
                    file = request.files[field]
                    if file and file.filename:
                        doc_path = save_uploaded_file(file, 'documents')
                        if doc_path:
                            uploaded_documents.append({
                                'type': field,
                                'path': doc_path,
                                'filename': file.filename
                            })
            
            if uploaded_documents:
                loan.documents_uploaded = json.dumps(uploaded_documents)
            
            # Set required documents list
            required_docs = ['income_proof', 'address_proof', 'bank_statement']
            if loan.loan_type in ['Home', 'Property']:
                required_docs.append('property_document')
            if loan.guarantor_name:
                required_docs.append('guarantor_document')
            
            loan.documents_required = json.dumps(required_docs)
            
            db.session.add(loan)
            db.session.commit()
            
            flash(f'Loan application #{loan.loan_number} submitted successfully!', 'success')
            trigger_metrics_update()
            return redirect(url_for('loan.detail', id=loan.id))
            
        except Exception as e:
            current_app.logger.error(f"Error creating loan: {e}")
            flash('An error occurred while processing the loan application.', 'error')
            db.session.rollback()
    
    # Get customers for dropdown (if customer not pre-selected)
    customers = []
    if not customer:
        customers = Customer.query.filter_by(status='active', verification_status='verified')\
            .order_by(Customer.first_name).all()
    
    return render_template('loans/loan_form.html', 
                         customer=customer, 
                         customers=customers)

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Loan detail page"""
    loan = Loan.query.get_or_404(id)
    
    # Get loan payments
    payments = loan.payments.order_by(Payment.payment_date.desc()).all()
    
    # Get amortization schedule if loan is active
    schedule = []
    if loan.status in ['active', 'disbursed'] and loan.disbursement_date:
        try:
            schedule = LoanCalculator.generate_amortization_schedule(
                float(loan.principal_amount),
                float(loan.interest_rate),
                loan.loan_term_months,
                loan.first_emi_date
            )
        except:
            pass
    
    # Parse documents
    required_docs = []
    uploaded_docs = []
    
    if loan.documents_required:
        try:
            required_docs = json.loads(loan.documents_required)
        except:
            pass
    
    if loan.documents_uploaded:
        try:
            uploaded_docs = json.loads(loan.documents_uploaded)
        except:
            pass
    
    return render_template('loans/loan_detail.html',
                         loan=loan,
                         payments=payments,
                         schedule=schedule,
                         required_docs=required_docs,
                         uploaded_docs=uploaded_docs)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit loan (only for pending loans)"""
    loan = Loan.query.get_or_404(id)
    
    # Check permissions
    if loan.status != 'pending':
        flash('Only pending loans can be edited.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    if not current_user.is_manager() and loan.created_by != current_user.id:
        flash('You do not have permission to edit this loan.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    if request.method == 'POST':
        try:
            # Update editable fields
            loan.loan_type = request.form.get('loan_type', loan.loan_type)
            
            # Update amounts if changed
            new_principal = Decimal(request.form.get('principal_amount', loan.principal_amount))
            new_rate = Decimal(request.form.get('interest_rate', loan.interest_rate))
            new_term = int(request.form.get('loan_term_months', loan.loan_term_months))
            
            if (new_principal != loan.principal_amount or 
                new_rate != loan.interest_rate or 
                new_term != loan.loan_term_months):
                
                loan.principal_amount = new_principal
                loan.interest_rate = new_rate
                loan.loan_term_months = new_term
                loan.update_calculations()
            
            # Update guarantor information
            loan.guarantor_name = request.form.get('guarantor_name', loan.guarantor_name)
            loan.guarantor_phone = request.form.get('guarantor_phone', loan.guarantor_phone)
            loan.guarantor_relationship = request.form.get('guarantor_relationship', loan.guarantor_relationship)
            loan.guarantor_income = request.form.get('guarantor_income') or loan.guarantor_income
            
            db.session.commit()
            flash('Loan updated successfully!', 'success')
            return redirect(url_for('loan.detail', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error updating loan: {e}")
            flash('An error occurred while updating the loan.', 'error')
            db.session.rollback()
    
    return render_template('loans/edit_loan.html', loan=loan)

@bp.route('/<int:id>/approve', methods=['POST'])
@login_required
@requires_role('admin')
def approve(id):
    """Approve loan"""
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'pending':
        flash('Only pending loans can be approved.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    approval_notes = request.form.get('approval_notes')
    
    try:
        loan.approve_loan(current_user.id, approval_notes)
        db.session.commit()
        
        flash(f'Loan #{loan.loan_number} has been approved!', 'success')
        trigger_metrics_update()
        
    except Exception as e:
        current_app.logger.error(f"Error approving loan: {e}")
        flash('An error occurred while approving the loan.', 'error')
        db.session.rollback()
    
    return redirect(url_for('loan.detail', id=id))

@bp.route('/<int:id>/reject', methods=['POST'])
@login_required
@requires_role('admin')
def reject(id):
    """Reject loan"""
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'pending':
        flash('Only pending loans can be rejected.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    rejection_reason = request.form.get('rejection_reason')
    if not rejection_reason:
        flash('Rejection reason is required.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    try:
        loan.status = 'rejected'
        loan.rejection_reason = rejection_reason
        loan.approved_by = current_user.id
        loan.approval_date = date.today()
        
        db.session.commit()
        
        flash(f'Loan #{loan.loan_number} has been rejected.', 'warning')
        trigger_metrics_update()
        
    except Exception as e:
        current_app.logger.error(f"Error rejecting loan: {e}")
        flash('An error occurred while rejecting the loan.', 'error')
        db.session.rollback()
    
    return redirect(url_for('loan.detail', id=id))

@bp.route('/<int:id>/disburse', methods=['POST'])
@login_required
@requires_role('manager')
def disburse(id):
    """Disburse approved loan"""
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'approved':
        flash('Only approved loans can be disbursed.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    try:
        disbursement_amount = request.form.get('disbursement_amount')
        if disbursement_amount:
            disbursement_amount = Decimal(disbursement_amount)
        else:
            disbursement_amount = loan.principal_amount
        
        loan.disburse_loan(disbursement_amount)
        db.session.commit()
        
        flash(f'Loan #{loan.loan_number} has been disbursed successfully!', 'success')
        trigger_metrics_update()
        
    except Exception as e:
        current_app.logger.error(f"Error disbursing loan: {e}")
        flash(f'An error occurred while disbursing the loan: {e}', 'error')
        db.session.rollback()
    
    return redirect(url_for('loan.detail', id=id))

@bp.route('/<int:id>/close', methods=['POST'])
@login_required
@requires_role('manager')
def close_loan(id):
    """Close loan (mark as completed)"""
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'active':
        flash('Only active loans can be closed.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    if loan.outstanding_balance > 0:
        flash('Loan cannot be closed with outstanding balance.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    try:
        loan.status = 'closed'
        db.session.commit()
        
        flash(f'Loan #{loan.loan_number} has been closed successfully!', 'success')
        trigger_metrics_update()
        
    except Exception as e:
        current_app.logger.error(f"Error closing loan: {e}")
        flash('An error occurred while closing the loan.', 'error')
        db.session.rollback()
    
    return redirect(url_for('loan.detail', id=id))

@bp.route('/<int:id>/upload-document', methods=['POST'])
@login_required
def upload_document(id):
    """Upload additional document for loan"""
    loan = Loan.query.get_or_404(id)
    
    if 'document' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    file = request.files['document']
    document_type = request.form.get('document_type', 'other')
    
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('loan.detail', id=id))
    
    if file and allowed_file(file.filename):
        doc_path = save_uploaded_file(file, 'documents')
        if doc_path:
            # Add to existing documents
            existing_docs = []
            if loan.documents_uploaded:
                try:
                    existing_docs = json.loads(loan.documents_uploaded)
                except:
                    pass
            
            existing_docs.append({
                'type': document_type,
                'path': doc_path,
                'filename': file.filename,
                'uploaded_at': datetime.utcnow().isoformat()
            })
            
            loan.documents_uploaded = json.dumps(existing_docs)
            db.session.commit()
            
            flash('Document uploaded successfully!', 'success')
        else:
            flash('Failed to upload document.', 'error')
    else:
        flash('Invalid file type.', 'error')
    
    return redirect(url_for('loan.detail', id=id))

@bp.route('/api/calculate-emi', methods=['POST'])
@login_required
def api_calculate_emi():
    """API endpoint for EMI calculation"""
    try:
        data = request.get_json()
        
        principal = float(data.get('principal', 0))
        interest_rate = float(data.get('interest_rate', 0))
        tenure_months = int(data.get('tenure_months', 0))
        
        if principal <= 0 or interest_rate < 0 or tenure_months <= 0:
            return jsonify({'error': 'Invalid input parameters'}), 400
        
        emi = LoanCalculator.calculate_emi(principal, interest_rate, tenure_months)
        total_amount = LoanCalculator.calculate_total_amount(principal, interest_rate, tenure_months)
        total_interest = LoanCalculator.calculate_total_interest(principal, interest_rate, tenure_months)
        
        return jsonify({
            'emi': float(emi),
            'total_amount': float(total_amount),
            'total_interest': float(total_interest)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/check-eligibility', methods=['POST'])
@login_required
def api_check_eligibility():
    """API endpoint for loan eligibility check"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        loan_amount = float(data.get('loan_amount', 0))
        interest_rate = float(data.get('interest_rate', 10))
        tenure_months = int(data.get('tenure_months', 240))
        
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        if not customer.monthly_income:
            return jsonify({'error': 'Customer monthly income not available'}), 400
        
        existing_emi = customer.get_monthly_emi_total()
        max_eligible = LoanEligibilityCalculator.calculate_max_loan_amount(
            float(customer.monthly_income), float(existing_emi), 
            interest_rate, tenure_months
        )
        
        is_eligible = loan_amount <= max_eligible
        
        return jsonify({
            'eligible': is_eligible,
            'max_eligible_amount': max_eligible,
            'requested_amount': loan_amount,
            'monthly_income': float(customer.monthly_income),
            'existing_emi': float(existing_emi),
            'available_income': float(customer.monthly_income) * 0.5 - float(existing_emi)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/reports/pending-approvals')
@login_required
@requires_role('admin')
def pending_approvals():
    """Report of pending loan approvals"""
    pending_loans = Loan.query.filter_by(status='pending')\
        .order_by(Loan.created_at.asc()).all()
    
    return render_template('loans/pending_approvals.html', loans=pending_loans)

@bp.route('/reports/overdue-loans')
@login_required
@requires_role('manager')
def overdue_loans():
    """Report of overdue loans"""
    active_loans = Loan.query.filter_by(status='active').all()
    overdue_loans = [loan for loan in active_loans if loan.is_overdue()]
    
    return render_template('loans/overdue_loans.html', loans=overdue_loans)