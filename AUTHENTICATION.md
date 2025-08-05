# AGV Finance & Loans - Authentication System Documentation

## Overview

This document describes the comprehensive Auth0 authentication system implemented for AGV Finance & Loans. The system provides enterprise-grade security with biometric authentication support, role-based access control, and advanced session management.

## Features

### 🔐 Authentication Methods
- **Auth0 SSO**: Single Sign-On with OAuth 2.0 flow
- **WebAuthn Biometrics**: Fingerprint, Face ID, Windows Hello support
- **USB Security Keys**: Hardware keys (YubiKey, etc.)
- **Multi-Factor Authentication**: Enhanced security for sensitive operations

### 👥 User Management
- **Role-Based Access Control**: Admin, Employee, and Viewer roles
- **User Registration**: Admin-only employee account creation
- **Profile Management**: User preferences and settings
- **Account Security**: Lockout protection and failed attempt tracking

### 🛡️ Security Features
- **Session Management**: Timeout warnings and concurrent session limits
- **Audit Logging**: Comprehensive security event tracking
- **Rate Limiting**: Protection against brute force attacks
- **CSRF Protection**: Form security against cross-site attacks
- **Security Headers**: Content Security Policy and security headers

## Setup Instructions

### 1. Environment Configuration

Create or update your `.env` file with the following Auth0 configuration:

```bash
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=your-api-identifier

# WebAuthn Configuration (optional)
WEBAUTHN_RP_ID=localhost  # Change to your domain in production
WEBAUTHN_RP_NAME=AGV Finance & Loans
WEBAUTHN_ORIGIN=http://localhost:5000  # Change to your URL in production

# Redis Configuration (for production rate limiting)
REDIS_URL=redis://localhost:6379/0

# Security Settings
SECRET_KEY=your-very-secure-secret-key
FLASK_ENV=development  # Change to 'production' for production
```

### 2. Auth0 Application Setup

In your Auth0 Dashboard:

1. **Create a Regular Web Application**
2. **Configure Allowed URLs**:
   - Allowed Callback URLs: `https://your-domain.com/auth/callback`
   - Allowed Logout URLs: `https://your-domain.com/`
   - Allowed Web Origins: `https://your-domain.com`

3. **Enable Advanced Settings**:
   - Grant Types: Authorization Code, Refresh Token, Implicit
   - Token Endpoint Authentication Method: POST

4. **Security Settings**:
   - Enable Multi-Factor Authentication
   - Configure Brute Force Protection
   - Set up Anomaly Detection

### 3. Database Migration

Run database migrations to create the new authentication tables:

```bash
# Initialize migrations (if not already done)
flask db init

# Create migration for new authentication models
flask db migrate -m "Add authentication models"

# Apply migrations
flask db upgrade
```

### 4. Install Dependencies

Install the new authentication dependencies:

```bash
pip install -r requirements.txt
```

## Usage Guide

### For Administrators

#### Creating New Employee Accounts

1. Log in as an admin user
2. Navigate to `/auth/register`
3. Fill in employee details:
   - Full Name
   - Email Address
   - Role (Admin, Employee, or Viewer)
4. Click "Create Employee Account"

The new employee will receive login instructions and can set up biometric authentication on first login.

#### Managing User Sessions

Administrators can view and manage user sessions through the audit logs and user management interface.

### For Employees

#### Logging In

**Option 1: Auth0 SSO**
1. Click "Sign in with Auth0"
2. Complete Auth0 authentication (may include MFA)
3. You'll be redirected to the dashboard

**Option 2: Biometric Authentication**
1. Enter your email address
2. Click "Sign in with Biometrics"
3. Follow device prompts (fingerprint, Face ID, etc.)
4. Complete authentication

#### Setting Up Biometric Authentication

1. After first login, you'll be prompted to set up 2FA
2. Choose your preferred method:
   - Device biometrics (fingerprint, Face ID)
   - USB security key (YubiKey, etc.)
3. Follow the setup wizard
4. Test your new authentication method

#### Managing Your Profile

1. Navigate to your profile page
2. Update personal information and preferences
3. Manage active sessions
4. Set up additional security keys

## Security Features

### Session Security

- **Automatic timeout** after 30 minutes of inactivity
- **Session warnings** at 25 minutes
- **Concurrent session limits** (maximum 3 sessions per user)
- **Secure session storage** with HttpOnly cookies

### Audit Logging

All security events are logged including:
- Login/logout activities
- Failed authentication attempts
- Permission denials
- Suspicious activity detection
- Administrative actions

### Rate Limiting

Protection against abuse:
- **Login attempts**: 5 attempts per 15 minutes per IP
- **API calls**: 100 requests per minute per user
- **Password reset**: 3 attempts per hour per email
- **Account lockout**: 24 hours after 10 failed attempts

## API Endpoints

### Authentication Routes

- `GET /auth/login` - Display login page
- `GET /auth/auth0-login` - Initiate Auth0 OAuth flow
- `GET /auth/callback` - Handle Auth0 callback
- `GET /auth/logout` - Logout and cleanup sessions
- `GET /auth/register` - Admin-only registration page (requires admin role)
- `GET /auth/profile` - User profile management
- `GET /auth/setup-2fa` - Two-factor authentication setup

### WebAuthn API Routes

- `POST /auth/webauthn/register/begin` - Start biometric registration
- `POST /auth/webauthn/register/complete` - Complete biometric registration
- `POST /auth/webauthn/authenticate/begin` - Start biometric authentication
- `POST /auth/webauthn/authenticate/complete` - Complete biometric authentication

### Session Management

- `GET /auth/terminate-session/<id>` - Terminate specific session
- `GET /auth/terminate-all-sessions` - Terminate all other sessions

## Browser Support

### WebAuthn/Biometric Authentication

**Fully Supported:**
- Chrome 67+ (Windows, macOS, Android)
- Firefox 60+ (Windows, macOS)
- Safari 14+ (macOS, iOS)
- Edge 18+ (Windows)

**Platform Authenticators:**
- Windows Hello (Windows 10+)
- Touch ID / Face ID (macOS, iOS)
- Fingerprint sensors (Android)

**Hardware Authenticators:**
- YubiKey 5 series
- Google Titan keys
- Feitian keys
- Any FIDO2/WebAuthn compatible device

## Troubleshooting

### Common Issues

**"Biometrics Not Supported" Error**
- Ensure you're using a supported browser
- Check that your device has biometric capabilities
- Verify the site is served over HTTPS (required for WebAuthn)

**Auth0 Authentication Fails**
- Verify Auth0 configuration in `.env`
- Check Auth0 application settings
- Ensure callback URLs are correctly configured

**Session Timeout Issues**
- Check server time synchronization
- Verify session configuration
- Review network connectivity

**Database Connection Errors**
- Ensure PostgreSQL is running
- Verify database credentials
- Check database connectivity

### Getting Help

For technical support:
- Contact IT Support: support@agvfinance.com
- Check application logs for detailed error messages
- Review Auth0 logs in the Auth0 Dashboard

## Production Deployment

### Security Checklist

Before deploying to production:

- [ ] Change `FLASK_ENV` to `production`
- [ ] Use HTTPS for all URLs
- [ ] Configure proper Auth0 production settings
- [ ] Set up Redis for rate limiting
- [ ] Enable security headers
- [ ] Configure proper CORS settings
- [ ] Set up monitoring and alerting
- [ ] Review and test backup procedures

### Performance Considerations

- Use Redis for session storage and rate limiting
- Configure database connection pooling
- Set up load balancing for multiple instances
- Monitor authentication endpoint performance
- Consider CDN for static assets

## Compliance and Auditing

The authentication system supports compliance requirements through:

- **Comprehensive audit trails** for all authentication events
- **Session tracking** with detailed metadata
- **Security event logging** with risk assessment
- **Failed attempt monitoring** and alerting
- **Data retention** policies for audit logs

All security events include:
- User identification
- IP address and geolocation
- User agent and device information
- Timestamp and action details
- Risk assessment and anomaly flags