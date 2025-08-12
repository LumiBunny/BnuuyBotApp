from flask import Flask, render_template, jsonify, request, redirect, url_for
from audio import SpeechToText, TTSEngine
from chat import BunnyChat, ChatHistory
import time
import os
import logging
from flask import request

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Initialize Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

# Initialize core components
bunny = BunnyChat()
tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
# Modified STT settings for better microphone detection
stt = SpeechToText(
    model_size="small", 
    device="cuda", 
    compute_type="float16",
    vad_aggressiveness=1,  # Less aggressive voice detection (was 2)
    silence_threshold=0.8,  # Lower silence threshold (was 1.0)
    streaming_interval=0.5  # Longer intervals for better detection
)

# Global state variables
transcription_history = []
llm_responses = []
current_text = "Waiting for speech..."
is_transcribing = False
tts_enabled = True  # TTS is enabled by default

# NEW: Unified message buffering system
message_buffer = []  # Buffer for all messages during TTS playback
is_tts_playing = False  # Track TTS state globally

# Event handlers
def handle_final_result(text):
    global transcription_history, current_text, message_buffer, is_tts_playing
    if text:
        timestamp = time.strftime("%H:%M:%S")
        
        # ALWAYS add to UI history for individual display
        transcription_history.append({"text": text, "time": timestamp})
        current_text = text
        
        # NEW: Check if TTS is playing and buffer message if needed
        if is_tts_playing:
            print(f"TTS is playing, buffering message: {text}")
            message_buffer.append(text)
            # Note: Message is displayed in UI but NOT sent to BunnyChat yet
        else:
            # Process immediately if TTS is not playing
            process_message(text)

def process_message(text):
    """Process a single message or combined buffered messages"""
    print(f"Processing message for BunnyChat: {text}")
    
    # Use the new get_response method signature with message parameter
    response = bunny.get_response(text, user_id="lumi")
    
    handle_completion(response)
    
    # Add to TTS queue only if TTS is enabled
    if tts_enabled:
        tts.add_to_queue(response)

def process_buffered_messages():
    """Process all buffered messages when TTS finishes"""
    global message_buffer, is_tts_playing
    
    if message_buffer:
        combined_text = " ".join(message_buffer)
        print(f"Processing combined buffered messages for BunnyChat: {combined_text}")
        
        # Process the combined message (this generates the bot response)
        process_message(combined_text)
        
        # Clear buffer
        message_buffer = []
    
    is_tts_playing = False

def on_tts_started():
    """Called when TTS starts playing"""
    global is_tts_playing, message_buffer
    is_tts_playing = True
    message_buffer = []  # Clear any old buffer
    print("DEBUG: TTS playback started, message buffering enabled (UI still shows individual messages)")

def on_tts_finished():
    """Called when TTS finishes playing"""
    print("DEBUG: TTS playback finished, processing buffered messages")
    process_buffered_messages()

def handle_completion(text):
    global llm_responses
    timestamp = time.strftime("%H:%M:%S")
    
    if not any(response["text"] == text for response in llm_responses):
        llm_responses.append({"text": text, "time": timestamp})

stt.on_final_result = handle_final_result

# NEW: Connect TTS callbacks to our unified system
tts.on_playback_started = on_tts_started
tts.on_playback_finished = on_tts_finished

# Also connect STT callbacks for consistency
stt.on_tts_started = on_tts_started
stt.on_tts_finished = on_tts_finished

tts.start()

# Routes
@app.route('/')
def index():
    return render_template('index.html', 
                          is_active=is_transcribing, 
                          current_text=current_text,
                          tts_enabled=tts_enabled)

@app.route('/start_listening', methods=['POST'])
def start_listening():
    global is_transcribing
    success = False
    message = ""
    
    try:
        stt.start()
        is_transcribing = True
        success = True
        message = "Listening started"
        print("\n[INFO] Speech recognition started")
    except Exception as e:
        message = f"Error starting listening: {str(e)}"
        print(f"\n[ERROR] {message}")
    
    return jsonify({
        "success": success,
        "message": message
    })

@app.route('/stop_listening', methods=['POST'])
def stop_listening():
    global is_transcribing
    success = False
    message = ""
    
    try:
        stt.stop()
        is_transcribing = False
        success = True
        message = "Listening stopped"
        print("\n[INFO] Speech recognition stopped")
    except Exception as e:
        message = f"Error stopping listening: {str(e)}"
        print(f"\n[ERROR] {message}")
    
    return jsonify({
        "success": success,
        "message": message
    })

@app.route('/load_chat', methods=['POST'])
def load_chat():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({"success": False, "message": "No filename provided"})
        
        success = bunny.load_chat_history(filename)
        if success:
            return jsonify({"success": True, "message": f"Chat loaded from {filename}"})
        else:
            return jsonify({"success": False, "message": "Failed to load chat history"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/list_histories', methods=['GET'])
def list_histories():
    history_dir = "chat_history"
    try:
        files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
        return jsonify({"success": True, "histories": sorted(files, reverse=True)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/load_chat_history', methods=['POST'])
def load_chat_history():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400
    
    try:
        # Reset the chat history and load the selected one
        system_prompt = bunny.chat_history.messages[0]['content'] if bunny.chat_history.messages else None
        
        # Load the chat history from file
        new_history = ChatHistory.load_from_file(filename, system_prompt=system_prompt)
        
        # Update the bunny's chat history
        bunny.chat_history = new_history
        
        # Clear the transcription history and LLM responses to prevent duplication
        # These arrays are used by the polling system for plain text display
        # We don't want to populate them with loaded history to avoid duplication
        global transcription_history, llm_responses
        transcription_history = []
        llm_responses = []
        
        # Extract messages for the UI (chat bubbles only)
        messages = []
        for msg in new_history.messages:
            # Only add to messages for chat bubble display, not to polling arrays
            messages.append({
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp']
            })
        
        return jsonify({
            "success": True, 
            "messages": messages,
            "message": f"Loaded chat history: {filename}"
        })
        
    except Exception as e:
        app.logger.error(f"Error loading chat history: {str(e)}")
        return jsonify({"success": False, "error": f"Failed to load chat history: {str(e)}"}), 500



@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    return jsonify({
        "transcriptions": transcription_history,
        "responses": llm_responses,
        "current_text": current_text,
        "is_listening": is_transcribing
    })

@app.route('/send_text', methods=['POST'])
def send_text():
    data = request.json
    text = data.get('text', '')
    
    if text:
        # NEW: Use the same unified handler as STT
        handle_final_result(text)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "No text provided"})

@app.route('/clear', methods=['POST'])
def clear_chat():
    # Clear only the UI chat display without resetting the conversation context
    global transcription_history, llm_responses, current_text
    
    # Clear the visual history
    transcription_history = []
    llm_responses = []
    current_text = "Waiting for speech..."
    
    print("\n[INFO] Chat display cleared (UI only)")
    
    return jsonify({
        "success": True,
        "message": "Chat display cleared. The conversation context is still active."
    })

@app.route('/end_chat', methods=['POST'])
def end_chat():
    reset_application_state()
    return jsonify({"success": True, "message": "Chat ended successfully"})

@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    # Fully reset the chat context and clear UI state
    try:
        # Reset the chat context in the bunny instance
        bunny.reset_chat()
        
        # Clear the UI state
        global transcription_history, llm_responses, current_text, is_transcribing
        transcription_history = []
        llm_responses = []
        current_text = "Waiting for speech..."
        is_transcribing = False
        
        # Stop any ongoing TTS
        tts.stop()
        
        # Stop any ongoing STT
        try:
            stt.stop()
        except:
            pass  # Ignore if STT wasn't running
        
        print("\n[INFO] Chat fully reset - context and UI cleared")
        
        return jsonify({
            "success": True,
            "message": "Chat has been fully reset. All context has been cleared."
        })
    except Exception as e:
        app.logger.error(f"Error resetting chat: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error resetting chat: {str(e)}"
        })

@app.route('/toggle_tts', methods=['POST'])
def toggle_tts():
    global tts_enabled
    
    try:
        tts_enabled = not tts_enabled
        status = "enabled" if tts_enabled else "disabled"
        message = f"TTS {status}"
        print(f"\n[INFO] TTS {status}")
        
        return jsonify({
            "success": True,
            "message": message,
            "tts_enabled": tts_enabled
        })
    except Exception as e:
        message = f"Error toggling TTS: {str(e)}"
        print(f"\n[ERROR] {message}")
        return jsonify({
            "success": False,
            "message": message,
            "tts_enabled": tts_enabled
        })

def reset_application_state():
    global is_transcribing, current_text
    
    try:
        stt.stop()
    except:
        pass
        
    is_transcribing = False
    current_text = "Waiting for speech..."
    
    print("\n[INFO] Application state reset to defaults")

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Shut down the Flask server
    shutdown_server()
    return jsonify({"success": True, "message": "Server is shutting down..."})

def shutdown_server():
    # Helper function to shut down the Flask server
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os._exit(0)
    func()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Live Transcription Server with BunnyChat")
    print("="*50)
    print("1. Open your browser and go to: http://localhost:5000")
    print("2. Click 'Start Listening' to begin transcription")
    print("3. Speak into your microphone")
    print("4. Your speech and the AI responses will appear in the conversation")
    print("5. Click 'Clear History' to reset the conversation")
    print("="*50 + "\n")
    
    reset_application_state()
    
    app.run(host='0.0.0.0', port=5000, debug=False)