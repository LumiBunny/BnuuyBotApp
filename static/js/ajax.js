let pollingInterval = null;

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
                console.log('Mic response:', data);
                // Update UI
                updateMicStatus(data.is_active);
            })
            .catch(error => console.error('Error with mic action:', error));
        });
    }
    
    // Intercept timer form submission
    const timerForm = document.getElementById('timer-form');
    if (timerForm) {
        timerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const action = this.getAttribute('action');
            
            fetch(action, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('Timer response:', data);
                // Instead of page reload, update UI
                updateTimerStatus(data.timer_active);
            })
            .catch(error => console.error('Error with timer action:', error));
        });
    }
    
    // Intercept clear form submission
    const clearForm = document.getElementById('clear-form');
    if (clearForm) {
        clearForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch('/clear', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('Clear response:', data);
                if (data.success) {
                    const conversation = document.getElementById('conversation');
                    conversation.innerHTML = '<p>No conversation history yet. Start speaking to begin.</p>';
                }
            })
            .catch(error => console.error('Error clearing conversation:', error));
        });
    }
    
    // Intercept end chat form submission
    const endChatForm = document.getElementById('end-chat-form');
    if (endChatForm) {
        endChatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch('/end_chat', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('End chat response:', data);
                if (data.success) {
                    alert('Chat session ended.');
                    // Stop polling
                    if (pollingInterval) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                    }
                }
            })
            .catch(error => console.error('Error ending chat:', error));
        });
    }
    
    // Intercept user ID form submission
    const userIdForm = document.getElementById('user-id-form');
    if (userIdForm) {
        userIdForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/set_user_id', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Set user ID response:', data);
                
                // If the user ID was successfully updated
                if (data.success) {
                    // Get the new user ID from the form
                    const newUserId = document.getElementById('user_id').value.trim() || "User";
                    
                    // Update all existing user message names in the conversation
                    const userMessages = document.querySelectorAll('.transcript-item .message-name');
                    userMessages.forEach(nameElement => {
                        nameElement.textContent = newUserId;
                    });
                    
                    // Show success message
                    alert(data.message);
                } else {
                    // Show error message
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error setting user ID:', error);
                alert('Error updating user ID. Please try again.');
            });
        });
    }
    
    // Intercept text message form submission
    const textMessageForm = document.getElementById('text-message-form');
    if (textMessageForm) {
        textMessageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const messageInput = document.getElementById('message_text');
            
            fetch('/send_message', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Send message response:', data);
                if (data.success) {
                    messageInput.value = '';
                    // Trigger input event to adjust height
                    messageInput.dispatchEvent(new Event('input'));
                }
            })
            .catch(error => console.error('Error sending message:', error));
        });
    }
    
    // Helper function to update mic status in UI
    function updateMicStatus(isActive) {
        // Update the mic form action
        if (micForm) {
            micForm.setAttribute('action', isActive ? '/stop' : '/start');
        }
        
                // Update the mic button
                const micButton = micForm ? micForm.querySelector('button') : null;
                if (micButton) {
                    micButton.title = isActive ? 'Stop listening' : 'Start listening';
                    micButton.className = `icon-button ${isActive ? 'btn-mic-on' : 'btn-mic-off'}`;
                    
                    // Update the icon
                    const icon = micButton.querySelector('i');
                    if (icon) {
                        icon.className = `fa-solid ${isActive ? 'fa-microphone' : 'fa-microphone-slash'}`;
                    }
                }
                
                // Update status indicator
                const statusIndicators = document.querySelectorAll('.status-indicator');
                if (statusIndicators.length > 0) {
                    statusIndicators[0].className = `status-indicator ${isActive ? 'status-active' : 'status-inactive'}`;
                    
                    // Update the text next to the indicator
                    const statusText = statusIndicators[0].nextElementSibling;
                    if (statusText) {
                        statusText.textContent = isActive ? 'Active' : 'Inactive';
                    }
                }
            }
            
            // Helper function to update timer status in UI
            function updateTimerStatus(isActive) {
                // Update the timer form action
                if (timerForm) {
                    timerForm.setAttribute('action', isActive ? '/stop_timer' : '/start_timer');
                }
                
                // Update the timer button
                const timerButton = timerForm ? timerForm.querySelector('button') : null;
                if (timerButton) {
                    timerButton.title = isActive ? 'Stop self-prompting' : 'Start self-prompting';
                    timerButton.className = `icon-button ${isActive ? 'btn-timer-on' : 'btn-timer-off'}`;
                    
                    // Update the icon
                    const icon = timerButton.querySelector('i');
                    if (icon) {
                        icon.className = `fa-regular ${isActive ? 'fa-hourglass-half' : 'fa-hourglass'}`;
                    }
                }
                
                // Update status indicator
                const statusIndicators = document.querySelectorAll('.status-indicator');
                if (statusIndicators.length > 1) {
                    statusIndicators[1].className = `status-indicator ${isActive ? 'status-active' : 'status-inactive'}`;
                    
                    // Update the text next to the indicator
                    const statusText = statusIndicators[1].nextElementSibling;
                    if (statusText) {
                        statusText.textContent = isActive ? 'Active' : 'Inactive';
                    }
                }
            }
            
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
                fetch('/update')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Update data:', data);
                        updateConversation(data);
                        updateMicStatus(data.is_active);
                        updateTimerStatus(data.timer_active);
                    })
                    .catch(error => console.error('Error fetching updates:', error));
            }
            
            // Update conversation with new messages
            function updateConversation(data) {
                const conversationDiv = document.getElementById('conversation');
                if (!conversationDiv) return;
                
                // Check if user was already at the bottom before updating
                const wasAtBottom = isScrolledToBottom(conversationDiv);
                
                // Save the scroll button if it exists before clearing the conversation
                let scrollButton = document.getElementById('scroll-to-bottom');
                if (scrollButton) {
                    // Remove it temporarily so it doesn't get deleted when we clear the conversation
                    scrollButton.parentNode.removeChild(scrollButton);
                }
                
                // Helper function to check if a message is already displayed
                function isMessageDisplayed(type, text) {
                    const selector = type === 'user' ? '.transcript-item' : 
                                     type === 'bot' ? '.bunny-item' : 
                                     '.system-message';
                    const messages = conversationDiv.querySelectorAll(selector);
                    
                    for (let i = 0; i < messages.length; i++) {
                        // Look for the content based on message type
                        let content;
                        if (type === 'user' || type === 'system') {
                            content = messages[i].querySelector('.transcript-content');
                        } else {
                            content = messages[i].querySelector('.response-content');
                        }
                        
                        if (content && content.textContent.trim() === text.trim()) {
                            return true;
                        }
                    }
                    return false;
                }
                
                // Combine all messages into a single array with type information
                const allMessages = [];
                
                // Add user messages to the combined array
                if (data.history && data.history.length > 0) {
                    data.history.forEach(item => {
                        allMessages.push({
                            type: 'user',
                            text: item.text,
                            time: item.time
                        });
                    });
                }
                
                // Add bot messages to the combined array
                if (data.llm_responses && data.llm_responses.length > 0) {
                    data.llm_responses.forEach(item => {
                        allMessages.push({
                            type: 'bot',
                            text: item.text,
                            time: item.time
                        });
                    });
                }
                
                // Add system messages to the combined array
                if (data.system_messages && data.system_messages.length > 0) {
                    data.system_messages.forEach(item => {
                        allMessages.push({
                            type: 'system',
                            text: item.text,
                            time: item.time
                        });
                    });
                }
                
                // Sort all messages by timestamp
                allMessages.sort((a, b) => {
                    // Convert time strings to Date objects for comparison
                    const timeA = new Date(`1970-01-01T${a.time}`);
                    const timeB = new Date(`1970-01-01T${b.time}`);
                    return timeA - timeB;
                });
                
                // Clear existing messages if we have messages to display
                if (allMessages.length > 0) {
                    conversationDiv.innerHTML = '';
                }
                
                // Add all messages in chronological order
                allMessages.forEach(item => {
                    const messageDiv = document.createElement('div');
                    
                    if (item.type === 'user') {
                        messageDiv.className = 'transcript-item';
                        messageDiv.innerHTML = `
                            <div class="message-name">${data.user_id || "User"}</div>
                            <div class="transcript-content">${item.text}</div>
                            <div class="time">${item.time}</div>
                        `;
                    } else if (item.type === 'bot') {
                        messageDiv.className = 'bunny-item';
                        messageDiv.innerHTML = `
                            <div class="message-name">Bunny</div>
                            <div class="response-content">${item.text}</div>
                            <div class="time">${item.time}</div>
                        `;
                    } else if (item.type === 'system') {
                        messageDiv.className = 'system-message';
                        messageDiv.innerHTML = `
                            <div class="message-name">System</div>
                            <div class="transcript-content">${item.text}</div>
                            <div class="time">${item.time}</div>
                        `;
                    }
                    
                    conversationDiv.appendChild(messageDiv);
                });
                
                // If we removed the scroll button earlier, add it back
                if (scrollButton) {
                    conversationDiv.appendChild(scrollButton);
                } else {
                    // Create the scroll button if it doesn't exist
                    scrollButton = createScrollButton(conversationDiv);
                }
                
                // Update scroll button visibility based on scroll position
                if (scrollButton) {
                    if (wasAtBottom) {
                        conversationDiv.scrollTop = conversationDiv.scrollHeight;
                        scrollButton.style.display = 'none';
                        console.log('Hiding scroll button - at bottom');
                    } else {
                        scrollButton.style.display = 'block';
                        console.log('Showing scroll button - not at bottom');
                    }
                }
                
                // Make sure we only attach the scroll event listener once
                if (!conversationDiv.hasScrollListener) {
                    conversationDiv.addEventListener('scroll', function() {
                        const btn = document.getElementById('scroll-to-bottom');
                        if (!btn) return;
                        
                        // Update button position
                        updateScrollButtonPosition(btn, conversationDiv);
                        
                        if (isScrolledToBottom(conversationDiv)) {
                            btn.style.display = 'none';
                        } else {
                            btn.style.display = 'block';
                        }
                    });
                    
                    // Also update position when window is resized
                    window.addEventListener('resize', function() {
                        const btn = document.getElementById('scroll-to-bottom');
                        if (btn) {
                            updateScrollButtonPosition(btn, conversationDiv);
                        }
                    });
                    
                    conversationDiv.hasScrollListener = true;
                }
            }
            
            // Start the update polling
            startPolling();
        });