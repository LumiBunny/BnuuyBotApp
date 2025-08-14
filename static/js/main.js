// Add this at the top of your main.js, after the OutputManager definition
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
    
    // Map server event types to OutputManager methods
    const eventHandlers = {
        'system': OutputManager.system,
        'tts_on': OutputManager.ttsOn,
        'tts_off': OutputManager.ttsOff,
        'tts_playing': OutputManager.ttsPlaying,
        'tts_finished': OutputManager.ttsFinished,
        'stt_on': OutputManager.sttOn,
        'stt_off': OutputManager.sttOff,
        'stt_transcribing': OutputManager.sttTranscribing,
        'bot_processing': OutputManager.botProcessing,
        'inner_thoughts': OutputManager.innerThoughts,
        'preferences': OutputManager.preferences,
        'interests': OutputManager.interests,
        'mood': OutputManager.mood,
        'memories': OutputManager.memories,
        'continuation': OutputManager.continuation
    };
    
    // Call the appropriate handler if it exists
    const handler = eventHandlers[data.type];
    if (handler) {
        handler(data.content, data.data);
    } else {
        console.warn('Unknown event type:', data.type);
        OutputManager.system(data.content || 'Unknown event', data.data);
    }
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

// Output Message Types with Emojis
const OutputTypes = {
    BOT_PROCESSING: { type: 'bot-processing', emoji: '🤖', label: 'Processing' },
    BOT_PREVIEW: { type: 'bot-preview', emoji: '🐰', label: 'Bot' },
    INNER_THOUGHTS: { type: 'inner-thoughts', emoji: '💭', label: 'Thinking' },
    PREFERENCES: { type: 'preferences', emoji: '💕', label: 'Preferences' },
    INTERESTS: { type: 'interests', emoji: '🎯', label: 'Interests' },
    MOOD: { type: 'mood', emoji: '😊', label: 'Mood' },
    MEMORIES: { type: 'memories', emoji: '🧠', label: 'Memories' },
    TTS_ON: { type: 'tts-on', emoji: '🔊', label: 'TTS' },
    TTS_OFF: { type: 'tts-off', emoji: '🔇', label: 'TTS' },
    TTS_PLAYING: { type: 'tts-playing', emoji: '▶️', label: 'TTS' },
    TTS_FINISHED: { type: 'tts-finished', emoji: '⏹️', label: 'TTS' },
    STT_ON: { type: 'stt-on', emoji: '🎤', label: 'STT' },
    STT_OFF: { type: 'stt-off', emoji: '🎙️', label: 'STT' },
    STT_TRANSCRIBING: { type: 'stt-transcribing', emoji: '✍️', label: 'STT' },
    SYSTEM: { type: 'system', emoji: '⚙️', label: 'System' },
    CONTINUATION: { type: 'continuation', emoji: '↩️', label: 'Continue' }
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
    
    // Set the appropriate class based on message type
    let messageClass = 'output-message';
    if (outputType === OutputTypes.SYSTEM) {
        messageClass += ' system-output';  // This will apply the light gray background
    } else if (outputType === OutputTypes.BOT_PREVIEW) {
        messageClass += ' bot-preview';   // This will apply the light lilac background
    }
    
    if (isStreaming) {
        messageClass += ' streaming';     // Add streaming class if needed
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
    
    // Auto-scroll if needed
    if (isOutputScrolledToBottom()) {
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
        addOutputMessage(message, OutputTypes.BOT_PROCESSING);
    },
    
    botPreview(message) {
        addOutputMessage(message, OutputTypes.BOT_PREVIEW);
    },
    
    // Inner thoughts
    innerThoughts(thoughts) {
        addOutputMessage(thoughts, OutputTypes.INNER_THOUGHTS);
    },
    
    // Preferences
    preferences(prefs) {
        addOutputMessage(formatObjectOutput(prefs), OutputTypes.PREFERENCES);
    },
    
    // Interests
    interests(interests) {
        addOutputMessage(formatObjectOutput(interests), OutputTypes.INTERESTS);
    },
    
    // Mood detection
    mood(moodData) {
        addOutputMessage(formatObjectOutput(moodData), OutputTypes.MOOD);
    },
    
    // Relevant memories
    memories(memories) {
        addOutputMessage(formatObjectOutput(memories), OutputTypes.MEMORIES);
    },
    
    // TTS events
    ttsOn() {
        addOutputMessage('TTS: Text-to-speech enabled', OutputTypes.TTS_ON);
    },
    
    ttsOff() {
        addOutputMessage('TTS: Text-to-speech disabled', OutputTypes.TTS_OFF);
    },
    
    ttsPlaying(text) {
        addOutputMessage('TTS: Starting audio playback', OutputTypes.TTS_PLAYING);
    },
    
    ttsFinished() {
        addOutputMessage('TTS: Playback finished', OutputTypes.TTS_FINISHED);
    },
    
    // STT events
    sttOn() {
        addOutputMessage('Speech recognition started', OutputTypes.STT_ON);
    },
    
    sttOff() {
        addOutputMessage('Speech recognition stopped', OutputTypes.STT_OFF);
    },
    
    sttTranscribing(status) {
        if (typeof status === 'string') {
            addOutputMessage(status, OutputTypes.STT_TRANSCRIBING);
        } else if (status && status.text) {
            addOutputMessage(`Transcribing: ${status.text}`, OutputTypes.STT_TRANSCRIBING);
        }
    },
    
    // Continuation
    continuation(data) {
        addOutputMessage('Continuing response...', OutputTypes.CONTINUATION);
    },
    
    // System messages
    system(message, data) {
        addOutputMessage(message, OutputTypes.SYSTEM, data);
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