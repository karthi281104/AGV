// AGV Finance and Loans - Main JavaScript

// Global variables
let currentUser = null;
let notifications = [];

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadCurrentUser();
});

// Initialize application
function initializeApp() {
    console.log('AGV Finance App Initialized');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize popovers
    initializePopovers();
    
    // Setup form validation
    setupFormValidation();
    
    // Setup AJAX error handling
    setupAjaxErrorHandling();
}

// Setup event listeners
function setupEventListeners() {
    // File upload handlers
    setupFileUploadHandlers();
    
    // Form submission handlers
    setupFormSubmissionHandlers();
    
    // Search handlers
    setupSearchHandlers();
    
    // Navigation handlers
    setupNavigationHandlers();
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Bootstrap popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Setup form validation
function setupFormValidation() {
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
}

// Setup AJAX error handling
function setupAjaxErrorHandling() {
    // Global fetch error handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showAlert('error', 'An unexpected error occurred. Please try again.');
    });
}

// Setup file upload handlers
function setupFileUploadHandlers() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        const dropZone = input.closest('.file-upload-area');
        
        if (dropZone) {
            // Drag and drop handlers
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
            
            dropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            });
            
            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                input.files = files;
                updateFileList(input);
            });
        }
        
        // File selection handler
        input.addEventListener('change', function() {
            updateFileList(input);
        });
    });
}

// Update file list display
function updateFileList(input) {
    const fileList = input.parentElement.querySelector('.file-list');
    if (!fileList) return;
    
    fileList.innerHTML = '';
    
    for (let i = 0; i < input.files.length; i++) {
        const file = input.files[i];
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex align-items-center justify-content-between p-2 bg-light rounded mt-2';
        
        fileItem.innerHTML = `
            <span><i class="bi bi-file-earmark"></i> ${file.name}</span>
            <small class="text-muted">${formatFileSize(file.size)}</small>
        `;
        
        fileList.appendChild(fileItem);
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Setup form submission handlers
function setupFormSubmissionHandlers() {
    const ajaxForms = document.querySelectorAll('.ajax-form');
    
    ajaxForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormAjax(form);
        });
    });
}

// Submit form via AJAX
async function submitFormAjax(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: form.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', result.message || 'Operation completed successfully.');
            
            if (result.redirect) {
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 1000);
            }
        } else {
            showAlert('error', result.error || 'Operation failed.');
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showAlert('error', 'An error occurred while processing your request.');
    } finally {
        // Reset button state
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }
}

// Setup search handlers
function setupSearchHandlers() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(function(input) {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(input);
            }, 300);
        });
    });
}

// Perform search
async function performSearch(input) {
    const query = input.value.trim();
    const searchUrl = input.dataset.searchUrl;
    const resultsContainer = document.querySelector(input.dataset.resultsContainer);
    
    if (!query || !searchUrl || !resultsContainer) return;
    
    try {
        const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
        const results = await response.json();
        
        displaySearchResults(results, resultsContainer);
    } catch (error) {
        console.error('Search error:', error);
    }
}

// Display search results
function displaySearchResults(results, container) {
    container.innerHTML = '';
    
    if (results.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3">No results found.</p>';
        return;
    }
    
    results.forEach(function(result) {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item p-2 border-bottom';
        resultItem.innerHTML = formatSearchResult(result);
        container.appendChild(resultItem);
    });
}

// Format search result
function formatSearchResult(result) {
    return `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-1">${result.name}</h6>
                <small class="text-muted">${result.identifier || ''}</small>
            </div>
            <small class="text-muted">${result.type || ''}</small>
        </div>
    `;
}

// Setup navigation handlers
function setupNavigationHandlers() {
    // Handle navigation timing
    const navigationItems = document.querySelectorAll('.nav-link');
    
    navigationItems.forEach(function(item) {
        item.addEventListener('click', function() {
            // Add loading state to navigation
            showPageLoading();
        });
    });
}

// Show page loading
function showPageLoading() {
    const loader = document.createElement('div');
    loader.id = 'page-loader';
    loader.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
    loader.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
    loader.style.zIndex = '9999';
    loader.innerHTML = '<div class="spinner-border text-primary"></div>';
    
    document.body.appendChild(loader);
    
    // Remove loader after navigation or timeout
    setTimeout(() => {
        const existingLoader = document.getElementById('page-loader');
        if (existingLoader) {
            existingLoader.remove();
        }
    }, 3000);
}

// Load current user information
async function loadCurrentUser() {
    try {
        const userMeta = document.querySelector('meta[name="current-user"]');
        if (userMeta) {
            currentUser = JSON.parse(userMeta.content);
        }
    } catch (error) {
        console.error('Error loading user information:', error);
    }
}

// Show alert message
function showAlert(type, message, duration = 5000) {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertElement);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (alertElement.parentElement) {
            alertElement.remove();
        }
    }, duration);
}

// Create alert container if it doesn't exist
function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

// Format currency for display
function formatCurrency(amount, currency = '₹') {
    if (typeof amount !== 'number') {
        amount = parseFloat(amount) || 0;
    }
    
    return currency + amount.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Format date for display
function formatDate(dateString, format = 'dd/mm/yyyy') {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    
    switch (format) {
        case 'dd/mm/yyyy':
            return `${day}/${month}/${year}`;
        case 'mm/dd/yyyy':
            return `${month}/${day}/${year}`;
        case 'yyyy-mm-dd':
            return `${year}-${month}-${day}`;
        default:
            return date.toLocaleDateString();
    }
}

// Validate form fields
function validateForm(form) {
    const errors = [];
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            errors.push(`${field.labels[0]?.textContent || field.name} is required.`);
        }
    });
    
    return errors;
}

// Show confirmation dialog
function showConfirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Export functions for use in other scripts
window.AGV = {
    showAlert,
    formatCurrency,
    formatDate,
    validateForm,
    showConfirmDialog,
    submitFormAjax,
    performSearch
};

// Remove page loader when page loads
window.addEventListener('load', function() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.remove();
    }
});