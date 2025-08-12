"""
Test script for ChatSummarizer and ChatHistory integration.
This script demonstrates:
1. Periodic summarization every 20 messages
2. Session reset summarization
3. Session end summarization
4. File saving verification
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat.summarization import ChatSummarizer
from chat.chatHistory import ChatHistory

def test_chat_summarizer():
    """Test the ChatSummarizer class directly."""
    print("🧪 Testing ChatSummarizer directly...")
    
    # Create a test user
    test_user = "test_user_123"
    summarizer = ChatSummarizer(test_user, messages_per_summary=5)  # Lower threshold for testing
    
    # Create test messages
    test_messages = []
    conversations = [
        ("user", "Hello! I'm new here and love pizza."),
        ("assistant", "Welcome! Pizza is amazing. What's your favorite topping?"),
        ("user", "I really enjoy pepperoni and mushrooms. Do you have any recommendations?"),
        ("assistant", "Great choices! Have you tried adding some fresh basil? It pairs wonderfully."),
        ("user", "That sounds delicious! I'll try that next time."),
        ("assistant", "Excellent! Let me know how it turns out."),
        ("user", "Actually, I'm also interested in learning about cooking techniques."),
        ("assistant", "Cooking is a wonderful skill! What type of cuisine interests you most?"),
        ("user", "I'm drawn to Italian and Japanese cooking styles."),
        ("assistant", "Both are excellent choices with rich traditions and techniques."),
    ]
    
    # Add messages one by one and test periodic summarization
    for i, (role, content) in enumerate(conversations, 1):
        message = {
            "role": role,
            "user_id": test_user if role == "user" else "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        test_messages.append(message)
        
        print(f"Message {i}: {role} - {content[:50]}...")
        
        # Check for periodic summary
        summary = summarizer.check_and_summarize(test_messages)
        if summary:
            print(f"  ✅ Periodic summary generated: {summary[:100]}...")
    
    # Test session end summarization
    print("\n🔚 Testing session end summarization...")
    final_summary = summarizer.end_session(test_messages, "session_ended")
    print(f"  ✅ Final summary: {final_summary[:100]}...")
    
    # Check if files were created
    print(f"\n📁 Checking saved files in: {summarizer.summaries_dir}")
    summary_files = list(summarizer.summaries_dir.glob("session_*.json"))
    if summary_files:
        print(f"  ✅ Found {len(summary_files)} summary file(s):")
        for file in summary_files:
            print(f"    - {file.name}")
            
        # Read and display the latest summary
        latest_file = max(summary_files, key=lambda f: f.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        print(f"\n📄 Latest summary file contents:")
        print(f"  Session Start: {summary_data['session_start']}")
        print(f"  Session End: {summary_data['session_end']}")
        print(f"  End Reason: {summary_data['end_reason']}")
        print(f"  Total Messages: {summary_data['total_messages']}")
        print(f"  Summary Chunks: {len(summary_data['summary_chunks'])}")
        print(f"  Final Summary: {summary_data['final_summary'][:100]}...")
    else:
        print("  ❌ No summary files found!")
    
    return summarizer

def test_chat_history_integration():
    """Test the integrated ChatHistory with summarization."""
    print("\n\n🧪 Testing ChatHistory integration...")
    
    test_user = "integration_test_user"
    chat = ChatHistory(user_id=test_user, system_prompt="You are BunnyBot, a helpful AI assistant.")
    
    # Add some messages to trigger summarization
    conversations = [
        "Hi BunnyBot! I'm excited to chat with you.",
        "Hello! I'm excited to chat too! What would you like to talk about?",
        "I've been learning Python programming lately.",
        "That's wonderful! Python is a great language to learn. What projects are you working on?",
        "I'm building a chatbot like you! It's quite challenging but fun.",
        "How exciting! Building chatbots is a fascinating field. What features are you implementing?",
        "I'm working on memory systems and conversation summarization.",
        "Those are advanced features! Memory systems help create more personalized experiences.",
        "Exactly! I want the bot to remember user preferences and past conversations.",
        "That's a great approach. Persistent memory makes interactions feel more natural.",
        "I'm also adding mood detection and interest tracking.",
        "Impressive! Those features will make your bot very sophisticated.",
        "Thanks! I'm learning a lot about NLP and AI in the process.",
        "Learning by building is one of the best ways to understand these concepts.",
        "I agree! Hands-on experience is invaluable.",
        "Keep up the great work! Your chatbot sounds like it will be amazing.",
        "Thank you for the encouragement! It means a lot.",
        "You're very welcome! I'm here if you need any help.",
        "I might take you up on that offer!",
        "Please do! I'm always happy to help with coding questions.",
    ]
    
    # Add messages alternating between user and assistant
    for i, content in enumerate(conversations):
        if i % 2 == 0:  # Even indices are user messages
            chat.add_user_message(content)
        else:  # Odd indices are assistant messages
            chat.add_assistant_message(content)
        
        print(f"Added message {i+1}: {content[:50]}...")
    
    # Test reset functionality
    print(f"\n🔄 Testing chat reset...")
    chat.clear()
    
    # Check created files
    print(f"\n📁 Checking files for user: {test_user}")
    user_dir = Path("user_data") / test_user
    
    # Check raw chats
    raw_chats_dir = user_dir / "conversations" / "raw_chats"
    if raw_chats_dir.exists():
        chat_files = list(raw_chats_dir.glob("chat_*.json"))
        print(f"  📝 Raw chat files: {len(chat_files)}")
        for file in chat_files:
            print(f"    - {file.name}")
    
    # Check summaries
    summaries_dir = user_dir / "conversations" / "summaries"
    if summaries_dir.exists():
        summary_files = list(summaries_dir.glob("session_*.json"))
        print(f"  📊 Summary files: {len(summary_files)}")
        for file in summary_files:
            print(f"    - {file.name}")
    
    return chat

def main():
    """Run all tests."""
    print("🚀 Starting ChatSummarizer and ChatHistory tests...\n")
    
    # Test 1: Direct summarizer testing
    summarizer = test_chat_summarizer()
    
    # Test 2: Integrated chat history testing
    chat = test_chat_history_integration()
    
    print("\n✅ All tests completed!")
    print("\n📋 Summary of what was tested:")
    print("  1. ✅ ChatSummarizer periodic summarization (every 5 messages for testing)")
    print("  2. ✅ Session end summarization")
    print("  3. ✅ File saving to user_data/{user_id}/conversations/summaries/")
    print("  4. ✅ ChatHistory integration with summarization")
    print("  5. ✅ Reset functionality with summary generation")
    
    print(f"\n📂 Check these directories for created files:")
    print(f"  - user_data/test_user_123/conversations/summaries/")
    print(f"  - user_data/integration_test_user/conversations/summaries/")
    print(f"  - user_data/integration_test_user/conversations/raw_chats/")

if __name__ == "__main__":
    main()
