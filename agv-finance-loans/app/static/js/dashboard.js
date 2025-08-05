// Dashboard Specific JavaScript

let socket = null;
let dashboardCharts = {};

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    // Initialize Socket.IO connection
    initializeSocket();
    
    // Initialize charts
    initializeCharts();
    
    // Initialize real-time updates
    startRealTimeUpdates();
    
    // Initialize dashboard interactions
    initializeDashboardInteractions();
}

function initializeSocket() {
    if (typeof io !== 'undefined') {
        socket = io('/dashboard');
        
        socket.on('connect', function() {
            console.log('Connected to dashboard updates');
            updateConnectionStatus(true);
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from dashboard updates');
            updateConnectionStatus(false);
        });
        
        socket.on('metrics_update', function(data) {
            updateMetrics(data);
        });
        
        socket.on('dashboard_refresh', function() {
            // Refresh charts and metrics
            refreshDashboardData();
        });
        
        // Request initial metrics
        socket.emit('request_metrics');
    }
}

function updateConnectionStatus(connected) {
    const statusElement = document.querySelector('.badge.bg-success');
    if (statusElement) {
        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>Live Data';
            statusElement.className = 'badge bg-success';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>Offline';
            statusElement.className = 'badge bg-secondary';
        }
    }
}

function updateMetrics(metrics) {
    // Update metric values with animation
    Object.keys(metrics).forEach(function(key) {
        const metric = metrics[key];
        const valueElement = document.getElementById(key + 'Value');
        
        if (valueElement) {
            animateNumber(valueElement, metric.formatted_value);
        }
        
        // Update change indicators
        updateChangeIndicator(key, metric.change);
    });
}

function animateNumber(element, targetValue) {
    element.style.transform = 'scale(1.1)';
    element.style.transition = 'all 0.3s ease';
    
    setTimeout(function() {
        element.textContent = targetValue;
        element.style.transform = 'scale(1)';
    }, 150);
}

function updateChangeIndicator(metricKey, change) {
    const metricCard = document.querySelector(`#${metricKey}Value`).closest('.metric-card');
    const changeElement = metricCard.querySelector('small');
    
    if (changeElement) {
        const isPositive = change >= 0;
        const arrow = isPositive ? 'up' : 'down';
        const colorClass = isPositive ? 'text-success' : 'text-danger';
        
        // Special case for overdue amount (positive change is bad)
        if (metricKey === 'overdue_amount') {
            colorClass = isPositive ? 'text-danger' : 'text-success';
        }
        
        changeElement.className = colorClass;
        changeElement.innerHTML = `
            <i class="fas fa-arrow-${arrow}"></i>
            ${Math.abs(change).toFixed(1)}% from last month
        `;
    }
}

function initializeCharts() {
    // Initialize chart containers
    const chartContainers = document.querySelectorAll('canvas[id$="Chart"]');
    
    chartContainers.forEach(function(canvas) {
        const chartType = canvas.id.replace('Chart', '');
        loadChart(chartType, canvas);
    });
}

function loadChart(chartType, canvas) {
    const ctx = canvas.getContext('2d');
    
    // Show loading state
    showChartLoading(canvas);
    
    // Fetch chart data
    fetch(`/dashboard/api/chart-data/${getChartApiName(chartType)}?period=30`)
        .then(response => response.json())
        .then(data => {
            hideChartLoading(canvas);
            createChart(chartType, ctx, data);
        })
        .catch(error => {
            console.error('Error loading chart:', error);
            hideChartLoading(canvas);
            showChartError(canvas);
        });
}

function getChartApiName(chartType) {
    const apiNames = {
        'disbursement': 'loan-disbursement',
        'collection': 'payment-collection',
        'loanStatus': 'loan-status',
        'monthlyTrends': 'monthly-trends',
        'customerGrowth': 'customer-growth',
        'portfolioAnalysis': 'portfolio-analysis'
    };
    
    return apiNames[chartType] || chartType;
}

function createChart(chartType, ctx, data) {
    const config = getChartConfig(chartType, data);
    
    // Destroy existing chart if it exists
    if (dashboardCharts[chartType]) {
        dashboardCharts[chartType].destroy();
    }
    
    dashboardCharts[chartType] = new Chart(ctx, config);
}

function getChartConfig(chartType, data) {
    const baseConfig = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 20,
                    usePointStyle: true
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#6c757d'
                }
            },
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#6c757d'
                }
            }
        }
    };
    
    switch (chartType) {
        case 'disbursement':
            return {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Disbursement Amount',
                        data: data.amounts,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    ...baseConfig,
                    scales: {
                        ...baseConfig.scales,
                        y: {
                            ...baseConfig.scales.y,
                            ticks: {
                                ...baseConfig.scales.y.ticks,
                                callback: function(value) {
                                    return '₹' + value.toLocaleString('en-IN');
                                }
                            }
                        }
                    }
                }
            };
            
        case 'collection':
            return {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Collection Amount',
                        data: data.amounts,
                        backgroundColor: 'rgba(25, 135, 84, 0.8)',
                        borderColor: '#198754',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    ...baseConfig,
                    scales: {
                        ...baseConfig.scales,
                        y: {
                            ...baseConfig.scales.y,
                            ticks: {
                                ...baseConfig.scales.y.ticks,
                                callback: function(value) {
                                    return '₹' + value.toLocaleString('en-IN');
                                }
                            }
                        }
                    }
                }
            };
            
        case 'loanStatus':
            return {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.counts,
                        backgroundColor: [
                            '#198754', // Active - Green
                            '#ffc107', // Pending - Yellow
                            '#0dcaf0', // Approved - Cyan
                            '#6c757d', // Closed - Gray
                            '#dc3545'  // Defaulted - Red
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    ...baseConfig,
                    scales: undefined,
                    plugins: {
                        ...baseConfig.plugins,
                        legend: {
                            position: 'right'
                        }
                    }
                }
            };
            
        default:
            return {
                type: 'line',
                data: data,
                options: baseConfig
            };
    }
}

function showChartLoading(canvas) {
    const container = canvas.parentElement;
    const loading = document.createElement('div');
    loading.className = 'chart-loading d-flex justify-content-center align-items-center position-absolute w-100 h-100';
    loading.style.background = 'rgba(255, 255, 255, 0.8)';
    loading.style.top = '0';
    loading.style.left = '0';
    loading.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
    
    container.style.position = 'relative';
    container.appendChild(loading);
}

function hideChartLoading(canvas) {
    const container = canvas.parentElement;
    const loading = container.querySelector('.chart-loading');
    if (loading) {
        loading.remove();
    }
}

function showChartError(canvas) {
    const container = canvas.parentElement;
    const error = document.createElement('div');
    error.className = 'chart-error d-flex flex-column justify-content-center align-items-center position-absolute w-100 h-100';
    error.style.background = 'rgba(255, 255, 255, 0.9)';
    error.style.top = '0';
    error.style.left = '0';
    error.innerHTML = `
        <i class="fas fa-exclamation-triangle text-warning fa-2x mb-2"></i>
        <p class="text-muted mb-0">Unable to load chart</p>
    `;
    
    container.appendChild(error);
}

function startRealTimeUpdates() {
    // Update metrics every 30 seconds
    setInterval(function() {
        if (socket && socket.connected) {
            socket.emit('request_metrics');
        } else {
            // Fallback to HTTP request
            fetch('/dashboard/api/metrics')
                .then(response => response.json())
                .then(data => updateMetrics(data))
                .catch(error => console.error('Error updating metrics:', error));
        }
    }, 30000);
    
    // Update charts every 5 minutes
    setInterval(function() {
        refreshCharts();
    }, 300000);
}

function refreshCharts() {
    Object.keys(dashboardCharts).forEach(function(chartType) {
        const canvas = document.getElementById(chartType + 'Chart');
        if (canvas) {
            loadChart(chartType, canvas);
        }
    });
}

function refreshDashboardData() {
    // Refresh all dashboard components
    if (socket && socket.connected) {
        socket.emit('request_metrics');
    }
    
    refreshCharts();
    
    // Show refresh indicator
    const refreshButton = document.querySelector('[onclick="refreshActivities()"]');
    if (refreshButton) {
        const icon = refreshButton.querySelector('i');
        icon.classList.add('fa-spin');
        setTimeout(function() {
            icon.classList.remove('fa-spin');
        }, 1000);
    }
}

function initializeDashboardInteractions() {
    // Metric card hover effects
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Quick action button clicks
    const quickActionButtons = document.querySelectorAll('.quick-actions .btn');
    quickActionButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            showLoading(this);
        });
    });
    
    // Activity feed interactions
    const activityItems = document.querySelectorAll('.activity-item');
    activityItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const url = this.dataset.url;
            if (url) {
                window.location.href = url;
            }
        });
    });
}

// Chart period selector
function changePeriod(period, chartType) {
    const canvas = document.getElementById(chartType + 'Chart');
    if (canvas) {
        // Update the fetch URL with new period
        const ctx = canvas.getContext('2d');
        showChartLoading(canvas);
        
        fetch(`/dashboard/api/chart-data/${getChartApiName(chartType)}?period=${period}`)
            .then(response => response.json())
            .then(data => {
                hideChartLoading(canvas);
                createChart(chartType, ctx, data);
            })
            .catch(error => {
                console.error('Error loading chart:', error);
                hideChartLoading(canvas);
                showChartError(canvas);
            });
    }
}

// Export dashboard functions
window.Dashboard = {
    refreshDashboardData,
    refreshCharts,
    changePeriod,
    updateMetrics
};