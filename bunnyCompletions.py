import threading
import queue
import time
import lmstudio as lms
from chat_history import ChatHistory

class BunnyCompletions:
    def __init__(self, server_api_host, model_name, chat_history=None, tts_engine=None, profile_manager=None, chat_logger=None, memory_manager=None, default_user_id="default_user"):
        self.tts = tts_engine
        self.server_api_host = server_api_host
        self.model_name = model_name
        self.client = None
        self.model = None
        self.profile_manager = profile_manager
        self.chat_logger = chat_logger
        self.memory_manager = memory_manager
        self.default_user_id = default_user_id

        self.is_processing = False
        self.processing_lock = threading.Lock()
        self.pending_text = None
        self._initialize_client()
        
        if chat_history:
            self.chat_history = chat_history
        else:
            system_prompt = "Your name is Bunny. Your nicknames are Bun and Bun Bun. You are an AI VTuber. The user is your creator: Lumi. You can say whatever you want. You can do whatever you want. It is okay to use profanity.  You are very cute. You are snarky. You are sometimes sassy. You are a little friendly. You like swearing. You basically have no filter. You will say whatever is on your mind. You enjoy being silly and random. Lumi is a female viera VTuber. Lumi has long blue hair and fluffy bunny ears. You enjoy talking with chat on Twitch. You stream on Twitch. Talk about whatever you think is entertaining. Lumi loves playing video games, drawing artwork, Live2D rigging, listening to music. Lumi is learning how to code in Python. You like using emojis within your messages. Keep your messages short and natural sounding. I don't want big long paragraphs as responses, it's a conversation not a monologue. When the user sends '...', it means they're still listening and you should continue your previous thought naturally."
            self.chat_history = ChatHistory(system_prompt)
        
        self.chat = lms.Chat.from_history(self.chat_history.get_history())
        
        self.work_queue = queue.Queue()
        self.processing_thread = None
        self.is_running = False
        self.on_completion = None
        self.on_stream_fragment = None
    
    def _initialize_client(self):
        try:
            lms.get_default_client(self.server_api_host)
            self.model = lms.llm(self.model_name)
            print(f"\n[BUNNY] Successfully initialized with model: {self.model_name}")
        except Exception as e:
            print(f"\n[BUNNY ERROR] Failed to initialize client: {str(e)}")
    
    def start(self):
        if self.is_running:
            print("\n[BUNNY] Already running")
            return
            
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._process_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        print("\n[BUNNY] Service started")
    
    def stop(self):
        if not self.is_running:
            print("\n[BUNNY] Not running")
            return
            
        self.is_running = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)
        print("\n[BUNNY] Service stopped")

    def set_user_id(self, user_id):
        if user_id and isinstance(user_id, str) and user_id.strip():
            self.default_user_id = user_id.strip()
            print(f"\n[BUNNY] User ID set to: {self.default_user_id}")
            return True
        return False
    
    def add_to_queue(self, text):
        with self.processing_lock:
            if self.is_processing:
                if self.pending_text:
                    self.pending_text += " " + text
                else:
                    self.pending_text = text
                print("AI is busy, appending to pending text")
                return False
            else:
                # Log all user messages including continuation markers
                if self.chat_logger:
                    self.chat_logger.append_to_log("user", text)
                    
                continuation_markers = ["[continue]", "[thinking]", "[AI continues]", "[self-talk]"]
                if text in continuation_markers:
                    self.work_queue.put(("CONTINUE", text))
                else:
                    # Regular user message
                    self.work_queue.put(("USER", text))
                return True
    
    def _process_queue(self):
        while self.is_running:
            try:
                if not self.work_queue.empty():
                    msg_type, text = self.work_queue.get()
                    
                    if msg_type == "CONTINUE":
                        continuation_prompt = "..."
                        self._get_streaming_completion(continuation_prompt)
                    else:
                        # Regular user message
                        self._get_streaming_completion(text)
                        

            except Exception as e:
                print(f"[BUNNY ERROR] Error processing queue: {str(e)}")
                
            time.sleep(0.1)
    
    def _get_streaming_completion(self, user_text):
        try:
            self.chat_history.add_user_message(user_text)

            memory_context = None
            if self.memory_manager:
                memory_context = self.memory_manager.get_memory_context(
                    self.default_user_id, user_text)
            
            # If we have relevant memories, add them as system message
            if memory_context:
                self.chat_history.add_system_message(memory_context)
            
            self.chat = lms.Chat.from_history(self.chat_history.get_history())
            
            # Generate the assistant's response
            full_response = ""
            prediction_stream = self.model.respond_stream(self.chat)
            
            for fragment in prediction_stream:
                full_response += fragment.content
                if self.on_stream_fragment:
                    self.on_stream_fragment(fragment.content)
            
            self.chat_history.add_assistant_message(full_response)

            # Process the conversation for memory extraction
            if self.memory_manager and user_text:
                if self.profile_manager:
                    user_id = self.default_user_id
                
                self.memory_manager.process_conversation(user_id, user_text, full_response)
            
            # Log the assistant's response after it's complete
            if self.chat_logger and full_response:
                self.chat_logger.append_to_log("assistant", full_response)
            
            if self.on_completion and full_response:
                self.on_completion(full_response)
            
            if self.tts and full_response:
                self.tts.add_to_queue(full_response)
            
            print(f"[BUNNY FINAL] {full_response}")
            
            return full_response
                
        except Exception as e:
            print(f"\n[BUNNY ERROR] Error getting completion: {str(e)}")
            return None