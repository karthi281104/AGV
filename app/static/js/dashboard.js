/**
 * AGV Finance & Loans Dashboard JavaScript
 * Real-time dashboard with WebSocket updates, Chart.js visualizations, and interactive features
 */

class AGVDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.updateInterval = null;
        this.isConnected = false;
        this.lastUpdated = null;
        
        this.init();
    }

    /**
     * Initialize the dashboard
     */
    init() {
        console.log('Initializing AGV Finance Dashboard...');
        
        // Setup Socket.IO connection
        this.setupSocketConnection();
        
        // Load initial data
        this.loadInitialData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize charts
        this.initializeCharts();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        console.log('Dashboard initialized successfully');
    }

    /**
     * Setup WebSocket connection for real-time updates
     */
    setupSocketConnection() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to dashboard websocket');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from dashboard websocket');
                this.isConnected = false;
                this.updateConnectionStatus(false);
            });

            this.socket.on('metrics_update', (data) => {
                this.updateMetrics(data);
            });

            this.socket.on('chart_update', (data) => {
                this.updateCharts(data);
            });

            this.socket.on('notifications_update', (data) => {
                this.updateNotifications(data.notifications);
            });

            this.socket.on('data_update', (data) => {
                this.handleDataUpdate(data);
            });

            this.socket.on('error', (error) => {
                console.error('Socket error:', error);
                this.showError('Real-time connection error');
            });
            
        } catch (error) {
            console.error('Failed to setup socket connection:', error);
            this.showError('Failed to establish real-time connection');
        }
    }

    /**
     * Load initial dashboard data
     */
    async loadInitialData() {
        try {
            this.showLoading(true);
            
            // Load metrics, charts, and activities in parallel
            const [metricsResponse, chartsResponse, activitiesResponse, notificationsResponse] = await Promise.all([
                fetch('/dashboard/api/metrics'),
                fetch('/dashboard/api/charts'),
                fetch('/dashboard/api/activities'),
                fetch('/dashboard/api/notifications')
            ]);

            if (metricsResponse.ok) {
                const metricsData = await metricsResponse.json();
                this.updateMetrics(metricsData);
            }

            if (chartsResponse.ok) {
                const chartsData = await chartsResponse.json();
                this.updateCharts(chartsData);
            }

            if (activitiesResponse.ok) {
                const activitiesData = await activitiesResponse.json();
                this.updateActivities(activitiesData.activities);
            }

            if (notificationsResponse.ok) {
                const notificationsData = await notificationsResponse.json();
                this.updateNotifications(notificationsData.notifications);
            }

            this.lastUpdated = new Date();
            this.updateLastUpdatedTime();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Setup event listeners for interactive elements
     */
    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.loadInitialData();
        });

        // Export button
        document.getElementById('exportBtn')?.addEventListener('click', () => {
            this.exportData();
        });

        // Search functionality
        document.getElementById('searchToggle')?.addEventListener('click', () => {
            this.toggleSearch();
        });

        document.getElementById('searchBtn')?.addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Refresh activities
        document.getElementById('refreshActivities')?.addEventListener('click', () => {
            this.refreshActivities();
        });

        // Metric card click handlers for drill-down
        this.setupMetricCardHandlers();
    }

    /**
     * Setup metric card click handlers
     */
    setupMetricCardHandlers() {
        const metricCards = [
            'customersCard', 'disbursedCard', 'interestCard', 
            'overdueCard', 'activeLoansCard', 'collectionsCard'
        ];

        metricCards.forEach(cardId => {
            const card = document.getElementById(cardId);
            if (card) {
                card.addEventListener('click', () => {
                    this.handleMetricCardClick(cardId);
                });
                card.style.cursor = 'pointer';
            }
        });
    }

    /**
     * Initialize Chart.js charts
     */
    initializeCharts() {
        this.initializePortfolioChart();
        this.initializeTrendsChart();
    }

    /**
     * Initialize portfolio breakdown pie chart
     */
    initializePortfolioChart() {
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) return;

        this.charts.portfolio = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Gold Loans', 'Bond Loans'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: [
                        '#ffc107',
                        '#17a2b8'
                    ],
                    borderWidth: 0,
                    hoverBorderWidth: 3,
                    hoverBorderColor: '#fff'
                }]
            },
            options: {
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
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ₹${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize monthly trends line chart
     */
    initializeTrendsChart() {
        const ctx = document.getElementById('trendsChart');
        if (!ctx) return;

        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Disbursements',
                    data: [],
                    borderColor: '#0066cc',
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Collections',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Amount (₹)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    /**
     * Update dashboard metrics
     */
    updateMetrics(data) {
        try {
            // Update customer metrics
            if (data.customers) {
                this.updateElement('totalCustomers', this.formatNumber(data.customers.total));
                this.updateTrend('customersTrend', data.customers.growth_rate, '%');
            }

            // Update portfolio metrics
            if (data.portfolio) {
                this.updateElement('totalDisbursed', this.formatCurrency(data.portfolio.total_disbursed));
                this.updateElement('totalInterest', this.formatCurrency(data.portfolio.total_interest_accrued));
                this.updateElement('activeLoans', this.formatNumber(data.portfolio.total_active_loans));
            }

            // Update overdue metrics
            if (data.overdue) {
                this.updateElement('overdueAmount', this.formatCurrency(data.overdue.total_overdue_amount));
                this.updateTrend('overdueTrend', data.overdue.default_rate, '%', data.overdue.risk_level);
            }

            // Update collection metrics
            if (data.collections) {
                this.updateElement('monthlyCollections', this.formatCurrency(data.collections.current_month_collections));
                this.updateTrend('collectionsTrend', data.collections.collection_efficiency, '%');
            }

            // Update financial ratios
            if (data.financial_ratios) {
                this.updateTrend('interestTrend', data.financial_ratios.interest_yield, '%');
            }

            // Add animation to updated cards
            this.animateMetricCards();

        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }

    /**
     * Update charts with new data
     */
    updateCharts(data) {
        try {
            // Update portfolio chart
            if (data.portfolio_breakdown && this.charts.portfolio) {
                const portfolioData = data.portfolio_breakdown;
                this.charts.portfolio.data.datasets[0].data = [
                    portfolioData.gold?.amount || 0,
                    portfolioData.bond?.amount || 0
                ];
                this.charts.portfolio.update('active');
            }

            // Update trends chart
            if (data.monthly_disbursements && data.monthly_collections && this.charts.trends) {
                const disbursements = data.monthly_disbursements;
                const collections = data.monthly_collections;
                
                // Get last 6 months of data
                const months = disbursements.slice(-6).map(item => item.month);
                const disbursementAmounts = disbursements.slice(-6).map(item => item.amount);
                const collectionAmounts = collections.slice(-6).map(item => item.amount);
                
                this.charts.trends.data.labels = months;
                this.charts.trends.data.datasets[0].data = disbursementAmounts;
                this.charts.trends.data.datasets[1].data = collectionAmounts;
                this.charts.trends.update('active');
            }

        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    /**
     * Update activities list
     */
    updateActivities(activities) {
        const container = document.getElementById('recentActivities');
        if (!container || !activities) return;

        if (activities.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-history text-muted fs-3"></i>
                    <p class="text-muted mt-2">No recent activities</p>
                </div>
            `;
            return;
        }

        const activitiesHtml = activities.map(activity => `
            <div class="activity-item fade-in" data-activity-id="${activity.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <div class="activity-description">${activity.activity_description}</div>
                        <div class="activity-time">
                            <i class="fas fa-clock me-1"></i>
                            ${this.formatDateTime(activity.created_at)}
                        </div>
                    </div>
                    <div class="activity-type">
                        <span class="badge bg-primary">${activity.activity_type}</span>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = activitiesHtml;
    }

    /**
     * Update notifications panel
     */
    updateNotifications(notifications) {
        const container = document.getElementById('notificationsPanel');
        const badge = document.getElementById('notificationBadge');
        
        if (!container) return;

        if (!notifications || notifications.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-bell-slash text-muted fs-3"></i>
                    <p class="text-muted mt-2">No new notifications</p>
                </div>
            `;
            if (badge) badge.textContent = '0';
            return;
        }

        const notificationsHtml = notifications.map(notification => `
            <div class="notification-item ${notification.type} fade-in">
                <div class="d-flex align-items-start">
                    <div class="notification-icon me-3">
                        ${this.getNotificationIcon(notification.type)}
                    </div>
                    <div class="flex-grow-1">
                        <div class="notification-message">${notification.message}</div>
                        ${notification.action ? `
                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="dashboard.handleNotificationAction('${notification.action}')">
                                Take Action
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = notificationsHtml;
        if (badge) badge.textContent = notifications.length;
    }

    /**
     * Utility methods
     */
    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            element.classList.add('bounce-in');
            setTimeout(() => element.classList.remove('bounce-in'), 600);
        }
    }

    updateTrend(elementId, value, suffix = '', riskLevel = null) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const trendElement = element.querySelector('.trend-value');
        const iconElement = element.querySelector('i');
        
        if (trendElement) {
            trendElement.textContent = value + suffix;
        }

        // Update trend direction and color based on value and context
        if (iconElement) {
            let trendClass = 'fas fa-minus text-secondary';
            
            if (riskLevel) {
                // Special handling for risk indicators
                if (riskLevel === 'high') trendClass = 'fas fa-exclamation-triangle text-danger';
                else if (riskLevel === 'medium') trendClass = 'fas fa-exclamation-circle text-warning';
                else trendClass = 'fas fa-check-circle text-success';
            } else {
                // Regular trend indicators
                if (value > 0) trendClass = 'fas fa-arrow-up text-success';
                else if (value < 0) trendClass = 'fas fa-arrow-down text-danger';
            }
            
            iconElement.className = trendClass;
        }
    }

    formatCurrency(amount) {
        return '₹' + parseFloat(amount).toLocaleString('en-IN', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    formatNumber(number) {
        return parseFloat(number).toLocaleString('en-IN');
    }

    formatDateTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getNotificationIcon(type) {
        const icons = {
            'critical': '<i class="fas fa-exclamation-triangle text-danger"></i>',
            'warning': '<i class="fas fa-exclamation-circle text-warning"></i>',
            'info': '<i class="fas fa-info-circle text-info"></i>',
            'success': '<i class="fas fa-check-circle text-success"></i>'
        };
        return icons[type] || icons['info'];
    }

    /**
     * Event handlers
     */
    async performSearch() {
        const query = document.getElementById('searchInput')?.value.trim();
        if (!query) return;

        try {
            const response = await fetch(`/dashboard/api/search?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const results = await response.json();
                this.showSearchResults(results);
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed');
        }
    }

    showSearchResults(results) {
        const modal = new bootstrap.Modal(document.getElementById('searchModal'));
        const resultsContainer = document.getElementById('searchResults');
        
        let html = '';
        
        ['customers', 'loans', 'payments'].forEach(type => {
            if (results[type] && results[type].length > 0) {
                html += `
                    <div class="search-result-section">
                        <h6 class="text-uppercase fw-bold text-muted">${type}</h6>
                        ${results[type].map(item => `
                            <div class="search-result-item" onclick="dashboard.handleSearchResultClick('${type}', ${item.id})">
                                <div class="fw-bold">${item.full_name || item.loan_id || item.payment_id}</div>
                                <div class="text-muted small">${item.phone || item.principal_amount || item.payment_amount}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        });
        
        if (!html) {
            html = '<div class="text-center py-4"><p class="text-muted">No results found</p></div>';
        }
        
        resultsContainer.innerHTML = html;
        modal.show();
    }

    async exportData() {
        try {
            this.showLoading(true);
            const response = await fetch('/dashboard/api/export/metrics');
            if (response.ok) {
                const data = await response.json();
                this.downloadJson(data, 'dashboard-metrics.json');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showError('Export failed');
        } finally {
            this.showLoading(false);
        }
    }

    downloadJson(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    toggleSearch() {
        const searchRow = document.getElementById('searchRow');
        if (searchRow) {
            searchRow.classList.toggle('d-none');
            if (!searchRow.classList.contains('d-none')) {
                document.getElementById('searchInput')?.focus();
            }
        }
    }

    animateMetricCards() {
        const cards = document.querySelectorAll('.metric-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('bounce-in');
                setTimeout(() => card.classList.remove('bounce-in'), 600);
            }, index * 100);
        });
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            if (connected) {
                statusElement.innerHTML = '<i class="fas fa-wifi me-1"></i>Connected';
                statusElement.className = 'badge bg-success connection-status';
            } else {
                statusElement.innerHTML = '<i class="fas fa-wifi me-1"></i>Disconnected';
                statusElement.className = 'badge bg-danger connection-status';
            }
        }
    }

    updateLastUpdatedTime() {
        const element = document.getElementById('lastUpdated');
        if (element && this.lastUpdated) {
            element.textContent = this.formatDateTime(this.lastUpdated.toISOString());
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('d-none');
            } else {
                overlay.classList.add('d-none');
            }
        }
    }

    showError(message) {
        // Create and show error toast
        console.error(message);
        // You can implement a toast notification system here
    }

    startPeriodicUpdates() {
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            if (this.isConnected) {
                this.socket.emit('request_metrics_update');
                this.updateLastUpdatedTime();
            }
        }, 30000);
    }

    handleDataUpdate(data) {
        console.log('Data update received:', data.type);
        // Handle specific data updates from WebSocket
        switch (data.type) {
            case 'new_loan':
            case 'new_payment':
            case 'new_customer':
                this.socket.emit('request_metrics_update');
                this.refreshActivities();
                break;
        }
    }

    async refreshActivities() {
        try {
            const response = await fetch('/dashboard/api/activities');
            if (response.ok) {
                const data = await response.json();
                this.updateActivities(data.activities);
            }
        } catch (error) {
            console.error('Error refreshing activities:', error);
        }
    }

    handleMetricCardClick(cardId) {
        // Handle metric card clicks for drill-down functionality
        console.log('Metric card clicked:', cardId);
        // Implement navigation to detailed views
    }

    handleSearchResultClick(type, id) {
        // Handle search result clicks
        console.log('Search result clicked:', type, id);
        // Implement navigation to detail pages
    }

    handleNotificationAction(action) {
        // Handle notification action buttons
        console.log('Notification action:', action);
        // Implement specific actions based on notification type
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new AGVDashboard();
});