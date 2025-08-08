from flask import Flask, render_template, jsonify, request, redirect, url_for
from stt_module import SpeechToText
from tts_module import TTSEngine
from bunnyChat import BunnyChat
from chatHistory import ChatHistory
import time
import os
import logging
from flask import request
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Initialize Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

# Initialize core components
bunny = BunnyChat()
tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
stt = SpeechToText(model_size="small", device="cuda", compute_type="float16")

# Global state variables
transcription_history = []
llm_responses = []
current_text = "Waiting for speech..."
is_transcribing = False

# Event handlers
def handle_final_result(text):
    global transcription_history, current_text
    if text:
        timestamp = time.strftime("%H:%M:%S")
        transcription_history.append({"text": text, "time": timestamp})
        current_text = text
        
        bunny.add_user_message(text)
        response = bunny.get_response()
        
        handle_completion(response)
        
        tts.add_to_queue(response)
        bunny.add_assistant_message(response)

def handle_completion(text):
    global llm_responses
    timestamp = time.strftime("%H:%M:%S")
    
    if not any(response["text"] == text for response in llm_responses):
        llm_responses.append({"text": text, "time": timestamp})

stt.on_final_result = handle_final_result

tts.start()

def shutdown_server():
    # Helper function to shut down the Flask server
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os._exit(0)
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Shut down the Flask server
    shutdown_server()
    return jsonify({"success": True, "message": "Server is shutting down..."})

# Routes
@app.route('/')
def index():
    return render_template('index.html', 
                          is_active=is_transcribing, 
                          current_text=current_text)

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
        # Process the text as if it came from STT
        handle_final_result(text)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "No text provided"})

@app.route('/clear', methods=['POST'])
def clear_chat():
    """Clear only the UI chat display without resetting the conversation context"""
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
    """Fully reset the chat context and clear UI state"""
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

def reset_application_state():
    global is_transcribing, current_text
    
    try:
        stt.stop()
    except:
        pass
        
    is_transcribing = False
    current_text = "Waiting for speech..."
    
    print("\n[INFO] Application state reset to defaults")

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