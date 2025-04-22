import random
import threading
import time

class ConversationPrompter:
    def __init__(self, bunny_completions, min_seconds=5, max_seconds=30, tts_engine=None):
        self.bunny = bunny_completions
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self.is_running = False
        self.timer_thread = None
        self.last_interaction_time = time.time()
        self.tts_engine = tts_engine
        
    def start(self):
        if self.is_running:
            print("Prompter already running")
            return
            
        self.is_running = True
        self.last_interaction_time = time.time()
        self.timer_thread = threading.Thread(target=self._prompt_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        print("Conversation prompter started")
        
    def stop(self):
        if not self.is_running:
            print("Prompter not running")
            return
            
        self.is_running = False
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=2)
        print("Conversation prompter stopped")
    
    def reset_timer(self):
        self.last_interaction_time = time.time()

    def on_voice_activity_started(self):
        self.is_voice_active = True
        self.last_interaction_time = float('inf')

    def on_voice_activity_ended(self):
        self.is_voice_active = False
        self.last_interaction_time = time.time()
    
    def _prompt_loop(self):
        while self.is_running:
            time.sleep(1)
            
            elapsed = time.time() - self.last_interaction_time
            
            if elapsed >= self.min_seconds:
                chance = min(1.0, (elapsed - self.min_seconds) / (self.max_seconds - self.min_seconds))
                
                if random.random() < chance:
                    self._send_continuation_prompt()
                    self.last_interaction_time = time.time()  # Reset timer
    
    def _send_continuation_prompt(self):
        if self.tts_engine and self.tts_engine.is_speaking():
            self.last_interaction_time = time.time()
            return
        
        continuation_prompts = [
            "[continue]", "[thinking]", "[AI continues]", "[self-talk]"
        ]
        chosen_prompt = random.choice(continuation_prompts)
        
        print(f"[AUTO CONTINUATION REQUEST: {chosen_prompt}]")
        self.bunny.add_to_queue(chosen_prompt)