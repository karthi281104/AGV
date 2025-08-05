from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.customer import Customer
from app.models.loan import Loan
from app.utils.helpers import allowed_file, save_uploaded_file
import os
from datetime import datetime
import json

bp = Blueprint('customer', __name__)

@bp.route('/')
@login_required
def list_customers():
    """List all customers with search and pagination."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    per_page = 20
    
    # Build query
    query = Customer.query
    
    if search:
        query = query.filter(
            db.or_(
                Customer.name.contains(search),
                Customer.phone.contains(search),
                Customer.customer_id.contains(search),
                Customer.email.contains(search)
            )
        )
    
    customers = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('customers/customer_list.html', 
                         customers=customers, 
                         search=search)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """Add new customer."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('customer.list_customers'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'phone', 'address', 'aadhar_number']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('customers/add_customer.html')
            
            # Check if Aadhar number already exists
            existing_customer = Customer.query.filter_by(
                aadhar_number=request.form.get('aadhar_number')
            ).first()
            
            if existing_customer:
                flash('A customer with this Aadhar number already exists.', 'error')
                return render_template('customers/add_customer.html')
            
            # Handle photo upload
            photo_path = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    photo_path = save_uploaded_file(file, 'customers')
            
            # Parse date of birth
            dob = None
            if request.form.get('date_of_birth'):
                try:
                    dob = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date of birth format.', 'error')
                    return render_template('customers/add_customer.html')
            
            # Create customer
            customer = Customer(
                name=request.form.get('name'),
                phone=request.form.get('phone'),
                email=request.form.get('email') or None,
                address=request.form.get('address'),
                aadhar_number=request.form.get('aadhar_number'),
                pan_number=request.form.get('pan_number') or None,
                photo_path=photo_path,
                date_of_birth=dob,
                occupation=request.form.get('occupation') or None,
                annual_income=float(request.form.get('annual_income')) if request.form.get('annual_income') else None
            )
            
            db.session.add(customer)
            db.session.commit()
            
            flash(f'Customer {customer.name} added successfully with ID: {customer.customer_id}', 'success')
            return redirect(url_for('customer.view_customer', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to add customer. Please try again.', 'error')
            current_app.logger.error(f'Add customer error: {str(e)}')
    
    return render_template('customers/add_customer.html')

@bp.route('/<int:id>')
@login_required
def view_customer(id):
    """View customer details."""
    customer = Customer.query.get_or_404(id)
    
    # Get customer's loan history
    loans = customer.loans.order_by(Loan.created_at.desc()).all()
    
    # Calculate summary statistics
    total_loans = len(loans)
    active_loans = len([l for l in loans if l.status == 'disbursed'])
    total_disbursed = sum(float(l.principal_amount) for l in loans if l.status == 'disbursed')
    outstanding_amount = customer.get_outstanding_amount()
    
    stats = {
        'total_loans': total_loans,
        'active_loans': active_loans,
        'total_disbursed': total_disbursed,
        'outstanding_amount': outstanding_amount
    }
    
    return render_template('customers/customer_detail.html', 
                         customer=customer, 
                         loans=loans,
                         stats=stats)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    """Edit customer details."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('customer.view_customer', id=id))
    
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'phone', 'address']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('customers/edit_customer.html', customer=customer)
            
            # Check if Aadhar number is being changed and if it already exists
            new_aadhar = request.form.get('aadhar_number')
            if new_aadhar != customer.aadhar_number:
                existing_customer = Customer.query.filter_by(aadhar_number=new_aadhar).first()
                if existing_customer:
                    flash('A customer with this Aadhar number already exists.', 'error')
                    return render_template('customers/edit_customer.html', customer=customer)
            
            # Handle photo upload
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old photo if exists
                    if customer.photo_path:
                        old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], customer.photo_path)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    customer.photo_path = save_uploaded_file(file, 'customers')
            
            # Parse date of birth
            if request.form.get('date_of_birth'):
                try:
                    customer.date_of_birth = datetime.strptime(
                        request.form.get('date_of_birth'), '%Y-%m-%d'
                    ).date()
                except ValueError:
                    flash('Invalid date of birth format.', 'error')
                    return render_template('customers/edit_customer.html', customer=customer)
            
            # Update customer details
            customer.name = request.form.get('name')
            customer.phone = request.form.get('phone')
            customer.email = request.form.get('email') or None
            customer.address = request.form.get('address')
            customer.aadhar_number = new_aadhar
            customer.pan_number = request.form.get('pan_number') or None
            customer.occupation = request.form.get('occupation') or None
            
            if request.form.get('annual_income'):
                customer.annual_income = float(request.form.get('annual_income'))
            
            db.session.commit()
            
            flash('Customer details updated successfully.', 'success')
            return redirect(url_for('customer.view_customer', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update customer. Please try again.', 'error')
            current_app.logger.error(f'Edit customer error: {str(e)}')
    
    return render_template('customers/edit_customer.html', customer=customer)

@bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_customer_status(id):
    """Toggle customer active status."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('customer.view_customer', id=id))
    
    customer = Customer.query.get_or_404(id)
    
    try:
        # Check if customer has active loans
        if customer.has_active_loans() and customer.is_active:
            flash('Cannot deactivate customer with active loans.', 'error')
            return redirect(url_for('customer.view_customer', id=id))
        
        customer.is_active = not customer.is_active
        db.session.commit()
        
        status = 'activated' if customer.is_active else 'deactivated'
        flash(f'Customer has been {status}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update customer status.', 'error')
        current_app.logger.error(f'Toggle customer status error: {str(e)}')
    
    return redirect(url_for('customer.view_customer', id=id))

@bp.route('/<int:id>/biometric', methods=['GET', 'POST'])
@login_required
def manage_biometric(id):
    """Manage customer biometric data."""
    if not current_user.can_manage_loans():
        flash('Access denied.', 'error')
        return redirect(url_for('customer.view_customer', id=id))
    
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Handle biometric data (placeholder for actual biometric integration)
            biometric_data = request.form.get('biometric_data')
            
            if biometric_data:
                # In a real implementation, this would be processed biometric data
                customer.biometric_data = json.dumps({
                    'enrolled_at': datetime.now().isoformat(),
                    'data': biometric_data,
                    'enrolled_by': current_user.id
                })
                
                db.session.commit()
                flash('Biometric data updated successfully.', 'success')
            else:
                flash('No biometric data provided.', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash('Failed to update biometric data.', 'error')
            current_app.logger.error(f'Biometric update error: {str(e)}')
        
        return redirect(url_for('customer.view_customer', id=id))
    
    return render_template('customers/biometric.html', customer=customer)

@bp.route('/api/search')
@login_required
def api_search_customers():
    """API endpoint for customer search."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify([])
    
    customers = Customer.query.filter(
        db.or_(
            Customer.name.contains(query),
            Customer.phone.contains(query),
            Customer.customer_id.contains(query)
        )
    ).filter_by(is_active=True).limit(limit).all()
    
    return jsonify([{
        'id': c.id,
        'customer_id': c.customer_id,
        'name': c.name,
        'phone': c.phone,
        'email': c.email
    } for c in customers])

@bp.route('/export')
@login_required
def export_customers():
    """Export customers to CSV."""
    if not current_user.can_access_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('customer.list_customers'))
    
    # This would implement CSV export functionality
    flash('Export functionality coming soon.', 'info')
    return redirect(url_for('customer.list_customers'))