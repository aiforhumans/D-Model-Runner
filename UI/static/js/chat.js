// D-Model-Runner Chat Interface JavaScript

class ChatInterface {
    constructor() {
        this.messageInput = document.getElementById('message-input');
        this.chatForm = document.getElementById('chat-form');
        this.chatMessages = document.getElementById('chat-messages');
        this.sendButton = document.getElementById('send-button');
        this.modelSelect = document.getElementById('model-select');
        this.statusIndicator = document.getElementById('connection-status');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('.status-text');
        
        this.currentModel = this.modelSelect.value;
        this.isLoading = false;
        
        this.initializeEventListeners();
        this.checkHealth();
    }
    
    initializeEventListeners() {
        // Form submission
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Model selection change
        this.modelSelect.addEventListener('change', (e) => {
            this.currentModel = e.target.value;
            this.addSystemMessage(`Switched to model: ${this.currentModel}`);
        });
        
        // Enter key handling
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    async checkHealth() {
        try {
            this.updateStatus('connecting', 'Checking connection...');
            
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('connected', 'Connected to D-Model-Runner');
            } else {
                this.updateStatus('error', `Connection issues: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            this.updateStatus('error', 'Cannot connect to server');
            console.error('Health check failed:', error);
        }
    }
    
    updateStatus(status, message) {
        this.statusText.textContent = message;
        this.statusDot.className = `status-dot ${status}`;
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) {
            return;
        }
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input and disable form
        this.messageInput.value = '';
        this.setLoading(true);
        
        try {
            // Show typing indicator
            const typingId = this.addTypingIndicator();
            
            // Send request to API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: this.currentModel
                })
            });
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            const data = await response.json();
            
            if (data.success) {
                // Add assistant response
                this.addMessage('assistant', data.response);
                this.updateStatus('connected', `Response from ${data.model}`);
            } else {
                // Handle API errors
                this.addErrorMessage(data.error || 'Unknown error occurred');
                this.updateStatus('error', 'Request failed');
            }
            
        } catch (error) {
            this.removeTypingIndicator();
            this.addErrorMessage(`Network error: ${error.message}`);
            this.updateStatus('error', 'Network error');
            console.error('Chat request failed:', error);
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addErrorMessage(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<strong>Error:</strong> ${error}`;
        
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }
    
    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant-message';
        typingDiv.id = 'typing-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content loading-indicator';
        contentDiv.innerHTML = 'Thinking<span class="loading-dots">...</span>';
        
        typingDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
        
        return 'typing-indicator';
    }
    
    removeTypingIndicator(id = 'typing-indicator') {
        const typingDiv = document.getElementById(id);
        if (typingDiv) {
            typingDiv.remove();
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        this.sendButton.disabled = loading;
        
        const sendText = this.sendButton.querySelector('.send-text');
        const sendLoading = this.sendButton.querySelector('.send-loading');
        
        if (loading) {
            sendText.style.display = 'none';
            sendLoading.style.display = 'inline';
        } else {
            sendText.style.display = 'inline';
            sendLoading.style.display = 'none';
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});