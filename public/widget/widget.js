/**
 * AI Customer Support Chat Widget
 * Embeddable widget for website integration
 */

(function () {
    'use strict';

    // Configuration
    const CONFIG = {
        apiUrl: window.AI_CHAT_API_URL || '/api/v1',
        sessionKey: 'ai_chat_session_id',
        maxMessageLength: 1000,
        typingDelay: 1500
    };

    // State
    let state = {
        sessionId: null,
        isOpen: false,
        isTyping: false,
        messages: []
    };

    // DOM Elements
    const elements = {};

    /**
     * Initialize the chat widget
     */
    function init() {
        // Cache DOM elements
        elements.widget = document.getElementById('ai-chat-widget');
        elements.toggle = document.getElementById('chat-toggle');
        elements.window = document.getElementById('chat-window');
        elements.messagesContainer = document.getElementById('messages-container');
        elements.input = document.getElementById('message-input');
        elements.sendBtn = document.getElementById('send-btn');
        elements.minimizeBtn = document.getElementById('minimize-btn');
        elements.typingIndicator = document.getElementById('typing-indicator');

        // Load or generate session ID
        state.sessionId = localStorage.getItem(CONFIG.sessionKey);
        if (!state.sessionId) {
            state.sessionId = 'sess_' + generateId();
            localStorage.setItem(CONFIG.sessionKey, state.sessionId);
        }

        // Attach event listeners
        attachEventListeners();

        console.log('AI Chat Widget initialized');
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        // Toggle chat window
        elements.toggle.addEventListener('click', toggleChat);
        if (elements.minimizeBtn) {
            elements.minimizeBtn.addEventListener('click', toggleChat);
        }

        // Send message
        elements.sendBtn.addEventListener('click', sendMessage);
        elements.input.addEventListener('keydown', handleInputKeydown);
        elements.input.addEventListener('input', handleInputChange);

        // Quick actions
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.dataset.message;
                if (message) {
                    elements.input.value = message;
                    sendMessage();
                }
            });
        });
    }

    /**
     * Toggle chat window visibility
     */
    function toggleChat() {
        state.isOpen = !state.isOpen;

        elements.toggle.classList.toggle('active', state.isOpen);
        elements.window.classList.toggle('hidden', !state.isOpen);

        if (state.isOpen) {
            elements.input.focus();
            scrollToBottom();
        }
    }

    /**
     * Handle input keydown events
     */
    function handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    /**
     * Handle input change events
     */
    function handleInputChange() {
        const hasContent = elements.input.value.trim().length > 0;
        elements.sendBtn.disabled = !hasContent;

        // Auto-resize textarea
        elements.input.style.height = 'auto';
        elements.input.style.height = Math.min(elements.input.scrollHeight, 100) + 'px';
    }

    /**
     * Send a message to the chatbot
     */
    async function sendMessage() {
        const message = elements.input.value.trim();
        if (!message || state.isTyping) return;

        // Clear input
        elements.input.value = '';
        elements.sendBtn.disabled = true;
        elements.input.style.height = 'auto';

        // Add user message to UI
        addMessage('user', message);

        // Show typing indicator
        showTyping(true);

        try {
            const response = await fetch(`${CONFIG.apiUrl}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: state.sessionId,
                    channel: 'web'
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();

            // Update session ID if changed
            if (data.session_id) {
                state.sessionId = data.session_id;
                localStorage.setItem(CONFIG.sessionKey, state.sessionId);
            }

            // Hide typing and show response
            showTyping(false);
            addMessage('bot', data.response, data);

            // Handle escalation
            if (data.escalate) {
                addMessage('system', '🔄 Connecting you with a human agent...');
            }

            // Show suggested actions
            if (data.suggested_actions && data.suggested_actions.length > 0) {
                showSuggestedActions(data.suggested_actions);
            }

        } catch (error) {
            console.error('Chat error:', error);
            showTyping(false);
            addMessage('bot', 'Sorry, I encountered an error. Please try again or type "human" to speak with an agent.');
        }
    }

    /**
     * Add a message to the chat
     */
    function addMessage(type, content, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${escapeHtml(content)}</p>
                    <span class="message-time">${time}</span>
                </div>
            `;
        } else if (type === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                    </svg>
                </div>
                <div class="message-content">
                    <p>${formatMessage(content)}</p>
                    <span class="message-time">${time}</span>
                </div>
            `;

            // Check for order info in metadata
            if (metadata.order_info) {
                const orderCard = createOrderCard(metadata.order_info);
                messageDiv.querySelector('.message-content').appendChild(orderCard);
            }
        } else if (type === 'system') {
            messageDiv.className = 'message system-message';
            messageDiv.innerHTML = `
                <div class="message-content" style="background: rgba(59, 130, 246, 0.2); text-align: center; width: 100%;">
                    <p>${content}</p>
                </div>
            `;
        }

        // Remove quick actions after first user message
        const quickActions = elements.messagesContainer.querySelector('.quick-actions');
        if (quickActions && type === 'user') {
            quickActions.remove();
        }

        elements.messagesContainer.appendChild(messageDiv);
        scrollToBottom();

        // Store message
        state.messages.push({ type, content, time, metadata });
    }

    /**
     * Show suggested actions
     */
    function showSuggestedActions(actions) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'quick-actions';

        actions.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'quick-action-btn';
            btn.textContent = action.label;
            btn.addEventListener('click', () => {
                elements.input.value = action.label;
                sendMessage();
            });
            actionsDiv.appendChild(btn);
        });

        elements.messagesContainer.appendChild(actionsDiv);
        scrollToBottom();
    }

    /**
     * Create order tracking card
     */
    function createOrderCard(order) {
        const card = document.createElement('div');
        card.className = 'order-card';

        const statusClass = order.status === 'delivered' ? 'delivered' :
            order.status === 'shipped' ? 'shipped' : 'processing';

        card.innerHTML = `
            <div class="order-card-header">
                <span class="order-id">${order.order_id}</span>
                <span class="order-status ${statusClass}">${order.status}</span>
            </div>
            <div class="order-timeline">
                ${order.timeline ? order.timeline.map((item, index) => `
                    <div class="timeline-item">
                        <span class="timeline-dot ${index === order.timeline.length - 1 ? 'current' : 'completed'}"></span>
                        <span>${item.status}</span>
                    </div>
                `).join('') : ''}
            </div>
            ${order.estimated_delivery ? `
                <p style="margin-top: 10px; font-size: 12px; color: var(--text-secondary);">
                    📅 Estimated Delivery: ${order.estimated_delivery}
                </p>
            ` : ''}
        `;

        return card;
    }

    /**
     * Show/hide typing indicator
     */
    function showTyping(show) {
        state.isTyping = show;
        elements.typingIndicator.classList.toggle('hidden', !show);
        if (show) scrollToBottom();
    }

    /**
     * Scroll to bottom of messages
     */
    function scrollToBottom() {
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    /**
     * Format message content (markdown-like)
     */
    function formatMessage(content) {
        return content
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Links
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
            // Lists
            .replace(/^• (.*)$/gm, '<li>$1</li>');
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Generate random ID
     */
    function generateId() {
        return Math.random().toString(36).substring(2, 15);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for external use
    window.AIChatWidget = {
        open: () => { if (!state.isOpen) toggleChat(); },
        close: () => { if (state.isOpen) toggleChat(); },
        sendMessage: (msg) => { elements.input.value = msg; sendMessage(); }
    };

})();
