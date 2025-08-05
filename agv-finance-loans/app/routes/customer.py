"""
Customer management routes for AGV Finance and Loans
CRUD operations with biometric enrollment and document management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import json
from datetime import datetime

from app import db
from app.models.customer import Customer
from app.models.loan import Loan
from app.models.payment import Payment
from app.utils.auth import requires_auth, requires_role
from app.utils.helpers import (save_uploaded_file, allowed_file, format_currency, 
                              validate_email, validate_phone, validate_pan, 
                              validate_aadhaar, paginate_query, flash_form_errors)

bp = Blueprint('customer', __name__)

@bp.route('/')
@login_required
def list_customers():
    """List all customers with pagination and search"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('CUSTOMERS_PER_PAGE', 15)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    verification_filter = request.args.get('verification', '')
    
    # Build query
    query = Customer.query
    
    if search:
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone_primary.ilike(f'%{search}%'),
                Customer.id_number.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if verification_filter:
        query = query.filter_by(verification_status=verification_filter)
    
    # Order by creation date (newest first)
    query = query.order_by(Customer.created_at.desc())
    
    # Paginate
    customers = paginate_query(query, page, per_page)
    
    return render_template('customers/customer_list.html', 
                         customers=customers,
                         search=search,
                         status_filter=status_filter,
                         verification_filter=verification_filter)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """Add new customer"""
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 
                             'email', 'phone_primary', 'address_line1', 'city', 
                             'state', 'postal_code', 'id_type', 'id_number']
            
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('customers/add_customer.html')
            
            # Validate email format
            email = request.form.get('email')
            if not validate_email(email):
                flash('Invalid email format.', 'error')
                return render_template('customers/add_customer.html')
            
            # Check if email already exists
            if Customer.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return render_template('customers/add_customer.html')
            
            # Validate phone number
            phone = request.form.get('phone_primary')
            if not validate_phone(phone):
                flash('Invalid phone number format.', 'error')
                return render_template('customers/add_customer.html')
            
            # Validate ID number
            id_type = request.form.get('id_type')
            id_number = request.form.get('id_number')
            
            if id_type == 'PAN' and not validate_pan(id_number):
                flash('Invalid PAN number format.', 'error')
                return render_template('customers/add_customer.html')
            elif id_type == 'Aadhaar' and not validate_aadhaar(id_number):
                flash('Invalid Aadhaar number format.', 'error')
                return render_template('customers/add_customer.html')
            
            # Check if ID number already exists
            if Customer.query.filter_by(id_number=id_number).first():
                flash('ID number already registered.', 'error')
                return render_template('customers/add_customer.html')
            
            # Create customer
            customer = Customer(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                middle_name=request.form.get('middle_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=request.form.get('gender'),
                marital_status=request.form.get('marital_status'),
                email=email,
                phone_primary=phone,
                phone_secondary=request.form.get('phone_secondary'),
                address_line1=request.form.get('address_line1'),
                address_line2=request.form.get('address_line2'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                postal_code=request.form.get('postal_code'),
                country=request.form.get('country', 'India'),
                id_type=id_type,
                id_number=id_number,
                employment_status=request.form.get('employment_status'),
                employer_name=request.form.get('employer_name'),
                job_title=request.form.get('job_title'),
                monthly_income=request.form.get('monthly_income') or None,
                employment_duration_years=request.form.get('employment_duration_years') or None,
                bank_name=request.form.get('bank_name'),
                bank_account_number=request.form.get('bank_account_number'),
                bank_ifsc=request.form.get('bank_ifsc'),
                credit_score=request.form.get('credit_score') or None,
                created_by=current_user.id
            )
            
            # Handle document upload
            uploaded_documents = []
            if 'id_document' in request.files:
                id_file = request.files['id_document']
                if id_file and id_file.filename:
                    doc_path = save_uploaded_file(id_file, 'documents')
                    if doc_path:
                        customer.id_document_path = doc_path
                        uploaded_documents.append(doc_path)
            
            # Handle additional documents
            for i in range(5):  # Allow up to 5 additional documents
                file_key = f'additional_document_{i}'
                if file_key in request.files:
                    doc_file = request.files[file_key]
                    if doc_file and doc_file.filename:
                        doc_path = save_uploaded_file(doc_file, 'documents')
                        if doc_path:
                            uploaded_documents.append(doc_path)
            
            if uploaded_documents:
                customer.documents_uploaded = json.dumps(uploaded_documents)
            
            db.session.add(customer)
            db.session.commit()
            
            flash(f'Customer {customer.full_name} has been added successfully!', 'success')
            return redirect(url_for('customer.detail', id=customer.id))
            
        except ValueError as e:
            flash(f'Invalid date format: {e}', 'error')
        except Exception as e:
            current_app.logger.error(f"Error adding customer: {e}")
            flash('An error occurred while adding the customer.', 'error')
            db.session.rollback()
    
    return render_template('customers/add_customer.html')

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Customer detail page"""
    customer = Customer.query.get_or_404(id)
    
    # Get customer's loans
    loans = customer.loans.order_by(Loan.created_at.desc()).all()
    
    # Get recent payments
    recent_payments = Payment.query.filter_by(customer_id=id)\
        .order_by(Payment.payment_date.desc()).limit(10).all()
    
    # Calculate summary statistics
    total_loans = len(loans)
    active_loans = len([loan for loan in loans if loan.status == 'active'])
    total_disbursed = sum(float(loan.disbursed_amount or 0) for loan in loans)
    total_outstanding = customer.get_total_outstanding_amount()
    
    summary = {
        'total_loans': total_loans,
        'active_loans': active_loans,
        'total_disbursed': total_disbursed,
        'total_outstanding': float(total_outstanding),
        'monthly_emi': float(customer.get_monthly_emi_total())
    }
    
    return render_template('customers/customer_detail.html',
                         customer=customer,
                         loans=loans,
                         payments=recent_payments,
                         summary=summary)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit customer"""
    customer = Customer.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_manager() and customer.created_by != current_user.id:
        flash('You do not have permission to edit this customer.', 'error')
        return redirect(url_for('customer.detail', id=id))
    
    if request.method == 'POST':
        try:
            # Update customer fields
            customer.first_name = request.form.get('first_name', customer.first_name)
            customer.last_name = request.form.get('last_name', customer.last_name)
            customer.middle_name = request.form.get('middle_name', customer.middle_name)
            customer.phone_primary = request.form.get('phone_primary', customer.phone_primary)
            customer.phone_secondary = request.form.get('phone_secondary', customer.phone_secondary)
            customer.address_line1 = request.form.get('address_line1', customer.address_line1)
            customer.address_line2 = request.form.get('address_line2', customer.address_line2)
            customer.city = request.form.get('city', customer.city)
            customer.state = request.form.get('state', customer.state)
            customer.postal_code = request.form.get('postal_code', customer.postal_code)
            customer.employment_status = request.form.get('employment_status', customer.employment_status)
            customer.employer_name = request.form.get('employer_name', customer.employer_name)
            customer.job_title = request.form.get('job_title', customer.job_title)
            
            # Update financial information
            if request.form.get('monthly_income'):
                customer.monthly_income = float(request.form.get('monthly_income'))
            if request.form.get('employment_duration_years'):
                customer.employment_duration_years = int(request.form.get('employment_duration_years'))
            if request.form.get('credit_score'):
                customer.credit_score = int(request.form.get('credit_score'))
            
            customer.bank_name = request.form.get('bank_name', customer.bank_name)
            customer.bank_account_number = request.form.get('bank_account_number', customer.bank_account_number)
            customer.bank_ifsc = request.form.get('bank_ifsc', customer.bank_ifsc)
            
            db.session.commit()
            flash('Customer information updated successfully!', 'success')
            return redirect(url_for('customer.detail', id=id))
            
        except Exception as e:
            current_app.logger.error(f"Error updating customer: {e}")
            flash('An error occurred while updating the customer.', 'error')
            db.session.rollback()
    
    return render_template('customers/edit_customer.html', customer=customer)

@bp.route('/<int:id>/verify', methods=['POST'])
@login_required
@requires_role('manager')
def verify(id):
    """Verify customer"""
    customer = Customer.query.get_or_404(id)
    
    verification_status = request.form.get('verification_status')
    notes = request.form.get('verification_notes')
    
    if verification_status in ['verified', 'rejected']:
        customer.verification_status = verification_status
        customer.verification_notes = notes
        customer.verified_by = current_user.id
        customer.verified_at = datetime.utcnow()
        
        if verification_status == 'verified':
            customer.kyc_status = 'completed'
        
        db.session.commit()
        flash(f'Customer has been {verification_status}!', 'success')
    else:
        flash('Invalid verification status.', 'error')
    
    return redirect(url_for('customer.detail', id=id))

@bp.route('/<int:id>/biometric-enroll')
@login_required
def biometric_enroll(id):
    """Biometric enrollment page"""
    customer = Customer.query.get_or_404(id)
    
    if customer.biometric_enrolled:
        flash('Customer biometric data already enrolled.', 'info')
        return redirect(url_for('customer.detail', id=id))
    
    return render_template('customers/biometric_enroll.html', customer=customer)

@bp.route('/api/<int:id>/biometric-enroll', methods=['POST'])
@login_required
def api_biometric_enroll(id):
    """API endpoint for biometric enrollment"""
    customer = Customer.query.get_or_404(id)
    
    try:
        biometric_data = request.get_json()
        
        # In a real implementation, you would process and encrypt the biometric data
        # For now, we'll just mark as enrolled
        customer.fingerprint_data = json.dumps(biometric_data.get('fingerprint', {}))
        customer.face_recognition_data = json.dumps(biometric_data.get('face', {}))
        customer.biometric_enrolled = True
        customer.biometric_enrollment_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Biometric enrollment successful'})
        
    except Exception as e:
        current_app.logger.error(f"Biometric enrollment error: {e}")
        return jsonify({'success': False, 'error': 'Enrollment failed'}), 500

@bp.route('/<int:id>/documents')
@login_required
def documents(id):
    """Customer documents page"""
    customer = Customer.query.get_or_404(id)
    
    # Parse uploaded documents
    documents = []
    if customer.documents_uploaded:
        try:
            doc_paths = json.loads(customer.documents_uploaded)
            for path in doc_paths:
                documents.append({
                    'path': path,
                    'filename': path.split('/')[-1],
                    'type': path.split('.')[-1].upper()
                })
        except:
            pass
    
    return render_template('customers/documents.html', customer=customer, documents=documents)

@bp.route('/<int:id>/upload-document', methods=['POST'])
@login_required
def upload_document(id):
    """Upload additional document"""
    customer = Customer.query.get_or_404(id)
    
    if 'document' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('customer.documents', id=id))
    
    file = request.files['document']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('customer.documents', id=id))
    
    if file and allowed_file(file.filename):
        doc_path = save_uploaded_file(file, 'documents')
        if doc_path:
            # Add to existing documents
            existing_docs = []
            if customer.documents_uploaded:
                try:
                    existing_docs = json.loads(customer.documents_uploaded)
                except:
                    pass
            
            existing_docs.append(doc_path)
            customer.documents_uploaded = json.dumps(existing_docs)
            
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
        else:
            flash('Failed to upload document.', 'error')
    else:
        flash('Invalid file type.', 'error')
    
    return redirect(url_for('customer.documents', id=id))

@bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for customer search"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify([])
    
    customers = Customer.query.filter(
        db.or_(
            Customer.first_name.ilike(f'%{query}%'),
            Customer.last_name.ilike(f'%{query}%'),
            Customer.email.ilike(f'%{query}%'),
            Customer.phone_primary.ilike(f'%{query}%'),
            Customer.id_number.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.full_name,
            'email': customer.email,
            'phone': customer.phone_primary,
            'status': customer.status,
            'verification_status': customer.verification_status
        })
    
    return jsonify(results)

@bp.route('/export')
@login_required
@requires_role('manager')
def export():
    """Export customers to CSV"""
    # This would implement CSV export functionality
    # For now, return a simple message
    flash('Export functionality will be implemented soon.', 'info')
    return redirect(url_for('customer.list_customers'))