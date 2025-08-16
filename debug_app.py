#!/usr/bin/env python3
"""
Debug version of app.py to identify Flask initialization errors
"""

import traceback
import sys

def debug_imports():
    """Test imports step by step to identify the problematic module"""
    try:
        print("Testing Flask imports...")
        from flask import Flask, render_template, jsonify, request, redirect, url_for
        from flask_socketio import SocketIO, emit, join_room, leave_room
        print("✓ Flask imports successful")
        
        print("Testing services.audio imports...")
        from services.audio import SpeechToText, TTSEngine
        print("✓ Audio services imports successful")
        
        print("Testing core.chat imports...")
        from core.chat import BunnyChat, ChatHistory
        print("✓ Core chat imports successful")
        
        print("Testing component initialization...")
        
        # Test BunnyChat initialization
        print("Initializing BunnyChat...")
        bunny = BunnyChat()
        print("✓ BunnyChat initialized successfully")
        
        # Test TTSEngine initialization
        print("Initializing TTSEngine...")
        tts = TTSEngine(voice="en-US-AnaNeural", speed=1.15)
        print("✓ TTSEngine initialized successfully")
        
        # Test SpeechToText initialization
        print("Initializing SpeechToText...")
        stt = SpeechToText(
            model_size="small", 
            device="cuda", 
            compute_type="float16",
            vad_aggressiveness=1,
            silence_threshold=0.8,
            streaming_interval=0.5
        )
        print("✓ SpeechToText initialized successfully")
        
        print("\n🎉 ALL COMPONENTS INITIALIZED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR DURING INITIALIZATION:")
        print(f"Error: {e}")
        print(f"Error Type: {type(e).__name__}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_imports()
    if not success:
        print("\n🔍 This error is likely causing your Flask internal server error.")
        sys.exit(1)
    else:
        print("\n✅ No initialization errors found. The Flask error might be elsewhere.")
