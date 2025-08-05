function calculateLoanPayment(principal, annualInterestRate, years) {
    const monthlyInterestRate = annualInterestRate / 100 / 12;
    const numberOfPayments = years * 12;
    const denominator = Math.pow(1 + monthlyInterestRate, numberOfPayments) - 1;

    if (denominator === 0) {
        return principal; // If interest rate is 0
    }

    const monthlyPayment = (principal * monthlyInterestRate * Math.pow(1 + monthlyInterestRate, numberOfPayments)) / denominator;
    return monthlyPayment;
}

function calculateTotalPayment(monthlyPayment, years) {
    return monthlyPayment * years * 12;
}

function calculateTotalInterest(totalPayment, principal) {
    return totalPayment - principal;
}

// Example usage
document.addEventListener('DOMContentLoaded', function() {
    const loanForm = document.getElementById('loan-form');
    loanForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const principal = parseFloat(document.getElementById('principal').value);
        const annualInterestRate = parseFloat(document.getElementById('interest').value);
        const years = parseInt(document.getElementById('years').value);

        const monthlyPayment = calculateLoanPayment(principal, annualInterestRate, years);
        const totalPayment = calculateTotalPayment(monthlyPayment, years);
        const totalInterest = calculateTotalInterest(totalPayment, principal);

        document.getElementById('monthly-payment').innerText = monthlyPayment.toFixed(2);
        document.getElementById('total-payment').innerText = totalPayment.toFixed(2);
        document.getElementById('total-interest').innerText = totalInterest.toFixed(2);
    });
});