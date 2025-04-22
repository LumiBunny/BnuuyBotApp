import requests
import io
import pygame
import numpy as np
import librosa
import sounddevice as sd
import threading
import re

# I'm using openai-edge-tts from https://github.com/travisvn/openai-edge-tts
class TTSEngine:
    def __init__(self, voice="en-US-AnaNeural", speed=1.15, api_url="http://localhost:5050/v1/audio/speech"):
        self.voice = voice
        self.speed = speed
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer your_api_key_here"  # Replace if needed
        }
        
        pygame.mixer.init()
        
        self.current_thread = None

    def clean_text_for_speech(self, text):
        if not text:
            return text
            
        cleaned_text = re.sub(r'\*[^*]*\*', '', text)
        
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
        
    def speak(self, text, wait=True, pitch_factor=1.0):
        if not text:
            return False
            
        cleaned_text = self.clean_text_for_speech(text)
        if not cleaned_text:
            return False
        
        if not wait:
            self.current_thread = threading.Thread(
                target=self._speak_thread, 
                args=(cleaned_text, pitch_factor)
            )
            self.current_thread.daemon = True
            self.current_thread.start()
            return True
        else:
            return self._speak_thread(cleaned_text, pitch_factor)
    
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
                if pitch_factor != 1.0 and pitch_factor > 0:
                    audio_bytes = io.BytesIO(response.content)
                    y, sr = librosa.load(audio_bytes, sr=24000)
                    
                    n_steps = 12 * np.log2(pitch_factor)
                    y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps)
                    
                    sd.play(y_shifted, sr)
                    sd.wait()
                else:
                    audio_file = io.BytesIO(response.content)
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                
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
            
    def is_speaking(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            return True
        return False

# Simple usage example
if __name__ == "__main__":
    tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
    
    # Basic usage
    print("Testing basic speech...")
    tts.speak("Hello! I'm Bunny, your virtual assistant. I'm here to help you get off your ass you lazy fuck.")