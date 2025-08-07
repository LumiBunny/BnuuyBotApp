let pollingInterval = null;

// Global function to toggle history list
function toggleHistoryList() {
    const historyList = document.getElementById('history-list');
    if (historyList.style.display === 'none' || !historyList.style.display) {
        historyList.style.display = 'block';
        loadHistoryFiles();
    } else {
        historyList.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Set up load history button
    const loadHistoryBtn = document.querySelector('.btn-load');
    if (loadHistoryBtn) {
        loadHistoryBtn.addEventListener('click', toggleHistoryList);
    }
    
    // Intercept mic form submission
    const micForm = document.getElementById('mic-form');
    if (micForm) {
        micForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const action = this.getAttribute('action');
            
            fetch(action, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('Mic action response:', data);
                if (data.success) {
                    // Update the form action
                    this.setAttribute('action', 
                        action.includes('start_listening') ? '/stop_listening' : '/start_listening');
                    
                    // Update the button
                    const button = this.querySelector('button');
                    if (button) {
                        button.title = action.includes('start_listening') ? 'Stop listening' : 'Start listening';
                        button.className = `icon-button ${action.includes('start_listening') ? 'btn-mic-on' : 'btn-mic-off'}`;
                        
                        // Update the icon
                        const icon = button.querySelector('i');
                        if (icon) {
                            icon.className = `fa-solid ${action.includes('start_listening') ? 'fa-microphone' : 'fa-microphone-slash'}`;
                        }
                    }
                    
                    // Update status indicator
                    const statusIndicator = document.querySelector('.status-indicator');
                    if (statusIndicator) {
                        statusIndicator.className = `status-indicator ${action.includes('start_listening') ? 'status-active' : 'status-inactive'}`;
                        
                        // Update the text next to the indicator
                        const statusText = statusIndicator.nextElementSibling;
                        if (statusText) {
                            statusText.textContent = action.includes('start_listening') ? 'Active' : 'Inactive';
                        }
                    }
                }
            })
            .catch(error => console.error('Error with mic action:', error));
        });
    }

    // Intercept clear form submission
    const clearForm = document.getElementById('clear-chat-form');
    if (clearForm) {
        clearForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch('/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                console.log('Clear response:', data);
                if (data.success) {
                    // Clear the conversation div
                    const conversationDiv = document.getElementById('conversation');
                    if (conversationDiv) {
                        conversationDiv.innerHTML = '';
                    }
                }
            })
            .catch(error => console.error('Error clearing conversation:', error));
        });
    }

    // Handle chat history functionality
    function toggleHistoryList() {
        const historyList = document.getElementById('history-list');
        if (historyList.style.display === 'none') {
            historyList.style.display = 'block';
            loadHistoryFiles();
        } else {
            historyList.style.display = 'none';
        }
    }

    function loadHistoryFiles() {
        const historyFiles = document.getElementById('history-files');
        if (!historyFiles) return;
        
        // Show loading state
        historyFiles.innerHTML = '<p class="loading-text">Loading chat histories...</p>';
        
        fetch('/list_histories')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.histories && data.histories.length > 0) {
                    let html = '<ul class="history-file-list">';
                    
                    // Sort by most recent first (assuming filename starts with chat_YYYYMMDD_HHMMSS)
                    const sortedHistories = [...data.histories].sort().reverse();
                    
                    sortedHistories.forEach(file => {
                        // Extract date/time from filename for display
                        let displayName = file;
                        let fileDate = '';
                        
                        // Try to extract and format the date from the filename
                        // Expected format: chat_YYYYMMDD_HHMMSS.json
                        const match = file.match(/chat_(\d{8})_(\d{6})\.json/);
                        if (match) {
                            try {
                                const dateStr = match[1]; // YYYYMMDD
                                const timeStr = match[2]; // HHMMSS
                                const year = dateStr.substring(0, 4);
                                const month = dateStr.substring(4, 6);
                                const day = dateStr.substring(6, 8);
                                const hour = timeStr.substring(0, 2);
                                const minute = timeStr.substring(2, 4);
                                
                                const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:00`);
                                displayName = date.toLocaleString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    hour12: true
                                });
                                
                                fileDate = date.toISOString();
                            } catch (e) {
                                console.error('Error parsing date from filename:', e);
                            }
                        }
                        
                        html += `
                            <li class="history-file-item" data-filename="${file}" data-date="${fileDate}">
                                <a href="#" class="history-file-link">
                                    <i class="fa-regular fa-comment-dots"></i>
                                    <span class="history-file-name">${displayName}</span>
                                </a>
                            </li>`;
                    });
                    html += '</ul>';
                    historyFiles.innerHTML = html;
                    
                    // Add click event listeners to all history file links
                    document.querySelectorAll('.history-file-link').forEach(link => {
                        link.addEventListener('click', function(e) {
                            e.preventDefault();
                            const listItem = this.closest('.history-file-item');
                            const filename = listItem.getAttribute('data-filename');
                            loadChatHistory(filename);
                        });
                    });
                } else {
                    historyFiles.innerHTML = `
                        <div class="no-history">
                            <i class="fa-regular fa-folder-open"></i>
                            <p>No chat histories found.</p>
                        </div>`;
                }
            })
            .catch(error => {
                console.error('Error loading history files:', error);
                if (historyFiles) {
                    historyFiles.innerHTML = `
                        <div class="error-message">
                            <i class="fa-solid fa-exclamation-triangle"></i>
                            <p>Error loading chat histories. Please try again later.</p>
                        </div>`;
                }
            });
    }

    function loadChatHistory(filename) {
        console.log('Loading chat history:', filename);
        
        // Stop polling to prevent interference with chat bubble display
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Hide the history list after selection
        const historyList = document.getElementById('history-list');
        if (historyList) {
            historyList.style.display = 'none';
        }
        
        // Show loading indicator and clear the conversation
        const conversationDiv = document.getElementById('conversation');
        if (conversationDiv) {
            conversationDiv.innerHTML = '<div class="message loading">Loading chat history...</div>';
        }
        
        // Clear the global state to prevent duplicates
        transcription_history = [];
        llm_responses = [];
        
        // Make an AJAX call to load the chat history
        fetch('/load_chat_history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename: filename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear the conversation div
                if (conversationDiv) {
                    conversationDiv.innerHTML = '';
                }
                
                // Add each message to the conversation using existing CSS classes
                if (data.messages && Array.isArray(data.messages)) {
                    data.messages.forEach(msg => {
                        if (msg.role === 'user' || msg.role === 'assistant') {
                            const messageDiv = document.createElement('div');
                            // Use existing CSS classes that are properly styled
                            messageDiv.className = msg.role === 'user' ? 'transcript-item' : 'bunny-item';
                            
                            // Format timestamp if available
                            let timestamp = '';
                            if (msg.timestamp) {
                                try {
                                    const date = new Date(msg.timestamp);
                                    timestamp = date.toLocaleTimeString();
                                } catch (e) {
                                    console.error('Error formatting timestamp:', e);
                                }
                            }
                            
                            // Use the proper HTML structure for existing CSS classes
                            messageDiv.innerHTML = `
                                <div class="message-name">${msg.role === 'user' ? 'You' : 'Bunny'}</div>
                                <div class="${msg.role === 'user' ? 'transcript-content' : 'response-content'}">${msg.content || ''}</div>
                                ${timestamp ? `<div class="time">${timestamp}</div>` : ''}
                            `;
                            
                            if (conversationDiv) {
                                conversationDiv.appendChild(messageDiv);
                            }
                        }
                    });
                    
                    // Scroll to bottom of conversation
                    if (conversationDiv) {
                        conversationDiv.scrollTop = conversationDiv.scrollHeight;
                    }
                }
                
                // Show success message
                const statusDiv = document.createElement('div');
                statusDiv.className = 'system-message';
                statusDiv.textContent = data.message || 'Chat history loaded successfully';
                if (conversationDiv) {
                    conversationDiv.appendChild(statusDiv);
                    conversationDiv.scrollTop = conversationDiv.scrollHeight;
                }
                
                // Restart polling after chat bubbles are loaded
                setTimeout(() => {
                    startPolling();
                }, 1000); // Wait 1 second to ensure chat bubbles are stable
            } else {
                // Show error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = data.error || 'Failed to load chat history';
                if (conversationDiv) {
                    conversationDiv.innerHTML = '';
                    conversationDiv.appendChild(errorDiv);
                }
            }
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
            if (conversationDiv) {
                conversationDiv.innerHTML = `
                    <div class="error-message">
                        Error loading chat history: ${error.message}
                    </div>
                `;
            }
        });
    }

    // Intercept end chat form submission
    const endChatForm = document.getElementById('end-chat-form');
    if (endChatForm) {
        endChatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to shut down the application? This will end the chat session and close the server.')) {
                fetch('/shutdown', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show a message before the page becomes unresponsive
                        alert('Shutting down the application. You may need to refresh your browser after the server has fully stopped.');
                        // The server will close the connection, so we'll let the browser handle it
                    } else {
                        alert('Failed to shut down: ' + (data.message || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error shutting down:', error);
                    // If we get an error, the server might have shut down anyway
                    alert('The server is shutting down. You may need to refresh your browser.');
                });
            }
        });
    }

    // Handle reset chat form submission
    const resetChatForm = document.getElementById('reset-chat-form');
    if (resetChatForm) {
        resetChatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show confirmation dialog
            if (confirm('Are you sure you want to reset the chat history and context? This will clear all conversation history and start a new chat.')) {
                // Show loading state
                const button = this.querySelector('button');
                const icon = button ? button.querySelector('i') : null;
                if (icon) {
                    const originalIcon = icon.className;
                    icon.className = 'fa-solid fa-spinner fa-spin';
                    
                    // Send reset request
                    fetch('/reset_chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Restore icon
                        if (icon) {
                            icon.className = originalIcon;
                        }
                        
                        if (data.success) {
                            // Clear the conversation display
                            const conversation = document.getElementById('conversation');
                            if (conversation) {
                                conversation.innerHTML = '';
                            }
                            
                            // Show success message
                            alert(data.message);
                        } else {
                            alert('Error: ' + (data.message || 'Failed to reset chat'));
                        }
                    })
                    .catch(error => {
                        console.error('Error resetting chat:', error);
                        alert('Error resetting chat. Please try again.');
                        
                        // Restore icon on error
                        if (icon) {
                            icon.className = originalIcon;
                        }
                    });
                }
            }
        });
    }

    // Intercept text message form submission
    const textMessageForm = document.getElementById('text-message-form');
    if (textMessageForm) {
        textMessageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageInput = document.getElementById('message_text');
            const text = messageInput.value.trim();
            
            if (!text) return; // Don't send empty messages
            
            // Clear the input immediately
            messageInput.value = '';
            // Trigger input event to adjust height
            messageInput.dispatchEvent(new Event('input'));
            
            fetch('/send_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Send message response:', data);
                // We've already cleared the input, so no need to do it again
            })
            .catch(error => console.error('Error sending message:', error));
        });
    }

    // Add reset chat button handler
    const resetChatBtn = document.getElementById('reset-chat-btn');
    if (resetChatBtn) {
        resetChatBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show confirmation dialog
            if (confirm('Are you sure you want to reset the chat history and context? This cannot be undone.')) {
                // Show loading state
                const icon = this.querySelector('i');
                if (icon) {
                    icon.className = 'fa-solid fa-spinner fa-spin';
                }
                
                // Send reset request
                fetch('/reset_chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    // Restore icon
                    if (icon) {
                        icon.className = 'fa-solid fa-rotate-left';
                    }
                    
                    if (data.success) {
                        // Clear the conversation display
                        const conversation = document.getElementById('conversation');
                        if (conversation) {
                            conversation.innerHTML = '';
                        }
                        
                        // Show success message
                        alert(data.message);
                    } else {
                        alert('Error: ' + (data.message || 'Failed to reset chat'));
                    }
                })
                .catch(error => {
                    console.error('Error resetting chat:', error);
                    alert('Error resetting chat. Please try again.');
                    
                    // Restore icon on error
                    if (icon) {
                        icon.className = 'fa-solid fa-rotate-left';
                    }
                });
            }
        });
    }

    // Start polling for updates
    startPolling();
});

// Create a global stopPolling function
window.stopPolling = function() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
};

// Start polling for updates
function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(fetchUpdates, 1000); // Poll every second
}

function fetchUpdates() {
    fetch('/get_transcription')
        .then(response => response.json())
        .then(data => {
            console.log('Update data:', data);
            updateConversation(data);
            updateMicStatus(data.is_listening);
        })
        .catch(error => console.error('Error fetching updates:', error));
}

// Update conversation with new messages
function updateConversation(data) {
    const conversationDiv = document.getElementById('conversation');
    if (!conversationDiv) return;
    
    // Check if user was already at the bottom before updating
    const wasAtBottom = isScrolledToBottom(conversationDiv);
    
    // Clear "No conversation history yet" message if present
    if ((data.transcriptions && data.transcriptions.length > 0) || 
        (data.responses && data.responses.length > 0)) {
        const noHistoryMsg = conversationDiv.querySelector('p:only-child');
        if (noHistoryMsg && noHistoryMsg.textContent.includes('No conversation history yet')) {
            conversationDiv.innerHTML = '';
        }
    }
    
    // Add user transcriptions
    if (data.transcriptions) {
        data.transcriptions.forEach(item => {
            if (!isMessageDisplayed('user', item.text)) {
                const userMessageDiv = document.createElement('div');
                userMessageDiv.className = 'transcript-item';
                userMessageDiv.innerHTML = `
                    <div class="message-name">You</div>
                    <div class="transcript-content">${item.text}</div>
                    <div class="time">${item.time}</div>
                `;
                conversationDiv.appendChild(userMessageDiv);
            }
        });
    }
    
        // Add AI responses
        if (data.responses) {
            data.responses.forEach(item => {
                if (!isMessageDisplayed('bot', item.text)) {
                    const botMessageDiv = document.createElement('div');
                    botMessageDiv.className = 'bunny-item';
                    botMessageDiv.innerHTML = `
                        <div class="message-name">Bunny</div>
                        <div class="response-content">${item.text}</div>
                        <div class="time">${item.time}</div>
                    `;
                    conversationDiv.appendChild(botMessageDiv);
                }
            });
        }
        
        // If user was at the bottom before, scroll back to bottom
        if (wasAtBottom) {
            conversationDiv.scrollTop = conversationDiv.scrollHeight;
        }
    }

    // Helper function to check if a message is already displayed
    function isMessageDisplayed(type, text) {
        const conversationDiv = document.getElementById('conversation');
        if (!conversationDiv) return false;
        
        // Check for both formats: plain text (transcript-item/bunny-item) and chat bubbles (message)
        const plainTextSelector = type === 'user' ? '.transcript-item' : '.bunny-item';
        const chatBubbleSelector = type === 'user' ? '.message.user' : '.message.assistant';
        
        // Check plain text format first
        const plainTextMessages = conversationDiv.querySelectorAll(plainTextSelector);
        for (let i = 0; i < plainTextMessages.length; i++) {
            let content;
            if (type === 'user') {
                content = plainTextMessages[i].querySelector('.transcript-content');
            } else {
                content = plainTextMessages[i].querySelector('.response-content');
            }
            
            if (content && content.textContent.trim() === text.trim()) {
                return true;
            }
        }
        
        // Check chat bubble format (from loaded history) to prevent duplicates
        const chatBubbleMessages = conversationDiv.querySelectorAll(chatBubbleSelector);
        for (let i = 0; i < chatBubbleMessages.length; i++) {
            const content = chatBubbleMessages[i].querySelector('.message-content');
            if (content && content.textContent.trim() === text.trim()) {
                return true;
            }
        }
        
        return false;
    }

    // Helper function to check if scrolled to bottom
    function isScrolledToBottom(element) {
        return Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) < 10;
    }

    // Update mic status based on server state
    function updateMicStatus(isListening) {
        const micForm = document.getElementById('mic-form');
        if (!micForm) return;
        
        // Only update if the current state doesn't match
        const currentAction = micForm.getAttribute('action');
        const shouldBeListening = currentAction.includes('stop_listening');
        
        if (isListening !== shouldBeListening) {
            // Update the form action
            micForm.setAttribute('action', isListening ? '/stop_listening' : '/start_listening');
            
            // Update the button
            const button = micForm.querySelector('button');
            if (button) {
                button.title = isListening ? 'Stop listening' : 'Start listening';
                button.className = `icon-button ${isListening ? 'btn-mic-on' : 'btn-mic-off'}`;
                
                // Update the icon
                const icon = button.querySelector('i');
                if (icon) {
                    icon.className = `fa-solid ${isListening ? 'fa-microphone' : 'fa-microphone-slash'}`;
                }
            }
            
            // Update status indicator
            const statusIndicator = document.querySelector('.status-indicator');
            if (statusIndicator) {
                statusIndicator.className = `status-indicator ${isListening ? 'status-active' : 'status-inactive'}`;
                
                // Update the text next to the indicator
                const statusText = statusIndicator.nextElementSibling;
                if (statusText) {
                    statusText.textContent = isListening ? 'Active' : 'Inactive';
                }
            }
        }
    }