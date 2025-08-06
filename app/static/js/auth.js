// Enhanced authentication functionality for AGV Finance & Loans

document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupFormHandlers();
    checkBiometricSupport();
    setupPasswordToggle();
});

function initializeAuth() {
    // Basic auth initialization
    console.log('Auth system initialized');
    
    // Check for remember device setting
    const rememberDevice = localStorage.getItem('agv_remember_device');
    if (rememberDevice === 'true') {
        const rememberCheckbox = document.getElementById('remember');
        if (rememberCheckbox) {
            rememberCheckbox.checked = true;
        }
    }
}

function setupFormHandlers() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performLogin();
        });
    }

    // Setup social login buttons
    const googleBtn = document.querySelector('.google-btn');
    const microsoftBtn = document.querySelector('.microsoft-btn');
    
    if (googleBtn) {
        googleBtn.addEventListener('click', () => initiateAuth0Login('google-oauth2'));
    }
    
    if (microsoftBtn) {
        microsoftBtn.addEventListener('click', () => initiateAuth0Login('windowslive'));
    }
}

function setupPasswordToggle() {
    const toggleButton = document.querySelector('.toggle-password');
    if (toggleButton) {
        toggleButton.addEventListener('click', togglePassword);
    }
}

async function performLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember').checked;

    if (!email || !password) {
        showError('Please enter both email and password.');
        return;
    }

    try {
        showLoading(true);
        
        // Store remember device preference
        if (remember) {
            localStorage.setItem('agv_remember_device', 'true');
        } else {
            localStorage.removeItem('agv_remember_device');
        }

        // For now, handle demo login client-side
        if (email === 'demo@agvfinance.com' && password === 'demo123') {
            // Submit form for demo login
            const form = document.getElementById('loginForm');
            const formData = new FormData();
            formData.append('username', 'demo');
            formData.append('password', 'demo123');
            
            const response = await fetch('/auth/login', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                window.location.href = '/dashboard';
            } else {
                throw new Error('Login failed');
            }
        } else {
            // Redirect to Auth0 for other logins
            initiateAuth0Login();
        }
        
    } catch (error) {
        showError('Login failed. Please check your credentials.');
        console.error('Login error:', error);
    } finally {
        showLoading(false);
    }
}

function initiateAuth0Login(connection = null) {
    let authUrl = '/auth/auth0-login';
    if (connection) {
        authUrl += `?connection=${connection}`;
    }
    window.location.href = authUrl;
}

function togglePassword() {
    const passwordField = document.getElementById('password');
    const toggleIcon = document.querySelector('.toggle-password i');
    
    if (passwordField && toggleIcon) {
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            toggleIcon.classList.replace('fa-eye', 'fa-eye-slash');
        } else {
            passwordField.type = 'password';
            toggleIcon.classList.replace('fa-eye-slash', 'fa-eye');
        }
    }
}

async function checkBiometricSupport() {
    const biometricBtn = document.querySelector('.biometric-btn');
    
    if (!biometricBtn) return;
    
    try {
        if (window.PublicKeyCredential) {
            const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
            
            if (available) {
                biometricBtn.style.display = 'flex';
                biometricBtn.addEventListener('click', authenticateWithBiometric);
            } else {
                biometricBtn.style.display = 'none';
            }
        } else {
            biometricBtn.style.display = 'none';
        }
    } catch (error) {
        console.log('Biometric check failed:', error);
        biometricBtn.style.display = 'none';
    }
}

async function authenticateWithBiometric() {
    try {
        showLoading(true);
        showMessage('Biometric authentication is not yet implemented. Please use email/password or Auth0 login.', 'info');
    } catch (error) {
        showError('Biometric authentication failed.');
        console.error('WebAuthn error:', error);
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    const button = document.querySelector('.secure-login-btn');
    
    if (!button) return;
    
    if (show) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
        button.disabled = true;
    } else {
        button.innerHTML = '<i class="fas fa-sign-in-alt"></i> Secure Login';
        button.disabled = false;
    }
}

function showError(message) {
    showMessage(message, 'error');
}

function showSuccess(message) {
    showMessage(message, 'success');
}

function showMessage(message, type = 'error') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.error-message, .success-message, .info-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    
    const icon = type === 'error' ? 'fas fa-exclamation-circle' : 
                 type === 'success' ? 'fas fa-check-circle' : 
                 'fas fa-info-circle';
    
    messageDiv.innerHTML = `
        <i class="${icon}"></i>
        ${message}
    `;
    
    // Add styles for info messages
    if (type === 'info') {
        messageDiv.style.cssText = `
            background: rgba(33, 150, 243, 0.1);
            border: 1px solid rgba(33, 150, 243, 0.3);
            color: #1976d2;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        `;
    }
    
    // Insert at the top of the form
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        loginForm.prepend(messageDiv);
        messageDiv.style.display = 'flex';
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// Utility function for base64 conversion (for future WebAuthn implementation)
function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

// Handle browser back button
window.addEventListener('popstate', function(event) {
    // Clear any loading states
    showLoading(false);
});

// Handle form submission on Enter key
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.id === 'email' || activeElement.id === 'password')) {
            e.preventDefault();
            performLogin();
        }
    }
});