"""
Helper utilities for AGV Finance and Loans
General utility functions for file handling, formatting, validation, etc.
"""

import os
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from werkzeug.utils import secure_filename
from flask import current_app, flash
import re

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder='documents'):
    """Save uploaded file and return the file path"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    # Create upload path
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, unique_filename)
    
    try:
        file.save(file_path)
        return os.path.join(folder, unique_filename)
    except Exception as e:
        current_app.logger.error(f"Error saving file: {e}")
        return None

def delete_file(file_path):
    """Delete a file from the filesystem"""
    if not file_path:
        return True
    
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {e}")
        return False

def format_currency(amount, currency_symbol='₹'):
    """Format amount as currency"""
    if amount is None:
        return f"{currency_symbol}0.00"
    
    # Convert to float if Decimal
    if isinstance(amount, Decimal):
        amount = float(amount)
    
    # Format with Indian numbering system
    def indian_format(num):
        s = str(int(num))
        if len(s) <= 3:
            return s
        
        # Add commas in Indian style
        result = s[-3:]  # Last 3 digits
        s = s[:-3]
        
        while len(s) > 2:
            result = s[-2:] + ',' + result
            s = s[:-2]
        
        if s:
            result = s + ',' + result
        
        return result
    
    # Split integer and decimal parts
    integer_part = int(amount)
    decimal_part = amount - integer_part
    
    formatted_integer = indian_format(integer_part)
    
    if decimal_part > 0:
        return f"{currency_symbol}{formatted_integer}.{decimal_part:.2f}"[:-3] + f"{decimal_part:.2f}"[1:]
    else:
        return f"{currency_symbol}{formatted_integer}.00"

def format_percentage(value, decimal_places=2):
    """Format value as percentage"""
    if value is None:
        return "0.00%"
    
    if isinstance(value, Decimal):
        value = float(value)
    
    return f"{value:.{decimal_places}f}%"

def format_date(date_obj, format_str='%d %b %Y'):
    """Format date object to string"""
    if not date_obj:
        return "-"
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            return date_obj
    
    return date_obj.strftime(format_str)

def format_datetime(datetime_obj, format_str='%d %b %Y, %I:%M %p'):
    """Format datetime object to string"""
    if not datetime_obj:
        return "-"
    
    if isinstance(datetime_obj, str):
        try:
            datetime_obj = datetime.fromisoformat(datetime_obj)
        except:
            return datetime_obj
    
    return datetime_obj.strftime(format_str)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Indian phone number"""
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Indian mobile number
    if len(phone_digits) == 10 and phone_digits[0] in '6789':
        return True
    elif len(phone_digits) == 12 and phone_digits.startswith('91') and phone_digits[2] in '6789':
        return True
    elif len(phone_digits) == 13 and phone_digits.startswith('+91') and phone_digits[3] in '6789':
        return True
    
    return False

def validate_pan(pan):
    """Validate PAN number format"""
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return re.match(pattern, pan.upper()) is not None

def validate_aadhaar(aadhaar):
    """Validate Aadhaar number format"""
    # Remove spaces and hyphens
    aadhaar_digits = re.sub(r'[\s-]', '', aadhaar)
    
    # Check if it's 12 digits
    if len(aadhaar_digits) != 12 or not aadhaar_digits.isdigit():
        return False
    
    # Simple checksum validation (Verhoeff algorithm)
    # This is a simplified version
    return True

def validate_ifsc(ifsc):
    """Validate IFSC code format"""
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    return re.match(pattern, ifsc.upper()) is not None

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except:
            return None
    
    today = date.today()
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age

def generate_loan_number():
    """Generate unique loan number"""
    prefix = "AGV"
    year = datetime.now().year
    timestamp = int(datetime.now().timestamp())
    
    return f"{prefix}{year}{timestamp % 1000000}"

def generate_customer_id():
    """Generate unique customer ID"""
    prefix = "CUST"
    year = datetime.now().year
    timestamp = int(datetime.now().timestamp())
    
    return f"{prefix}{year}{timestamp % 1000000}"

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove special characters and replace spaces with underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_json_loads(json_string, default=None):
    """Safely load JSON string"""
    if not json_string:
        return default or {}
    
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default or {}

def safe_json_dumps(obj):
    """Safely dump object to JSON string"""
    try:
        return json.dumps(obj, default=json_serial)
    except (TypeError, ValueError):
        return '{}'

def mask_sensitive_data(data, mask_char='*'):
    """Mask sensitive data for display"""
    if not data:
        return data
    
    if len(data) <= 4:
        return mask_char * len(data)
    
    # Show first 2 and last 2 characters
    return data[:2] + mask_char * (len(data) - 4) + data[-2:]

def get_file_size_human_readable(file_path):
    """Get file size in human readable format"""
    try:
        size = os.path.getsize(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"
    except OSError:
        return "Unknown"

def flash_form_errors(form):
    """Flash all form validation errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", 'error')

def get_risk_color(risk_level):
    """Get bootstrap color class for risk level"""
    risk_colors = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger'
    }
    return risk_colors.get(risk_level.lower(), 'secondary')

def get_status_color(status):
    """Get bootstrap color class for status"""
    status_colors = {
        'active': 'success',
        'pending': 'warning',
        'approved': 'info',
        'disbursed': 'primary',
        'closed': 'secondary',
        'rejected': 'danger',
        'defaulted': 'danger',
        'completed': 'success',
        'failed': 'danger',
        'verified': 'success',
        'unverified': 'warning'
    }
    return status_colors.get(status.lower(), 'secondary')

def paginate_query(query, page, per_page, error_out=False):
    """Paginate a SQLAlchemy query"""
    try:
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=error_out
        )
    except Exception as e:
        current_app.logger.error(f"Pagination error: {e}")
        return query.paginate(page=1, per_page=per_page, error_out=False)

def create_breadcrumb(items):
    """Create breadcrumb navigation items"""
    breadcrumb = []
    for item in items:
        if isinstance(item, dict):
            breadcrumb.append(item)
        else:
            breadcrumb.append({'text': item, 'url': None})
    return breadcrumb

def format_loan_status_badge(status):
    """Format loan status as HTML badge"""
    color = get_status_color(status)
    return f'<span class="badge badge-{color}">{status.title()}</span>'

def calculate_business_days(start_date, end_date):
    """Calculate number of business days between two dates"""
    from datetime import timedelta
    
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def get_next_business_day(start_date, days=1):
    """Get the next business day after specified number of business days"""
    from datetime import timedelta
    
    current_date = start_date
    business_days_added = 0
    
    while business_days_added < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            business_days_added += 1
    
    return current_date