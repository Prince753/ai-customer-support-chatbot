/**
 * Admin Dashboard JavaScript
 * Handles charts, data loading, and interactions
 */

(function () {
    'use strict';

    const CONFIG = {
        apiUrl: 'http://localhost:8000/api/v1',
        refreshInterval: 30000 // 30 seconds
    };

    // Sample data for demo
    const sampleData = {
        conversations: [
            { id: 'sess_abc123', name: 'John D.', initials: 'JD', preview: 'Where is my order ORD-2024-001?', time: '2 min ago', status: 'active', channel: 'web' },
            { id: 'sess_def456', name: 'Sarah M.', initials: 'SM', preview: 'I want to return my headphones', time: '15 min ago', status: 'escalated', channel: 'whatsapp' },
            { id: 'sess_ghi789', name: 'Mike R.', initials: 'MR', preview: 'Thanks for your help!', time: '1 hour ago', status: 'closed', channel: 'web' },
            { id: 'sess_jkl012', name: 'Emily W.', initials: 'EW', preview: 'Do you have this in blue?', time: '2 hours ago', status: 'active', channel: 'web' },
            { id: 'sess_mno345', name: 'David K.', initials: 'DK', preview: 'My payment failed', time: '3 hours ago', status: 'escalated', channel: 'whatsapp' }
        ],
        volumeData: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'Conversations',
                    data: [45, 52, 38, 67, 55, 42, 48],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Resolved',
                    data: [42, 48, 35, 60, 50, 40, 45],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        channelData: {
            labels: ['Website', 'WhatsApp'],
            datasets: [{
                data: [65, 35],
                backgroundColor: ['#667eea', '#25D366'],
                borderWidth: 0
            }]
        }
    };

    /**
     * Initialize dashboard
     */
    function init() {
        renderConversations();
        initCharts();
        attachEventListeners();
        startAutoRefresh();
    }

    /**
     * Render conversations list
     */
    function renderConversations() {
        const container = document.getElementById('conversations-list');
        if (!container) return;

        container.innerHTML = sampleData.conversations.map(conv => `
            <div class="conversation-item" data-id="${conv.id}">
                <div class="conversation-avatar">${conv.initials}</div>
                <div class="conversation-info">
                    <div class="conversation-header">
                        <span class="conversation-name">${conv.name}</span>
                        <span class="conversation-time">${conv.time}</span>
                    </div>
                    <p class="conversation-preview">${conv.preview}</p>
                </div>
                <span class="conversation-status ${conv.status}">${conv.status}</span>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => openConversation(item.dataset.id));
        });
    }

    /**
     * Initialize Chart.js charts
     */
    function initCharts() {
        initVolumeChart();
        initChannelChart();
    }

    /**
     * Volume chart (line chart)
     */
    function initVolumeChart() {
        const ctx = document.getElementById('volumeChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: sampleData.volumeData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)'
                        },
                        beginAtZero: true
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    /**
     * Channel distribution chart (doughnut)
     */
    function initChannelChart() {
        const ctx = document.getElementById('channelChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: sampleData.channelData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            }
        });
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                navigateTo(page);
            });
        });

        // Chart period buttons
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // Update chart data based on period
            });
        });

        // Search
        const searchInput = document.querySelector('.search-box input');
        if (searchInput) {
            searchInput.addEventListener('input', debounce((e) => {
                searchConversations(e.target.value);
            }, 300));
        }
    }

    /**
     * Navigate to a page
     */
    function navigateTo(page) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        console.log('Navigate to:', page);
    }

    /**
     * Open conversation detail
     */
    function openConversation(id) {
        console.log('Open conversation:', id);
        // In a full implementation, this would open a conversation detail view
    }

    /**
     * Search conversations
     */
    function searchConversations(query) {
        console.log('Search:', query);
        // Filter conversations based on query
    }

    /**
     * Fetch stats from API
     */
    async function fetchStats() {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/admin/stats`);
            if (response.ok) {
                const data = await response.json();
                updateStats(data);
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    /**
     * Update stats in UI
     */
    function updateStats(data) {
        const elements = {
            'total-conversations': data.total_conversations,
            'resolution-rate': `${Math.round(data.resolution_rate * 100)}%`,
            'avg-response': `${data.avg_response_time_seconds}s`,
            'satisfaction': `${data.customer_satisfaction}/5`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });
    }

    /**
     * Fetch conversations from API
     */
    async function fetchConversations() {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/admin/conversations?limit=5`);
            if (response.ok) {
                const data = await response.json();
                // Update conversations list
            }
        } catch (error) {
            console.error('Error fetching conversations:', error);
        }
    }

    /**
     * Start auto-refresh
     */
    function startAutoRefresh() {
        setInterval(() => {
            fetchStats();
            fetchConversations();
        }, CONFIG.refreshInterval);
    }

    /**
     * Debounce helper
     */
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

    /**
     * Format date helper
     */
    function formatTimeAgo(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes} min ago`;
        if (hours < 24) return `${hours} hours ago`;
        return `${days} days ago`;
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
