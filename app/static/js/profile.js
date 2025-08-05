/**
 * Profile Management JavaScript
 * Handles profile tabs and user preference management
 */

const ProfileManager = {
    init() {
        this.bindTabEvents();
        this.bindFormEvents();
    },

    bindTabEvents() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const targetTab = e.target.getAttribute('data-tab');
                
                // Remove active class from all tabs and buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button and corresponding content
                e.target.classList.add('active');
                document.getElementById(`${targetTab}-tab`).classList.add('active');
            });
        });
    },

    bindFormEvents() {
        const profileForm = document.querySelector('.profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', this.handleProfileUpdate.bind(this));
        }
    },

    async handleProfileUpdate(event) {
        // Let the form submit normally for now
        // Could be enhanced with AJAX submission in the future
    }
};

/**
 * Two-Factor Setup Management
 */
const TwoFactorSetup = {
    currentStep: 1,
    selectedMethod: null,

    init() {
        this.bindEvents();
        this.showStep(1);
    },

    bindEvents() {
        // Method selection
        const methodOptions = document.querySelectorAll('.method-option');
        methodOptions.forEach(option => {
            option.addEventListener('click', this.selectMethod.bind(this));
        });

        // Navigation buttons
        const continueBtn = document.getElementById('continue-setup');
        const startRegBtn = document.getElementById('start-registration');
        const backBtn = document.getElementById('back-to-methods');

        if (continueBtn) {
            continueBtn.addEventListener('click', this.continueToStep2.bind(this));
        }

        if (startRegBtn) {
            startRegBtn.addEventListener('click', this.startRegistration.bind(this));
        }

        if (backBtn) {
            backBtn.addEventListener('click', this.backToStep1.bind(this));
        }
    },

    selectMethod(event) {
        const option = event.currentTarget;
        const method = option.getAttribute('data-method');

        // Remove selection from all options
        document.querySelectorAll('.method-option').forEach(opt => {
            opt.classList.remove('selected');
        });

        // Select this option
        option.classList.add('selected');
        this.selectedMethod = method;

        // Enable continue button
        const continueBtn = document.getElementById('continue-setup');
        if (continueBtn) {
            continueBtn.disabled = false;
        }
    },

    continueToStep2() {
        if (!this.selectedMethod) return;
        this.showStep(2);
    },

    backToStep1() {
        this.showStep(1);
    },

    async startRegistration() {
        if (!window.WebAuthnManager) {
            this.showError('WebAuthn not available');
            return;
        }

        try {
            this.showRegistrationStatus('Starting registration...', 'loading');
            
            const credentialName = document.getElementById('credential-name').value || 'Security Key';
            const result = await WebAuthnManager.beginRegistration(credentialName);

            if (result.success) {
                this.showRegistrationStatus('Registration successful!', 'success');
                setTimeout(() => {
                    this.showStep(3);
                }, 2000);
            } else {
                this.showRegistrationStatus(result.error || 'Registration failed', 'error');
            }

        } catch (error) {
            this.showRegistrationStatus('Registration failed: ' + error.message, 'error');
        }
    },

    showStep(step) {
        // Hide all steps
        document.querySelectorAll('.step').forEach(stepEl => {
            stepEl.classList.remove('active');
        });

        // Show target step
        const targetStep = document.getElementById(`step-${step}`);
        if (targetStep) {
            targetStep.classList.add('active');
        }

        this.currentStep = step;
    },

    showRegistrationStatus(message, type) {
        const statusEl = document.getElementById('registration-status');
        const iconEl = statusEl.querySelector('.status-icon');
        const messageEl = statusEl.querySelector('.status-message');

        statusEl.className = `registration-status ${type}`;
        messageEl.textContent = message;

        // Update icon
        iconEl.className = 'status-icon';
        switch (type) {
            case 'loading':
                iconEl.classList.add('loading');
                break;
            case 'success':
                iconEl.classList.add('success');
                break;
            case 'error':
                iconEl.classList.add('error');
                break;
        }

        statusEl.style.display = 'block';
    },

    showError(message) {
        this.showRegistrationStatus(message, 'error');
    }
};

// Export for use in templates
window.ProfileManager = ProfileManager;
window.TwoFactorSetup = TwoFactorSetup;