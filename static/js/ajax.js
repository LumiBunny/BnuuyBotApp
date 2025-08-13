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

    // Intercept TTS form submission
    const ttsForm = document.getElementById('tts-form');
    if (ttsForm) {
        ttsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const action = this.getAttribute('action');
            
            fetch(action, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('TTS toggle response:', data);
                if (data.success) {
                    // Update the button
                    const button = this.querySelector('button');
                    if (button) {
                        button.title = data.tts_enabled ? 'Turn TTS off' : 'Turn TTS on';
                        button.className = `icon-button ${data.tts_enabled ? 'btn-tts-on' : 'btn-tts-off'}`;
                        
                        // Update the icon
                        const icon = button.querySelector('i');
                        if (icon) {
                            icon.className = `fa-solid ${data.tts_enabled ? 'fa-volume-high' : 'fa-volume-xmark'}`;
                        }
                    }
                    
                    // Update TTS status indicator
                    const statusDiv = document.getElementById('status');
                    if (statusDiv) {
                        const ttsStatusDiv = statusDiv.children[2]; // Third child should be TTS status
                        if (ttsStatusDiv && ttsStatusDiv.textContent.includes('Speaking (TTS)')) {
                            const ttsIndicator = ttsStatusDiv.querySelector('.status-indicator');
                            if (ttsIndicator) {
                                ttsIndicator.className = `status-indicator ${data.tts_enabled ? 'status-active' : 'status-inactive'}`;
                                
                                // Update the text next to the indicator
                                const ttsStatusText = ttsIndicator.nextElementSibling;
                                if (ttsStatusText) {
                                    ttsStatusText.textContent = data.tts_enabled ? 'Active' : 'Inactive';
                                }
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }

    // Handle clear chat form submission (UI only)
    const clearForm = document.getElementById('clear-chat-form');
    if (clearForm) {
        clearForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state on the clear button
            const clearButton = this.querySelector('button[type="submit"]');
            const originalHTML = clearButton.innerHTML;
            clearButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            clearButton.disabled = true;
            
            fetch('/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                console.log('Clear chat response:', data);
                
                // Clear the conversation div
                const conversationDiv = document.getElementById('conversation');
                if (conversationDiv) {
                    conversationDiv.innerHTML = '';
                }
                
                // Show success message
                if (data.success) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'system-message';
                    messageDiv.textContent = data.message || 'Chat display has been cleared.';
                    conversationDiv.appendChild(messageDiv);
                    conversationDiv.scrollTop = conversationDiv.scrollHeight;
                }
            })
            .catch(error => {
                console.error('Error clearing chat:', error);
                alert('Failed to clear chat. Please check console for details.');
            })
            .finally(() => {
                // Restore button state
                clearButton.innerHTML = originalHTML;
                clearButton.disabled = false;
            });
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
                
                console.log('Original messages before sorting:', data.messages);
                
                const sortedMessages = [...data.messages].sort((a, b) => {
                    // Parse timestamps safely, default to 0 if invalid
                    const parseTime = (timestamp) => {
                        try {
                            // If timestamp is already a number, return it
                            if (typeof timestamp === 'number') return timestamp;
                            // If it's a string, try to parse it
                            if (typeof timestamp === 'string') {
                                // Handle ISO format with or without timezone
                                return new Date(timestamp).getTime() || 0;
                            }
                            return 0;
                        } catch (e) {
                            console.error('Error parsing timestamp:', e);
                            return 0;
                        }
                    };
                    
                    const timeA = parseTime(a.timestamp);
                    const timeB = parseTime(b.timestamp);
                    
                    console.log(`Comparing: ${a.role} (${a.timestamp} = ${timeA}) vs ${b.role} (${b.timestamp} = ${timeB})`);
                    
                    return timeA - timeB;
                });
                
                console.log('Messages after sorting:', sortedMessages);
                
                // Add each message to the conversation using existing CSS classes
                if (data.messages && Array.isArray(data.messages)) {
                    // Create a document fragment for better performance
                    const fragment = document.createDocumentFragment();
                    
                    sortedMessages.forEach(msg => {
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
                            
                            fragment.appendChild(messageDiv);
                        }
                    });
                    
                    // Append all messages at once for better performance
                    if (conversationDiv) {
                        conversationDiv.appendChild(fragment);
                        
                        // Scroll to bottom of conversation
                        conversationDiv.scrollTop = conversationDiv.scrollHeight;
                        
                        // Dispatch event that chat history is loaded
                        const event = new Event('chatHistoryLoaded');
                        document.dispatchEvent(event);
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
                }
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
        endChatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to end the chat session? This will save the conversation and shut down the application.')) {
                try {
                    // First, end the chat session
                    const endResponse = await fetch('/end_chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                    
                    const endData = await endResponse.json();
                    
                    if (endData.success) {
                        console.log('Chat session ended successfully');
                    } else {
                        console.warn('Failed to properly end chat session:', endData.message || 'Unknown error');
                    }
                    
                    // Then shut down the server
                    const shutdownResponse = await fetch('/shutdown', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                    
                    const shutdownData = await shutdownResponse.json();
                    
                    if (shutdownData.success) {
                        alert('Shutting down the application. You may need to refresh your browser after the server has fully stopped.');
                    } else {
                        alert('Failed to shut down: ' + (shutdownData.message || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error during shutdown:', error);
                    alert('The server is shutting down. You may need to refresh your browser.');
                }
            }
        });
    }

    // Handle reset chat form submission (full reset)
    const resetChatForm = document.getElementById('reset-chat-form');
    if (resetChatForm) {
        resetChatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show confirmation dialog
            if (confirm('Are you sure you want to reset the chat? This will clear all conversation history and context, and start a fresh chat session.')) {
                // Show loading state
                const button = this.querySelector('button[type="submit"]');
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                button.disabled = true;
                
                // Send reset request
                fetch('/reset_chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Reset chat response:', data);
                    
                    // Clear the conversation display
                    const conversationDiv = document.getElementById('conversation');
                    if (conversationDiv) {
                        conversationDiv.innerHTML = '';
                        
                        // Show success message in the chat
                        if (data.success) {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = 'system-message';
                            messageDiv.textContent = data.message || 'Chat has been fully reset. Starting a new conversation.';
                            conversationDiv.appendChild(messageDiv);
                            conversationDiv.scrollTop = conversationDiv.scrollHeight;
                        }
                    }
                    
                    // Update UI state
                    updateMicStatus(false);
                    
                    if (!data.success) {
                        throw new Error(data.message || 'Failed to reset chat');
                    }
                })
                .catch(error => {
                    console.error('Error resetting chat:', error);
                    
                    // Show error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = `Error: ${error.message || 'Failed to reset chat'}`;
                    
                    const conversationDiv = document.getElementById('conversation') || document.body;
                    conversationDiv.appendChild(errorDiv);
                    conversationDiv.scrollTop = conversationDiv.scrollHeight;
                })
                .finally(() => {
                    // Restore button state
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                });
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
    
    // Check if user was at bottom BEFORE adding new messages
    const wasAtBottom = isScrolledToBottom(conversationDiv);
    
    // Clear loading message if present
    if (conversationDiv.innerHTML === '<div class="message loading">Loading chat history...</div>') {
        conversationDiv.innerHTML = '';
    }
    
    // Combine and sort all messages by timestamp
    if ((data.transcriptions && data.transcriptions.length > 0) || 
        (data.responses && data.responses.length > 0)) {
        
        // Create a combined array of all messages with their type and timestamp
        const allMessages = [];
        
        // Add user messages (transcriptions)
        if (data.transcriptions) {
            data.transcriptions.forEach(item => {
                if (!isMessageDisplayed('user', item.text)) {
                    allMessages.push({
                        type: 'user',
                        text: item.text,
                        timestamp: parseTimeString(item.time)
                    });
                }
            });
        }
        
        // Add assistant messages (responses)
        if (data.responses) {
            data.responses.forEach(item => {
                if (!isMessageDisplayed('assistant', item.text)) {
                    allMessages.push({
                        type: 'assistant',
                        text: item.text,
                        timestamp: parseTimeString(item.time)
                    });
                }
            });
        }
        
        // Sort all messages by timestamp
        allMessages.sort((a, b) => a.timestamp - b.timestamp);
        
        // Create a document fragment for better performance
        const fragment = document.createDocumentFragment();
        
        // Add each message to the conversation
        allMessages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = msg.type === 'user' ? 'transcript-item' : 'bunny-item';
            
            const timeStr = formatTime(new Date(msg.timestamp));
            
            messageDiv.innerHTML = `
                <div class="message-name">${msg.type === 'user' ? 'You' : 'Bunny'}</div>
                <div class="${msg.type === 'user' ? 'transcript-content' : 'response-content'}">
                    ${msg.text}
                </div>
                <div class="time">${timeStr}</div>
            `;
            
            fragment.appendChild(messageDiv);
        });
        
        // Append all new messages at once
        conversationDiv.appendChild(fragment);
        
        // Conditional auto-scroll logic:
        // Only scroll to bottom if user was already at the bottom before new messages
        if (wasAtBottom) {
            // Use setTimeout to ensure DOM has updated before scrolling
            setTimeout(() => {
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
                console.log('Auto-scrolled to bottom (user was at bottom)');
            }, 10);
        } else {
            console.log('User not at bottom, skipping auto-scroll');
        }
        
        // Update scroll button visibility
        updateScrollButtonVisibility();
    }
}

// Helper function to parse time string (HH:MM:SS) to timestamp
function parseTimeString(timeStr) {
    const [hours, minutes, seconds] = timeStr.split(':').map(Number);
    const now = new Date();
    return new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        hours,
        minutes,
        seconds
    ).getTime();
}

// Helper function to format time as HH:MM:SS
function formatTime(date) {
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit', hour12: false});
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