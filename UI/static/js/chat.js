// D-Model-Runner Chat Interface JavaScript

class ChatInterface {
    constructor() {
        this.messageInput = document.getElementById('message-input');
        this.chatForm = document.getElementById('chat-form');
        this.chatMessages = document.getElementById('chat-messages');
        this.sendButton = document.getElementById('send-button');
        this.cancelButton = document.getElementById('cancel-button');
        this.modelSelect = document.getElementById('model-select');
        this.templateSelect = document.getElementById('template-select');
        this.templatePreviewBtn = document.getElementById('template-preview-btn');
        this.statusIndicator = document.getElementById('connection-status');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('.status-text');
        
        this.currentModel = this.modelSelect.value;
        this.currentTemplate = null;
        this.isLoading = false;
        this.currentStreamController = null; // For cancelling streams
        
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
        
        // Template selection change
        this.templateSelect.addEventListener('change', (e) => {
            this.handleTemplateSelection();
        });
        
        // Template preview button
        this.templatePreviewBtn.addEventListener('click', () => {
            this.showTemplatePreview();
        });
        
        // Enter key handling
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Cancel button
        this.cancelButton.addEventListener('click', () => {
            this.cancelCurrentRequest();
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
            // Use streaming for better user experience
            await this.sendMessageStreaming(message);
            
        } catch (error) {
            this.addErrorMessage(`Network error: ${error.message}`);
            this.updateStatus('error', 'Network error');
            console.error('Chat request failed:', error);
        } finally {
            this.setLoading(false);
        }
    }
    
    async sendMessageStreaming(message) {
        return new Promise((resolve, reject) => {
            try {
                // Create AbortController for cancellation
                this.currentStreamController = new AbortController();
                const signal = this.currentStreamController.signal;
                
                // Create assistant message placeholder
                const assistantMessageDiv = this.addStreamingMessage();
                let fullResponse = '';
                
                // Use fetch with streaming response
                fetch('/api/chat?stream=true', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        model: this.currentModel
                    }),
                    signal: signal // Attach abort signal
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    this.updateStatus('connected', `Streaming from ${this.currentModel}...`);
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';
                    
                    const readStream = () => {
                        reader.read().then(({ done, value }) => {
                            if (done) {
                                this.finalizeStreamingMessage(assistantMessageDiv, fullResponse);
                                this.updateStatus('connected', `Response complete from ${this.currentModel}`);
                                this.currentStreamController = null;
                                resolve();
                                return;
                            }
                            
                            // Check if request was cancelled
                            if (signal.aborted) {
                                reader.cancel();
                                return;
                            }
                            
                            // Decode the chunk and add to buffer
                            buffer += decoder.decode(value, { stream: true });
                            
                            // Process complete lines (SSE format: "data: {...}\n\n")
                            const lines = buffer.split('\n');
                            buffer = lines.pop(); // Keep incomplete line in buffer
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    try {
                                        const data = JSON.parse(line.slice(6)); // Remove 'data: '
                                        
                                        if (data.type === 'content') {
                                            fullResponse += data.content;
                                            this.updateStreamingMessage(assistantMessageDiv, fullResponse);
                                        } else if (data.error) {
                                            this.addErrorMessage(data.error);
                                            this.updateStatus('error', 'Streaming failed');
                                            reject(new Error(data.error));
                                            return;
                                        }
                                    } catch (parseError) {
                                        console.error('Failed to parse streaming data:', parseError);
                                    }
                                }
                            }
                            
                            readStream();
                        }).catch(error => {
                            if (error.name === 'AbortError') {
                                // Request was cancelled
                                this.finalizeStreamingMessage(assistantMessageDiv, fullResponse + ' [cancelled]');
                                resolve();
                                return;
                            }
                            
                            console.error('Stream reading error:', error);
                            this.addErrorMessage('Streaming connection failed');
                            this.updateStatus('error', 'Connection lost');
                            reject(error);
                        });
                    };
                    
                    readStream();
                })
                .catch(error => {
                    if (error.name === 'AbortError') {
                        // Request was cancelled
                        resolve();
                        return;
                    }
                    
                    console.error('Fetch error:', error);
                    this.addErrorMessage(`Network error: ${error.message}`);
                    this.updateStatus('error', 'Network error');
                    reject(error);
                });
                
            } catch (error) {
                reject(error);
            }
        });
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
        this.cancelButton.disabled = !loading;
        this.cancelButton.style.display = loading ? 'inline-block' : 'none';
        
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
    
    addStreamingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message streaming-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = '';
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.innerHTML = `${new Date().toLocaleTimeString()} <span class="streaming-indicator">●</span>`;
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    updateStreamingMessage(messageDiv, content) {
        const contentDiv = messageDiv.querySelector('.message-content');
        if (contentDiv) {
            contentDiv.textContent = content;
        }
        this.scrollToBottom();
    }
    
    finalizeStreamingMessage(messageDiv, finalContent) {
        const contentDiv = messageDiv.querySelector('.message-content');
        const metaDiv = messageDiv.querySelector('.message-meta');
        
        if (contentDiv) {
            contentDiv.textContent = finalContent;
        }
        
        if (metaDiv) {
            metaDiv.innerHTML = new Date().toLocaleTimeString();
        }
        
        // Remove streaming class
        messageDiv.classList.remove('streaming-message');
        this.scrollToBottom();
    }
    
    cancelCurrentRequest() {
        if (this.currentStreamController) {
            this.currentStreamController.abort();
            this.currentStreamController = null;
            this.addSystemMessage('Request cancelled by user');
            this.updateStatus('error', 'Request cancelled');
            this.setLoading(false);
        }
    }
    
    handleTemplateSelection() {
        const selectedTemplateId = this.templateSelect.value;
        
        if (selectedTemplateId) {
            this.currentTemplate = selectedTemplateId;
            this.templatePreviewBtn.style.display = 'inline-block';
            this.addSystemMessage(`Template selected: ${this.templateSelect.options[this.templateSelect.selectedIndex].text}`);
        } else {
            this.currentTemplate = null;
            this.templatePreviewBtn.style.display = 'none';
            this.addSystemMessage('Template cleared');
        }
    }
    
    showTemplatePreview() {
        if (!this.currentTemplate) return;
        
        // Get template details from the select option
        const selectedOption = this.templateSelect.options[this.templateSelect.selectedIndex];
        const templateName = selectedOption.text;
        const variables = selectedOption.getAttribute('data-variables') || '';
        
        let previewMessage = `📋 Template: ${templateName}\n`;
        
        if (variables) {
            const varList = variables.split(',');
            previewMessage += `Variables needed: ${varList.join(', ')}\n\n`;
            previewMessage += 'Please provide values for these variables to use this template.';
        } else {
            previewMessage += 'This template has no variables and can be used directly.';
        }
        
        this.addSystemMessage(previewMessage);
    }
    
    async loadTemplateVariables(templateId) {
        // This would make an API call to get template details
        // For now, we'll use the data from the select option
        try {
            const response = await fetch(`/api/templates/${templateId}`);
            if (response.ok) {
                const template = await response.json();
                return template.metadata.variables || [];
            }
        } catch (e) {
            console.error('Failed to load template variables:', e);
        }
        return [];
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});