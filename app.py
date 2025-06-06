from flask import Flask, render_template, redirect, url_for, jsonify, Response, request
from stt_module import SpeechToText
from tts_module import TTSEngine
from bunnyCompletions import BunnyCompletions
from chat_history import ChatHistory, ChatLogger
from self_prompt import ConversationPrompter
from voice_commands import VoiceCommandManager
from user_profile_manager import UserProfileManager, EnhancedPreferenceExtractor
from memory import MemoryManager
import time
import logging
import json
import datetime

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

chat_logger = ChatLogger(logs_directory="chat_logs")
chat_history = ChatHistory(
    system_prompt="Your name is Bunny. Your nicknames are Bun and Bun Bun. You are an AI VTuber. The user is your creator: Lumi. You can say whatever you want. You can do whatever you want. It is okay to use profanity.  You are very cute. You are snarky. You are sometimes sassy. You are a little friendly. You like swearing. You basically have no filter. You will say whatever is on your mind. You enjoy being silly and random. Lumi is a female viera VTuber. Lumi has long blue hair and fluffy bunny ears. You enjoy talking with chat on Twitch. You stream on Twitch. Talk about whatever you think is entertaining. Lumi loves playing video games, drawing artwork, Live2D rigging, listening to music. Lumi is learning how to code in Python. You like using emojis within your messages. Keep your messages short and natural sounding. I don't want big long paragraphs as responses, it's a conversation not a monologue. When the user sends '...', it means they're still listening and you should continue your previous thought naturally."
)

preference_extractor = EnhancedPreferenceExtractor()
profile_manager = UserProfileManager(
    storage_path="user_profiles", 
    preference_extractor=preference_extractor,
    chat_logger=chat_logger
)
memory_manager = MemoryManager(profile_manager=profile_manager)
memory_manager.start()

stt = SpeechToText(
    model_size="small",
    device="cuda",
    compute_type="float16"
)

tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
tts.start()

bunny = BunnyCompletions(
    server_api_host="192.168.2.47:1234", 
    model_name="darkidol-llama-3.1-8b-instruct-1.2-uncensored",
    chat_history=chat_history,
    tts_engine=tts,
    profile_manager=profile_manager,
    chat_logger=chat_logger,
    memory_manager=memory_manager,
    default_user_id="lumi"
)

prompter = ConversationPrompter(bunny, min_seconds=10, max_seconds=30, tts_engine=tts)
bunny.prompter = prompter
voice_manager = VoiceCommandManager()

tts.set_prompter(prompter)
tts.on_playback_started = stt.on_tts_started
tts.on_playback_finished = stt.on_tts_finished
stt.on_voice_activity_started = prompter.on_voice_activity_started
stt.on_voice_activity_ended = prompter.on_voice_activity_ended

transcription_history = []
llm_responses = []
current_text = "Waiting for speech..."
is_transcribing = False

def reset_application_state():
    global is_transcribing, current_text
    
    try:
        stt.stop()
    except:
        pass
        
    is_transcribing = False
    current_text = "Waiting for speech..."
    
    if 'prompter' in globals():
        if prompter.is_running:
            prompter.stop()
        prompter.reset_timer()
    
    if 'profile_manager' in globals():
        profile_manager.clear_cache()
        
    print("\n[INFO] Application state reset to defaults")

def handle_final_result(text):
    global transcription_history, current_text
    timestamp = time.strftime("%H:%M:%S")
    
    print(f"Final: {text}")
    
    if text and text.strip():
        if not any(item["text"] == text for item in transcription_history):
            transcription_history.append({"text": text, "time": timestamp})
        
        processed_text, is_command = voice_manager.process_input(text)
        
        if not is_command:
            bunny.add_to_queue(processed_text)
        
        current_text = ""

def handle_completion(text):
    global llm_responses, current_stream
    timestamp = time.strftime("%H:%M:%S")
    
    # Check if this message is already in llm_responses to prevent duplicates
    if not any(response["text"] == text for response in llm_responses):
        llm_responses.append({"text": text, "time": timestamp})

stt.on_final_result = handle_final_result
bunny.on_completion = handle_completion

bunny.start()

# Routes
@app.route('/')
def index():
    return render_template('index.html', 
                          is_active=is_transcribing, 
                          timer_active=prompter.is_running,  # Add timer status
                          current_text=current_text,
                          default_user_id=bunny.default_user_id)

@app.route('/reset_tts_state', methods=['POST'])
def reset_tts_state():
    stt.is_tts_playing = False
    stt.tts_playback_buffer = []
    return jsonify({"status": "TTS state reset"})

@app.route('/start_timer', methods=['POST'])
def start_timer():
    success = False
    message = ""
    
    try:
        prompter.start()
        print("\n[INFO] Self-prompt timer started")
        success = True
        message = "Timer started"
    except Exception as e:
        message = f"Error starting timer: {str(e)}"
        print(f"\n[ERROR] {message}")
    
    return jsonify({
        "success": success,
        "message": message,
        "timer_active": prompter.is_running
    })

@app.route('/stop_timer', methods=['POST'])
def stop_timer():
    success = False
    message = ""
    
    try:
        prompter.stop()
        print("\n[INFO] Self-prompt timer stopped")
        success = True
        message = "Timer stopped"
    except Exception as e:
        message = f"Error stopping timer: {str(e)}"
        print(f"\n[ERROR] {message}")
    
    return jsonify({
        "success": success,
        "message": message,
        "timer_active": prompter.is_running
    })

@app.route('/end_chat', methods=['POST'])
def end_chat():
    try:
        # Stop all services in the correct order
        prompter.stop()
        stt.stop()
        tts.stop()
        bunny.stop()
        print("\n[INFO] All services stopped")
        
        # Add a system message to the chat history - use a safer approach
        try:
            if hasattr(chat_logger, 'add_system_message'):
                chat_logger.add_system_message("Chat session ended. All services have been stopped.")
            # If the above doesn't work, you might need to implement a different approach
            # based on how your chat_logger is implemented
        except Exception as e:
            print(f"\n[WARNING] Could not add system message: {str(e)}")
            # This will prevent the error from stopping the entire function
        
        # Return a success message without redirecting
        return jsonify({
            "success": True,
            "message": "Chat session ended successfully."
        })
        
    except Exception as e:
        print(f"\n[ERROR] Error ending chat: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error ending chat: {str(e)}"
        })

@app.route('/start', methods=['POST'])
def start():
    global is_transcribing
    success = False
    message = ""
    
    if not is_transcribing:
        try:
            is_transcribing = True
            stt.start()
            print("\n[INFO] Transcription started")
            success = True
            message = "Transcription started"
        except Exception as e:
            message = f"Error starting transcription: {str(e)}"
            print(f"\n[ERROR] {message}")
    else:
        message = "Transcription already active"
    
    return jsonify({
        "success": success,
        "message": message,
        "is_active": is_transcribing
    })

@app.route('/stop', methods=['POST'])
def stop():
    global is_transcribing
    success = False
    message = ""
    
    if is_transcribing:
        try:
            is_transcribing = False
            stt.stop()
            print("\n[INFO] Transcription stopped")
            success = True
            message = "Transcription stopped"
        except Exception as e:
            message = f"Error stopping transcription: {str(e)}"
            print(f"\n[ERROR] {message}")
    else:
        message = "Transcription already inactive"
    
    return jsonify({
        "success": success,
        "message": message,
        "is_active": is_transcribing
    })

@app.route('/send_message', methods=['POST'])
def send_message():
    message_text = request.form.get('message_text', '').strip()
    success = False
    message = ""
    
    if message_text:
        try:
            # Add to history
            chat_history.add_user_message(message_text)
            
            # Send to bunny completions
            bunny.add_to_queue(message_text)
            
            # Update UI
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            transcription_history.append({"text": message_text, "time": timestamp})
            
            success = True
            message = "Message sent"
        except Exception as e:
            message = f"Error sending message: {str(e)}"
            print(f"\n[ERROR] {message}")
    else:
        message = "Empty message"
    
    return jsonify({
        "success": success,
        "message": message
    })

@app.route('/add_system_message', methods=['POST'])
def add_system_message():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Add to both chat history and chat logger
        chat_history.add_system_message(message)
        if chat_logger:
            chat_logger.add_system_message(message)
            
        # Also add to your transcription history for UI updates
        transcription_history.append({
            "type": "system", 
            "text": message, 
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        })
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/clear', methods=['POST'])
def clear():
    global transcription_history, llm_responses
    # Clear only the visual history
    transcription_history = []
    llm_responses = []
    print("\n[INFO] Visual history cleared, but AI chat context remains")
    
    return jsonify({
        "success": True,
        "message": "History cleared"
    })

@app.route('/set_user_id', methods=['POST'])
def set_user_id():
    user_id = request.form.get('user_id', '').strip()
    success = False
    message = ""
    
    if user_id:
        try:
            success = bunny.set_user_id(user_id)
            if success:
                message = f"User ID set to: {user_id}"
            else:
                message = "Failed to set user ID"
        except Exception as e:
            message = f"Error setting user ID: {str(e)}"
            print(f"\n[ERROR] {message}")
    else:
        message = "Invalid user ID"
    
    return jsonify({
        "success": success,
        "message": message
    })

@app.route('/update', methods=['GET'])
def update():
    # Get system messages
    system_messages = []
    
    # Try different ways to access system messages based on your implementation
    if hasattr(chat_logger, 'get_system_messages'):
        system_messages = chat_logger.get_system_messages()
    elif hasattr(chat_logger, 'system_messages'):
        system_messages = chat_logger.system_messages
    
    # Format system messages for the response
    formatted_system_messages = []
    for message in system_messages:
        formatted_system_messages.append({
            "text": message.get("content", ""),
            "time": message.get("time", datetime.datetime.now().strftime("%H:%M:%S"))
        })
    
    return jsonify({
        'current_text': current_text,
        'history': transcription_history,
        'is_active': is_transcribing,
        'timer_active': prompter.is_running,
        'llm_responses': llm_responses,
        'system_messages': formatted_system_messages,
        'user_id': bunny.default_user_id
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Live Transcription Server with BunnyCompletions")
    print("="*50)
    print("1. Open your browser and go to: http://localhost:5000")
    print("2. Click 'Start Listening' to begin transcription")
    print("3. Speak into your microphone")
    print("4. Your speech and the AI responses will appear in the conversation")
    print("5. Click 'Clear History' to reset the conversation")
    print("="*50 + "\n")
    
    reset_application_state()
    
    bunny.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)