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
                    
                    // Add system output message for STT toggle
                    if (typeof OutputManager !== 'undefined') {
                        if (action.includes('start_listening')) {
                            OutputManager.sttOn();
                        } else {
                            OutputManager.sttOff();
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
                    
                    // Add system output message for TTS toggle
                    if (typeof OutputManager !== 'undefined') {
                        if (data.tts_enabled) {
                            OutputManager.ttsOn();
                        } else {
                            OutputManager.ttsOff();
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

    // Add this new code to handle the placeholder
    function clearPlaceholderWhenMessagesExist() {
        const conversationDiv = document.getElementById('conversation');
        if (!conversationDiv) return;
        
        // If there are any messages in the conversation, remove the placeholder
        if ((conversationDiv.querySelectorAll('.message, .transcript-item, .bunny-item').length > 0) && 
            conversationDiv.innerHTML.includes('No conversation history yet')) {
            // Find and remove just the placeholder paragraph
            const placeholders = conversationDiv.querySelectorAll('p');
            placeholders.forEach(p => {
                if (p.textContent.includes('No conversation history yet')) {
                    p.remove();
                }
            });
        }
    }
    
    // Run once on page load
    clearPlaceholderWhenMessagesExist();
    
    // Also run whenever new messages might be added
    setInterval(clearPlaceholderWhenMessagesExist, 1000);

    /// Intercept end chat form submission
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
            
            // Clear placeholder text immediately when sending a message
            const conversationDiv = document.getElementById('conversation');
            if (conversationDiv && conversationDiv.innerHTML.includes('No conversation history yet')) {
                conversationDiv.innerHTML = '';
            }
            
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
    
    // More robust check for placeholder text
    if (conversationDiv.innerHTML.trim() === '<p>No conversation history yet. Start speaking to begin.</p>' || 
        conversationDiv.innerHTML.includes('No conversation history yet') ||
        conversationDiv.innerHTML === '<div class="message loading">Loading chat history...</div>') {
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
        
        // Only auto-scroll if user was already at bottom
        if (wasAtBottom) {
            // Use requestAnimationFrame for smoother scrolling
            requestAnimationFrame(() => {
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
                // Update scroll button visibility after scrolling
                updateScrollButtonVisibility();
            });
        } else {
            // Show scroll button if not at bottom
            updateScrollButtonVisibility();
        }
    }
}

// Update the scroll threshold to be consistent (5px)
function isScrolledToBottom(element) {
    if (!element) return true;
    const threshold = 5; // pixels from bottom
    return Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) <= threshold;
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
    if (!element) return true;
    const threshold = 5; // pixels from bottom
    return Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) <= threshold;
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

// Add this function if it doesn't exist
function updateScrollButtonVisibility() {
    const scrollButton = document.getElementById('scroll-to-bottom');
    if (!scrollButton) return;
    
    const conversationDiv = document.getElementById('conversation');
    if (!conversationDiv) return;
    
    // Show button only if not at bottom and there's enough content to scroll
    if (!isScrolledToBottom(conversationDiv) && 
        conversationDiv.scrollHeight > conversationDiv.clientHeight) {
        scrollButton.style.display = 'block';
    } else {
        scrollButton.style.display = 'none';
    }
}

// Function to load history files
function loadHistoryFiles() {
    fetch('/get_history_files')
        .then(response => response.json())
        .then(data => {
            const historyList = document.getElementById('history-list');
            if (!historyList) return;
            
            // Clear existing items
            historyList.innerHTML = '';
            
            if (data.files && data.files.length > 0) {
                // Sort files by date (newest first)
                data.files.sort((a, b) => {
                    return new Date(b.date) - new Date(a.date);
                });
                
                // Add each file to the list
                data.files.forEach(file => {
                    const listItem = document.createElement('div');
                    listItem.className = 'history-item';
                    
                    // Format the date for display
                    const fileDate = new Date(file.date);
                    const formattedDate = fileDate.toLocaleDateString() + ' ' + 
                                        fileDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    
                    listItem.innerHTML = `
                        <span class="history-date">${formattedDate}</span>
                        <span class="history-actions">
                            <button class="history-load" data-filename="${file.filename}" title="Load this conversation">
                                <i class="fa-solid fa-folder-open"></i>
                            </button>
                            <button class="history-delete" data-filename="${file.filename}" title="Delete this conversation">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </span>
                    `;
                    
                    historyList.appendChild(listItem);
                });
                
                // Add event listeners to the load buttons
                document.querySelectorAll('.history-load').forEach(button => {
                    button.addEventListener('click', function() {
                        const filename = this.getAttribute('data-filename');
                        loadHistoryFile(filename);
                    });
                });
                
                // Add event listeners to the delete buttons
                document.querySelectorAll('.history-delete').forEach(button => {
                    button.addEventListener('click', function() {
                        const filename = this.getAttribute('data-filename');
                        if (confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
                            deleteHistoryFile(filename);
                        }
                    });
                });
            } else {
                // No history files
                historyList.innerHTML = '<div class="no-history">No conversation history found.</div>';
            }
        })
        .catch(error => {
            console.error('Error loading history files:', error);
            const historyList = document.getElementById('history-list');
            if (historyList) {
                historyList.innerHTML = '<div class="error">Error loading history files.</div>';
            }
        });
}

// Function to load a specific history file
function loadHistoryFile(filename) {
    // Show loading state in the conversation area
    const conversationDiv = document.getElementById('conversation');
    if (conversationDiv) {
        conversationDiv.innerHTML = '<div class="message loading">Loading chat history...</div>';
    }
    
    // Hide the history list
    const historyList = document.getElementById('history-list');
    if (historyList) {
        historyList.style.display = 'none';
    }
    
    fetch(`/load_history/${filename}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.messages) {
                // Clear the conversation div
                conversationDiv.innerHTML = '';
                
                // Add each message to the conversation
                data.messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.role}`;
                    
                    messageDiv.innerHTML = `
                        <div class="message-header">
                            <div class="message-name">${msg.role === 'user' ? 'You' : 'Bunny'}</div>
                            <div class="message-time">${formatTime(new Date(msg.timestamp))}</div>
                        </div>
                        <div class="message-content">${msg.content}</div>
                    `;
                    
                    conversationDiv.appendChild(messageDiv);
                });
                
                // Scroll to bottom
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
            } else {
                // Show error
                conversationDiv.innerHTML = '<div class="error-message">Failed to load conversation history.</div>';
            }
        })
        .catch(error => {
            console.error('Error loading history file:', error);
            if (conversationDiv) {
                conversationDiv.innerHTML = '<div class="error-message">Error loading conversation history.</div>';
            }
        });
}

// Function to delete a history file
function deleteHistoryFile(filename) {
    fetch(`/delete_history/${filename}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload the history list
                loadHistoryFiles();
            } else {
                alert('Failed to delete file: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error deleting history file:', error);
            alert('Error deleting file. Please try again.');
        });
}