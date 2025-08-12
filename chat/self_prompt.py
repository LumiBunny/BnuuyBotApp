import random
import threading
import time

class ConversationPrompter:
    def __init__(self, bunny_completions, min_seconds=5, max_seconds=30, tts_engine=None):
        self.bunny = bunny_completions
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self.is_running = False  # Start with timer inactive
        self.timer_thread = None
        self.last_interaction_time = time.time()
        self.timer_active = False  # Start with timer inactive
        self.tts_engine = tts_engine
        
    def on_empty_transcription(self):
        self.timer_active = True
        elapsed = time.time() - self.last_interaction_time
        remaining = max(0, self.next_prompt_time - elapsed)
        
        print(f"\n🔄 Timer RESUMED - Next prompt in {remaining:.2f}s")
    
    def on_valid_transcription(self):
        self.timer_active = False
        print("Timer stopped - valid transcription received")
    
    def on_tts_finished(self):
        if not self.is_running:
            return  # Don't start any timers if the timer is not running
            
        self.timer_active = True
        self.last_interaction_time = time.time()
        next_prompt_time = random.uniform(self.min_seconds, self.max_seconds)
        self.next_prompt_time = next_prompt_time  # Store for reference
        
        # Don't create a new timer, just update the existing one's timing
        print(f"\n⏱️ New timer started - TTS playback complete. Next prompt in {next_prompt_time:.2f}s")
          
    def on_valid_transcription(self):
        self.timer_active = False
        print("\n⏸️ Timer STOPPED - Valid transcription received")
    
    def start(self):
        if self.is_running:
            print("Prompter already running")
            return
        
        # Check if TTS is playing
        if self.tts_engine and hasattr(self.tts_engine, 'is_playing') and self.tts_engine.is_playing:
            print("Cannot start timer while TTS is playing")
            return
        
        self.is_running = True
        self.timer_active = True
        self.last_interaction_time = time.time()
        self.next_prompt_time = random.uniform(self.min_seconds, self.max_seconds)
        print(f"Conversation prompter started. First prompt in {self.next_prompt_time:.2f}s if no interaction")
        
        # Only start a new thread if no thread exists or the existing one isn't alive
        if not self.timer_thread or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._prompt_loop)
            self.timer_thread.daemon = True
            self.timer_thread.start()
        else:
            print("Timer thread already running, not starting a new one")
    
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
        self.timer_active = False
        print("Timer paused due to voice activity")

    def on_voice_activity_ended(self):
        self.is_voice_active = False
        self.last_interaction_time = time.time()
    
    def _prompt_loop(self):
        if not hasattr(self, 'next_prompt_time'):
            self.next_prompt_time = random.uniform(self.min_seconds, self.max_seconds)
        
        while self.is_running:
            if self.timer_active:
                current_time = time.time()
                elapsed = current_time - self.last_interaction_time
                
                if elapsed >= self.next_prompt_time:
                    self._send_continuation_prompt()
                    self.last_interaction_time = current_time
                    self.next_prompt_time = random.uniform(self.min_seconds, self.max_seconds)
                    print(f"Next prompt will be in {self.next_prompt_time:.2f}s if no interaction")
            
            time.sleep(0.1)
    
    def _send_continuation_prompt(self):
        continuation_prompts = [
            "[continue]", "[thinking]", "[AI continues]", "[self-talk]"
        ]
        chosen_prompt = random.choice(continuation_prompts)
        
        print(f"[TIMER DONE: AUTO CONTINUATION REQUEST: {chosen_prompt}]")
        self.bunny.add_to_queue(chosen_prompt)