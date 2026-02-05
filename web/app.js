/**
 * Vinyl Collection Chatbot - Frontend Application
 */

// Get API base URL from config
const API_BASE_URL = window.__CONFIG__?.API_BASE_URL || 'http://localhost:3000';

// DOM elements
const transcript = document.getElementById('transcript');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const loading = document.getElementById('loading');
const exampleButtons = document.querySelectorAll('.example-btn');

// Session ID for tracking conversations
let sessionId = generateSessionId();

/**
 * Initialize application
 */
function init() {
    // Set up event listeners
    sendButton.addEventListener('click', handleSend);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });

    // Example button handlers
    exampleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            messageInput.value = query;
            handleSend();
        });
    });

    // Check health on load
    checkHealth();
}

/**
 * Generate a unique session ID
 */
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Handle send button click
 */
async function handleSend() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Clear input
    messageInput.value = '';

    // Disable input while processing
    setInputEnabled(false);

    // Add user message to transcript
    addMessage(message, 'user');

    // Show loading
    showLoading(true);

    try {
        // Send message to API
        const response = await sendMessage(message, sessionId);

        // Hide loading
        showLoading(false);

        // Add bot response
        addMessage(
            response.answer,
            'bot',
            response.toolUsed ? response.toolName : null,
            response.toolResults
        );

    } catch (error) {
        console.error('Error sending message:', error);
        showLoading(false);
        addMessage(
            'Sorry, I encountered an error. Please try again.',
            'error'
        );
    } finally {
        setInputEnabled(true);
        messageInput.focus();
    }
}

/**
 * Send message to chat API
 */
async function sendMessage(message, sessionId, mode = 'auto') {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message,
            sessionId,
            mode
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

/**
 * Get available tools from API
 */
async function getTools() {
    const response = await fetch(`${API_BASE_URL}/tools`);

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

/**
 * Check API health
 */
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

/**
 * Add message to transcript
 */
function addMessage(text, type, toolName = null, toolResults = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Format text with line breaks
    const paragraphs = text.split('\n').filter(line => line.trim());
    paragraphs.forEach(para => {
        const p = document.createElement('p');
        p.textContent = para;
        contentDiv.appendChild(p);
    });

    messageDiv.appendChild(contentDiv);

    // Add tool indicator if tool was used
    if (toolName) {
        const toolIndicator = document.createElement('div');
        toolIndicator.className = 'tool-indicator';
        toolIndicator.textContent = `🔧 Used tool: ${toolName}`;
        messageDiv.appendChild(toolIndicator);
    }

    // Add expandable tool results if available
    if (toolResults && toolResults.length > 0) {
        const resultsDiv = createToolResults(toolResults);
        messageDiv.appendChild(resultsDiv);
    }

    transcript.appendChild(messageDiv);

    // Scroll to bottom
    transcript.scrollTop = transcript.scrollHeight;
}

/**
 * Create expandable tool results section
 */
function createToolResults(results) {
    const container = document.createElement('div');
    container.className = 'tool-results';

    const header = document.createElement('div');
    header.className = 'tool-results-header';
    header.innerHTML = `
        <span>📋 Raw Results (${results.length})</span>
        <span class="tool-results-toggle">▼ Show</span>
    `;

    const content = document.createElement('div');
    content.className = 'tool-results-content collapsed';

    // Format results
    if (typeof results[0] === 'object') {
        content.textContent = JSON.stringify(results, null, 2);
    } else {
        content.textContent = results.join('\n');
    }

    // Toggle functionality
    let isExpanded = false;
    header.addEventListener('click', () => {
        isExpanded = !isExpanded;
        content.classList.toggle('collapsed');
        header.querySelector('.tool-results-toggle').textContent = 
            isExpanded ? '▲ Hide' : '▼ Show';
    });

    container.appendChild(header);
    container.appendChild(content);

    return container;
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    loading.style.display = show ? 'flex' : 'none';
}

/**
 * Enable/disable input controls
 */
function setInputEnabled(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
}

/**
 * Show error message
 */
function showError(message) {
    addMessage(message, 'error');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
