import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

def generate_secure_token(length=32):
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)

def generate_api_key():
    """Generate a secure API key."""
    return f"agv_{secrets.token_urlsafe(32)}"

def hash_password(password):
    """Hash a password using Werkzeug's security functions."""
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """Verify a password against its hash."""
    return check_password_hash(password_hash, password)

def generate_jwt_token(user_id, expires_in=3600):
    """Generate a JWT token for API authentication."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_jwt_token(token):
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_otp(length=6):
    """Generate a numeric OTP."""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def hash_data(data):
    """Generate SHA-256 hash of data."""
    return hashlib.sha256(str(data).encode()).hexdigest()

def verify_data_integrity(data, expected_hash):
    """Verify data integrity using hash comparison."""
    return hash_data(data) == expected_hash

def generate_session_token():
    """Generate a secure session token."""
    return secrets.token_hex(32)

def mask_sensitive_data(data, mask_char='*', visible_chars=4):
    """Mask sensitive data leaving only a few visible characters."""
    if not data or len(data) <= visible_chars:
        return data
    
    return data[:2] + mask_char * (len(data) - visible_chars) + data[-2:]

def validate_aadhar_number(aadhar):
    """Validate Aadhar number format."""
    if not aadhar:
        return False
    
    # Remove spaces and validate
    aadhar = aadhar.replace(' ', '')
    
    # Check if it's 12 digits
    if len(aadhar) != 12 or not aadhar.isdigit():
        return False
    
    # Basic checksum validation (simplified)
    # In production, implement full Verhoeff algorithm
    return True

def validate_pan_number(pan):
    """Validate PAN number format."""
    if not pan:
        return True  # PAN is optional
    
    # PAN format: 5 letters, 4 digits, 1 letter
    import re
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pattern, pan.upper()))

def validate_phone_number(phone):
    """Validate Indian phone number format."""
    if not phone:
        return False
    
    # Remove non-digit characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Check if it's 10 digits (Indian mobile) or 11 digits (with country code)
    if len(phone) == 10:
        return phone.startswith(('6', '7', '8', '9'))
    elif len(phone) == 11:
        return phone.startswith('91') and phone[2] in ('6', '7', '8', '9')
    elif len(phone) == 13:
        return phone.startswith('+91') and phone[3] in ('6', '7', '8', '9')
    
    return False

def sanitize_filename(filename):
    """Sanitize filename for safe storage."""
    import re
    # Remove unsafe characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    return filename

def generate_unique_filename(original_filename):
    """Generate a unique filename with timestamp."""
    import os
    from datetime import datetime
    
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = secrets.token_hex(4)
    
    return f"{sanitize_filename(name)}_{timestamp}_{random_suffix}{ext}"

def check_file_size(file, max_size_mb=10):
    """Check if uploaded file size is within limits."""
    # Get file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return size <= max_size_bytes

def get_file_type(filename):
    """Get file type from extension."""
    import os
    ext = os.path.splitext(filename)[1].lower()
    
    type_mapping = {
        '.pdf': 'document',
        '.doc': 'document',
        '.docx': 'document',
        '.txt': 'document',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.xls': 'spreadsheet',
        '.xlsx': 'spreadsheet',
        '.csv': 'spreadsheet'
    }
    
    return type_mapping.get(ext, 'unknown')