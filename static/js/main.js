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
    button.innerHTML = '<i class="fa-solid fa-arrow-down"></i>'; // Using Font Awesome icon
    button.title = 'Scroll to bottom';
    button.className = 'scroll-button';
    
    button.addEventListener('click', () => {
        container.scrollTop = container.scrollHeight;
        button.style.display = 'none';
    });
    
    // Add button to the body instead of the container
    document.body.appendChild(button);
    
    // Position the button to hover over the chat box
    updateScrollButtonPosition(button, container);
    
    // Update position on window resize
    window.addEventListener('resize', () => {
        updateScrollButtonPosition(button, container);
    });
    
    return button;
}

// Function to update the scroll button position
function updateScrollButtonPosition(button, container) {
    // Get container dimensions and position
    const containerRect = container.getBoundingClientRect();
    
    // Position button at the bottom center of the container
    button.style.left = (containerRect.left + containerRect.width / 2) + 'px';
    button.style.bottom = (window.innerHeight - containerRect.bottom + 20) + 'px';
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
});

// Auto-expanding textarea
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('message_text');
    if (textarea) {
        const setTextareaHeight = function() {
            // Reset height to auto to get the correct scrollHeight
            textarea.style.height = 'auto';
            
            // Calculate height difference
            const oldHeight = parseInt(textarea.style.height || '40', 10);
            const newHeight = Math.max(40, Math.min(120, textarea.scrollHeight));
            const heightDifference = newHeight - oldHeight;
            
            // Set the new height
            textarea.style.height = newHeight + 'px';
            
            // Adjust conversation height based on textarea height
            const conversationDiv = document.getElementById('conversation');
            const baseHeight = 99.5;CSS
            const baseInputHeight = 250;
            const additionalHeight = newHeight - 40;
            
            // Calculate new height for conversation
            conversationDiv.style.height = `calc(${baseHeight}vh - ${baseInputHeight + additionalHeight}px)`;
        };
        
        // Set initial height
        setTextareaHeight();
        
        // Update height on input
        textarea.addEventListener('input', setTextareaHeight);
        
        // Handle Enter key for submission
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('text-message-form').dispatchEvent(new Event('submit'));
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
            
            })
            .catch(error => {
                console.error('Error ending chat:', error);
            });
        });
    }
});

// For testing purposes later on.

/* function addTestSystemMessage() {
    // Send the test message to the server
    fetch('/add_system_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: 'This is a test system message.'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("System message added successfully");
        } else {
            console.error('Failed to add system message:', data.error);
        }
    })
    .catch(error => {
        console.error('Error sending system message:', error);
    });
} */