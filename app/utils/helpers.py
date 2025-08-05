import os
import uuid
from datetime import datetime, date
from werkzeug.utils import secure_filename
from flask import current_app, url_for
import re

# File upload configuration
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'
}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder='documents'):
    """
    Save uploaded file to the upload directory.
    
    Args:
        file: FileStorage object from request.files
        subfolder: Subfolder within upload directory
    
    Returns:
        Relative path to saved file
    """
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    # Return relative path
    return os.path.join(subfolder, unique_filename)

def get_file_url(file_path):
    """Generate URL for uploaded file."""
    if not file_path:
        return None
    
    return url_for('static', filename=f'uploads/{file_path}')

def delete_file(file_path):
    """Delete uploaded file."""
    if not file_path:
        return False
    
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        current_app.logger.error(f"Failed to delete file {file_path}: {str(e)}")
    
    return False

def format_currency(amount, currency_symbol='₹'):
    """Format amount as currency with Indian number formatting."""
    if amount is None:
        return f"{currency_symbol}0.00"
    
    try:
        amount = float(amount)
        
        # Indian number formatting (lakhs and crores)
        if amount >= 10000000:  # 1 crore
            crores = amount / 10000000
            return f"{currency_symbol}{crores:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            lakhs = amount / 100000
            return f"{currency_symbol}{lakhs:.2f} L"
        elif amount >= 1000:  # 1 thousand
            thousands = amount / 1000
            return f"{currency_symbol}{thousands:.2f} K"
        else:
            return f"{currency_symbol}{amount:,.2f}"
    
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

def format_date(date_obj, format_str='%d/%m/%Y'):
    """Format date object to string."""
    if not date_obj:
        return ''
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return date_obj
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    try:
        return date_obj.strftime(format_str)
    except (AttributeError, ValueError):
        return str(date_obj)

def format_datetime(datetime_obj, format_str='%d/%m/%Y %H:%M'):
    """Format datetime object to string."""
    if not datetime_obj:
        return ''
    
    if isinstance(datetime_obj, str):
        try:
            datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        except ValueError:
            return datetime_obj
    
    try:
        return datetime_obj.strftime(format_str)
    except (AttributeError, ValueError):
        return str(datetime_obj)

def calculate_age(birth_date):
    """Calculate age from birth date."""
    if not birth_date:
        return None
    
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
    
    today = date.today()
    age = today.year - birth_date.year
    
    if today.month < birth_date.month or \
       (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age

def validate_email(email):
    """Validate email address format."""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_receipt_number():
    """Generate unique receipt number."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"RCP{timestamp}{random_suffix}"

def generate_reference_number():
    """Generate unique reference number."""
    timestamp = datetime.now().strftime('%Y%m%d')
    random_suffix = uuid.uuid4().hex[:8].upper()
    return f"REF{timestamp}{random_suffix}"

def send_notification(user, title, message, notification_type='info'):
    """
    Send notification to user (placeholder for notification system).
    
    Args:
        user: User object
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
    """
    # This is a placeholder for actual notification implementation
    # In production, this would integrate with email, SMS, or push notification services
    
    current_app.logger.info(f"Notification to {user.email}: {title} - {message}")
    
    # Here you would implement:
    # - Email notifications using Flask-Mail
    # - SMS notifications using Twilio or similar
    # - Push notifications using FCM
    # - In-app notifications stored in database
    
    return True

def log_activity(user, action, details=None, entity_type=None, entity_id=None):
    """
    Log user activity (placeholder for activity logging).
    
    Args:
        user: User object
        action: Action performed
        details: Additional details
        entity_type: Type of entity (loan, customer, payment)
        entity_id: ID of the entity
    """
    # This is a placeholder for actual activity logging
    # In production, this would store activities in database
    
    log_entry = {
        'user_id': user.id,
        'user_email': user.email,
        'action': action,
        'details': details,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'timestamp': datetime.now(),
        'ip_address': None  # Would get from request context
    }
    
    current_app.logger.info(f"Activity: {log_entry}")
    
    # Here you would implement:
    # - Store in ActivityLog model
    # - Send to external logging service
    # - Update audit trail
    
    return True

def get_indian_states():
    """Get list of Indian states and union territories."""
    return [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
        'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
        'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
    ]

def get_loan_types():
    """Get available loan types."""
    return [
        {'value': 'personal', 'label': 'Personal Loan'},
        {'value': 'gold', 'label': 'Gold Loan'},
        {'value': 'vehicle', 'label': 'Vehicle Loan'},
        {'value': 'home', 'label': 'Home Loan'},
        {'value': 'business', 'label': 'Business Loan'},
        {'value': 'education', 'label': 'Education Loan'},
        {'value': 'agriculture', 'label': 'Agriculture Loan'}
    ]

def get_payment_methods():
    """Get available payment methods."""
    return [
        {'value': 'cash', 'label': 'Cash'},
        {'value': 'cheque', 'label': 'Cheque'},
        {'value': 'bank_transfer', 'label': 'Bank Transfer'},
        {'value': 'upi', 'label': 'UPI'},
        {'value': 'net_banking', 'label': 'Net Banking'},
        {'value': 'card', 'label': 'Card Payment'}
    ]

def get_user_roles():
    """Get available user roles."""
    return [
        {'value': 'employee', 'label': 'Employee'},
        {'value': 'manager', 'label': 'Manager'},
        {'value': 'admin', 'label': 'Administrator'}
    ]

def sanitize_input(input_string):
    """Sanitize user input to prevent XSS."""
    if not input_string:
        return input_string
    
    # Basic HTML escaping
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    
    for char, replacement in replacements.items():
        input_string = input_string.replace(char, replacement)
    
    return input_string

def generate_qr_code(data, size=10):
    """
    Generate QR code for data (placeholder).
    
    Args:
        data: Data to encode
        size: Size of QR code
    
    Returns:
        Path to generated QR code image
    """
    # This is a placeholder for QR code generation
    # In production, implement using qrcode library
    
    current_app.logger.info(f"QR code requested for: {data}")
    
    # Here you would implement:
    # import qrcode
    # qr = qrcode.QRCode(version=1, box_size=size, border=5)
    # qr.add_data(data)
    # qr.make(fit=True)
    # img = qr.make_image(fill_color="black", back_color="white")
    # Save and return path
    
    return None

def paginate_query(query, page, per_page=20):
    """Helper function for pagination."""
    try:
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    except Exception as e:
        current_app.logger.error(f"Pagination error: {str(e)}")
        return None