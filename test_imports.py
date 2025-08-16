#!/usr/bin/env python3
"""
Import Test Script for BnuuyBotApp
Tests all module imports to verify refactoring was successful
"""

def test_imports():
    print("Testing BnuuyBotApp imports after refactoring...")
    
    try:
        # Test services imports
        print("✓ Testing services.audio imports...")
        from services.audio import SpeechToText, TTSEngine
        print("  ✓ SpeechToText and TTSEngine imported successfully")
        
        # Test core.chat imports
        print("✓ Testing core.chat imports...")
        from core.chat import BunnyChat, ChatHistory
        print("  ✓ BunnyChat and ChatHistory imported successfully")
        
        # Test core.memory imports
        print("✓ Testing core.memory imports...")
        from core.memory import MemoryManager
        print("  ✓ MemoryManager imported successfully")
        
        # Test core.memory.preferences imports
        print("✓ Testing core.memory.preferences imports...")
        from core.memory.preferences import PreferenceExtractor, PreferenceResult
        print("  ✓ PreferenceExtractor and PreferenceResult imported successfully")
        
        # Test core.memory.interests imports
        print("✓ Testing core.memory.interests imports...")
        from core.memory.interests import InterestTracker
        print("  ✓ InterestTracker imported successfully")
        
        # Test core.memory.mood imports
        print("✓ Testing core.memory.mood imports...")
        from core.memory.mood import IntegratedMoodSystem, HybridMoodDetector, DynamicMoodContext
        print("  ✓ Mood system components imported successfully")
        
        # Test core.thinking imports
        print("✓ Testing core.thinking imports...")
        from core.thinking import InnerDialogue
        print("  ✓ InnerDialogue imported successfully")
        
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("Your refactoring is working correctly!")
        return True
        
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        print("There are still import issues that need to be fixed.")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
