// AGV Finance Calculator Functions

class LoanCalculator {
    static calculateEMI(principal, annualRate, months) {
        if (principal <= 0 || annualRate < 0 || months <= 0) {
            return 0;
        }
        
        const monthlyRate = annualRate / 100 / 12;
        
        if (monthlyRate === 0) {
            return principal / months;
        }
        
        const factor = Math.pow(1 + monthlyRate, months);
        return (principal * monthlyRate * factor) / (factor - 1);
    }
    
    static calculateTotalAmount(principal, annualRate, months) {
        const emi = this.calculateEMI(principal, annualRate, months);
        return emi * months;
    }
    
    static calculateTotalInterest(principal, annualRate, months) {
        const totalAmount = this.calculateTotalAmount(principal, annualRate, months);
        return totalAmount - principal;
    }
    
    static generateAmortizationSchedule(principal, annualRate, months) {
        const emi = this.calculateEMI(principal, annualRate, months);
        const monthlyRate = annualRate / 100 / 12;
        
        const schedule = [];
        let balance = principal;
        
        for (let month = 1; month <= months; month++) {
            const interestPayment = balance * monthlyRate;
            const principalPayment = emi - interestPayment;
            balance -= principalPayment;
            
            // Ensure balance doesn't go negative due to rounding
            if (balance < 0) {
                balance = 0;
            }
            
            schedule.push({
                month: month,
                emi: emi,
                principal: principalPayment,
                interest: interestPayment,
                balance: balance
            });
        }
        
        return schedule;
    }
    
    static calculatePrepaymentSavings(principal, annualRate, months, prepaymentAmount, prepaymentMonth) {
        const originalSchedule = this.generateAmortizationSchedule(principal, annualRate, months);
        
        if (prepaymentMonth > originalSchedule.length) {
            return null;
        }
        
        const balanceBeforePrepayment = originalSchedule[prepaymentMonth - 1].balance;
        const newBalance = Math.max(0, balanceBeforePrepayment - prepaymentAmount);
        
        if (newBalance === 0) {
            // Full prepayment - calculate savings
            const remainingPayments = months - prepaymentMonth;
            const originalEMI = this.calculateEMI(principal, annualRate, months);
            const savings = remainingPayments * originalEMI;
            
            return {
                savings: savings,
                monthsSaved: remainingPayments,
                newTenure: prepaymentMonth
            };
        } else {
            // Partial prepayment - recalculate EMI for remaining tenure
            const remainingMonths = months - prepaymentMonth;
            const newEMI = this.calculateEMI(newBalance, annualRate, remainingMonths);
            
            const originalRemainingTotal = (months - prepaymentMonth) * this.calculateEMI(principal, annualRate, months);
            const newRemainingTotal = newEMI * remainingMonths;
            
            return {
                savings: originalRemainingTotal - newRemainingTotal,
                newEMI: newEMI,
                monthsSaved: 0,
                newTenure: months
            };
        }
    }
}

class EligibilityCalculator {
    static calculateMaxLoanAmount(monthlyIncome, existingEMI, interestRate, tenureMonths, foirRatio = 0.5) {
        const availableIncome = (monthlyIncome * foirRatio) - existingEMI;
        
        if (availableIncome <= 0) {
            return 0;
        }
        
        const monthlyRate = interestRate / 100 / 12;
        
        if (monthlyRate === 0) {
            return availableIncome * tenureMonths;
        }
        
        const factor = Math.pow(1 + monthlyRate, tenureMonths);
        return (availableIncome * (factor - 1)) / (monthlyRate * factor);
    }
    
    static calculateDebtToIncomeRatio(monthlyIncome, totalMonthlyObligations) {
        if (monthlyIncome === 0) {
            return 0;
        }
        return (totalMonthlyObligations / monthlyIncome) * 100;
    }
    
    static calculateLoanToValueRatio(loanAmount, assetValue) {
        if (assetValue === 0) {
            return 0;
        }
        return (loanAmount / assetValue) * 100;
    }
    
    static getEligibilityStatus(monthlyIncome, existingEMI, loanAmount, interestRate, tenureMonths) {
        const maxEligible = this.calculateMaxLoanAmount(monthlyIncome, existingEMI, interestRate, tenureMonths);
        const debtRatio = this.calculateDebtToIncomeRatio(monthlyIncome, existingEMI + LoanCalculator.calculateEMI(loanAmount, interestRate, tenureMonths));
        
        let status = 'eligible';
        let message = 'You are eligible for this loan amount.';
        let recommendations = [];
        
        if (loanAmount > maxEligible) {
            status = 'not_eligible';
            message = `Requested amount exceeds eligibility. Maximum eligible: ₹${maxEligible.toLocaleString('en-IN')}`;
            recommendations.push(`Consider reducing loan amount to ₹${maxEligible.toLocaleString('en-IN')}`);
        }
        
        if (debtRatio > 60) {
            status = status === 'eligible' ? 'caution' : status;
            message = status === 'caution' ? 'High debt-to-income ratio. Loan approval may be difficult.' : message;
            recommendations.push('Consider improving income or reducing existing debts');
        }
        
        if (debtRatio > 40 && debtRatio <= 60) {
            recommendations.push('Moderate debt levels. Ensure timely payments on existing loans');
        }
        
        return {
            status: status,
            message: message,
            maxEligible: maxEligible,
            debtRatio: debtRatio,
            recommendations: recommendations
        };
    }
}

// Interactive Calculator Components
class InteractiveEMICalculator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.init();
    }
    
    init() {
        this.createCalculatorHTML();
        this.bindEvents();
        this.calculate();
    }
    
    createCalculatorHTML() {
        this.container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">EMI Calculator</h5>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">Loan Amount (₹)</label>
                            <input type="range" class="form-range" id="principalRange" min="100000" max="10000000" step="50000" value="500000">
                            <input type="number" class="form-control mt-2" id="principalInput" min="100000" max="10000000" value="500000">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Interest Rate (%)</label>
                            <input type="range" class="form-range" id="rateRange" min="5" max="30" step="0.25" value="10.5">
                            <input type="number" class="form-control mt-2" id="rateInput" min="5" max="30" step="0.25" value="10.5">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Tenure (Years)</label>
                            <input type="range" class="form-range" id="tenureRange" min="1" max="30" step="1" value="10">
                            <input type="number" class="form-control mt-2" id="tenureInput" min="1" max="30" value="10">
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-4">
                            <div class="card bg-primary text-white">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Monthly EMI</h6>
                                    <h4 id="emiResult">₹0</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-success text-white">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Total Interest</h6>
                                    <h4 id="interestResult">₹0</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-info text-white">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Total Amount</h6>
                                    <h4 id="totalResult">₹0</h4>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <button class="btn btn-outline-primary" onclick="this.showAmortization()">
                            <i class="fas fa-table me-2"></i>View Amortization Schedule
                        </button>
                        <button class="btn btn-outline-success" onclick="this.showPrepaymentAnalysis()">
                            <i class="fas fa-calculator me-2"></i>Prepayment Analysis
                        </button>
                    </div>
                    
                    <div id="amortizationTable" class="mt-4" style="display: none;"></div>
                    <div id="prepaymentAnalysis" class="mt-4" style="display: none;"></div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        const inputs = ['principal', 'rate', 'tenure'];
        
        inputs.forEach(input => {
            const rangeInput = document.getElementById(input + 'Range');
            const numberInput = document.getElementById(input + 'Input');
            
            rangeInput.addEventListener('input', () => {
                numberInput.value = rangeInput.value;
                this.calculate();
            });
            
            numberInput.addEventListener('input', () => {
                rangeInput.value = numberInput.value;
                this.calculate();
            });
        });
    }
    
    calculate() {
        const principal = parseFloat(document.getElementById('principalInput').value) || 0;
        const rate = parseFloat(document.getElementById('rateInput').value) || 0;
        const tenure = parseFloat(document.getElementById('tenureInput').value) || 0;
        
        if (principal > 0 && rate > 0 && tenure > 0) {
            const months = tenure * 12;
            const emi = LoanCalculator.calculateEMI(principal, rate, months);
            const totalAmount = LoanCalculator.calculateTotalAmount(principal, rate, months);
            const totalInterest = LoanCalculator.calculateTotalInterest(principal, rate, months);
            
            document.getElementById('emiResult').textContent = this.formatCurrency(emi);
            document.getElementById('interestResult').textContent = this.formatCurrency(totalInterest);
            document.getElementById('totalResult').textContent = this.formatCurrency(totalAmount);
        }
    }
    
    formatCurrency(amount) {
        return '₹' + Math.round(amount).toLocaleString('en-IN');
    }
    
    showAmortization() {
        const principal = parseFloat(document.getElementById('principalInput').value) || 0;
        const rate = parseFloat(document.getElementById('rateInput').value) || 0;
        const tenure = parseFloat(document.getElementById('tenureInput').value) || 0;
        
        if (principal > 0 && rate > 0 && tenure > 0) {
            const months = tenure * 12;
            const schedule = LoanCalculator.generateAmortizationSchedule(principal, rate, months);
            
            this.renderAmortizationTable(schedule);
        }
    }
    
    renderAmortizationTable(schedule) {
        const container = document.getElementById('amortizationTable');
        let html = `
            <h6>Amortization Schedule</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>EMI</th>
                            <th>Principal</th>
                            <th>Interest</th>
                            <th>Balance</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Show first 12 months and last 12 months for long tenures
        const showMonths = schedule.length > 24 ? 
            [...schedule.slice(0, 12), ...schedule.slice(-12)] : 
            schedule;
        
        showMonths.forEach((row, index) => {
            if (index === 12 && schedule.length > 24) {
                html += '<tr><td colspan="5" class="text-center text-muted">... (showing first and last 12 months) ...</td></tr>';
            }
            
            html += `
                <tr>
                    <td>${row.month}</td>
                    <td>${this.formatCurrency(row.emi)}</td>
                    <td>${this.formatCurrency(row.principal)}</td>
                    <td>${this.formatCurrency(row.interest)}</td>
                    <td>${this.formatCurrency(row.balance)}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
        container.style.display = 'block';
    }
    
    showPrepaymentAnalysis() {
        const container = document.getElementById('prepaymentAnalysis');
        container.innerHTML = `
            <h6>Prepayment Analysis</h6>
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Prepayment Amount (₹)</label>
                    <input type="number" class="form-control" id="prepaymentAmount" placeholder="Enter amount">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Prepayment After Month</label>
                    <input type="number" class="form-control" id="prepaymentMonth" placeholder="Enter month number">
                </div>
                <div class="col-12">
                    <button class="btn btn-primary" onclick="this.calculatePrepaymentSavings()">Calculate Savings</button>
                </div>
                <div id="prepaymentResults" class="col-12"></div>
            </div>
        `;
        container.style.display = 'block';
    }
    
    calculatePrepaymentSavings() {
        const principal = parseFloat(document.getElementById('principalInput').value) || 0;
        const rate = parseFloat(document.getElementById('rateInput').value) || 0;
        const tenure = parseFloat(document.getElementById('tenureInput').value) || 0;
        const prepaymentAmount = parseFloat(document.getElementById('prepaymentAmount').value) || 0;
        const prepaymentMonth = parseInt(document.getElementById('prepaymentMonth').value) || 0;
        
        if (principal > 0 && rate > 0 && tenure > 0 && prepaymentAmount > 0 && prepaymentMonth > 0) {
            const months = tenure * 12;
            const savings = LoanCalculator.calculatePrepaymentSavings(principal, rate, months, prepaymentAmount, prepaymentMonth);
            
            if (savings) {
                this.renderPrepaymentResults(savings);
            }
        }
    }
    
    renderPrepaymentResults(savings) {
        const container = document.getElementById('prepaymentResults');
        
        let html = `
            <div class="alert alert-success">
                <h6><i class="fas fa-piggy-bank me-2"></i>Prepayment Benefits</h6>
                <p><strong>Total Savings:</strong> ${this.formatCurrency(savings.savings)}</p>
        `;
        
        if (savings.monthsSaved > 0) {
            html += `<p><strong>Months Saved:</strong> ${savings.monthsSaved} months</p>`;
            html += `<p><strong>New Tenure:</strong> ${savings.newTenure} months</p>`;
        } else if (savings.newEMI) {
            html += `<p><strong>New EMI:</strong> ${this.formatCurrency(savings.newEMI)}</p>`;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
}

// Initialize calculators when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize EMI calculator if container exists
    if (document.getElementById('emiCalculator')) {
        new InteractiveEMICalculator('emiCalculator');
    }
    
    // Initialize eligibility calculator if container exists
    if (document.getElementById('eligibilityCalculator')) {
        initializeEligibilityCalculator();
    }
});

function initializeEligibilityCalculator() {
    const form = document.getElementById('eligibilityCalculatorForm');
    if (form) {
        form.addEventListener('input', function() {
            calculateEligibility();
        });
    }
}

function calculateEligibility() {
    const monthlyIncome = parseFloat(document.getElementById('monthlyIncome').value) || 0;
    const existingEMI = parseFloat(document.getElementById('existingEMI').value) || 0;
    const interestRate = parseFloat(document.getElementById('interestRate').value) || 10;
    const tenure = parseFloat(document.getElementById('tenure').value) || 20;
    
    if (monthlyIncome > 0) {
        const tenureMonths = tenure * 12;
        const maxEligible = EligibilityCalculator.calculateMaxLoanAmount(monthlyIncome, existingEMI, interestRate, tenureMonths);
        const maxEMI = LoanCalculator.calculateEMI(maxEligible, interestRate, tenureMonths);
        
        document.getElementById('maxLoanAmount').textContent = '₹' + Math.round(maxEligible).toLocaleString('en-IN');
        document.getElementById('maxEMI').textContent = '₹' + Math.round(maxEMI).toLocaleString('en-IN');
        
        // Show eligibility status
        const status = EligibilityCalculator.getEligibilityStatus(monthlyIncome, existingEMI, maxEligible, interestRate, tenureMonths);
        displayEligibilityStatus(status);
    }
}

function displayEligibilityStatus(status) {
    const container = document.getElementById('eligibilityStatus');
    if (container) {
        let alertClass = 'alert-info';
        if (status.status === 'eligible') alertClass = 'alert-success';
        if (status.status === 'caution') alertClass = 'alert-warning';
        if (status.status === 'not_eligible') alertClass = 'alert-danger';
        
        let html = `
            <div class="alert ${alertClass}">
                <h6>${status.message}</h6>
                <p><strong>Debt-to-Income Ratio:</strong> ${status.debtRatio.toFixed(1)}%</p>
        `;
        
        if (status.recommendations.length > 0) {
            html += '<p><strong>Recommendations:</strong></p><ul>';
            status.recommendations.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
}

// Export calculator classes
window.LoanCalculator = LoanCalculator;
window.EligibilityCalculator = EligibilityCalculator;
window.InteractiveEMICalculator = InteractiveEMICalculator;