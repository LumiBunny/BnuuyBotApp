import requests
import io
import tempfile
from mutagen.mp3 import MP3
import os
import pygame
import numpy as np
import librosa
import sounddevice as sd
import threading
import re
import queue
import time
import random

class TTSEngine:
    def __init__(self, voice="en-US-AnaNeural", speed=1.15, api_url="http://localhost:5050/v1/audio/speech"):
        self.voice = voice
        self.speed = speed
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.is_speaking = False
        self.was_speaking = False
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer your_api_key_here"  # Replace if needed
        }
        
        pygame.mixer.init()
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        
        self.end_event_thread = threading.Thread(target=self._monitor_playback_end)
        self.end_event_thread.daemon = True
        self.end_event_thread.start()
        
        self.current_thread = None

    def start(self):
        if self.is_running:
            print("TTS Engine already running")
            return
        
        self.is_running = True
        print("TTS Engine started")
        
        # Start the thread that processes the audio queue
        if not hasattr(self, 'queue_thread') or not self.queue_thread.is_alive():
            self.queue_thread = threading.Thread(target=self.process_audio_queue)
            self.queue_thread.daemon = True
            self.queue_thread.start()

    def set_prompter(self, prompter):
        self.prompter = prompter

    def speak_with_callback(self, text, callback=None):
        if not text:
            return
            
        cleaned_text = self.clean_text_for_speech(text)
        if not cleaned_text:
            return
        
        if hasattr(self, 'on_playback_started') and callable(self.on_playback_started):
            self.on_playback_started()
            
        data = {
            "input": cleaned_text,
            "voice": self.voice,
            "response_format": "mp3",
            "speed": self.speed
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.write(response.content)
                temp_file.close()
                
                audio = MP3(temp_file.name)
                duration = audio.info.length
                print(f"\n🔊 Starting audio playback (duration: {duration:.2f}s) at {time.strftime('%H:%M:%S')}")
                
                audio_file = io.BytesIO(response.content)
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                os.unlink(temp_file.name)
                
                timer_already_running = False
                if hasattr(self, '_current_timer') and self._current_timer is not None:
                    if self._current_timer.is_alive():
                        timer_already_running = True
                    else:
                        self._current_timer = None
                
                if callback:
                    # Modified callback wrapper to ensure on_playback_finished is called
                    def wrapped_callback():
                        if hasattr(self, 'on_playback_finished') and callable(self.on_playback_finished):
                            self.on_playback_finished()
                        callback()
                    
                    timer_thread = threading.Timer(duration + 0.5, wrapped_callback)
                    timer_thread.daemon = True
                    timer_thread.start()
                    self._current_timer = timer_thread
                    print(f"Timer will trigger callback at {time.strftime('%H:%M:%S', time.localtime(time.time() + duration + 0.5))}")
                elif hasattr(self, 'prompter') and self.prompter and not timer_already_running:
                    # Modified prompter callback to ensure on_playback_finished is called
                    def wrapped_prompter_callback():
                        if hasattr(self, 'on_playback_finished') and callable(self.on_playback_finished):
                            self.on_playback_finished()
                        self.prompter.on_tts_finished()
                    
                    timer_thread = threading.Timer(duration + 0.5, wrapped_prompter_callback)
                    timer_thread.daemon = True
                    timer_thread.start()
                    self._current_timer = timer_thread
                    print(f"Timer will trigger prompter callback at {time.strftime('%H:%M:%S', time.localtime(time.time() + duration + 0.5))}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error in TTS: {str(e)}")

    def process_audio_queue(self):
        while self.is_running:
            try:
                if not pygame.mixer.music.get_busy() and not self.audio_queue.empty():
                    text = self.audio_queue.get()
                    self.is_speaking = True
                    
                    cleaned_text = self.clean_text_for_speech(text)
                    if cleaned_text:
                        self.speak_with_callback(cleaned_text)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in audio processing: {str(e)}")

    # In tts_module.py
    def audio_finished_callback(self):
        self.is_speaking = False
        print("Audio playback finished")
        
        if hasattr(self, 'on_playback_finished') and callable(self.on_playback_finished):
            print("DEBUG: Calling on_playback_finished callback")
            self.on_playback_finished()
        else:
            print("DEBUG: No on_playback_finished callback available")

    def _monitor_playback_end(self):
        while self.is_running:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    self.is_speaking = False
                    print("Audio playback finished")
            time.sleep(0.1)
    
    def add_to_queue(self, text):
        if text:
            self.audio_queue.put(text)

    def clean_text_for_speech(self, text):
        if not text:
            return text
            
        cleaned_text = re.sub(r'\*[^*]*\*', '', text)
        
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
        
    def speak(self, text):
        self.speak_with_callback(text)
                
    def _speak_thread(self, text, pitch_factor):
        data = {
            "input": text,
            "voice": self.voice,
            "response_format": "mp3",
            "speed": self.speed
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                audio_file = io.BytesIO(response.content)
                
                from mutagen.mp3 import MP3
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.write(response.content)
                temp_file.close()
                
                audio = MP3(temp_file.name)
                duration = audio.info.length
                print(f"\n🔊 Starting audio playback (duration: {duration:.2f}s) at {time.strftime('%H:%M:%S')}")
                
                self.audio_end_time = time.time() + duration + 0.5  # Add a small buffer
                
                if pitch_factor != 1.0 and pitch_factor > 0:
                    y, sr = librosa.load(temp_file.name, sr=24000)
                    n_steps = 12 * np.log2(pitch_factor)
                    y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps)
                    sd.play(y_shifted, sr)
                    sd.wait()
                else:
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                
                os.unlink(temp_file.name)
                return True
            else:
                print(f"TTS Error: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"TTS Exception: {str(e)}")
            return False
    
    def stop(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        sd.stop()
        
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(0.1)
            self.current_thread = None

# Simple usage example
if __name__ == "__main__":
    tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
    
    # Basic usage
    print("Testing basic speech...")
    tts.speak("Hello! I'm Bunny, your virtual assistant. I'm here to help you get off your ass you lazy fuck.")