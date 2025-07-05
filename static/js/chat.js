class ChatInterface {
    constructor() {
        this.isLoading = false;
        this.autoScroll = true;
        this.currentMode = 'chat';
        this.webSearchEnabled = false;
        this.streamingMessage = null;
        this.maxTokens = 50000;
        this.mcpStatus = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSettings();
        this.focusInput();
        this.checkMCPStatus();
        this.setupDocumentUpload();
    }

    bindEvents() {
        // Message input events
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        messageInput.addEventListener('input', (e) => this.autoResize(e.target));

        // Button events
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('fileInput').addEventListener('change', () => this.uploadFile());
        document.getElementById('webSearchBtn').addEventListener('click', () => this.toggleWebSearch());

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
            autoScroll: document.getElementById('autoScrollCheck'),
            sound: document.getElementById('soundCheck'),
            streaming: document.getElementById('streamingCheck'),
            maxTokens: document.getElementById('maxTokensInput')
        };

        Object.entries(settingsElements).forEach(([key, element]) => {
            if (element) {
                element.addEventListener('change', (e) => {
                    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
                    this.updateSetting(key, value);
                });
            }
        });

        // Close modal when clicking outside
        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeSettings();
            }
        });

        document.getElementById('mcpStatusModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeMCPStatus();
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

    setupDocumentUpload() {
        const uploadArea = document.getElementById('documentUploadArea');
        
        // Drag and drop events
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        uploadArea.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
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

        // Update mode status
        const statusElement = document.getElementById('currentModeStatus');
        const modeNames = {
            'chat': 'Normal Chat',
            'document': 'Document Chat',
            'rag': 'RAG Mode',
            'image': 'Image Generation'
        };
        statusElement.textContent = modeNames[mode] || 'Unknown Mode';

        // Show/hide relevant UI elements
        const uploadArea = document.getElementById('documentUploadArea');
        const messageInput = document.getElementById('messageInput');
        
        if (mode === 'document' || mode === 'rag') {
            uploadArea.style.display = 'block';
            messageInput.placeholder = mode === 'document' 
                ? 'Upload a document and ask questions about it...'
                : 'Ask questions and I\'ll search for relevant information...';
        } else {
            uploadArea.style.display = 'none';
            messageInput.placeholder = 'Type your message here...';
        }

        if (mode === 'image') {
            this.openImageGenPanel();
        } else {
            this.closeImageGenPanel();
        }
    }

    toggleWebSearch() {
        this.webSearchEnabled = !this.webSearchEnabled;
        const searchBtn = document.getElementById('webSearchBtn');
        
        if (this.webSearchEnabled) {
            searchBtn.style.background = '#059669';
            searchBtn.title = 'Web Search: ON';
            searchBtn.innerHTML = '<i class="fas fa-search"></i>';
        } else {
            searchBtn.style.background = '#6b7280';
            searchBtn.title = 'Web Search: OFF';
            searchBtn.innerHTML = '<i class="fas fa-search"></i>';
        }
    }

    // Send message with enhanced routing
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
            // Route based on current mode and web search status
            if (this.webSearchEnabled) {
                await this.performWebSearch(message);
            } else {
                switch (this.currentMode) {
                    case 'document':
                        await this.sendDocumentChatMessage(message);
                        break;
                    case 'rag':
                        await this.sendRAGMessage(message);
                        break;
                    case 'image':
                        await this.generateImageFromMessage(message);
                        break;
                    default:
                        await this.sendChatMessage(message);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.hideTypingIndicator();
            this.isLoading = false;
            this.updateSendButton();
        }
    }

    async sendChatMessage(message) {
        try {
            const response = await fetch('/enhanced/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    stream: true,
                    mode: 'chat',
                    max_tokens: this.maxTokens
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await this.handleStreamingResponse(response);
        } catch (error) {
            throw error;
        }
    }

    async sendDocumentChatMessage(message) {
        try {
            const response = await fetch('/enhanced/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    stream: true,
                    mode: 'document',
                    max_tokens: this.maxTokens
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await this.handleStreamingResponse(response);
        } catch (error) {
            throw error;
        }
    }

    async sendRAGMessage(message) {
        try {
            const response = await fetch('/enhanced/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    stream: true,
                    mode: 'rag',
                    max_tokens: this.maxTokens
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await this.handleStreamingResponse(response);
        } catch (error) {
            throw error;
        }
    }

    async performWebSearch(query) {
        try {
            const response = await fetch('/enhanced/web_search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    num_results: 5,
                    search_type: 'web'
                })
            });

            const data = await response.json();
            
            if (data.success && data.results) {
                let searchResults = `🔍 Web Search Results for "${query}":\n\n`;
                
                if (data.results.organic_results) {
                    data.results.organic_results.slice(0, 5).forEach((result, index) => {
                        searchResults += `${index + 1}. **${result.title}**\n`;
                        searchResults += `   ${result.snippet}\n`;
                        searchResults += `   🔗 ${result.link}\n\n`;
                    });
                } else {
                    searchResults += 'No results found.';
                }
                
                this.addMessage('assistant', searchResults);
            } else {
                this.addMessage('assistant', `❌ Web search failed: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Web search error:', error);
            this.addMessage('assistant', '❌ Web search encountered an error. Please try again.');
        }
    }

    async generateImageFromMessage(prompt) {
        try {
            const response = await fetch('/enhanced/generate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            const data = await response.json();

            if (data.success && data.image_url) {
                this.addMessage('assistant', `🎨 Generated image for: "${prompt}"\n${data.image_url}`);
                this.addImageToPanel(data.image_url, prompt);
            } else {
                this.addMessage('assistant', `❌ Image generation failed: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Image generation error:', error);
            this.addMessage('assistant', '❌ Image generation encountered an error. Please try again.');
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
                            } else if (parsed.tool_status) {
                                // Handle tool execution status
                                this.updateStreamingMessage(messageId, `🔧 ${parsed.tool_status}...\n\n${fullText}`);
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

        await this.handleFileUpload(file);
        fileInput.value = '';
    }

    async handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        this.addMessage('user', `📎 Uploading: ${file.name}`);
        this.showTypingIndicator();

        try {
            const response = await fetch('/enhanced/upload_file', {
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
                    message += '\n\n✅ Document is now ready for chat! You can ask questions about its content.';
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
        }
    }

    // Image Generation
    openImageGenPanel() {
        document.getElementById('imageGenPanel').classList.add('show');
    }

    closeImageGenPanel() {
        document.getElementById('imageGenPanel').classList.remove('show');
        // Reset mode to chat if closing image panel
        if (this.currentMode === 'image') {
            this.switchMode('chat');
        }
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
            const response = await fetch('/enhanced/generate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            if (data.success && data.image_url) {
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

    // MCP Status
    async checkMCPStatus() {
        try {
            const response = await fetch('/mcp/status');
            const data = await response.json();
            
            this.mcpStatus = data;
            this.updateMCPStatusIndicator(data);
        } catch (error) {
            console.error('Error checking MCP status:', error);
            this.updateMCPStatusIndicator({ success: false, error: 'Connection failed' });
        }
    }

    updateMCPStatusIndicator(status) {
        const indicator = document.getElementById('mcpStatusIndicator');
        
        if (status.success && status.servers) {
            const activeServers = Object.values(status.servers).filter(Boolean).length;
            const totalServers = Object.keys(status.servers).length;
            
            if (activeServers === totalServers) {
                indicator.className = 'status-indicator online';
                indicator.innerHTML = '<i class="fas fa-circle"></i>';
            } else if (activeServers > 0) {
                indicator.className = 'status-indicator loading';
                indicator.innerHTML = '<i class="fas fa-circle"></i>';
            } else {
                indicator.className = 'status-indicator offline';
                indicator.innerHTML = '<i class="fas fa-circle"></i>';
            }
        } else {
            indicator.className = 'status-indicator offline';
            indicator.innerHTML = '<i class="fas fa-circle"></i>';
        }
    }

    showMCPStatus() {
        const modal = document.getElementById('mcpStatusModal');
        const content = document.getElementById('mcpStatusContent');
        
        modal.classList.add('show');
        
        if (this.mcpStatus.success && this.mcpStatus.servers) {
            let statusHTML = '<div class="setting-group">';
            
            Object.entries(this.mcpStatus.servers).forEach(([serverName, isActive]) => {
                const statusClass = isActive ? 'online' : 'offline';
                const statusText = isActive ? 'Online' : 'Offline';
                const icon = isActive ? 'fa-check-circle' : 'fa-times-circle';
                
                statusHTML += `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <span style="font-weight: 500;">${serverName.charAt(0).toUpperCase() + serverName.slice(1)} Server</span>
                        <span class="status-indicator ${statusClass}">
                            <i class="fas ${icon}"></i> ${statusText}
                        </span>
                    </div>
                `;
            });
            
            statusHTML += '</div>';
            content.innerHTML = statusHTML;
        } else {
            content.innerHTML = `
                <div class="status-indicator offline">
                    <i class="fas fa-exclamation-triangle"></i>
                    Unable to connect to MCP servers
                </div>
            `;
        }
    }

    closeMCPStatus() {
        document.getElementById('mcpStatusModal').classList.remove('show');
    }

    // Navigation functions
    newChat() {
        fetch('/new_session')
            .then(response => response.json())
            .then(data => {
                if (data.session_id) {
                    this.clearChatMessages();
                    this.addMessage('assistant', 'Hello! I\'m your AI assistant with enhanced capabilities. How can I help you today?');
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
            case 'maxTokens':
                this.maxTokens = parseInt(value) || 50000;
                break;
        }
    }

    loadSettings() {
        const settings = {
            autoScroll: localStorage.getItem('autoScroll') !== 'false',
            sound: localStorage.getItem('sound') === 'true',
            streaming: localStorage.getItem('streaming') !== 'false',
            maxTokens: parseInt(localStorage.getItem('maxTokens')) || 50000
        };

        // Apply settings
        this.autoScroll = settings.autoScroll;
        this.maxTokens = settings.maxTokens;

        // Update UI
        const elements = {
            autoScrollCheck: document.getElementById('autoScrollCheck'),
            soundCheck: document.getElementById('soundCheck'),
            streamingCheck: document.getElementById('streamingCheck'),
            maxTokensInput: document.getElementById('maxTokensInput')
        };

        Object.entries(elements).forEach(([key, element]) => {
            if (element) {
                const settingKey = key.replace('Check', '').replace('Input', '');
                if (element.type === 'checkbox') {
                    element.checked = settings[settingKey];
                } else {
                    element.value = settings[settingKey];
                }
            }
        });
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
    window.showMCPStatus = () => window.chatInterface.showMCPStatus();
    window.closeMCPStatus = () => window.chatInterface.closeMCPStatus();
    window.toggleSidebar = () => window.chatInterface.toggleSidebar();
    window.closeSidebar = () => window.chatInterface.closeSidebar();
    window.logout = () => window.chatInterface.logout();
    
    // Close modals with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeImageModal();
            window.chatInterface.closeSettings();
            window.chatInterface.closeMCPStatus();
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