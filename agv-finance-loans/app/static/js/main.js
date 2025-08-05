// AGV Finance and Loans - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.querySelector('.btn-close')) {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize number formatting
    initializeNumberFormatting();
    
    // Initialize auto-save functionality
    initializeAutoSave();
});

// Search Functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"]');
    
    searchInputs.forEach(function(input) {
        let timeout;
        
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                // Auto-submit search after 500ms of no typing
                if (input.value.length >= 2 || input.value.length === 0) {
                    const form = input.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            }, 500);
        });
    });
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Custom validators
    addCustomValidators();
}

// Custom Validators
function addCustomValidators() {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const email = input.value;
            const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
            
            if (email && !isValid) {
                input.setCustomValidity('Please enter a valid email address');
            } else {
                input.setCustomValidity('');
            }
        });
    });
    
    // Phone validation
    const phoneInputs = document.querySelectorAll('input[data-validate="phone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const phone = input.value.replace(/\D/g, '');
            const isValid = /^[6-9]\d{9}$/.test(phone) || /^91[6-9]\d{9}$/.test(phone);
            
            if (phone && !isValid) {
                input.setCustomValidity('Please enter a valid Indian mobile number');
            } else {
                input.setCustomValidity('');
            }
        });
    });
    
    // PAN validation
    const panInputs = document.querySelectorAll('input[data-validate="pan"]');
    panInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const pan = input.value.toUpperCase();
            const isValid = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(pan);
            
            input.value = pan;
            
            if (pan && !isValid) {
                input.setCustomValidity('Please enter a valid PAN number (e.g., ABCDE1234F)');
            } else {
                input.setCustomValidity('');
            }
        });
    });
    
    // Aadhaar validation
    const aadhaarInputs = document.querySelectorAll('input[data-validate="aadhaar"]');
    aadhaarInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const aadhaar = input.value.replace(/\D/g, '');
            const isValid = aadhaar.length === 12;
            
            if (aadhaar && !isValid) {
                input.setCustomValidity('Please enter a valid 12-digit Aadhaar number');
            } else {
                input.setCustomValidity('');
            }
        });
    });
}

// Number Formatting
function initializeNumberFormatting() {
    // Currency inputs
    const currencyInputs = document.querySelectorAll('input[data-format="currency"]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            let value = input.value.replace(/[^\d.]/g, '');
            input.value = value;
        });
        
        input.addEventListener('blur', function() {
            const value = parseFloat(input.value);
            if (!isNaN(value)) {
                input.value = value.toLocaleString('en-IN', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2
                });
            }
        });
        
        input.addEventListener('focus', function() {
            input.value = input.value.replace(/,/g, '');
        });
    });
    
    // Percentage inputs
    const percentageInputs = document.querySelectorAll('input[data-format="percentage"]');
    percentageInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            let value = input.value.replace(/[^\d.]/g, '');
            if (parseFloat(value) > 100) {
                value = '100';
            }
            input.value = value;
        });
    });
}

// Auto-save Functionality
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(function(input) {
            input.addEventListener('change', function() {
                saveFormData(form);
            });
        });
        
        // Load saved data on page load
        loadFormData(form);
    });
}

function saveFormData(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const formId = form.id || 'form_' + Date.now();
    
    localStorage.setItem('autosave_' + formId, JSON.stringify(data));
    
    // Show auto-save indicator
    showAutoSaveIndicator();
}

function loadFormData(form) {
    const formId = form.id || 'form_' + Date.now();
    const savedData = localStorage.getItem('autosave_' + formId);
    
    if (savedData) {
        const data = JSON.parse(savedData);
        
        Object.keys(data).forEach(function(key) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });
    }
}

function clearSavedFormData(form) {
    const formId = form.id || 'form_' + Date.now();
    localStorage.removeItem('autosave_' + formId);
}

function showAutoSaveIndicator() {
    const indicator = document.getElementById('autoSaveIndicator');
    if (indicator) {
        indicator.style.display = 'inline';
        setTimeout(function() {
            indicator.style.display = 'none';
        }, 2000);
    }
}

// Utility Functions
function formatCurrency(amount, currency = '₹') {
    if (isNaN(amount)) return currency + '0';
    
    return currency + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function formatPercentage(value, decimals = 2) {
    if (isNaN(value)) return '0%';
    return parseFloat(value).toFixed(decimals) + '%';
}

function formatDate(date, format = 'dd/mm/yyyy') {
    if (!date) return '-';
    
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    
    switch (format) {
        case 'dd/mm/yyyy':
            return `${day}/${month}/${year}`;
        case 'dd-mm-yyyy':
            return `${day}-${month}-${year}`;
        case 'yyyy-mm-dd':
            return `${year}-${month}-${day}`;
        default:
            return d.toLocaleDateString('en-IN');
    }
}

function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    spinner.setAttribute('role', 'status');
    
    element.prepend(spinner);
    element.disabled = true;
}

function hideLoading(element) {
    const spinner = element.querySelector('.spinner-border');
    if (spinner) {
        spinner.remove();
    }
    element.disabled = false;
}

function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${getAlertIcon(type)}
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after duration
    setTimeout(function() {
        if (alert.parentNode) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, duration);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    const icons = {
        'success': '<i class="fas fa-check-circle me-2"></i>',
        'danger': '<i class="fas fa-exclamation-triangle me-2"></i>',
        'warning': '<i class="fas fa-exclamation-circle me-2"></i>',
        'info': '<i class="fas fa-info-circle me-2"></i>'
    };
    
    return icons[type] || icons['info'];
}

// AJAX Helper
function makeRequest(url, method = 'GET', data = null, headers = {}) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        
        // Set default headers
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        
        // Set custom headers
        Object.keys(headers).forEach(function(key) {
            xhr.setRequestHeader(key, headers[key]);
        });
        
        // Set content type for POST requests
        if (method === 'POST' && data && !(data instanceof FormData)) {
            xhr.setRequestHeader('Content-Type', 'application/json');
        }
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    resolve(xhr.responseText);
                }
            } else {
                reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
            }
        };
        
        xhr.onerror = function() {
            reject(new Error('Network error'));
        };
        
        // Send request
        if (data) {
            if (data instanceof FormData) {
                xhr.send(data);
            } else {
                xhr.send(JSON.stringify(data));
            }
        } else {
            xhr.send();
        }
    });
}

// Export functions for use in other scripts
window.AGVFinance = {
    formatCurrency,
    formatPercentage,
    formatDate,
    showLoading,
    hideLoading,
    showAlert,
    makeRequest,
    saveFormData,
    loadFormData,
    clearSavedFormData
};