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

// Function to scroll chat to bottom
function scrollChatToBottom() {
    const conversationDiv = document.getElementById('conversation');
    if (conversationDiv) {
        console.log('Scrolling to bottom...');
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
        console.log('Scroll position set to:', conversationDiv.scrollTop, 'of', conversationDiv.scrollHeight);
    }
}

// Output Message Types with Emojis
const OutputTypes = {
    BOT_PROCESSING: { type: 'bot-processing', emoji: '🤖', label: 'Processing' },
    BOT_PREVIEW: { type: 'bot-preview', emoji: '🐰', label: 'Bot' },
    INNER_THOUGHTS: { type: 'inner-thoughts', emoji: '💭', label: 'Inner Thoughts' },
    PREFERENCES: { type: 'preferences', emoji: '💕', label: 'Preferences' },
    INTERESTS: { type: 'interests', emoji: '📚', label: 'Interests' },
    MOOD: { type: 'mood', emoji: '😊', label: 'Mood' },
    MEMORIES: { type: 'memories', emoji: '📝', label: 'Memories' },
    TTS_ON: { type: 'tts-on', emoji: '🔊', label: 'TTS ON' },
    TTS_OFF: { type: 'tts-off', emoji: '🔇', label: 'TTS OFF' },
    TTS_PLAYING: { type: 'tts-on', emoji: '🔊', label: 'Playing TTS' },
    STT_ON: { type: 'stt-on', emoji: '🎙️', label: 'STT ON' },
    STT_OFF: { type: 'stt-off', emoji: '🎙️', label: 'STT OFF' },
    STT_TRANSCRIBING: { type: 'stt-on', emoji: '🎙️', label: 'Transcribing audio' },
    CONTINUATION: { type: 'continuation', emoji: '🔄', label: 'Continuation' },
    SYSTEM: { type: 'system-output', emoji: '⚙️', label: 'System' }
};

// Track the last streaming message element
let lastStreamingMessage = null;
let lastStreamingType = null;

// Enhanced Output Panel Functions
function addOutputMessage(content, outputType = OutputTypes.SYSTEM, data = null, isStreaming = false) {
    const outputMessages = document.getElementById('output-messages');
    if (!outputMessages) {
        console.error('Output messages container not found');
        return null;
    }
    
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
            
            // Auto-scroll if needed
            if (isOutputScrolledToBottom()) {
                scrollOutputToBottom();
            } else {
                showOutputScrollButton();
            }
            
            return lastStreamingMessage;
        }
    }
    
    // Create a new message div
    const messageDiv = document.createElement('div');
    messageDiv.className = `output-message ${outputType.type} ${isStreaming ? 'streaming' : ''}`;
    
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
    });
    
    let messageContent = `<span class="emoji">${outputType.emoji}</span>`;
    messageContent += `<span class="output-label">${outputType.label}:</span> `;
    messageContent += `<span class="message-content">`;
    
    // Format different data types
    if (data && typeof data === 'object') {
        messageContent += formatObjectOutput(data);
    } else {
        messageContent += content || JSON.stringify(data, null, 2);
    }
    
    messageContent += `</span>`;
    messageContent += `<span class="timestamp">${timestamp}</span>`;
    messageDiv.innerHTML = messageContent;
    
    // Store scroll state before adding new message
    const wasScrolledToBottom = isOutputScrolledToBottom();
    
    // Add the message to the DOM
    outputMessages.appendChild(messageDiv);
    
    console.log('Message added, wasScrolledToBottom:', wasScrolledToBottom);
    
    // Update last streaming message reference if this is a streaming message
    if (isStreaming) {
        lastStreamingMessage = messageDiv;
        lastStreamingType = outputType;
    } else {
        // Clear the last streaming message reference if this is a non-streaming message
        lastStreamingMessage = null;
        lastStreamingType = null;
    }
    
    // Scroll to bottom if we were already at the bottom
    if (wasScrolledToBottom) {
        // Use setTimeout to ensure the DOM has updated
        setTimeout(scrollOutputToBottom, 50);
    } else {
        showOutputScrollButton();
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
    botProcessing: (message) => 
        addOutputMessage(message, OutputTypes.BOT_PROCESSING),
    
    botPreview: (message) => 
        addOutputMessage(message, OutputTypes.BOT_PREVIEW),
        
    // Inner thoughts
    innerThoughts: (thoughts) => 
        addOutputMessage(thoughts, OutputTypes.INNER_THOUGHTS, thoughts),
        
    // Preferences
    preferences: (prefs) => 
        addOutputMessage('Preferences updated', OutputTypes.PREFERENCES, prefs),
        
    // Interests
    interests: (interests) => 
        addOutputMessage('Interests updated', OutputTypes.INTERESTS, interests),
        
    // Mood detection
    mood: (moodData) => 
        addOutputMessage('Mood detected', OutputTypes.MOOD, moodData),
        
    // Relevant memories
    memories: (memories) => 
        addOutputMessage('Relevant memories', OutputTypes.MEMORIES, memories),
        
    // TTS events
    ttsOn: () => 
        addOutputMessage('Text-to-speech enabled', OutputTypes.TTS_ON),
    ttsOff: () => 
        addOutputMessage('Text-to-speech disabled', OutputTypes.TTS_OFF),
    ttsPlaying: (text) => 
        addOutputMessage(text || 'Playing audio...', OutputTypes.TTS_PLAYING),
        
    // STT events  
    sttOn: () => 
        addOutputMessage('Speech recognition enabled', OutputTypes.STT_ON),
    sttOff: () => 
        addOutputMessage('Speech recognition disabled', OutputTypes.STT_OFF),
    sttTranscribing: (status) => 
        addOutputMessage(status || 'Listening and transcribing...', OutputTypes.STT_TRANSCRIBING),
        
    // Continuation
    continuation: (data) => 
        addOutputMessage('Processing continuation', OutputTypes.CONTINUATION, data),
        
    // System messages
    system: (message, data) => 
        addOutputMessage(message, OutputTypes.SYSTEM, data)
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

function startOutputPolling() {
    // Poll for output events every 500ms
    outputPollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/get_output_events');
            const data = await response.json();
            
            if (data.success && data.events && data.events.length > 0) {
                // Process each event
                data.events.forEach(event => {
                    processOutputEvent(event);
                });
            }
        } catch (error) {
            console.error('Error polling output events:', error);
        }
    }, 500);
}

function stopOutputPolling() {
    if (outputPollingInterval) {
        clearInterval(outputPollingInterval);
        outputPollingInterval = null;
    }
}

function processOutputEvent(event) {
    const { type, content, data, is_streaming: isStreaming = false } = event;
    
    // Call the appropriate OutputManager method based on event type
    switch(type) {
        case 'botProcessing':
            OutputManager.botProcessing(content, data);
            break;
        case 'botPreview':
            // Pass the isStreaming flag to the output message
            addOutputMessage(content, OutputTypes.BOT_PREVIEW, data, isStreaming);
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
        case 'ttsOff':
            OutputManager.ttsOff();
            break;
        case 'ttsPlaying':
            OutputManager.ttsPlaying(content);
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

// Function to check if the user is scrolled to the bottom of the output panel
function isOutputScrolledToBottom() {
    const outputMessages = document.getElementById('output-messages');
    if (!outputMessages) return true;
    
    // Add a small threshold (5px) to account for potential rounding issues
    const threshold = 5;
    const isAtBottom = Math.abs(outputMessages.scrollHeight - outputMessages.clientHeight - outputMessages.scrollTop) <= threshold;
    
    console.log('isOutputScrolledToBottom:', 
                `scrollHeight: ${outputMessages.scrollHeight}, ` +
                `clientHeight: ${outputMessages.clientHeight}, ` +
                `scrollTop: ${outputMessages.scrollTop}, ` +
                `isAtBottom: ${isAtBottom}`);
    
    return isAtBottom;
}

// Function to scroll the output panel to the bottom
function scrollOutputToBottom() {
    const outputMessages = document.getElementById('output-messages');
    if (!outputMessages) return;
    
    console.log('scrollOutputToBottom: Attempting to scroll...');
    
    // Force a reflow before scrolling
    const scrollHeight = outputMessages.scrollHeight;
    outputMessages.scrollTop = scrollHeight;
    
    console.log(`scrollOutputToBottom: Set scrollTop to ${scrollHeight}`);
    
    // Double check if the scroll worked
    requestAnimationFrame(() => {
        if (Math.abs(outputMessages.scrollTop + outputMessages.clientHeight - outputMessages.scrollHeight) > 5) {
            console.log('scrollOutputToBottom: First attempt failed, forcing scroll again');
            outputMessages.scrollTop = outputMessages.scrollHeight;
        }
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
                scrollButton.style.display = 'block';
            }
        });
    }
    
    // Setup output panel
    setupOutputPanel();
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