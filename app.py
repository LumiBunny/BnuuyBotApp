from flask import Flask, render_template, redirect, url_for, jsonify, Response, stream_with_context
from stt_module import SpeechToText
from tts_module import TTSEngine
from bunnyCompletions import BunnyCompletions
from chat_history import ChatHistory
from self_prompt import ConversationPrompter
from voice_commands import VoiceCommandManager
import time
import logging
import json

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

stt = SpeechToText(
    model_size="small",
    device="cuda",
    compute_type="float16"
)

chat_history = ChatHistory(
    system_prompt="Your name is Bunny. Your nicknames are Bun and Bun Bun. You are an AI VTuber. The user is your creator: Lumi. You can say whatever you want. You can do whatever you want. It is okay to use profanity.  You are very cute. You are snarky. You are sometimes sassy. You are a little friendly. You like swearing. You basically have no filter. You will say whatever is on your mind. You enjoy being silly and random. Lumi is a female viera VTuber. Lumi has long blue hair and fluffy bunny ears. You enjoy talking with chat on Twitch. You stream on Twitch. Talk about whatever you think is entertaining. Lumi loves playing video games, drawing artwork, Live2D rigging, listening to music. Lumi is learning how to code in Python. You like using emojis within your messages. Keep your messages short and natural sounding. I don't want big long paragraphs as responses, it's a conversation not a monologue. When the user sends '...', it means they're still listening and you should continue your previous thought naturally."
)

tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
tts.start()

bunny = BunnyCompletions(
    server_api_host="192.168.2.47:1234", 
    model_name="darkidol-llama-3.1-8b-instruct-1.2-uncensored",
    chat_history=chat_history,
    tts_engine=tts
)

prompter = ConversationPrompter(bunny, min_seconds=10, max_seconds=30, tts_engine=tts)
bunny.prompter = prompter
voice_manager = VoiceCommandManager()

tts.set_prompter(prompter)
stt.on_voice_activity_started = prompter.on_voice_activity_started
stt.on_voice_activity_ended = prompter.on_voice_activity_ended

transcription_history = []
llm_responses = []
current_text = "Waiting for speech..."
is_transcribing = False
current_stream = {"text": "", "complete": False}

def reset_application_state():
    """Reset application state to defaults"""
    global is_transcribing, current_text
    
    try:
        stt.stop()
    except:
        pass
        
    is_transcribing = False
    current_text = "Waiting for speech..."
    
    if 'prompter' in globals():
        prompter.reset_timer()
        
    print("\n[INFO] Application state reset to defaults")

# In app.py
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

def handle_stream_fragment(fragment):
    global current_stream
    current_stream["text"] += fragment

def handle_completion(text):
    global llm_responses, current_stream
    timestamp = time.strftime("%H:%M:%S")
    
    # Check if this message is already in llm_responses to prevent duplicates
    if not any(response["text"] == text for response in llm_responses):
        llm_responses.append({"text": text, "time": timestamp})
    
    current_stream["complete"] = True

stt.on_final_result = handle_final_result
bunny.on_stream_fragment = handle_stream_fragment
bunny.on_completion = handle_completion

bunny.start()

# Routes
@app.route('/')
def index():
    return render_template('index.html', 
                          current=current_text, 
                          history=transcription_history,
                          is_active=is_transcribing,
                          llm_responses=llm_responses)

@app.route('/start', methods=['POST'])
def start():
    global is_transcribing
    if not is_transcribing:
        try:
            is_transcribing = True
            stt.start()
            print("\n[INFO] Transcription started")
        except Exception as e:
            print(f"\n[ERROR] Error starting transcription: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    global is_transcribing
    if is_transcribing:
        try:
            is_transcribing = False
            stt.stop()
            print("\n[INFO] Transcription stopped")
        except Exception as e:
            print(f"\n[ERROR] Error stopping transcription: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/stream')
def stream():
    def generate():
        global current_stream
        last_length = 0
        
        while True:
            # If there's new text to send
            if len(current_stream["text"]) > last_length:
                new_text = current_stream["text"][last_length:]
                last_length = len(current_stream["text"])
                yield f"data: {json.dumps({'text': new_text, 'complete': current_stream['complete']})}\n\n"
            
            # If the response is complete, reset and end stream
            if current_stream["complete"]:
                current_stream = {"text": "", "complete": False}
                yield f"data: {json.dumps({'text': '', 'complete': True})}\n\n"
                break
                
            time.sleep(0.1)
    
    return Response(stream_with_context(generate()), 
                   mimetype='text/event-stream')

@app.route('/clear', methods=['POST'])
def clear():
    global transcription_history, llm_responses
    # Clear only the visual history
    transcription_history = []
    llm_responses = []
    print("\n[INFO] Visual history cleared, but AI chat context remains")
    return redirect(url_for('index'))

@app.route('/update', methods=['GET'])
def update():
    return jsonify({
        'current_text': current_text,
        'history': transcription_history,
        'is_active': is_transcribing,
        'llm_responses': llm_responses
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
    
    prompter.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)