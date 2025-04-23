import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import webrtcvad
import queue
import threading
import struct
import time

class SpeechToText:
    def __init__(self,
                 model_size="small",
                 device="cuda",
                 compute_type="float16",
                 streaming_interval=0.3,
                 vad_aggressiveness=2,
                 silence_threshold=1.0,
                 frame_duration_ms=30,
                 padding_duration_ms=300,
                 language="en",
                 prompter=None
                 ):
        self.model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type,
            local_files_only=False
        )
        
        self.sample_rate = 16000
        self.vad_frame_ms = 30
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.language = language
        self.prompter = None
        if prompter:
            self.set_prompter(prompter)
        
        self.audio_queue = queue.Queue()
        
        self.is_speaking = False
        self.speech_buffer = []
        self.silence_frames = 0
        self.current_transcript = ""
        self.last_update_time = 0
        self.streaming_interval = streaming_interval
        self.silence_threshold = silence_threshold
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        
        self.is_running = False
        self.processing_thread = None
        self.stream = None
        
        self.on_interim_result = None
        self.on_final_result = None

    def is_speech(self, frame):
        amplitude = np.max(np.abs(frame))
        if amplitude < 0.03:
            return False
            
        pcm = struct.pack("h" * len(frame), 
                         *[int(s * 32768) for s in frame])
        return self.vad.is_speech(pcm, self.sample_rate)
    
    def filter_transcripts_by_confidence(self, text, audio_duration, confidence_threshold=0.6, max_chunk_duration=10.0):
        print("\n==== ENTERING filter_transcripts_by_confidence ====\n")
        
        if audio_duration < 0.75:
            required_confidence = max(0.8, confidence_threshold)
        else:
            required_confidence = confidence_threshold
        
        audio_data = self.speech_buffer_to_audio()
        
        samples_per_second = self.sample_rate
        max_samples = int(max_chunk_duration * samples_per_second)
        
        if len(audio_data) > max_samples:
            print(f"Audio too long ({len(audio_data)/samples_per_second:.2f}s), processing only last {max_chunk_duration}s")
            audio_data = audio_data[-max_samples:]
        
        segments = self.model.transcribe(
            audio_data,
            beam_size=2,
            language=self.language,
            vad_filter=False,
            word_timestamps=True
        )
        
        segments_list = list(segments)
        if not segments_list:
            print("No segments found in transcription")
            return ""
        
        avg_confidence = sum(segment.avg_logprob for segment in segments_list) / len(segments_list)
        normalized_confidence = min(1.0, max(0.0, (avg_confidence + 4) / 4))  # Normalize from log prob
        
        print(f"\nDEBUG: Transcript confidence: {normalized_confidence:.2f} - '{text}'\n")
        
        if normalized_confidence >= required_confidence:
            return text
        else:
            print(f"Rejected transcript (confidence: {normalized_confidence:.2f} < {required_confidence:.2f})")
            return ""
    
    def speech_buffer_to_audio(self):
        if not self.speech_buffer:
            return np.array([])
        return np.concatenate(self.speech_buffer)

    def default_display(self, text, is_final=False):
        if is_final:
            print(f"Final: {text}")

    def process_audio_queue(self):
        print("Listening for speech... (Press Ctrl+C to stop)")
        
        try:
            while self.is_running:
                if not self.audio_queue.empty():
                    chunk = self.audio_queue.get()
                    
                    has_speech = self.is_speech(chunk)
                    
                    if has_speech:
                        if not self.is_speaking:
                            self.is_speaking = True
                            print("\nSpeech detected...")
                            self.last_update_time = time.time()
                            if hasattr(self, 'on_voice_activity_started') and self.on_voice_activity_started:
                                self.on_voice_activity_started()
                        
                        self.silence_frames = 0
                        self.speech_buffer.append(chunk)
                        
                        current_time = time.time()
                        buffer_duration = len(self.speech_buffer) * (self.vad_frame_ms / 1000)
                        
                        if current_time - self.last_update_time >= self.streaming_interval and buffer_duration >= 0.6:
                            audio_data = np.concatenate(self.speech_buffer)
                            
                            segments, _ = self.model.transcribe(
                                audio_data, 
                                beam_size=5,
                                language=self.language,
                                vad_filter=False
                            )
                            
                            interim_text = "".join(segment.text for segment in segments).strip()
                            
                            # Fixed condition: Check if text is valid
                            if interim_text and "ლლლ" not in interim_text:
                                if self.on_interim_result:
                                    self.on_interim_result(interim_text)
                                else:
                                    self.default_display(interim_text)
                                
                            self.last_update_time = current_time
                            
                    else:
                        if self.is_speaking:
                            self.silence_frames += 1
                            
                            if self.silence_frames >= 50:
                                self.is_speaking = False
                                
                                if len(self.speech_buffer) > 0:
                                    audio_data = np.concatenate(self.speech_buffer)
                                    
                                    segments, _ = self.model.transcribe(
                                        audio_data,
                                        beam_size=5,
                                        language=self.language
                                    )
                                    
                                    final_text = "".join(segment.text for segment in segments).strip()
                                    
                                    # Fixed condition: Check if text is valid
                                    if final_text and "ლლლ" not in final_text:
                                        if self.on_final_result:
                                            self.on_final_result(final_text)
                                        else:
                                            self.default_display(final_text, is_final=True)
                                
                                self.speech_buffer = []
                                
                                if hasattr(self, 'on_voice_activity_ended') and self.on_voice_activity_ended:
                                    self.on_voice_activity_ended()
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Error in audio processing: {str(e)}")

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Status: {status}")
        
        self.audio_queue.put(indata[:, 0].copy())

    def start(self):
        if self.is_running:
            print("Already running")
            return
        
        self.is_running = True
        
        self.processing_thread = threading.Thread(target=self.process_audio_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=int(self.vad_frame_ms * self.sample_rate / 1000)
        )
        self.stream.start()
        
        print("Transcription started")

    def stop(self):
        if not self.is_running:
            print("Not running")
            return
        
        self.is_running = False
        
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)
        
        print("Transcription stopped")