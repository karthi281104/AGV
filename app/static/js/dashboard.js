// This file contains JavaScript functionality specific to the dashboard.

// Function to fetch and display user statistics
function fetchUserStatistics() {
    // Simulated API call to get user statistics
    fetch('/api/user/statistics')
        .then(response => response.json())
        .then(data => {
            document.getElementById('user-statistics').innerHTML = `
                <h3>User Statistics</h3>
                <p>Total Loans: ${data.totalLoans}</p>
                <p>Total Payments: ${data.totalPayments}</p>
                <p>Outstanding Balance: ${data.outstandingBalance}</p>
            `;
        })
        .catch(error => console.error('Error fetching user statistics:', error));
}

// Function to initialize dashboard
function initDashboard() {
    fetchUserStatistics();
}

// Event listener for DOMContentLoaded to initialize dashboard
document.addEventListener('DOMContentLoaded', initDashboard);