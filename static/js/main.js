const socket = io();

// Handle connection events
socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    OutputManager.system('Connected to server', {
        status: 'connected',
        socketId: socket.id
    });
});

socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
    OutputManager.system('Disconnected from server', {
        status: 'disconnected'
    });
});

// Handle output events from the server
socket.on('output_event', (data) => {
    console.log('Received output event:', data);
    
    // Convert the WebSocket event to match the polling format
    const event = {
        type: data.type,
        content: data.content,
        data: data.data || {},
        is_streaming: data.is_streaming || false
    };
    
    // Process the event using the same function as the polling system
    processOutputEvent(event);
});

// Handle user messages in the conversation container
socket.on('user_message', (data) => {
    console.log('Received user message:', data);
    
    const conversationDiv = document.getElementById('conversation');
    if (!conversationDiv) {
        console.error('Conversation container not found');
        return;
    }
    
    // Check if we should clear the loading/placeholder message
    if (conversationDiv.innerHTML.trim() === '<p>No conversation history yet. Start speaking to begin.</p>' || 
        conversationDiv.innerHTML.includes('No conversation history yet') ||
        conversationDiv.innerHTML === '<div class="message loading">Loading chat history...</div>') {
        conversationDiv.innerHTML = '';
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = 'transcript-item';
    
    // Format timestamp
    const timestamp = new Date();
    const timeStr = timestamp.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Set message content
    messageDiv.innerHTML = `
        <div class="message-name">You</div>
        <div class="transcript-content">${data.text}</div>
        <div class="time">${timeStr}</div>
    `;
    
    // Add to conversation
    conversationDiv.appendChild(messageDiv);
    
    // Scroll to bottom if user was already at bottom
    if (isScrolledToBottom(conversationDiv)) {
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
    }
    
    // Update scroll button visibility
    updateScrollButtonVisibility();
});

// Function to check if the user is at the bottom of the conversation
function isScrolledToBottom(element) {
    return Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) < 10;
}

// Function to update the scroll button visibility
function updateScrollButtonVisibility() {
    const conversationDiv = document.getElementById('conversation');
    const scrollButton = document.getElementById('scroll-to-bottom');
    
    if (!conversationDiv || !scrollButton) return;
    
    const atBottom = isScrolledToBottom(conversationDiv);
    scrollButton.style.display = atBottom ? 'none' : 'block';
}

// Function to check if the user is scrolled to the bottom of the output panel
function isOutputScrolledToBottom() {
    const outputMessages = document.getElementById('output-messages');
    if (!outputMessages) return true;
    
    const threshold = 10; // Consistent with conversation panel
    const isAtBottom = Math.abs(outputMessages.scrollHeight - outputMessages.clientHeight - outputMessages.scrollTop) <= threshold;
    
    return isAtBottom;
}

// Function to scroll the output panel to bottom
function scrollOutputToBottom() {
    const outputMessages = document.getElementById('output-messages');
    if (!outputMessages) return;
    
    // Use requestAnimationFrame for smoother scrolling
    requestAnimationFrame(() => {
        outputMessages.scrollTop = outputMessages.scrollHeight;
        // Hide scroll button after scrolling
        hideOutputScrollButton();
    });
}

// Function to show the output scroll button
function showOutputScrollButton() {
    const scrollBtn = document.getElementById('output-scroll-btn');
    if (scrollBtn) {
        scrollBtn.style.display = 'block';
    }
}

// Function to hide the output scroll button
function hideOutputScrollButton() {
    const scrollBtn = document.getElementById('output-scroll-btn');
    if (scrollBtn) {
        scrollBtn.style.display = 'none';
    }
}

// Output Message Types with Emojis
const OutputTypes = {
    botProcessing: { type: 'botProcessing', emoji: '🤖', label: 'Processing message' },
    botPreview: { type: 'botPreview', emoji: '🐰', label: 'Bot' },
    innerThoughts: { type: 'innerThoughts', emoji: '💭', label: 'Thinking' },
    preferences: { type: 'preferences', emoji: '💕', label: 'Preferences' },
    interests: { type: 'interests', emoji: '📚', label: 'Interests' },
    mood: { type: 'mood', emoji: '😊', label: 'Mood' },
    memories: { type: 'memories', emoji: '🧠', label: 'Memories' },
    ttsOn: { type: 'ttsOn', emoji: '🔊', label: 'TTS On' },
    ttsOffManual: { type: 'ttsOffManual', emoji: '🔇', label: 'TTS Off' },
    ttsOffPlaybackFinished: { type: 'ttsOffPlaybackFinished', emoji: '🔉', label: 'TTS Finished' },
    ttsPlaying: { type: 'ttsPlaying', emoji: '🔊', label: 'TTS Playing' },
    ttsFinished: { type: 'ttsFinished', emoji: '🔉', label: 'TTS Finished' },
    sttOn: { type: 'sttOn', emoji: '🎤', label: 'Listening' },
    sttOff: { type: 'sttOff', emoji: '🎤', label: 'Not Listening' },
    sttTranscribing: { type: 'sttTranscribing', emoji: '✍️', label: 'Transcribing' },
    continuation: { type: 'continuation', emoji: '⏭️', label: 'Continuing' },
    system: { type: 'system', emoji: '⚙️', label: 'System' }
};

// Track the last streaming message element
let lastStreamingMessage = null;
let lastStreamingType = null;

// Enhanced Output Panel Functions
function addOutputMessage(content, outputType = OutputTypes.system, data = null, isStreaming = false) {
    console.log('Adding output message:', { 
        content, 
        outputType, 
        hasData: !!data,
        isStreaming
    });
    const outputMessages = document.getElementById('output-messages');
    if (!outputMessages) {
        console.error('Output messages container not found');
        return null;
    }
    
    // Check if user is at bottom before adding new messages
    const wasAtBottom = isOutputScrolledToBottom();
    
    console.log(`Adding ${isStreaming ? 'streaming ' : ''}${outputType.label} message:`, content || data);
    
    // If this is a streaming message and the last message was a streaming message of the same type,
    // update it instead of creating a new one
    if (isStreaming && lastStreamingMessage && outputType === lastStreamingType) {
        // Update the existing streaming message
        const contentElement = lastStreamingMessage.querySelector('.message-content');
        if (contentElement) {
            // Append the new content
            contentElement.textContent += content;
            
            // Update the timestamp
            const timestampElement = lastStreamingMessage.querySelector('.timestamp');
            if (timestampElement) {
                timestampElement.textContent = new Date().toLocaleTimeString('en-US', { 
                    hour12: false, 
                    hour: '2-digit', 
                    minute: '2-digit',
                    second: '2-digit',
                    fractionalSecondDigits: 3
                });
            }
            
            // Auto-scroll if user was at bottom
            if (wasAtBottom) {
                scrollOutputToBottom();
            } else {
                showOutputScrollButton();
            }
            
            return lastStreamingMessage;
        }
    }
    
    // Create a new message div
    const messageDiv = document.createElement('div');
    
    // Set the appropriate class based on message type
    let messageClass = 'output-message';
    if (outputType === OutputTypes.system) {
        messageClass += ' system-output';
    } else if (outputType === OutputTypes.botPreview) {
        messageClass += ' bot-preview';
    }
    
    if (isStreaming) {
        messageClass += ' streaming';
    }
    
    messageDiv.className = messageClass;
    
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
    });
    
    // Format the message content
    let messageContent = content;
    if (data && typeof data === 'object') {
        try {
            messageContent = formatObjectOutput(data);
        } catch (e) {
            console.error('Error formatting object output:', e);
            messageContent = JSON.stringify(data, null, 2);
        }
    }
    
    // Set the message HTML
    messageDiv.innerHTML = `
        <span class="emoji">${outputType.emoji}</span>
        <span class="output-label">${outputType.label}:</span>
        <span class="message-content">${messageContent || ''}</span>
        <span class="timestamp">${timestamp}</span>
    `;
    
    // Add to the output container
    outputMessages.appendChild(messageDiv);
    
    // Auto-scroll if user was at bottom, otherwise show scroll button
    if (wasAtBottom) {
        scrollOutputToBottom();
    } else {
        showOutputScrollButton();
    }
    
    // Update last streaming message reference if this is a streaming message
    if (isStreaming) {
        lastStreamingMessage = messageDiv;
        lastStreamingType = outputType;
    } else {
        lastStreamingMessage = null;
        lastStreamingType = null;
    }
    
    return messageDiv;
}

// Helper to format object output with pretty printing
function formatObjectOutput(obj) {
    if (obj === null || obj === undefined) return '';
    if (typeof obj === 'string') return obj;
    
    try {
        if (obj instanceof Error) {
            return `<div class="error-output">${obj.message || 'Error occurred'}</div>`;
        }
        
        if (Array.isArray(obj)) {
            return obj.map(item => 
                `<div class="output-item">• ${formatObjectOutput(item)}</div>`
            ).join('');
        }
        
        if (typeof obj === 'object') {
            return Object.entries(obj).map(([key, value]) => 
                `<div class="output-item"><strong>${key}:</strong> ${formatObjectOutput(value)}</div>`
            ).join('');
        }
        
        return String(obj);
    } catch (e) {
        console.error('Error formatting output:', e);
        return '[Complex data]';
    }
}

// Output Manager with enhanced functionality
const OutputManager = {
    // Bot processing and preview
    botProcessing(message) {
        addOutputMessage(message, OutputTypes.botProcessing);
    },
    
    botPreview(message) {
        addOutputMessage(message, OutputTypes.botPreview);
    },
    
    // Inner thoughts
    innerThoughts(thoughts) {
        addOutputMessage(thoughts, OutputTypes.innerThoughts);
    },
    
    // Preferences
    preferences(prefs) {
        addOutputMessage(formatObjectOutput(prefs), OutputTypes.preferences);
    },
    
    // Interests
    interests(interests) {
        addOutputMessage(formatObjectOutput(interests), OutputTypes.interests);
    },
    
    // Mood detection
    mood(moodData) {
        addOutputMessage(formatObjectOutput(moodData), OutputTypes.mood);
    },
    
    // Relevant memories
    memories(memories) {
        addOutputMessage(formatObjectOutput(memories), OutputTypes.memories);
    },
    
    // TTS events
    ttsOn() {
        addOutputMessage('TTS: Text-to-speech enabled', OutputTypes.ttsOn);
    },
    
    ttsOffManual() {
        addOutputMessage('TTS: Text-to-speech disabled', OutputTypes.ttsOffManual);
    },
    
    ttsOffPlaybackFinished() {
        addOutputMessage('TTS: Playback finished', OutputTypes.ttsOffPlaybackFinished);
    },
    
    ttsPlaying(text) {
        addOutputMessage('TTS: Starting audio playback', OutputTypes.ttsPlaying);
    },
    
    ttsFinished() {
        addOutputMessage('TTS: Playback finished', OutputTypes.ttsFinished);
    },
    
    // STT events
    sttOn() {
        addOutputMessage('Speech recognition started', OutputTypes.sttOn);
    },
    
    sttOff() {
        addOutputMessage('Speech recognition stopped', OutputTypes.sttOff);
    },
    
    sttTranscribing(status) {
        if (typeof status === 'string') {
            addOutputMessage(status, OutputTypes.sttTranscribing);
        } else if (status && status.text) {
            addOutputMessage(`Transcribing: ${status.text}`, OutputTypes.sttTranscribing);
        }
    },
    
    // Continuation
    continuation(data) {
        addOutputMessage('Continuing response...', OutputTypes.continuation);
    },
    
    // System messages
    system(message, data) {
        addOutputMessage(message, OutputTypes.system, data);
    }
};

// Initialize with system message
function setupOutputPanel() {
    const outputMessages = document.getElementById('output-messages');
    const scrollBtn = document.getElementById('output-scroll-btn');
    
    if (!outputMessages || !scrollBtn) return;
    
    // Setup scroll button click handler
    scrollBtn.addEventListener('click', scrollOutputToBottom);
    
    // Setup scroll event listener
    outputMessages.addEventListener('scroll', function() {
        if (isOutputScrolledToBottom()) {
            hideOutputScrollButton();
        } else {
            showOutputScrollButton();
        }
    });
}

// Output Events Polling System
let outputPollingInterval = null;

// Stop polling when page unloads
function stopOutputPolling() {
    if (outputPollingInterval) {
        clearInterval(outputPollingInterval);
        outputPollingInterval = null;
    }
}

function processOutputEvent(event) {
    const { type, content, data, is_streaming: isStreaming = false } = event;
    console.log('Processing output event:', event);
    // Call the appropriate OutputManager method based on event type
    switch(type) {
        case 'botProcessing':
            OutputManager.botProcessing(content, data);
            break;
        case 'botPreview':
            // Pass the isStreaming flag to the output message
            addOutputMessage(content, OutputTypes.botPreview, data, isStreaming);
            break;
        case 'innerThoughts':
            OutputManager.innerThoughts(content, data);
            break;
        case 'preferences':
            OutputManager.preferences(content, data);
            break;
        case 'interests':
            OutputManager.interests(content, data);
            break;
        case 'mood':
            OutputManager.mood(content, data);
            break;
        case 'memories':
            OutputManager.memories(content, data);
            break;
        case 'ttsOn':
            OutputManager.ttsOn();
            break;
        case 'ttsOffManual':
            OutputManager.ttsOffManual();
            break;
        case 'ttsOffPlaybackFinished':
            OutputManager.ttsOffPlaybackFinished();
            break;
        case 'ttsPlaying':
            OutputManager.ttsPlaying(content);
            break;
        case 'ttsFinished':
            OutputManager.ttsFinished();
            break;
        case 'sttOn':
            OutputManager.sttOn();
            break;
        case 'sttOff':
            OutputManager.sttOff();
            break;
        case 'sttTranscribing':
            OutputManager.sttTranscribing(content);
            break;
        case 'system':
            OutputManager.system(content, data);
            break;
        case 'continuation':
            OutputManager.continuation(content, data);
            break;
        default:
            console.warn('Unknown output event type:', type);
    }
}

// Initialize output panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    setupOutputPanel();
    
    // Add initial system message
    OutputManager.system('Output panel initialized and ready', { status: 'active' });
    
    // Start polling for output events
    startOutputPolling();
    console.log('Output events polling started');
});

// Stop polling when page unloads
window.addEventListener('beforeunload', () => {
    stopOutputPolling();
});

// Make OutputManager globally available
window.OutputManager = OutputManager;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired');
    const conversationDiv = document.getElementById('conversation');
    
    // Create the scroll-to-bottom button
    createScrollButton(conversationDiv);
    
    // Initial scroll to bottom
    scrollChatToBottom();
    
    // Scroll again after a short delay to catch any dynamically loaded content
    setTimeout(scrollChatToBottom, 300);
    
    // Scroll again when window is fully loaded
    window.addEventListener('load', function() {
        console.log('Window load event fired');
        scrollChatToBottom();
        
        // One more check after everything should be loaded
        setTimeout(scrollChatToBottom, 500);
    });
    
    // Set up scroll event listener for the scroll-to-bottom button
    if (conversationDiv) {
        conversationDiv.addEventListener('scroll', function() {
            const scrollButton = document.getElementById('scroll-to-bottom');
            if (!scrollButton) return;
            
            if (isScrolledToBottom(conversationDiv)) {
                scrollButton.style.display = 'none';
            } else {
                scrollButton.style.display = 'flex';
            }
        });
    }
    
    // Setup output panel
    setupOutputPanel();
});

// Create scroll-to-bottom button
function createScrollButton(container) {
    // Create button element
    const button = document.createElement('button');
    button.id = 'scroll-to-bottom';
    button.title = 'Scroll to bottom';
    button.innerHTML = '▼';
    button.style.display = 'none';
    
    // Hover effects
    button.addEventListener('mouseover', () => {
        button.style.backgroundColor = '#5a3a8a';
        button.style.transform = 'scale(1.1)';
    });
    
    button.addEventListener('mouseout', () => {
        button.style.backgroundColor = '#6e48aa';
        button.style.transform = 'scale(1)';
    });
    
    // Add click handler
    button.addEventListener('click', () => {
        scrollChatToBottom();
    });
    
    // Add scroll event listener to show/hide button
    const updateButtonVisibility = () => {
        const atBottom = isScrolledToBottom(container);
        button.style.display = atBottom ? 'none' : 'flex';
    };
    
    container.addEventListener('scroll', updateButtonVisibility);
    
    // Add button to the container
    container.style.position = 'relative';
    container.appendChild(button);
    
    // Initial check after a small delay
    setTimeout(updateButtonVisibility, 100);
    
    // Also check on window resize
    window.addEventListener('resize', updateButtonVisibility);
    
    return button;
}

// Function to scroll chat to bottom
function scrollChatToBottom() {
    const conversationDiv = document.getElementById('conversation');
    if (conversationDiv) {
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
    }
}

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

// Function to check if the conversation is scrolled to bottom
function isConversationScrolledToBottom(conversationDiv) {
    if (!conversationDiv) return true;
    const threshold = 10; // pixels from bottom
    return Math.abs(conversationDiv.scrollHeight - conversationDiv.clientHeight - conversationDiv.scrollTop) <= threshold;
}

// Function to update conversation scroll button visibility
function updateConversationScrollButton() {
    const conversationDiv = document.getElementById('conversation');
    const scrollButton = document.getElementById('scroll-to-bottom-conversation-btn');
    
    if (!conversationDiv || !scrollButton) return;
    
    if (isConversationScrolledToBottom(conversationDiv)) {
        scrollButton.classList.remove('visible');
    } else {
        scrollButton.classList.add('visible');
    }
}

// Function to scroll conversation to bottom
function scrollConversationToBottom() {
    const conversationDiv = document.getElementById('conversation');
    if (conversationDiv) {
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
        updateConversationScrollButton();
    }
}

// Add scroll event listener for conversation
function setupConversationScroll() {
    const conversationDiv = document.getElementById('conversation');
    const scrollButton = document.getElementById('scroll-to-bottom-conversation-btn');
    
    if (!conversationDiv || !scrollButton) return;
    
    // Handle scroll events on conversation
    conversationDiv.addEventListener('scroll', updateConversationScrollButton);
    
    // Handle click on scroll button
    scrollButton.addEventListener('click', scrollConversationToBottom);
    
    // Initial check
    updateConversationScrollButton();
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired');
    
    // Existing code...
    const conversationDiv = document.getElementById('conversation');
    
    // Setup conversation scroll functionality
    setupConversationScroll();
    
    // Initial scroll to bottom
    scrollConversationToBottom();
    
    // Scroll again after a short delay to catch any dynamically loaded content
    setTimeout(scrollConversationToBottom, 300);
    
    // Rest of your existing code...
    
    // Update the existing scroll event listener to use our new function
    if (conversationDiv) {
        conversationDiv.addEventListener('scroll', updateConversationScrollButton);
    }
});

// Update the existing scrollChatToBottom function to use our new function
function scrollChatToBottom() {
    scrollConversationToBottom();
}