#!/usr/bin/env python3
"""
Simple test to verify memory system is working
"""

from memory.memory_manager import MemoryManager
from preferences.preferences import PreferenceExtractor
from interests.interest_tracker import InterestTracker

def test_memory_system():
    print("🧪 Testing memory system...")
    
    # Initialize components
    memory_manager = MemoryManager()
    preference_extractor = PreferenceExtractor()
    interest_tracker = InterestTracker(memory_manager)
    
    user_id = "lumi"
    test_message = "I love playing Minecraft and cooking pasta"
    
    print(f"📝 Testing with message: '{test_message}'")
    
    # Test 1: Preference extraction and saving
    print("\n1️⃣ Testing preference extraction...")
    try:
        preferences = preference_extractor.extract_preferences(test_message, user_id)
        if preferences:
            memory_manager.save_preferences(user_id, preferences)
            print(f"✅ Saved {len(preferences)} preferences")
        else:
            print("❌ No preferences extracted")
    except Exception as e:
        print(f"❌ Preference test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Interest tracking
    print("\n2️⃣ Testing interest tracking...")
    try:
        interests = interest_tracker.track_conversation_interests(user_id, test_message)
        print(f"✅ Tracked interests: {interests}")
    except Exception as e:
        print(f"❌ Interest tracking failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Memory saving
    print("\n3️⃣ Testing memory saving...")
    try:
        memory_manager.add_memory(
            user_id,
            "User mentioned loving Minecraft and cooking",
            "conversation",
            importance=0.8,
            tags=["gaming", "cooking", "preferences"]
        )
        print("✅ Memory saved successfully")
    except Exception as e:
        print(f"❌ Memory saving failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check if files were created
    print("\n4️⃣ Checking if files were created...")
    import os
    
    files_to_check = [
        "user_data/lumi/profile/preferences.json",
        "user_data/lumi/profile/interests.json", 
        "user_data/lumi/profile/important_memories.json"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} exists ({size} bytes)")
            
            # Show content if small
            if size < 1000:
                with open(file_path, 'r') as f:
                    content = f.read()
                    print(f"   Content: {content[:200]}...")
        else:
            print(f"❌ {file_path} does not exist")

if __name__ == "__main__":
    test_memory_system()
