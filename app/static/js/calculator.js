// Calculator JavaScript for AGV Finance

// Calculator state
let calculatorState = {
    emi: {
        principal: 0,
        rate: 0,
        tenure: 0,
        result: null
    },
    goldLoan: {
        weight: 0,
        purity: 22,
        rate: 5000,
        ltv: 75,
        result: null
    }
};

// Initialize calculators when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCalculators();
    setupCalculatorEventListeners();
    loadDefaultValues();
});

// Initialize calculators
function initializeCalculators() {
    console.log('Calculators initialized');
    
    // Setup input formatters
    setupInputFormatters();
    
    // Setup real-time calculation
    setupRealTimeCalculation();
    
    // Setup result animations
    setupResultAnimations();
}

// Setup calculator event listeners
function setupCalculatorEventListeners() {
    // EMI Calculator form
    const emiForm = document.getElementById('emiCalculatorForm');
    if (emiForm) {
        emiForm.addEventListener('submit', handleEmiCalculation);
        
        // Real-time calculation on input change
        const emiInputs = emiForm.querySelectorAll('input');
        emiInputs.forEach(input => {
            input.addEventListener('input', debounce(calculateEmiRealTime, 500));
        });
    }
    
    // Gold Loan Calculator form
    const goldLoanForm = document.getElementById('goldLoanCalculatorForm');
    if (goldLoanForm) {
        goldLoanForm.addEventListener('submit', handleGoldLoanCalculation);
        
        // Real-time calculation on input change
        const goldLoanInputs = goldLoanForm.querySelectorAll('input, select');
        goldLoanInputs.forEach(input => {
            input.addEventListener('input', debounce(calculateGoldLoanRealTime, 500));
            input.addEventListener('change', debounce(calculateGoldLoanRealTime, 500));
        });
    }
    
    // Slider inputs for better UX
    setupSliderInputs();
    
    // Copy result buttons
    setupCopyResultButtons();
}

// Load default values
function loadDefaultValues() {
    // Load saved values from localStorage
    const savedEmi = localStorage.getItem('agv_emi_calculator');
    if (savedEmi) {
        const emiData = JSON.parse(savedEmi);
        populateEmiForm(emiData);
    }
    
    const savedGoldLoan = localStorage.getItem('agv_gold_loan_calculator');
    if (savedGoldLoan) {
        const goldLoanData = JSON.parse(savedGoldLoan);
        populateGoldLoanForm(goldLoanData);
    }
    
    // Set current gold rates (this would come from an API in production)
    updateCurrentGoldRates();
}

// Setup input formatters
function setupInputFormatters() {
    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = formatCurrencyInput(this.value);
            }
        });
    });
    
    // Format percentage inputs
    const percentageInputs = document.querySelectorAll('.percentage-input');
    percentageInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                const value = parseFloat(this.value);
                this.value = value.toFixed(2);
            }
        });
    });
}

// Setup real-time calculation
function setupRealTimeCalculation() {
    const realtimeCheckbox = document.getElementById('realtimeCalculation');
    if (realtimeCheckbox) {
        realtimeCheckbox.addEventListener('change', function() {
            if (this.checked) {
                calculateEmiRealTime();
                calculateGoldLoanRealTime();
            }
        });
    }
}

// Setup result animations
function setupResultAnimations() {
    // Add animation classes to result containers
    const resultContainers = document.querySelectorAll('.calculation-result');
    resultContainers.forEach(container => {
        container.classList.add('result-container');
    });
}

// Handle EMI calculation
async function handleEmiCalculation(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const principal = parseFloat(formData.get('principal')) || 0;
    const rate = parseFloat(formData.get('rate')) || 0;
    const tenure = parseInt(formData.get('tenure')) || 0;
    
    if (principal <= 0 || rate <= 0 || tenure <= 0) {
        showCalculatorError('emiResult', 'Please enter valid values for all fields.');
        return;
    }
    
    try {
        showCalculatorLoading('emiResult');
        
        const result = await calculateEmi(principal, rate, tenure);
        displayEmiResult(result);
        
        // Save to localStorage
        saveEmiData({ principal, rate, tenure });
        
    } catch (error) {
        showCalculatorError('emiResult', error.message || 'Calculation failed. Please try again.');
    }
}

// Handle Gold Loan calculation
async function handleGoldLoanCalculation(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const weight = parseFloat(formData.get('weight')) || 0;
    const purity = parseFloat(formData.get('purity')) || 22;
    const rate = parseFloat(formData.get('rate')) || 0;
    const ltv = parseFloat(formData.get('ltv')) || 75;
    
    if (weight <= 0 || rate <= 0) {
        showCalculatorError('goldLoanResult', 'Please enter valid values for weight and rate.');
        return;
    }
    
    try {
        showCalculatorLoading('goldLoanResult');
        
        const result = await calculateGoldLoan(weight, purity, rate, ltv);
        displayGoldLoanResult(result);
        
        // Save to localStorage
        saveGoldLoanData({ weight, purity, rate, ltv });
        
    } catch (error) {
        showCalculatorError('goldLoanResult', error.message || 'Calculation failed. Please try again.');
    }
}

// Calculate EMI
async function calculateEmi(principal, rate, tenure) {
    const response = await fetch('/api/calculate-emi', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ principal, rate, tenure })
    });
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.error);
    }
    
    return result;
}

// Calculate Gold Loan
async function calculateGoldLoan(weight, purity, rate, ltv = 75) {
    const response = await fetch('/api/calculate-gold-loan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ weight, purity, rate, ltv })
    });
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.error);
    }
    
    return result;
}

// Calculate EMI in real-time
async function calculateEmiRealTime() {
    const realtimeCheckbox = document.getElementById('realtimeCalculation');
    if (!realtimeCheckbox || !realtimeCheckbox.checked) return;
    
    const principal = parseFloat(document.getElementById('principal')?.value) || 0;
    const rate = parseFloat(document.getElementById('rate')?.value) || 0;
    const tenure = parseInt(document.getElementById('tenure')?.value) || 0;
    
    if (principal > 0 && rate > 0 && tenure > 0) {
        try {
            const result = await calculateEmi(principal, rate, tenure);
            displayEmiResult(result, true);
        } catch (error) {
            // Silently fail for real-time calculation
            console.error('Real-time EMI calculation error:', error);
        }
    }
}

// Calculate Gold Loan in real-time
async function calculateGoldLoanRealTime() {
    const realtimeCheckbox = document.getElementById('realtimeCalculation');
    if (!realtimeCheckbox || !realtimeCheckbox.checked) return;
    
    const weight = parseFloat(document.getElementById('goldWeight')?.value) || 0;
    const purity = parseFloat(document.getElementById('goldPurity')?.value) || 22;
    const rate = parseFloat(document.getElementById('goldRate')?.value) || 0;
    
    if (weight > 0 && rate > 0) {
        try {
            const result = await calculateGoldLoan(weight, purity, rate);
            displayGoldLoanResult(result, true);
        } catch (error) {
            // Silently fail for real-time calculation
            console.error('Real-time Gold Loan calculation error:', error);
        }
    }
}

// Display EMI result
function displayEmiResult(result, isRealtime = false) {
    const resultContainer = document.getElementById('emiResult');
    if (!resultContainer) return;
    
    resultContainer.innerHTML = `
        <div class="alert alert-success calculation-result ${isRealtime ? 'realtime-result' : ''}" role="alert">
            <h6 class="mb-3"><i class="bi bi-calculator"></i> EMI Calculation Result</h6>
            <div class="row g-3">
                <div class="col-md-4">
                    <div class="result-item text-center">
                        <h4 class="text-primary mb-1">₹${result.emi.toLocaleString('en-IN')}</h4>
                        <small class="text-muted">Monthly EMI</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="result-item text-center">
                        <h5 class="text-success mb-1">₹${result.total_amount.toLocaleString('en-IN')}</h5>
                        <small class="text-muted">Total Amount</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="result-item text-center">
                        <h5 class="text-warning mb-1">₹${result.total_interest.toLocaleString('en-IN')}</h5>
                        <small class="text-muted">Total Interest</small>
                    </div>
                </div>
            </div>
            <hr class="my-3">
            <div class="d-flex gap-2">
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="showPaymentSchedule(${JSON.stringify(result).replace(/"/g, '&quot;')})">
                    <i class="bi bi-table"></i> Payment Schedule
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="copyCalculationResult('emi', ${JSON.stringify(result).replace(/"/g, '&quot;')})">
                    <i class="bi bi-clipboard"></i> Copy Result
                </button>
                <button type="button" class="btn btn-sm btn-outline-info" onclick="shareCalculation('emi')">
                    <i class="bi bi-share"></i> Share
                </button>
            </div>
        </div>
    `;
    
    resultContainer.classList.remove('d-none');
    animateResult(resultContainer);
    
    // Update state
    calculatorState.emi.result = result;
}

// Display Gold Loan result
function displayGoldLoanResult(result, isRealtime = false) {
    const resultContainer = document.getElementById('goldLoanResult');
    if (!resultContainer) return;
    
    resultContainer.innerHTML = `
        <div class="alert alert-warning calculation-result ${isRealtime ? 'realtime-result' : ''}" role="alert">
            <h6 class="mb-3"><i class="bi bi-gem"></i> Gold Loan Calculation Result</h6>
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="result-item text-center">
                        <h4 class="text-warning mb-1">₹${result.eligible_amount.toLocaleString('en-IN')}</h4>
                        <small class="text-muted">Eligible Loan Amount</small>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-item text-center">
                        <h5 class="text-info mb-1">₹${result.gold_value.toLocaleString('en-IN')}</h5>
                        <small class="text-muted">Total Gold Value</small>
                    </div>
                </div>
            </div>
            <hr class="my-3">
            <div class="row text-center">
                <div class="col-6">
                    <small class="text-muted d-block">LTV Ratio</small>
                    <strong>75%</strong>
                </div>
                <div class="col-6">
                    <small class="text-muted d-block">Purity</small>
                    <strong>${result.details.purity_percentage || 0}%</strong>
                </div>
            </div>
            <hr class="my-3">
            <div class="d-flex gap-2">
                <button type="button" class="btn btn-sm btn-outline-warning" onclick="generateGoldLoanQuote(${JSON.stringify(result).replace(/"/g, '&quot;')})">
                    <i class="bi bi-file-text"></i> Generate Quote
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="copyCalculationResult('goldLoan', ${JSON.stringify(result).replace(/"/g, '&quot;')})">
                    <i class="bi bi-clipboard"></i> Copy Result
                </button>
            </div>
        </div>
    `;
    
    resultContainer.classList.remove('d-none');
    animateResult(resultContainer);
    
    // Update state
    calculatorState.goldLoan.result = result;
}

// Show calculator loading
function showCalculatorLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Calculating...</span>
            </div>
            <p class="mt-2 text-muted">Calculating...</p>
        </div>
    `;
    
    container.classList.remove('d-none');
}

// Show calculator error
function showCalculatorError(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${message}
        </div>
    `;
    
    container.classList.remove('d-none');
}

// Animate result display
function animateResult(container) {
    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';
    
    requestAnimationFrame(() => {
        container.style.transition = 'all 0.3s ease';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    });
}

// Setup slider inputs
function setupSliderInputs() {
    // Create range sliders for better UX
    const numericInputs = document.querySelectorAll('input[type="number"]');
    
    numericInputs.forEach(input => {
        const slider = createSliderForInput(input);
        if (slider) {
            input.parentNode.appendChild(slider);
        }
    });
}

// Create slider for input
function createSliderForInput(input) {
    const min = input.min || 0;
    const max = input.max || (input.id === 'principal' ? 10000000 : input.id === 'tenure' ? 360 : 30);
    const step = input.step || 1;
    
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.className = 'form-range mt-2';
    slider.min = min;
    slider.max = max;
    slider.step = step;
    slider.value = input.value || min;
    
    // Sync slider with input
    slider.addEventListener('input', function() {
        input.value = this.value;
        input.dispatchEvent(new Event('input'));
    });
    
    input.addEventListener('input', function() {
        slider.value = this.value;
    });
    
    return slider;
}

// Setup copy result buttons
function setupCopyResultButtons() {
    // Already handled in displayResult functions
}

// Copy calculation result
function copyCalculationResult(type, result) {
    let text = '';
    
    if (type === 'emi') {
        text = `EMI Calculation Result\n` +
               `Monthly EMI: ₹${result.emi.toLocaleString('en-IN')}\n` +
               `Total Amount: ₹${result.total_amount.toLocaleString('en-IN')}\n` +
               `Total Interest: ₹${result.total_interest.toLocaleString('en-IN')}`;
    } else if (type === 'goldLoan') {
        text = `Gold Loan Calculation Result\n` +
               `Eligible Amount: ₹${result.eligible_amount.toLocaleString('en-IN')}\n` +
               `Gold Value: ₹${result.gold_value.toLocaleString('en-IN')}\n` +
               `LTV Ratio: 75%`;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showAlert('success', 'Calculation result copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showAlert('error', 'Failed to copy result. Please try again.');
    });
}

// Share calculation
function shareCalculation(type) {
    if (navigator.share) {
        const shareData = {
            title: `AGV Finance - ${type === 'emi' ? 'EMI' : 'Gold Loan'} Calculator`,
            text: `Check out this ${type === 'emi' ? 'EMI' : 'Gold Loan'} calculation from AGV Finance`,
            url: window.location.href
        };
        
        navigator.share(shareData);
    } else {
        // Fallback to copying URL
        navigator.clipboard.writeText(window.location.href).then(() => {
            showAlert('success', 'Calculator URL copied to clipboard!');
        });
    }
}

// Show payment schedule
function showPaymentSchedule(result) {
    // This would open a modal with detailed payment schedule
    console.log('Payment schedule for:', result);
    showAlert('info', 'Payment schedule feature coming soon!');
}

// Generate gold loan quote
function generateGoldLoanQuote(result) {
    // This would generate a formal quote
    console.log('Generate quote for:', result);
    showAlert('info', 'Quote generation feature coming soon!');
}

// Save EMI data
function saveEmiData(data) {
    localStorage.setItem('agv_emi_calculator', JSON.stringify(data));
}

// Save Gold Loan data
function saveGoldLoanData(data) {
    localStorage.setItem('agv_gold_loan_calculator', JSON.stringify(data));
}

// Populate EMI form
function populateEmiForm(data) {
    if (data.principal) document.getElementById('principal').value = data.principal;
    if (data.rate) document.getElementById('rate').value = data.rate;
    if (data.tenure) document.getElementById('tenure').value = data.tenure;
}

// Populate Gold Loan form
function populateGoldLoanForm(data) {
    if (data.weight) document.getElementById('goldWeight').value = data.weight;
    if (data.purity) document.getElementById('goldPurity').value = data.purity;
    if (data.rate) document.getElementById('goldRate').value = data.rate;
}

// Update current gold rates
function updateCurrentGoldRates() {
    // In production, this would fetch from an API
    const goldRateInput = document.getElementById('goldRate');
    if (goldRateInput && !goldRateInput.value) {
        goldRateInput.value = 5000; // Default rate
    }
}

// Format currency input
function formatCurrencyInput(value) {
    const num = parseFloat(value.replace(/[^\d.]/g, ''));
    return isNaN(num) ? '' : num.toLocaleString('en-IN');
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export calculator functions
window.Calculator = {
    calculateEmi,
    calculateGoldLoan,
    copyCalculationResult,
    shareCalculation,
    showPaymentSchedule,
    generateGoldLoanQuote
};