// Function to update the UI with new data
function updateUI(data) {
    console.log("Received data:", data);
    
    // Update status indicators
    const transcriptionStatus = document.querySelectorAll('#status div')[0];
    
    transcriptionStatus.innerHTML = `Listening (mic): 
        <span class="status-indicator ${data.is_active ? 'status-active' : 'status-inactive'}"></span>
        ${data.is_active ? 'Active' : 'Inactive'}`;
    
    // Combine history and LLM responses into a single timeline
    const conversationDiv = document.getElementById('conversation');
    
    // Check if user was already at the bottom before we update
    const wasAtBottom = isScrolledToBottom(conversationDiv);
    
    // Check if we have any messages to display
    if ((data.history && data.history.length > 0) || 
        (data.llm_responses && data.llm_responses.length > 0) || 
        (data.system_messages && data.system_messages.length > 0)) {
        
        // Clear existing content
        conversationDiv.innerHTML = '';
        
        // Create a combined timeline of user messages, bot responses, and system messages
        let combined = [];
        
        // Add user messages with type
        if (data.history) {
            data.history.forEach(item => {
                combined.push({
                    text: item.text,
                    time: item.time,
                    type: 'user'
                });
            });
        }
        
        // Add bot responses with type
        if (data.llm_responses) {
            data.llm_responses.forEach(item => {
                combined.push({
                    text: item.text,
                    time: item.time,
                    type: 'bot'
                });
            });
        }
        
        // Add system messages with type
        if (data.system_messages) {
            data.system_messages.forEach(item => {
                combined.push({
                    text: item.text,
                    time: item.time,
                    type: 'system'
                });
            });
        }
        
        // Sort by time - fix the sorting method
        combined.sort((a, b) => {
            // Convert time strings to comparable values
            const timeA = a.time.split(':').map(Number);
            const timeB = b.time.split(':').map(Number);
            
            // Compare hours
            if (timeA[0] !== timeB[0]) {
                return timeA[0] - timeB[0];
            }
            
            // Compare minutes
            if (timeA[1] !== timeB[1]) {
                return timeA[1] - timeB[1];
            }
            
            // Compare seconds
            return timeA[2] - timeB[2];
        });
        
        // Add each item to the conversation
        combined.forEach(item => {
            const messageDiv = document.createElement('div');
            let name = '';
            
            // Set the appropriate class and name based on message type
            if (item.type === 'user') {
                messageDiv.className = 'transcript-item';
                // Use the user_id from the page, or default to "User"
                name = document.getElementById('user_id')?.value || "User";
            } else if (item.type === 'bot') {
                messageDiv.className = 'bunny-item';
                name = "Bunny";
            } else if (item.type === 'system') {
                messageDiv.className = 'system-message';
                name = "System";
            }
            
            messageDiv.innerHTML = `
                <div class="message-name">${name}</div>
                <div class="transcript-content">${item.text}</div>
                <div class="time">${item.time}</div>
            `;
            
            conversationDiv.appendChild(messageDiv);
        });
        
        // Only scroll to bottom if user was already at the bottom
        if (wasAtBottom) {
            conversationDiv.scrollTop = conversationDiv.scrollHeight;
        } else {
            // Show the scroll button
            const scrollButton = createScrollButton(conversationDiv);
            if (scrollButton) scrollButton.style.display = 'block';
        }
    }
}

function addTestSystemMessage() {
    const conversationDiv = document.getElementById('conversation');
    const systemMessageDiv = document.createElement('div');
    systemMessageDiv.className = 'system-message';
    
    systemMessageDiv.innerHTML = `
        <div class="message-name">System</div>
        <div class="transcript-content">
            This is a test system message.
        </div>
        <div class="time">${new Date().toLocaleTimeString()}</div>
    `;
    
    conversationDiv.appendChild(systemMessageDiv);
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
    
    // Send the test message to the server
    fetch('/add_system_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: 'This is a test system message.'
        })
    });
}

// Function to fetch updates from the server
function fetchUpdates() {
    fetch('/update')
        .then(response => response.json())
        .then(data => {
            // Update the UI with new data
            updateUI(data);
        })
        .catch(error => console.error('Error fetching updates:', error));
}

// Start the update interval when the page loads
function startUpdates() {
    updateInterval = setInterval(fetchUpdates, 500);
}

// Update the UI every 500ms
let updateInterval;

function setupStreaming() {
    const source = new EventSource('/stream');
    const conversationDiv = document.getElementById('conversation');
    let responseText = "";
    
    source.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Received event data:", data);
        
        // Show typing indicator when processing starts
        if (data.processing_started) {
            console.log("Processing started, showing typing indicator");
            showTypingIndicator();
        }
        
        // Collect text but don't display it yet
        if (data.text) {
            responseText += data.text;
        }
        
        // When complete, display the full message at once
        if (data.complete) {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Only create and display the message if we have text
            if (responseText) {
                const wasAtBottom = isScrolledToBottom(conversationDiv);
                
                // Create the complete response div
                const responseDiv = document.createElement('div');
                responseDiv.className = 'bunny-item';
                responseDiv.innerHTML = `
                    <div class="message-name">Bunny</div>
                    <div class="transcript-content">${responseText}</div>
                    <div class="time">${new Date().toLocaleTimeString()}</div>
                `;
                
                conversationDiv.appendChild(responseDiv);
                
                // Handle scrolling
                if (wasAtBottom) {
                    conversationDiv.scrollTop = conversationDiv.scrollHeight;
                } else {
                    const scrollButton = createScrollButton(conversationDiv);
                    if (scrollButton) scrollButton.style.display = 'block';
                }
            }
            
            // Reset for next message
            responseText = "";
            source.close();
            setTimeout(setupStreaming, 1000);
        }
    };
    
    source.onerror = function() {
        hideTypingIndicator();
        source.close();
        setTimeout(setupStreaming, 5000);
    };
}

function showTypingIndicator() {
    const conversationDiv = document.getElementById('conversation');
    // Remove any existing indicators first
    hideTypingIndicator();
    
    // Create and add the indicator
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
        <div class="message-name">Bunny</div>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <div class="time">${new Date().toLocaleTimeString()}</div>
    `;
    conversationDiv.appendChild(indicator);
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Function to check if the user is at the bottom of the conversation
function isScrolledToBottom(element) {
    return Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) < 10;
}

// Function to create the scroll-to-bottom button
function createScrollButton(container) {
    // Check if button already exists
    if (document.getElementById('scroll-to-bottom')) return;
    
    const button = document.createElement('button');
    button.id = 'scroll-to-bottom';
    button.innerHTML = '↓';
    button.title = 'Scroll to bottom';
    button.className = 'scroll-button';
    
    button.addEventListener('click', () => {
        container.scrollTop = container.scrollHeight;
        button.style.display = 'none';
    });
    
    document.body.appendChild(button);
    return button;
}

document.addEventListener('DOMContentLoaded', function() {
    const conversationDiv = document.getElementById('conversation');
    
    conversationDiv.addEventListener('scroll', function() {
        const scrollButton = document.getElementById('scroll-to-bottom');
        if (!scrollButton) return;
        
        if (isScrolledToBottom(conversationDiv)) {
            scrollButton.style.display = 'none';
        } else {
            scrollButton.style.display = 'block';
        }
    });
    
    startUpdates();
    fetchUpdates();
    setupStreaming();
});

// Auto-expanding textarea
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('message_text');
    if (textarea) {
        // Function to set precise height
        const setTextareaHeight = function() {
            textarea.style.height = '40px'; // Set consistent default height
            
            // Only expand beyond default if content requires it
            if (textarea.scrollHeight > 40) {
                textarea.style.height = Math.min(120, textarea.scrollHeight) + 'px';
            }
        };
        
        // Set initial height
        setTextareaHeight();
        
        // Update height on input
        textarea.addEventListener('input', setTextareaHeight);
        
        // Handle Enter key for submission
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('text-message-form').submit();
            }
        });
    }
});

// Update the end chat handler
document.addEventListener('DOMContentLoaded', function() {
    // Get the end chat form
    const endChatForm = document.getElementById('end-chat-form');
    
    if (endChatForm) {
        endChatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Send the end chat request
            fetch('/end_chat', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('End chat response:', data);
                
                // Add a system message to the conversation
                const conversationDiv = document.getElementById('conversation');
                const systemMessageDiv = document.createElement('div');
                systemMessageDiv.className = 'system-message';
                
                // Make sure to include the name div
                systemMessageDiv.innerHTML = `
                    <div class="message-name">System</div>
                    <div class="transcript-content">
                        Chat session ended. All services have been stopped.
                    </div>
                    <div class="time">${new Date().toLocaleTimeString()}</div>
                `;
                
                conversationDiv.appendChild(systemMessageDiv);
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
                
                // Disable all buttons except the end chat button (which is already used)
                const buttons = document.querySelectorAll('button:not([form="end-chat-form"])');
                buttons.forEach(button => {
                    button.disabled = true;
                });
                
                // Stop the update interval
                clearInterval(updateInterval);
            })
            .catch(error => {
                console.error('Error ending chat:', error);
            });
        });
    }
});