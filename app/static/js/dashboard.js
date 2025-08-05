// Dashboard JavaScript for AGV Finance

// Dashboard state
let dashboardSocket = null;
let metricsUpdateInterval = null;
let charts = {};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupSocketConnection();
    loadInitialData();
    setupEventListeners();
});

// Initialize dashboard
function initializeDashboard() {
    console.log('Dashboard initialized');
    
    // Setup real-time clock
    updateClock();
    setInterval(updateClock, 1000);
    
    // Setup metrics refresh
    setupMetricsRefresh();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
}

// Setup Socket.IO connection for real-time updates
function setupSocketConnection() {
    if (typeof io !== 'undefined') {
        dashboardSocket = io();
        
        dashboardSocket.on('connect', function() {
            console.log('Connected to dashboard updates');
            addConnectionIndicator(true);
        });
        
        dashboardSocket.on('disconnect', function() {
            console.log('Disconnected from dashboard updates');
            addConnectionIndicator(false);
        });
        
        dashboardSocket.on('metrics_update', function(data) {
            updateMetrics(data);
            updateLastUpdatedTime();
        });
        
        dashboardSocket.on('notification', function(data) {
            showDashboardNotification(data);
        });
        
        // Request initial metrics update
        dashboardSocket.emit('request_metrics_update');
    }
}

// Load initial dashboard data
async function loadInitialData() {
    try {
        // Load metrics
        await refreshMetrics();
        
        // Load chart data
        await loadChartData();
        
        // Mark dashboard as loaded
        document.body.classList.add('dashboard-loaded');
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showAlert('error', 'Failed to load dashboard data. Please refresh the page.');
    }
}

// Setup dashboard event listeners
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshMetrics');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshMetrics();
            refreshBtn.classList.add('rotating');
            setTimeout(() => refreshBtn.classList.remove('rotating'), 1000);
        });
    }
    
    // Filter changes for charts
    const chartFilters = document.querySelectorAll('.chart-filter');
    chartFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            updateChart(this.dataset.chart, this.value);
        });
    });
    
    // Quick action buttons
    setupQuickActions();
}

// Setup metrics refresh interval
function setupMetricsRefresh() {
    // Refresh metrics every 30 seconds
    metricsUpdateInterval = setInterval(refreshMetrics, 30000);
}

// Refresh dashboard metrics
async function refreshMetrics() {
    try {
        const response = await fetch('/dashboard/api/metrics');
        const metrics = await response.json();
        
        updateMetrics(metrics);
        updateLastUpdatedTime();
        
    } catch (error) {
        console.error('Error refreshing metrics:', error);
    }
}

// Update dashboard metrics display
function updateMetrics(metrics) {
    // Update each metric with animation
    updateMetricValue('customersWithLoans', metrics.customers_with_loans);
    updateMetricValue('totalDisbursed', formatCurrency(metrics.total_disbursed));
    updateMetricValue('totalInterest', formatCurrency(metrics.total_interest_accrued));
    updateMetricValue('outstandingPrincipal', formatCurrency(metrics.outstanding_principal));
    updateMetricValue('overdueLoans', metrics.overdue_loans_count);
    updateMetricValue('monthlyCollections', formatCurrency(metrics.monthly_collections));
    
    // Trigger animations
    animateMetricCards();
}

// Update individual metric value with animation
function updateMetricValue(elementId, newValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const currentValue = element.textContent;
    if (currentValue !== newValue.toString()) {
        // Add update animation
        element.classList.add('metric-update');
        element.textContent = newValue;
        
        setTimeout(() => {
            element.classList.remove('metric-update');
        }, 500);
    }
}

// Animate metric cards
function animateMetricCards() {
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
}

// Update last updated time
function updateLastUpdatedTime() {
    const lastUpdatedElement = document.getElementById('lastUpdated');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleTimeString();
    }
}

// Update dashboard clock
function updateClock() {
    const clockElement = document.getElementById('dashboardClock');
    if (clockElement) {
        const now = new Date();
        clockElement.textContent = now.toLocaleTimeString();
    }
}

// Add connection indicator
function addConnectionIndicator(connected) {
    let indicator = document.getElementById('connectionIndicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'connectionIndicator';
        indicator.className = 'position-fixed top-0 end-0 m-3';
        indicator.style.zIndex = '1060';
        document.body.appendChild(indicator);
    }
    
    indicator.className = `position-fixed top-0 end-0 m-3 badge ${connected ? 'bg-success' : 'bg-danger'}`;
    indicator.innerHTML = `<i class="bi bi-wifi${connected ? '' : '-off'}"></i> ${connected ? 'Connected' : 'Disconnected'}`;
    
    if (connected) {
        indicator.innerHTML += '<span class="real-time-indicator ms-1"></span>';
    }
}

// Initialize charts
function initializeCharts() {
    // Monthly collections chart
    initializeMonthlyCollectionsChart();
    
    // Loan distribution chart
    initializeLoanDistributionChart();
    
    // Payment trends chart
    initializePaymentTrendsChart();
}

// Initialize monthly collections chart
function initializeMonthlyCollectionsChart() {
    const ctx = document.getElementById('monthlyCollectionsChart');
    if (!ctx) return;
    
    charts.monthlyCollections = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Collections',
                data: [],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

// Initialize loan distribution chart
function initializeLoanDistributionChart() {
    const ctx = document.getElementById('loanDistributionChart');
    if (!ctx) return;
    
    charts.loanDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#0d6efd',
                    '#198754',
                    '#ffc107',
                    '#dc3545',
                    '#6f42c1',
                    '#fd7e14'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Initialize payment trends chart
function initializePaymentTrendsChart() {
    const ctx = document.getElementById('paymentTrendsChart');
    if (!ctx) return;
    
    charts.paymentTrends = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Daily Payments',
                data: [],
                backgroundColor: '#198754'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

// Load chart data
async function loadChartData() {
    try {
        // Load monthly collections data
        const collectionsResponse = await fetch('/dashboard/api/chart-data?type=monthly_collections');
        const collectionsData = await collectionsResponse.json();
        updateMonthlyCollectionsChart(collectionsData);
        
        // Load loan distribution data
        const distributionResponse = await fetch('/dashboard/api/chart-data?type=loan_distribution');
        const distributionData = await distributionResponse.json();
        updateLoanDistributionChart(distributionData);
        
        // Load payment trends data
        const trendsResponse = await fetch('/dashboard/api/chart-data?type=payment_trends');
        const trendsData = await trendsResponse.json();
        updatePaymentTrendsChart(trendsData);
        
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Update monthly collections chart
function updateMonthlyCollectionsChart(data) {
    if (!charts.monthlyCollections || !data.monthly_collections) return;
    
    const chart = charts.monthlyCollections;
    chart.data.labels = data.monthly_collections.map(item => item.month);
    chart.data.datasets[0].data = data.monthly_collections.map(item => item.collections);
    chart.update();
}

// Update loan distribution chart
function updateLoanDistributionChart(data) {
    if (!charts.loanDistribution || !data.loan_distribution) return;
    
    const chart = charts.loanDistribution;
    chart.data.labels = data.loan_distribution.map(item => item.type);
    chart.data.datasets[0].data = data.loan_distribution.map(item => item.amount);
    chart.update();
}

// Update payment trends chart
function updatePaymentTrendsChart(data) {
    if (!charts.paymentTrends || !data.payment_trends) return;
    
    const chart = charts.paymentTrends;
    chart.data.labels = data.payment_trends.map(item => new Date(item.date).toLocaleDateString());
    chart.data.datasets[0].data = data.payment_trends.map(item => item.amount);
    chart.update();
}

// Setup quick actions
function setupQuickActions() {
    const quickActionBtns = document.querySelectorAll('.quick-action');
    
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Add click animation
            this.classList.add('btn-clicked');
            setTimeout(() => {
                this.classList.remove('btn-clicked');
            }, 200);
        });
    });
}

// Show dashboard notification
function showDashboardNotification(notification) {
    const container = document.getElementById('notificationContainer') || createNotificationContainer();
    
    const notificationElement = document.createElement('div');
    notificationElement.className = `alert alert-${notification.type} alert-dismissible fade show notification-item`;
    notificationElement.innerHTML = `
        <i class="bi bi-${getNotificationIcon(notification.type)} me-2"></i>
        <strong>${notification.title}</strong> ${notification.message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notificationElement);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notificationElement.parentElement) {
            notificationElement.remove();
        }
    }, 5000);
}

// Create notification container
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notificationContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// Get notification icon
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'info': 'info-circle',
        'warning': 'exclamation-triangle',
        'danger': 'x-circle'
    };
    return icons[type] || 'bell';
}

// Export dashboard functions
window.Dashboard = {
    refreshMetrics,
    updateMetrics,
    loadChartData,
    showDashboardNotification
};

// Cleanup when page unloads
window.addEventListener('beforeunload', function() {
    if (metricsUpdateInterval) {
        clearInterval(metricsUpdateInterval);
    }
    
    if (dashboardSocket) {
        dashboardSocket.disconnect();
    }
});

// Handle visibility change to pause/resume updates
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Pause updates when tab is not visible
        if (metricsUpdateInterval) {
            clearInterval(metricsUpdateInterval);
            metricsUpdateInterval = null;
        }
    } else {
        // Resume updates when tab becomes visible
        if (!metricsUpdateInterval) {
            setupMetricsRefresh();
            refreshMetrics();
        }
    }
});