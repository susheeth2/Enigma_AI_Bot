class ChatInterface {
    constructor() {
        this.isLoading = false;
        this.autoScroll = true;
        this.currentMode = 'chat';
        this.streamingMessage = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSettings();
        this.focusInput();
    }

    bindEvents() {
        // Message input events
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        messageInput.addEventListener('input', (e) => this.autoResize(e.target));

        // Button events
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('fileInput').addEventListener('change', () => this.uploadFile());

        // Mode selector events
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchMode(e.target.dataset.mode));
        });

        // Settings events
        this.bindSettingsEvents();

        // Mobile events
        this.bindMobileEvents();

        // Image generation events
        this.bindImageGenEvents();
    }

    bindSettingsEvents() {
        const settingsElements = {
            theme: document.getElementById('themeSelect'),
            fontSize: document.getElementById('fontSizeSelect'),
            autoScroll: document.getElementById('autoScrollCheck'),
            sound: document.getElementById('soundCheck')
        };

        Object.entries(settingsElements).forEach(([key, element]) => {
            if (element) {
                element.addEventListener('change', (e) => this.updateSetting(key, e.target.value || e.target.checked));
            }
        });

        // Close modal when clicking outside
        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeSettings();
            }
        });
    }

    bindMobileEvents() {
        const overlay = document.getElementById('overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.closeSidebar());
        }
    }

    bindImageGenEvents() {
        const generateBtn = document.getElementById('generateBtn');
        const promptTextarea = document.getElementById('imagePromptInput');
        
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateImage());
        }

        if (promptTextarea) {
            promptTextarea.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    this.generateImage();
                }
            });
        }

        // Example prompts
        document.querySelectorAll('.example-prompt').forEach(prompt => {
            prompt.addEventListener('click', (e) => {
                this.setImagePrompt(e.target.textContent.trim());
            });
        });

        // Close panel
        const closePanelBtn = document.getElementById('closePanelBtn');
        if (closePanelBtn) {
            closePanelBtn.addEventListener('click', () => this.closeImageGenPanel());
        }
    }

    // Auto-resize textarea
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px';
    }

    // Handle keyboard shortcuts
    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    // Switch between chat modes
    switchMode(mode) {
        this.currentMode = mode;
        
        // Update active button
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Show/hide relevant UI elements
        if (mode === 'image') {
            this.openImageGenPanel();
        } else {
            this.closeImageGenPanel();
        }
    }

    // Send message with streaming support
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || this.isLoading) return;

        // Clear input and reset height
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        this.isLoading = true;
        this.updateSendButton();

        // Add user message
        this.addMessage('user', message);
        this.showTypingIndicator();

        try {
            if (this.currentMode === 'search') {
                await this.performWebSearch(message);
            } else {
                await this.sendChatMessage(message);
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', 'Sorry, I encountered a network error. Please try again.');
        } finally {
            this.hideTypingIndicator();
            this.isLoading = false;
            this.updateSendButton();
        }
    }

    async sendChatMessage(message) {
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, stream: true })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Check if response supports streaming
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/stream')) {
                await this.handleStreamingResponse(response);
            } else {
                const data = await response.json();
                if (data.error) {
                    this.addMessage('assistant', 'Sorry, I encountered an error: ' + data.error);
                } else {
                    this.addMessage('assistant', data.ai_response);
                }
            }
        } catch (error) {
            throw error;
        }
    }

    async handleStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Create streaming message
        const messageId = this.addStreamingMessage('assistant');
        let fullText = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            this.finishStreamingMessage(messageId);
                            return;
                        }
                        
                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.content) {
                                fullText += parsed.content;
                                this.updateStreamingMessage(messageId, fullText);
                            }
                        } catch (e) {
                            // Ignore parsing errors for partial chunks
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Streaming error:', error);
            this.finishStreamingMessage(messageId);
            this.addMessage('assistant', 'Sorry, there was an error with the streaming response.');
        }
    }

    async performWebSearch(query) {
        // Placeholder for web search functionality
        // This will be implemented when the backend route is ready
        this.addMessage('assistant', `🔍 Web search functionality will be implemented soon. You searched for: "${query}"`);
    }

    // Add message to chat
    addMessage(role, content) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const avatar = role === 'user' ? this.getUserInitial() : 'AI';
        
        // Handle image content
        let messageContent = content;
        if (content.includes('data:image/') || content.includes('/static/generated_images/')) {
            const imageMatch = content.match(/(data:image\/[^"]+|\/static\/generated_images\/[^"]+)/);
            if (imageMatch) {
                const imageUrl = imageMatch[1];
                messageContent = content.replace(imageMatch[0], '');
                messageContent += `<br><img src="${imageUrl}" alt="Generated Image" class="generated-image" onclick="openImageModal('${imageUrl}')">`;
            }
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${messageContent.replace(/\n/g, '<br>')}</div>
                <div class="message-time">${timeString}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        
        if (this.autoScroll) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        return messageDiv;
    }

    addStreamingMessage(role) {
        const messageDiv = this.addMessage(role, '');
        const messageText = messageDiv.querySelector('.message-text');
        messageText.classList.add('streaming-text');
        return messageDiv;
    }

    updateStreamingMessage(messageElement, content) {
        const messageText = messageElement.querySelector('.message-text');
        messageText.innerHTML = content.replace(/\n/g, '<br>');
        
        if (this.autoScroll) {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    finishStreamingMessage(messageElement) {
        const messageText = messageElement.querySelector('.message-text');
        messageText.classList.remove('streaming-text');
    }

    getUserInitial() {
        const username = document.querySelector('.user-name')?.textContent || 'U';
        return username.charAt(0).toUpperCase();
    }

    // Typing indicator
    showTypingIndicator() {
        document.getElementById('typing-indicator').classList.add('show');
        if (this.autoScroll) {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    hideTypingIndicator() {
        document.getElementById('typing-indicator').classList.remove('show');
    }

    // Update send button state
    updateSendButton() {
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = this.isLoading;
        sendBtn.innerHTML = this.isLoading ? '<i class="fas fa-spinner fa-spin"></i>' : '<i class="fas fa-paper-plane"></i>';
    }

    // File upload
    async uploadFile() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        this.addMessage('user', `📎 Uploading: ${file.name}`);
        this.showTypingIndicator();

        try {
            const response = await fetch('/upload_file', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                this.addMessage('assistant', 'Upload failed: ' + data.error);
            } else {
                let message = data.message;
                
                if (data.type === 'document') {
                    message += ` (${data.chunks} chunks processed)`;
                } else if (data.type === 'image') {
                    message += `\n\nImage Analysis: ${data.description}`;
                }
                
                this.addMessage('assistant', message);
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.addMessage('assistant', 'File upload failed. Please try again.');
        } finally {
            this.hideTypingIndicator();
            fileInput.value = '';
        }
    }

    // Image Generation
    openImageGenPanel() {
        document.getElementById('imageGenPanel').classList.add('show');
    }

    closeImageGenPanel() {
        document.getElementById('imageGenPanel').classList.remove('show');
        // Reset mode to chat
        this.switchMode('chat');
    }

    setImagePrompt(text) {
        const promptInput = document.getElementById('imagePromptInput');
        if (promptInput) {
            promptInput.value = text;
            promptInput.focus();
        }
    }

    async generateImage() {
        const promptInput = document.getElementById('imagePromptInput');
        const prompt = promptInput.value.trim();

        if (!prompt) {
            alert('Please enter a prompt to generate an image');
            return;
        }

        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            if (data.image_url) {
                // Add to chat
                this.addMessage('assistant', `🎨 Generated image for: "${prompt}"\n${data.image_url}`);
                
                // Add to image panel
                this.addImageToPanel(data.image_url, prompt);
                
                // Clear prompt
                promptInput.value = '';
            } else {
                throw new Error(data.error || 'Failed to generate image');
            }

        } catch (error) {
            console.error('Generation error:', error);
            alert(`Failed to generate image: ${error.message}`);
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Image';
        }
    }

    addImageToPanel(imageUrl, prompt) {
        const imagesContainer = document.getElementById('generatedImages');
        if (!imagesContainer) return;

        const imageCard = document.createElement('div');
        imageCard.className = 'image-card';
        
        imageCard.innerHTML = `
            <img src="${imageUrl}" alt="Generated Image" onclick="openImageModal('${imageUrl}')">
            <div class="image-card-info">
                <div class="image-prompt">${prompt}</div>
                <div class="image-actions">
                    <button class="image-action" onclick="openImageModal('${imageUrl}')">
                        <i class="fas fa-expand"></i> View
                    </button>
                    <a href="${imageUrl}" download="generated-image.png" class="image-action">
                        <i class="fas fa-download"></i> Download
                    </a>
                </div>
            </div>
        `;
        
        imagesContainer.insertBefore(imageCard, imagesContainer.firstChild);
    }

    // Navigation functions
    newChat() {
        fetch('/new_session')
            .then(response => response.json())
            .then(data => {
                if (data.session_id) {
                    this.clearChatMessages();
                    this.addMessage('assistant', 'Hello! I\'m your AI assistant. How can I help you today?');
                }
            })
            .catch(error => console.error('Error creating new session:', error));
    }

    clearChat() {
        if (confirm('Are you sure you want to clear this chat?')) {
            this.clearChatMessages();
            this.addMessage('assistant', 'Chat cleared. How can I help you today?');
        }
    }

    clearChatMessages() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = `
            <div class="typing-indicator" id="typing-indicator">
                <div class="message-avatar">AI</div>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
    }

    // Settings
    openSettings() {
        document.getElementById('settingsModal').classList.add('show');
    }

    closeSettings() {
        document.getElementById('settingsModal').classList.remove('show');
    }

    updateSetting(key, value) {
        localStorage.setItem(key, value);
        
        switch (key) {
            case 'autoScroll':
                this.autoScroll = value;
                break;
            case 'theme':
                this.applyTheme(value);
                break;
            case 'fontSize':
                this.applyFontSize(value);
                break;
        }
    }

    loadSettings() {
        const settings = {
            theme: localStorage.getItem('theme') || 'light',
            fontSize: localStorage.getItem('fontSize') || 'medium',
            autoScroll: localStorage.getItem('autoScroll') !== 'false',
            sound: localStorage.getItem('sound') === 'true'
        };

        // Apply settings
        this.autoScroll = settings.autoScroll;
        this.applyTheme(settings.theme);
        this.applyFontSize(settings.fontSize);

        // Update UI
        const elements = {
            themeSelect: document.getElementById('themeSelect'),
            fontSizeSelect: document.getElementById('fontSizeSelect'),
            autoScrollCheck: document.getElementById('autoScrollCheck'),
            soundCheck: document.getElementById('soundCheck')
        };

        Object.entries(elements).forEach(([key, element]) => {
            if (element) {
                const settingKey = key.replace('Select', '').replace('Check', '');
                if (element.type === 'checkbox') {
                    element.checked = settings[settingKey];
                } else {
                    element.value = settings[settingKey];
                }
            }
        });
    }

    applyTheme(theme) {
        // Theme application logic would go here
        document.documentElement.setAttribute('data-theme', theme);
    }

    applyFontSize(size) {
        // Font size application logic would go here
        document.documentElement.setAttribute('data-font-size', size);
    }

    // Mobile functions
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
    }

    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
    }

    focusInput() {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.focus();
        }
    }

    // Utility functions
    logout() {
        if (confirm('Are you sure you want to logout?')) {
            window.location.href = '/logout';
        }
    }
}

// Global functions for HTML onclick handlers
function openImageModal(imageSrc) {
    document.getElementById('modalImage').src = imageSrc;
    document.getElementById('imageModal').classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    document.getElementById('imageModal').classList.remove('show');
    document.body.style.overflow = 'auto';
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatInterface = new ChatInterface();
    
    // Global function bindings for HTML onclick handlers
    window.newChat = () => window.chatInterface.newChat();
    window.clearChat = () => window.chatInterface.clearChat();
    window.openSettings = () => window.chatInterface.openSettings();
    window.closeSettings = () => window.chatInterface.closeSettings();
    window.toggleSidebar = () => window.chatInterface.toggleSidebar();
    window.closeSidebar = () => window.chatInterface.closeSidebar();
    window.logout = () => window.chatInterface.logout();
    
    // Close modals with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeImageModal();
            window.chatInterface.closeSettings();
            window.chatInterface.closeImageGenPanel();
        }
    });
    
    // Close image modal when clicking outside
    document.getElementById('imageModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeImageModal();
        }
    });
});