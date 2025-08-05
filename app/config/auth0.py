"""
Auth0 Configuration Module
Handles Auth0 settings, WebAuthn configuration, and security headers
"""
import os
from datetime import timedelta


class Auth0Config:
    """Auth0 configuration settings"""
    
    # Basic Auth0 settings
    DOMAIN = os.environ.get('AUTH0_DOMAIN')
    CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET')
    AUDIENCE = os.environ.get('AUTH0_AUDIENCE')
    
    # Auth0 URLs
    BASE_URL = f"https://{DOMAIN}" if DOMAIN else None
    AUTHORIZATION_URL = f"{BASE_URL}/authorize" if BASE_URL else None
    TOKEN_URL = f"{BASE_URL}/oauth/token" if BASE_URL else None
    USER_INFO_URL = f"{BASE_URL}/userinfo" if BASE_URL else None
    LOGOUT_URL = f"{BASE_URL}/v2/logout" if BASE_URL else None
    
    # OAuth scopes
    SCOPES = 'openid profile email'
    
    # Callback URLs
    CALLBACK_URL = os.environ.get('AUTH0_CALLBACK_URL', '/auth/callback')
    LOGOUT_REDIRECT_URL = os.environ.get('AUTH0_LOGOUT_REDIRECT_URL', '/')


class WebAuthnConfig:
    """WebAuthn/FIDO2 configuration for biometric authentication"""
    
    # WebAuthn settings
    RP_ID = os.environ.get('WEBAUTHN_RP_ID', 'localhost')  # Relying Party ID
    RP_NAME = os.environ.get('WEBAUTHN_RP_NAME', 'AGV Finance & Loans')
    ORIGIN = os.environ.get('WEBAUTHN_ORIGIN', 'http://localhost:5000')
    
    # Timeout settings (in milliseconds)
    REGISTRATION_TIMEOUT = 60000  # 60 seconds
    AUTHENTICATION_TIMEOUT = 60000  # 60 seconds
    
    # User verification requirement
    USER_VERIFICATION = 'preferred'  # 'required', 'preferred', 'discouraged'
    
    # Authenticator attachment
    AUTHENTICATOR_ATTACHMENT = None  # None, 'platform', 'cross-platform'
    
    # Resident key requirement
    RESIDENT_KEY = 'preferred'  # 'required', 'preferred', 'discouraged'


class SessionConfig:
    """Session security configuration"""
    
    # Session timeout
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_TIMEOUT_WARNING = timedelta(minutes=25)  # Warn 5 minutes before timeout
    
    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Concurrent session limits
    MAX_SESSIONS_PER_USER = 3
    
    # Session regeneration
    REGENERATE_SESSION_ON_LOGIN = True


class SecurityConfig:
    """Security headers and CSRF configuration"""
    
    # CSRF settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = os.environ.get('FLASK_ENV') == 'production'
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.auth0.com https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://*.auth0.com; "
            "frame-src https://js.stripe.com;"
        )
    }


class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Redis configuration for rate limiting
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate limit settings
    RATE_LIMITS = {
        'login': '5 per 15 minutes',  # Login attempts
        'api': '100 per minute',      # API calls
        'password_reset': '3 per hour',  # Password reset attempts
        'registration': '10 per hour',   # Registration attempts
    }
    
    # Account lockout settings
    ACCOUNT_LOCKOUT_THRESHOLD = 10  # Failed attempts before lockout
    ACCOUNT_LOCKOUT_DURATION = timedelta(hours=24)


def get_auth0_client_config():
    """Get Auth0 client configuration for OAuth"""
    return {
        'client_id': Auth0Config.CLIENT_ID,
        'client_secret': Auth0Config.CLIENT_SECRET,
        'server_metadata_url': f'{Auth0Config.BASE_URL}/.well-known/openid_configuration',
        'client_kwargs': {
            'scope': Auth0Config.SCOPES
        }
    }


def get_webauthn_config():
    """Get WebAuthn configuration dictionary"""
    return {
        'rp_id': WebAuthnConfig.RP_ID,
        'rp_name': WebAuthnConfig.RP_NAME,
        'origin': WebAuthnConfig.ORIGIN,
        'registration_timeout': WebAuthnConfig.REGISTRATION_TIMEOUT,
        'authentication_timeout': WebAuthnConfig.AUTHENTICATION_TIMEOUT,
        'user_verification': WebAuthnConfig.USER_VERIFICATION,
        'authenticator_attachment': WebAuthnConfig.AUTHENTICATOR_ATTACHMENT,
        'resident_key': WebAuthnConfig.RESIDENT_KEY,
    }


def apply_security_headers(app):
    """Apply security headers to Flask app"""
    @app.after_request
    def set_security_headers(response):
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response