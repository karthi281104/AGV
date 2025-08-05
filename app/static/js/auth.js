/**
 * Enhanced Authentication JavaScript
 * Handles Auth0 integration, WebAuthn biometric authentication, and session management
 */

// Authentication Handler
const AuthHandler = {
    init() {
        this.bindEvents();
        this.checkWebAuthnSupport();
    },

    bindEvents() {
        const webauthnForm = document.getElementById('webauthn-form');
        if (webauthnForm) {
            webauthnForm.addEventListener('submit', this.handleWebAuthnLogin.bind(this));
        }

        // Biometric setup links
        const setupLink = document.getElementById('setup-biometrics');
        if (setupLink) {
            setupLink.addEventListener('click', this.redirectToSetup.bind(this));
        }

        // Account issues link
        const issuesLink = document.getElementById('account-issues');
        if (issuesLink) {
            issuesLink.addEventListener('click', this.showAccountHelp.bind(this));
        }
    },

    checkWebAuthnSupport() {
        const biometricMethod = document.querySelector('.auth-method.biometric');
        const webauthnBtn = document.getElementById('webauthn-btn');
        
        if (!window.PublicKeyCredential) {
            // WebAuthn not supported
            if (biometricMethod) {
                biometricMethod.classList.add('unsupported');
                const notice = document.createElement('div');
                notice.className = 'support-notice';
                notice.innerHTML = '<i class="icon-info"></i> Biometric authentication is not supported on this device or browser.';
                biometricMethod.appendChild(notice);
            }
            if (webauthnBtn) {
                webauthnBtn.disabled = true;
                webauthnBtn.textContent = 'Biometrics Not Supported';
            }
        } else {
            // Check for platform authenticator
            PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
                .then(available => {
                    if (available && biometricMethod) {
                        biometricMethod.classList.add('platform-available');
                    }
                });
        }
    },

    async handleWebAuthnLogin(event) {
        event.preventDefault();
        
        const email = document.getElementById('email').value;
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        
        if (!email) {
            this.showError('Please enter your email address.');
            return;
        }

        try {
            this.showStatus('Preparing authentication...', 'loading');
            
            // Begin WebAuthn authentication
            const beginResponse = await fetch('/auth/webauthn/authenticate/begin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    csrf_token: csrfToken
                })
            });

            if (!beginResponse.ok) {
                const error = await beginResponse.json();
                throw new Error(error.error || 'Authentication failed');
            }

            const options = await beginResponse.json();
            
            // Convert base64 strings to ArrayBuffers
            options.challenge = this.base64ToArrayBuffer(options.challenge);
            if (options.allowCredentials) {
                options.allowCredentials.forEach(cred => {
                    cred.id = this.base64ToArrayBuffer(cred.id);
                });
            }

            this.showStatus('Touch your sensor or insert your security key...', 'waiting');

            // Get credential from authenticator
            const credential = await navigator.credentials.get({
                publicKey: options
            });

            this.showStatus('Verifying authentication...', 'loading');

            // Complete authentication
            const completeResponse = await fetch('/auth/webauthn/authenticate/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: {
                        id: credential.id,
                        rawId: this.arrayBufferToBase64(credential.rawId),
                        type: credential.type,
                        response: {
                            authenticatorData: this.arrayBufferToBase64(credential.response.authenticatorData),
                            clientDataJSON: this.arrayBufferToBase64(credential.response.clientDataJSON),
                            signature: this.arrayBufferToBase64(credential.response.signature),
                            userHandle: credential.response.userHandle ? this.arrayBufferToBase64(credential.response.userHandle) : null
                        }
                    },
                    csrf_token: csrfToken
                })
            });

            const result = await completeResponse.json();

            if (completeResponse.ok) {
                this.showStatus('Authentication successful! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = result.redirect || '/dashboard';
                }, 1000);
            } else {
                throw new Error(result.error || 'Authentication failed');
            }

        } catch (error) {
            console.error('WebAuthn authentication error:', error);
            this.showError(error.message || 'Biometric authentication failed. Please try again.');
        }
    },

    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('webauthn-status');
        const iconEl = statusEl.querySelector('.status-icon');
        const messageEl = statusEl.querySelector('.status-message');
        
        statusEl.className = `webauthn-status ${type}`;
        messageEl.textContent = message;
        
        // Update icon based on type
        iconEl.className = 'status-icon';
        switch (type) {
            case 'loading':
                iconEl.classList.add('loading');
                break;
            case 'waiting':
                iconEl.classList.add('waiting');
                break;
            case 'success':
                iconEl.classList.add('success');
                break;
            case 'error':
                iconEl.classList.add('error');
                break;
        }
        
        statusEl.style.display = 'block';
        
        // Auto-hide info messages after 5 seconds
        if (type === 'info') {
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 5000);
        }
    },

    showError(message) {
        this.showStatus(message, 'error');
    },

    redirectToSetup(event) {
        event.preventDefault();
        window.location.href = '/auth/setup-2fa';
    },

    showAccountHelp(event) {
        event.preventDefault();
        alert('If you\'re having trouble accessing your account, please contact IT Support at support@agvfinance.com or call the help desk.');
    },

    // Utility functions for WebAuthn
    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    },

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binaryString = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binaryString += String.fromCharCode(bytes[i]);
        }
        return btoa(binaryString);
    }
};

// Session Management
const SessionManager = {
    warningShown: false,
    timeoutWarning: 25 * 60 * 1000, // 25 minutes in milliseconds
    sessionTimeout: 30 * 60 * 1000, // 30 minutes in milliseconds
    warningTimer: null,
    logoutTimer: null,

    init() {
        this.startSessionMonitoring();
        this.bindEvents();
    },

    bindEvents() {
        // Session warning modal events
        const extendBtn = document.getElementById('extend-session');
        const logoutBtn = document.getElementById('logout-now');
        
        if (extendBtn) {
            extendBtn.addEventListener('click', this.extendSession.bind(this));
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', this.logoutNow.bind(this));
        }

        // Track user activity
        document.addEventListener('click', this.resetSessionTimer.bind(this));
        document.addEventListener('keypress', this.resetSessionTimer.bind(this));
        document.addEventListener('scroll', this.resetSessionTimer.bind(this));
    },

    startSessionMonitoring() {
        this.resetSessionTimer();
    },

    resetSessionTimer() {
        // Clear existing timers
        if (this.warningTimer) clearTimeout(this.warningTimer);
        if (this.logoutTimer) clearTimeout(this.logoutTimer);
        
        // Hide warning if shown
        this.hideWarning();

        // Set new timers
        this.warningTimer = setTimeout(() => {
            this.showWarning();
        }, this.timeoutWarning);

        this.logoutTimer = setTimeout(() => {
            this.forceLogout();
        }, this.sessionTimeout);
    },

    showWarning() {
        if (this.warningShown) return;
        
        this.warningShown = true;
        const modal = document.getElementById('session-warning-modal');
        if (modal) {
            modal.style.display = 'block';
            this.startCountdown();
        }
    },

    hideWarning() {
        this.warningShown = false;
        const modal = document.getElementById('session-warning-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    startCountdown() {
        const countdownEl = document.getElementById('countdown');
        if (!countdownEl) return;

        let timeLeft = 5 * 60; // 5 minutes in seconds
        
        const updateCountdown = () => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                this.forceLogout();
                return;
            }
            
            timeLeft--;
            setTimeout(updateCountdown, 1000);
        };
        
        updateCountdown();
    },

    extendSession() {
        // Make request to extend session
        fetch('/auth/extend-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        }).then(response => {
            if (response.ok) {
                this.resetSessionTimer();
            } else {
                this.forceLogout();
            }
        }).catch(() => {
            this.forceLogout();
        });
    },

    logoutNow() {
        window.location.href = '/auth/logout';
    },

    forceLogout() {
        alert('Your session has expired for security reasons. You will be logged out.');
        window.location.href = '/auth/logout';
    }
};

// WebAuthn Registration (for setup page)
const WebAuthnManager = {
    async beginRegistration(credentialName = 'Security Key') {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
            
            const response = await fetch('/auth/webauthn/register/begin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    csrf_token: csrfToken
                })
            });

            if (!response.ok) {
                throw new Error('Failed to start registration');
            }

            const options = await response.json();
            
            // Convert base64 strings to ArrayBuffers
            options.challenge = AuthHandler.base64ToArrayBuffer(options.challenge);
            options.user.id = AuthHandler.base64ToArrayBuffer(options.user.id);

            // Create credential
            const credential = await navigator.credentials.create({
                publicKey: options
            });

            // Complete registration
            const completeResponse = await fetch('/auth/webauthn/register/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: {
                        id: credential.id,
                        rawId: AuthHandler.arrayBufferToBase64(credential.rawId),
                        type: credential.type,
                        response: {
                            attestationObject: AuthHandler.arrayBufferToBase64(credential.response.attestationObject),
                            clientDataJSON: AuthHandler.arrayBufferToBase64(credential.response.clientDataJSON)
                        }
                    },
                    credential_name: credentialName,
                    csrf_token: csrfToken
                })
            });

            const result = await completeResponse.json();
            
            if (completeResponse.ok) {
                return { success: true, message: result.message };
            } else {
                throw new Error(result.error || 'Registration failed');
            }

        } catch (error) {
            console.error('WebAuthn registration error:', error);
            return { success: false, error: error.message };
        }
    },

    manageCredentials() {
        // Open credentials management interface
        // This would be implemented based on specific UI requirements
        alert('Credential management interface coming soon!');
    }
};

// Export for use in other scripts
window.AuthHandler = AuthHandler;
window.SessionManager = SessionManager;
window.WebAuthnManager = WebAuthnManager;