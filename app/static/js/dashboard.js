// AGV Finance Dashboard JavaScript

class Dashboard {
    constructor() {
        this.socket = null;
        this.updateInterval = null;
        this.lastUpdateTime = null;
        this.init();
    }

    init() {
        this.initializeComponents();
        this.setupEventListeners();
        this.loadInitialData();
        this.setupAutoRefresh();
        this.initializeWebSocket();
    }

    initializeComponents() {
        // Initialize sidebar toggle
        this.setupSidebarToggle();
        
        // Initialize loading overlay
        this.loadingOverlay = document.getElementById('loading-overlay');
        
        // Format numbers with currency
        this.currencyFormatter = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });

        // Number formatter for counts
        this.numberFormatter = new Intl.NumberFormat('en-IN');
    }

    setupSidebarToggle() {
        const sidebarCollapse = document.getElementById('sidebarCollapse');
        const sidebarCollapseTop = document.getElementById('sidebarCollapseTop');
        const sidebar = document.getElementById('sidebar');
        const content = document.getElementById('content');

        const toggleSidebar = () => {
            if (window.innerWidth <= 768) {
                // Mobile behavior
                sidebar.classList.toggle('show');
            } else {
                // Desktop behavior
                sidebar.classList.toggle('collapsed');
                content.classList.toggle('expanded');
            }
        };

        if (sidebarCollapse) {
            sidebarCollapse.addEventListener('click', toggleSidebar);
        }
        
        if (sidebarCollapseTop) {
            sidebarCollapseTop.addEventListener('click', toggleSidebar);
        }

        // Close sidebar on mobile when clicking outside
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !sidebarCollapseTop.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('show');
            }
        });
    }

    setupEventListeners() {
        // Search functionality
        const searchBox = document.querySelector('.search-box input');
        if (searchBox) {
            searchBox.addEventListener('input', this.debounce((e) => {
                this.handleSearch(e.target.value);
            }, 300));
        }

        // Notification click handler
        const notificationBtn = document.querySelector('.notifications .btn');
        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => {
                this.markNotificationsAsRead();
            });
        }
    }

    loadInitialData() {
        this.showLoading();
        Promise.all([
            this.fetchDashboardStats(),
            this.fetchRecentActivities()
        ]).then(() => {
            this.hideLoading();
            this.updateLastUpdateTime();
        }).catch((error) => {
            console.error('Error loading dashboard data:', error);
            this.hideLoading();
            this.showError('Failed to load dashboard data');
        });
    }

    async fetchDashboardStats() {
        try {
            const response = await fetch('/dashboard/api/stats');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.updateMetrics(data);
            return data;
        } catch (error) {
            console.error('Error fetching dashboard stats:', error);
            this.showError('Failed to load dashboard statistics');
            return null;
        }
    }

    async fetchRecentActivities() {
        try {
            const response = await fetch('/dashboard/api/recent-activities');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.updateRecentActivities(data);
            return data;
        } catch (error) {
            console.error('Error fetching recent activities:', error);
            this.showError('Failed to load recent activities');
            return null;
        }
    }

    updateMetrics(data) {
        if (!data) return;

        // Update Total Customers
        this.updateMetricValue('total-customers', this.numberFormatter.format(data.total_customers || 0));
        this.updateMetricValue('customers-growth', data.new_customers_month || 0);

        // Update Total Disbursed
        this.updateMetricValue('total-disbursed', this.currencyFormatter.format(data.total_disbursed || 0));
        this.updateMetricValue('disbursed-growth', this.calculateGrowthPercentage(data.total_disbursed, data.prev_month_disbursed));

        // Update Interest Accrued
        this.updateMetricValue('total-interest', this.currencyFormatter.format(data.total_interest || 0));
        this.updateMetricValue('interest-growth', this.calculateGrowthPercentage(data.total_interest, data.prev_month_interest));

        // Update Active Loans
        this.updateMetricValue('active-loans', this.numberFormatter.format(data.active_loans || 0));
        this.updateMetricValue('loans-change', data.loans_disbursed_month || 0);

        // Update Overdue Balances
        const overdueAmount = data.overdue_amount || 0;
        this.updateMetricValue('overdue-amount', this.currencyFormatter.format(overdueAmount));
        this.updateMetricValue('overdue-count', data.overdue_loans || 0);

        // Update Monthly Collections
        this.updateMetricValue('monthly-collections', this.currencyFormatter.format(data.monthly_collections || 0));
        this.updateMetricValue('collections-growth', this.calculateCollectionPercentage(data.monthly_collections, data.monthly_target));

        // Add animation to updated cards
        this.animateMetricCards();
    }

    updateMetricValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            element.classList.add('fade-in');
            setTimeout(() => element.classList.remove('fade-in'), 500);
        }
    }

    calculateGrowthPercentage(current, previous) {
        if (!previous || previous === 0) return 0;
        return Math.round(((current - previous) / previous) * 100);
    }

    calculateCollectionPercentage(collected, target) {
        if (!target || target === 0) return 0;
        return Math.round((collected / target) * 100);
    }

    animateMetricCards() {
        const cards = document.querySelectorAll('.metric-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.transform = 'scale(1.02)';
                setTimeout(() => {
                    card.style.transform = 'scale(1)';
                }, 200);
            }, index * 100);
        });
    }

    updateRecentActivities(data) {
        if (!data) return;

        this.updateRecentLoans(data.recent_loans || []);
        this.updateRecentCustomers(data.recent_customers || []);
        this.updatePaymentAlerts(data.payment_alerts || []);
    }

    updateRecentLoans(loans) {
        const tableBody = document.querySelector('#recent-loans-table tbody');
        if (!tableBody) return;

        if (loans.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No recent loans found</td></tr>';
            return;
        }

        tableBody.innerHTML = loans.map(loan => `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="customer-avatar" style="width: 32px; height: 32px; margin-right: 10px;">
                            ${this.getInitials(loan.customer_name)}
                        </div>
                        <div>
                            <div class="fw-semibold">${loan.customer_name}</div>
                            <small class="text-muted">${loan.customer_id}</small>
                        </div>
                    </div>
                </td>
                <td class="fw-semibold">${this.currencyFormatter.format(loan.principal_amount)}</td>
                <td><span class="badge bg-secondary">${loan.loan_type}</span></td>
                <td><span class="status-badge ${loan.status}">${this.capitalizeFirst(loan.status)}</span></td>
                <td class="text-muted">${this.formatDate(loan.disbursed_date)}</td>
            </tr>
        `).join('');
    }

    updateRecentCustomers(customers) {
        const container = document.getElementById('recent-customers-list');
        if (!container) return;

        if (customers.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No recent customers found</p>';
            return;
        }

        container.innerHTML = customers.map(customer => `
            <div class="customer-item">
                <div class="customer-avatar">
                    ${this.getInitials(customer.full_name)}
                </div>
                <div class="customer-details">
                    <h6>${customer.full_name}</h6>
                    <small>${customer.phone}</small><br>
                    <small class="text-muted">${this.formatDate(customer.created_at)}</small>
                </div>
            </div>
        `).join('');
    }

    updatePaymentAlerts(alerts) {
        const container = document.getElementById('payment-alerts');
        if (!container) return;

        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No payment alerts</p>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-icon ${alert.severity}">
                    <i class="fas ${alert.severity === 'danger' ? 'fa-exclamation-triangle' : 'fa-clock'}"></i>
                </div>
                <div class="alert-content">
                    <h6>${alert.title}</h6>
                    <small>${alert.message}</small>
                </div>
            </div>
        `).join('');
    }

    getInitials(name) {
        if (!name) return 'U';
        return name.split(' ').map(word => word.charAt(0)).join('').substring(0, 2).toUpperCase();
    }

    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }

    setupAutoRefresh() {
        // Refresh data every 5 minutes
        this.updateInterval = setInterval(() => {
            this.refreshData();
        }, 5 * 60 * 1000);
    }

    refreshData() {
        console.log('Refreshing dashboard data...');
        this.fetchDashboardStats();
        this.fetchRecentActivities();
        this.updateLastUpdateTime();
    }

    updateLastUpdateTime() {
        this.lastUpdateTime = new Date();
        const timeElement = document.getElementById('last-update-time');
        if (timeElement) {
            timeElement.textContent = this.lastUpdateTime.toLocaleTimeString('en-IN');
        }
    }

    initializeWebSocket() {
        try {
            // Initialize Socket.IO for real-time updates
            if (typeof io !== 'undefined') {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    console.log('Connected to dashboard updates');
                });

                this.socket.on('dashboard_update', (data) => {
                    console.log('Received dashboard update:', data);
                    this.handleRealtimeUpdate(data);
                });

                this.socket.on('disconnect', () => {
                    console.log('Disconnected from dashboard updates');
                });
            }
        } catch (error) {
            console.log('WebSocket not available, using polling only');
        }
    }

    handleRealtimeUpdate(data) {
        if (data.type === 'stats') {
            this.updateMetrics(data.data);
        } else if (data.type === 'activities') {
            this.updateRecentActivities(data.data);
        }
        this.updateLastUpdateTime();
    }

    handleSearch(query) {
        if (query.length < 2) return;
        
        console.log('Searching for:', query);
        // Implement search functionality here
        // This could search customers, loans, etc.
    }

    markNotificationsAsRead() {
        const notificationCount = document.getElementById('notification-count');
        if (notificationCount) {
            notificationCount.textContent = '0';
            notificationCount.style.display = 'none';
        }
    }

    showLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('show');
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('show');
        }
    }

    showError(message) {
        console.error(message);
        // You could show a toast notification here
        // For now, we'll just log it
    }

    debounce(func, wait) {
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

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});