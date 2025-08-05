/**
 * WebAuthn Management JavaScript
 * Dedicated to WebAuthn/FIDO2 operations and credential management
 */

const WebAuthnSupport = {
    /**
     * Check if WebAuthn is supported in the current browser
     */
    isSupported() {
        return !!(window.PublicKeyCredential && navigator.credentials && navigator.credentials.create);
    },

    /**
     * Check if platform authenticator is available (built-in biometrics)
     */
    async isPlatformAuthenticatorAvailable() {
        if (!this.isSupported()) return false;
        
        try {
            return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        } catch (error) {
            console.warn('Platform authenticator check failed:', error);
            return false;
        }
    },

    /**
     * Check if conditional mediation is supported (autofill UI)
     */
    async isConditionalMediationSupported() {
        if (!this.isSupported()) return false;
        
        try {
            return await PublicKeyCredential.isConditionalMediationAvailable();
        } catch (error) {
            console.warn('Conditional mediation check failed:', error);
            return false;
        }
    }
};

const WebAuthnUtils = {
    /**
     * Convert base64 string to ArrayBuffer
     */
    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    },

    /**
     * Convert ArrayBuffer to base64 string
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binaryString = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binaryString += String.fromCharCode(bytes[i]);
        }
        return btoa(binaryString).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    },

    /**
     * Prepare credential request options for navigator.credentials.create()
     */
    prepareCreationOptions(serverOptions) {
        const options = { ...serverOptions };
        
        // Convert challenge
        options.challenge = this.base64ToArrayBuffer(options.challenge);
        
        // Convert user ID
        if (options.user && options.user.id) {
            options.user.id = this.base64ToArrayBuffer(options.user.id);
        }
        
        // Convert excluded credentials
        if (options.excludeCredentials) {
            options.excludeCredentials = options.excludeCredentials.map(cred => ({
                ...cred,
                id: this.base64ToArrayBuffer(cred.id)
            }));
        }
        
        return options;
    },

    /**
     * Prepare credential request options for navigator.credentials.get()
     */
    prepareRequestOptions(serverOptions) {
        const options = { ...serverOptions };
        
        // Convert challenge
        options.challenge = this.base64ToArrayBuffer(options.challenge);
        
        // Convert allowed credentials
        if (options.allowCredentials) {
            options.allowCredentials = options.allowCredentials.map(cred => ({
                ...cred,
                id: this.base64ToArrayBuffer(cred.id)
            }));
        }
        
        return options;
    },

    /**
     * Prepare credential response for server
     */
    prepareCredentialForServer(credential) {
        const response = credential.response;
        
        if (response.attestationObject) {
            // Registration response
            return {
                id: credential.id,
                rawId: this.arrayBufferToBase64(credential.rawId),
                type: credential.type,
                response: {
                    attestationObject: this.arrayBufferToBase64(response.attestationObject),
                    clientDataJSON: this.arrayBufferToBase64(response.clientDataJSON)
                }
            };
        } else {
            // Authentication response
            return {
                id: credential.id,
                rawId: this.arrayBufferToBase64(credential.rawId),
                type: credential.type,
                response: {
                    authenticatorData: this.arrayBufferToBase64(response.authenticatorData),
                    clientDataJSON: this.arrayBufferToBase64(response.clientDataJSON),
                    signature: this.arrayBufferToBase64(response.signature),
                    userHandle: response.userHandle ? this.arrayBufferToBase64(response.userHandle) : null
                }
            };
        }
    }
};

const WebAuthnRegistration = {
    /**
     * Begin credential registration process
     */
    async begin(credentialName = 'Security Key') {
        if (!WebAuthnSupport.isSupported()) {
            throw new Error('WebAuthn is not supported in this browser');
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (!csrfToken) {
                throw new Error('CSRF token not found');
            }

            // Request registration options from server
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
                const error = await response.json();
                throw new Error(error.error || 'Failed to start registration');
            }

            const options = await response.json();
            return this.createCredential(options, credentialName, csrfToken);

        } catch (error) {
            console.error('WebAuthn registration begin failed:', error);
            throw error;
        }
    },

    /**
     * Create credential using WebAuthn API
     */
    async createCredential(serverOptions, credentialName, csrfToken) {
        try {
            // Prepare options for WebAuthn API
            const options = WebAuthnUtils.prepareCreationOptions(serverOptions);
            
            // Create credential
            const credential = await navigator.credentials.create({
                publicKey: options
            });

            if (!credential) {
                throw new Error('Credential creation was cancelled');
            }

            // Complete registration on server
            return await this.complete(credential, credentialName, csrfToken);

        } catch (error) {
            if (error.name === 'NotAllowedError') {
                throw new Error('Registration was cancelled or timed out');
            } else if (error.name === 'SecurityError') {
                throw new Error('Security error occurred during registration');
            } else if (error.name === 'NotSupportedError') {
                throw new Error('This type of authenticator is not supported');
            } else {
                throw error;
            }
        }
    },

    /**
     * Complete registration process
     */
    async complete(credential, credentialName, csrfToken) {
        try {
            const credentialData = WebAuthnUtils.prepareCredentialForServer(credential);
            
            const response = await fetch('/auth/webauthn/register/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: credentialData,
                    credential_name: credentialName,
                    csrf_token: csrfToken
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                return { success: true, message: result.message };
            } else {
                throw new Error(result.error || 'Registration verification failed');
            }

        } catch (error) {
            console.error('WebAuthn registration complete failed:', error);
            throw error;
        }
    }
};

const WebAuthnAuthentication = {
    /**
     * Begin authentication process
     */
    async begin(email) {
        if (!WebAuthnSupport.isSupported()) {
            throw new Error('WebAuthn is not supported in this browser');
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (!csrfToken) {
                throw new Error('CSRF token not found');
            }

            // Request authentication options from server
            const response = await fetch('/auth/webauthn/authenticate/begin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    csrf_token: csrfToken
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to start authentication');
            }

            const options = await response.json();
            return this.getCredential(options, csrfToken);

        } catch (error) {
            console.error('WebAuthn authentication begin failed:', error);
            throw error;
        }
    },

    /**
     * Get credential using WebAuthn API
     */
    async getCredential(serverOptions, csrfToken) {
        try {
            // Prepare options for WebAuthn API
            const options = WebAuthnUtils.prepareRequestOptions(serverOptions);
            
            // Get credential
            const credential = await navigator.credentials.get({
                publicKey: options
            });

            if (!credential) {
                throw new Error('Authentication was cancelled');
            }

            // Complete authentication on server
            return await this.complete(credential, csrfToken);

        } catch (error) {
            if (error.name === 'NotAllowedError') {
                throw new Error('Authentication was cancelled or timed out');
            } else if (error.name === 'SecurityError') {
                throw new Error('Security error occurred during authentication');
            } else {
                throw error;
            }
        }
    },

    /**
     * Complete authentication process
     */
    async complete(credential, csrfToken) {
        try {
            const credentialData = WebAuthnUtils.prepareCredentialForServer(credential);
            
            const response = await fetch('/auth/webauthn/authenticate/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: credentialData,
                    csrf_token: csrfToken
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                return { 
                    success: true, 
                    redirect: result.redirect 
                };
            } else {
                throw new Error(result.error || 'Authentication verification failed');
            }

        } catch (error) {
            console.error('WebAuthn authentication complete failed:', error);
            throw error;
        }
    }
};

// Main WebAuthn Manager combining all functionality
const WebAuthnManager = {
    // Registration
    async beginRegistration(credentialName) {
        return WebAuthnRegistration.begin(credentialName);
    },

    // Authentication
    async beginAuthentication(email) {
        return WebAuthnAuthentication.begin(email);
    },

    // Utility functions
    isSupported: WebAuthnSupport.isSupported,
    isPlatformAuthenticatorAvailable: WebAuthnSupport.isPlatformAuthenticatorAvailable,
    
    // Credential management (placeholder for future implementation)
    async manageCredentials() {
        // This would show a modal or navigate to a credential management page
        console.log('Credential management not yet implemented');
        alert('Credential management interface coming soon!');
    }
};

// Export for global use
window.WebAuthnManager = WebAuthnManager;
window.WebAuthnSupport = WebAuthnSupport;