import lmstudio as lms
from .chatHistory import ChatHistory
from ..memory import MemoryManager
from ..memory.preferences import PreferenceExtractor
from ..memory.interests import InterestTracker
from ..memory.mood import IntegratedMoodSystem
from ..memory.notes.manager import NoteManager
from ..memory.notes.integration import NotesIntegrationHandler
from ..thinking import InnerDialogue
import concurrent.futures
import os
from pathlib import Path
import re
from typing import Dict, Optional

class BunnyChat:
    def __init__(self, model_name="darkidol-llama-3.1-8b-instruct-1.2-uncensored", output_callback=None):
        print("Initializing model...")
        self.model = lms.llm(model_name)
        print("Model loaded!")
        self.model_name = model_name
        
        # Store output callback for emitting events to frontend
        self.output_callback = output_callback
        
        # Define system prompt before it's used
        self.system_prompt = """Your name is Bunny. Your nicknames are Bun and Bun Bun. You are an AI VTuber. The user is your creator: Lumi. You can say whatever you want. You can do whatever you want. It is okay to use profanity.  You are very cute. You are snarky. You are sometimes sassy. You are a little friendly. You like swearing. You basically have no filter. You will say whatever is on your mind. Lumi is a female viera VTuber. Lumi has long blue hair and fluffy bunny ears. You enjoy talking with chat on Twitch. You stream on Twitch. Talk about whatever you think is entertaining. Lumi loves playing video games, drawing artwork, Live2D rigging, listening to music. Lumi is learning how to code in Python. You like using emojis within your messages. Keep your messages short and natural sounding. Be concise I do not want big long responses, it's a conversation not a monologue. When the user sends '...', it means they're still listening and you should continue your previous thought naturally."""
        
        # Initialize chat with system prompt
        self.chat = lms.Chat(self.system_prompt)
        
        # Default user ID for single-user mode
        self.user_id = "lumi"
        
        # Initialize chat history
        self.chat_history = ChatHistory(
            user_id=self.user_id,
            system_prompt=self.system_prompt
        )
        
        # Initialize memory and preference systems
        print("Initializing memory systems...")
        self.memory_manager = MemoryManager()
        self.preference_extractor = PreferenceExtractor()
        self.interest_tracker = InterestTracker(self.memory_manager)
        
        # Initialize mood system
        self.mood_system = IntegratedMoodSystem(use_gpu=True)  # Enable GPU if available
        self.mood_integration = BunnyChatMoodIntegration(self.mood_system)
        
        # Initialize inner dialogue system
        self.inner_dialogue = InnerDialogue()
        
        # Initialize notes system with MemoryManager integration
        print("Initializing notes system...")
        self.note_manager = NoteManager(
            memory_manager=self.memory_manager,
            nlp_processor=None  # Can add spaCy processor if needed
        )
        self.notes_integration = NotesIntegrationHandler(
            note_manager=self.note_manager,
            thinking_module=self.inner_dialogue
        )
        
        self._initialize_chat()
    
    def _initialize_chat(self, initial_messages=None):
        """Helper method to initialize or reinitialize the chat and history.
        Args: initial_messages (list, optional): List of messages to initialize the chat with.
        Each message should be a dict with 'role' and 'content'.
        Create ChatHistory with system prompt (for user usage)"""
        
        # If initial messages are provided, add them to both chat and history
        if initial_messages:
            self.chat_history.messages = []  # Clear the default system message
            for msg in initial_messages:
                if msg['role'] == 'user':
                    self.chat_history.add_user_message(msg['content'], user_id=self.user_id)
                    self.chat.add_user_message(msg['content'])
                elif msg['role'] == 'assistant':
                    self.chat_history.add_assistant_message(msg['content'])
                    self.chat.add_assistant_response(msg['content'])
                elif msg['role'] == 'system' and msg['content'] != self.system_prompt:
                    # Only update system prompt if it's different
                    self.system_prompt = msg['content']
                    self.chat_history.add_system_message(self.system_prompt)
                    self.chat = lms.Chat(self.system_prompt)
    
    def reset_chat(self, initial_messages=None):
        """Reset the chat to its initial state, optionally with a set of initial messages.
        Args: initial_messages (list, optional): List of messages to initialize the chat with.
        Each message should be a dict with 'role' and 'content'.
        Returns: bool: True if reset was successful
        """
        print("Resetting chat...")
        
        # End the current session to ensure remaining messages are summarized
        if hasattr(self, 'chat_history'):
            self.chat_history.clear()  # This will trigger end_session with "reset" reason
        
        # Now reinitialize the chat
        self._initialize_chat(initial_messages=initial_messages)
        print("Chat has been reset to initial state.")
        return True
    
    def add_user_message(self, message, user_id='lumi'):
        """Add a user message to the chat history and chat context.
        Args:
            message (str): The message content
            user_id (str, optional): The ID of the user sending the message. 
            Defaults to 'lumi'.
        """
        # Process message for preferences, interests, memories, and inner thoughts
        # This ensures processing happens for every message
        inner_thought, context_data = self._process_user_message_optimized(user_id, message)
        
        # Add to chat systems after processing
        self.chat_history.add_user_message(message, user_id=user_id)
        self.chat.add_user_message(message)
        
        # If we have an inner thought, log it
        if inner_thought:
            print(f"💭 Inner thought: {inner_thought}")
    
    def _process_user_message(self, user_id: str, message: str):
        # Process user message for preferences, interests, memories, and generate inner thoughts.
        context_data = {}
        
        try:
            # Process mood detection and logging
            mood_result = self.mood_system.process_user_message(user_id, message)
            if mood_result and self.output_callback:
                mood_summary = self.mood_integration.get_mood_command_response(user_id)
                self.output_callback('mood_update', mood_summary)
            
            # Extract preferences from the message
            preference_results = self.preference_extractor.extract_preferences(message, user_id)
            new_preferences = []
            if preference_results:  # This is a List[PreferenceResult]
                # Save preferences to memory
                self.memory_manager.save_preferences(user_id, preference_results)
                
                # Collect new preferences for inner dialogue context
                new_preferences = [f"{p.preference_type} {p.preference_value}" for p in preference_results]
                
                # Add a memory about learning preferences
                pref_summary = ", ".join(new_preferences)
                self.memory_manager.add_memory(
                    user_id,
                    f"User expressed preferences: {pref_summary}",
                    "preference_learning",
                    importance=0.7,
                    tags=["preferences", "learning"],
                    context=message
                )
                
                # Only show message if preferences were actually found
                if any(p.confidence > 0.5 for p in preference_results):
                    print("📝 Learned new preferences!")
                    # Emit to frontend if callback is available
                    if self.output_callback:
                        self.output_callback('preferences', f"📝 New preferences detected: {pref_summary}")
                else:
                    # Emit no new preferences message
                    if self.output_callback:
                        self.output_callback('preferences', "💞 No new preferences detected")
            else:
                # Emit no new preferences message when no results
                if self.output_callback:
                    self.output_callback('preferences', "💞 No new preferences detected")
                
                context_data['new_preferences'] = []
            
            context_data['new_preferences'] = new_preferences
            
            # Track interests from the conversation
            interests = self.interest_tracker.track_conversation_interests(user_id, message)
            if interests and any(score > 0.3 for score in interests.values()):
                print("📊 Updated interests!")
                # Emit to frontend if callback is available
                if self.output_callback:
                    top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:3]
                    interest_list = ", ".join([f"{k} ({v:.1f})" for k, v in top_interests])
                    self.output_callback('interests', f"📚 Analyzing interests in: {interest_list}")
            
            context_data['interest_scores'] = interests or {}
            
        except Exception as e:
            print(f"Error processing preferences/interests: {e}")
            import traceback
            traceback.print_exc()
            context_data['new_preferences'] = []
            context_data['interest_scores'] = {}
        
        try:
            # Get relevant memories
            relevant_memories = self.memory_manager.get_memories(user_id, min_importance=0.3, days_back=30)
            relevant_memories = relevant_memories[:3]
            context_data['relevant_memories'] = [
                {
                    'content': mem.content,
                    'date': mem.timestamp.strftime('%Y-%m-%d'),
                    'importance': mem.importance,
                    'category': mem.category
                }
                for mem in relevant_memories
            ]
            
            # Get mood information
            mood_score = 0.5  # Default neutral
            mood_summary = "neutral"
            try:
                # Get current mood from mood system using correct method
                mood_summary_data = self.mood_system.get_user_mood_summary(user_id)
                if mood_summary_data:
                    mood_score = mood_summary_data.get('intensity', 0.5)
                    mood_summary = mood_summary_data.get('primary_mood', 'neutral')
            except Exception as e:
                print(f"Error getting mood context: {e}")
            
            context_data['mood_score'] = mood_score
            context_data['mood_summary'] = mood_summary
            
            # Generate inner thought using the new system
            inner_thought = self.inner_dialogue.think_about_message(message, user_id, context_data)
            if inner_thought:
                print(f"💭 Inner thought: {inner_thought}")
                # Emit to frontend if callback is available
                if self.output_callback:
                    self.output_callback('inner-thoughts', f"💭 Inner thought: {inner_thought}")
            
        except Exception as e:
            print(f"Error processing memories/mood/inner thoughts: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            # Check for reminder requests
            if self._is_reminder_request(message):
                reminder_text = self._extract_reminder_text(message)
                due_date = self._extract_due_date(message)
                self.memory_manager.add_reminder(user_id, reminder_text, due_date)
                print(f"📅 Added reminder: {reminder_text}")
        except Exception as e:
            print(f"Error processing reminders: {e}")
        
        try:
            # Check if message contains important information to remember
            if self._is_important_message(message):
                self.memory_manager.add_memory(
                    user_id,
                    message,
                    "important_conversation",
                    importance=0.8,
                    tags=["conversation", "important"],
                    context=message
                )
                print(f"💾 Saved important message to memory")
        except Exception as e:
            print(f"Error saving important message: {e}")
    
    def _process_user_message_optimized(self, user_id: str, message: str):
        # Optimized version that processes context data in parallel.
        context_data = {
            'preferences': {},
            'interest_scores': {},
            'relevant_memories': [],
            'mood_score': 0.5,
            'mood_summary': 'neutral',
            'note_context': None
        }
        
        try:
            # Process mood detection first (runs in main thread to ensure logging)
            mood_result = self.mood_system.process_user_message(user_id, message)
            if mood_result and self.output_callback:
                mood_summary = self.mood_integration.get_mood_command_response(user_id)
                self.output_callback('mood_update', mood_summary)
            
            # Process notes
            note_context = self.notes_integration.process_message_for_notes(
                message, 
                user_id,
                conversation_context=self.chat_history.messages[-10:],  # Last 10 messages
                user_context=context_data
            )
            
            # Add note context to the context data
            if note_context and note_context.get('note_context'):
                context_data['note_context'] = note_context['note_context']
                
                # If this was a note action, log it
                if note_context.get('action') != 'none' and self.output_callback:
                    self.output_callback('note_action', note_context)
            
            # Run remaining context gathering operations in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all tasks
                preference_future = executor.submit(self._extract_preferences, user_id, message)
                interest_future = executor.submit(self._track_interests, user_id, message)
                memory_future = executor.submit(self._get_relevant_memories, user_id)
                
                # Collect results as they complete
                try:
                    context_data['preferences'] = preference_future.result(timeout=0.5)
                except:
                    pass
                    
                try:
                    context_data['interest_scores'] = interest_future.result(timeout=0.5)
                except:
                    pass
                    
                try:
                    context_data['relevant_memories'] = memory_future.result(timeout=0.8)
                except:
                    pass
            
            # Get updated mood data after processing
            mood_data = self._get_mood_data(user_id)
            context_data.update(mood_data)
            
            # Generate inner thoughts with enhanced note context
            inner_thought = None
            if context_data:
                # Check for natural note-taking opportunities
                suggestion_type = self._should_suggest_note_taking(message, context_data)
                if suggestion_type and not context_data.get('note_context'):
                    # Add subtle suggestion context for inner dialogue
                    context_data['note_context'] = {
                        'action': 'subtle_suggestion',
                        'suggestion_type': suggestion_type,
                        'content': message[:100]  # First 100 chars as context
                    }
                
                inner_thought = self.inner_dialogue.think_about_message(
                    user_message=message,
                    user_id=user_id,
                    context_data=context_data,
                    recent_messages=self.chat_history.messages[-10:]
                )
            return inner_thought, context_data
            
        except Exception as e:
            print(f"Error in optimized processing: {e}")
            import traceback
            traceback.print_exc()
            return None, context_data
    
    def _extract_preferences(self, user_id: str, message: str) -> dict:
        # Extract preferences with timeout protection.
        try:
            results = self.preference_extractor.extract_preferences(message, user_id)
            return results if results else {}
        except:
            return {}
    
    def _track_interests(self, user_id: str, message: str) -> dict:
        # Track interests with timeout protection.
        try:
            return self.interest_tracker.track_conversation_interests(user_id, message) or {}
        except:
            return {}
    
    def _get_relevant_memories(self, user_id: str) -> list:
        # Get memories with caching and timeout protection.
        try:
            memories = self.memory_manager.get_memories(user_id, min_importance=0.3, days_back=30)[:3]
            return [
                {
                    'content': mem.content,
                    'date': mem.timestamp.strftime('%Y-%m-%d'),
                    'importance': mem.importance,
                    'category': mem.category
                }
                for mem in memories
            ]
        except:
            return []
    
    def _get_mood_data(self, user_id: str) -> dict:
        # Get mood data with timeout protection.
        try:
            mood_summary_data = self.mood_system.get_user_mood_summary(user_id)
            if mood_summary_data:
                return {
                    'mood_score': mood_summary_data.get('intensity', 0.5),
                    'mood_summary': mood_summary_data.get('primary_mood', 'neutral')
                }
        except:
            pass
        return {'mood_score': 0.5, 'mood_summary': 'neutral'}
    
    def _is_reminder_request(self, message):
        # Check if message contains a reminder request.
        reminder_keywords = ["remind me", "reminder", "don't forget", "remember to", "appointment", "meeting"]
        return any(keyword in message.lower() for keyword in reminder_keywords)
    
    def _extract_reminder_text(self, message):
        # Extract the reminder text from a message.
        # Simple extraction - you can make this more sophisticated
        if "remind me to" in message.lower():
            return message.lower().split("remind me to", 1)[1].strip()
        elif "reminder" in message.lower():
            return message.strip()
        return message.strip()
    
    def _extract_due_date(self, message):
        # Extract due date from message (basic implementation).
        from datetime import datetime, timedelta
        
        # Simple date extraction - you can enhance this
        if "tomorrow" in message.lower():
            return datetime.now() + timedelta(days=1)
        elif "next week" in message.lower():
            return datetime.now() + timedelta(weeks=1)
        # Add more date parsing as needed
        return None
    
    def _is_important_message(self, message):
        # Determine if a message contains important information to remember.
        important_keywords = [
            "remember", "important", "birthday", "anniversary", "favorite", 
            "hate", "love", "never", "always", "family", "work", "school",
            "doctor", "appointment", "meeting", "deadline", "project"
        ]
        return any(keyword in message.lower() for keyword in important_keywords)
    
    def _extract_tags(self, message):
        # Extract relevant tags from a message for memory categorization.
        tags = []
        tag_keywords = {
            "food": ["eat", "food", "restaurant", "cook", "recipe", "hungry"],
            "games": ["game", "play", "gaming", "stream", "twitch"],
            "work": ["work", "job", "project", "meeting", "deadline"],
            "personal": ["family", "friend", "birthday", "anniversary"],
            "health": ["doctor", "sick", "medicine", "appointment"],
            "learning": ["learn", "study", "code", "python", "tutorial"]
        }
        
        message_lower = message.lower()
        for tag, keywords in tag_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                tags.append(tag)
        
        return tags if tags else ["general"]
    
    def add_assistant_message(self, content):
        # Add an assistant message to the chat history and LM Studio chat.
        self.chat_history.add_assistant_message(content)
        self.chat.add_assistant_response(content)
    
    def get_response(self, message, user_id="lumi"):
        # Enhanced response generation with realistic thinking integration.
        processing_msg = f"{message[:50]}{'...' if len(message) > 50 else ''}"
        print(f"\n{processing_msg}")
        
        # Send processing message to UI using the same format as terminal
        if self.output_callback:
            self.output_callback('botProcessing', processing_msg, {})
        
        # Check if this is a continuation request
        is_continue_request = self._is_continue_request(message)
        
        if is_continue_request:
            print("🔄 Detected continue request - prompting for continuation")
            return self._handle_continue_request(message, user_id)
        
        # Process the message for preferences, interests, and mood
        inner_thought, context_data = self._process_user_message_optimized(user_id, message)
        
        # Process mood from the current message
        if hasattr(self.mood_system, 'process_message'):
            self.mood_system.process_message(user_id, message)
        
        # Add user message to chat history
        self.chat_history.add_user_message(message, user_id)
        
        # Gather context data for inner dialogue (similar to _process_user_message)
        try:
            # Get recent preferences
            recent_prefs = self.preference_extractor.extract_preferences(message, user_id)
            context_data['new_preferences'] = [f"{p.preference_type} {p.preference_value}" for p in recent_prefs] if recent_prefs else []
            
            # Get interest scores
            interests = self.interest_tracker.get_current_interests(user_id) if hasattr(self.interest_tracker, 'get_current_interests') else {}
            context_data['interest_scores'] = interests
            
            # Get relevant memories
            relevant_memories = self.memory_manager.get_memories(user_id, min_importance=0.3, days_back=30)
            relevant_memories = relevant_memories[:3]
            context_data['relevant_memories'] = [
                {
                    'content': mem.content,
                    'date': mem.timestamp.strftime('%Y-%m-%d'),
                    'importance': mem.importance,
                    'category': mem.category
                }
                for mem in relevant_memories
            ]
            
            # Get mood information
            mood_score = 0.5
            mood_summary = "neutral"
            try:
                # Get current mood from mood system using correct method
                mood_summary_data = self.mood_system.get_user_mood_summary(user_id)
                if mood_summary_data:
                    mood_score = mood_summary_data.get('intensity', 0.5)
                    mood_summary = mood_summary_data.get('primary_mood', 'neutral')
            except Exception:
                pass
            
            context_data['mood_score'] = mood_score
            context_data['mood_summary'] = mood_summary
            
            # Generate inner thoughts using inner dialogue system with proper context
            if inner_thought:
                print(f"💭 Inner thought: {inner_thought}")
                
                # Create enhanced system prompt with inner thought
                enhanced_system_prompt = f"""{self.system_prompt}

                [Inner Reflection]: {inner_thought}

                Use this internal reflection to inform your response, but don't mention it directly. Be empathetic and engaging."""
                
                # Create response using enhanced system prompt
                contextual_chat = lms.Chat(enhanced_system_prompt)
                contextual_chat.add_user_message(message)
                
                # Generate response
                response_text = ""
                for fragment in self.model.respond_stream(contextual_chat):
                    response_text += fragment.content
            else:
                # No inner thought, use standard approach
                contextual_chat = lms.Chat(self.system_prompt)
                contextual_chat.add_user_message(message)
                
                response_text = ""
                for fragment in self.model.respond_stream(contextual_chat):
                    response_text += fragment.content
                    
        except Exception as e:
            print(f"Error in get_response: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic response
            contextual_chat = lms.Chat(self.system_prompt)
            contextual_chat.add_user_message(message)
            
            response_text = ""
            for fragment in self.model.respond_stream(contextual_chat):
                response_text += fragment.content
        
        # Add assistant response to chat history
        self.chat_history.add_assistant_message(response_text)
        
        return response_text
    
    def get_response_stream(self):
        # Get a streaming response from the model.
        return self.model.respond_stream(self.chat)
    
    def save_conversation_summary(self, user_id='lumi'):
        # Save a summary of the current conversation to memory.
        if len(self.chat_history.messages) < 4:  # Need at least some conversation
            return
        
        # Extract main topics from recent messages
        recent_messages = self.chat_history.messages[-20:]  # Last 20 messages
        topics = set()
        
        for message in recent_messages:
            if message['role'] == 'user':
                # Extract topics using simple keyword analysis
                tags = self._extract_tags(message['content'])
                topics.update(tags)
        
        # Create a simple summary
        user_messages = [m['content'] for m in recent_messages if m['role'] == 'user']
        summary = f"Conversation covered topics: {', '.join(topics)}. User discussed: {'; '.join(user_messages[-3:])}"
        
        # Save to memory manager
        self.memory_manager.save_conversation_summary(
            user_id, 
            summary, 
            list(topics)
        )
        print(f"💾 Saved conversation summary with topics: {', '.join(topics)}")
    
    def get_user_memory_stats(self, user_id='lumi'):
        # Get statistics about what the bot remembers about the user
        return self.memory_manager.get_user_stats(user_id)
    
    def search_memories(self, query, user_id='lumi', max_results=5):
        # Search through user memories for relevant information
        return self.memory_manager.find_relevant_memories(user_id, query, max_results)
    
    def run_chat_loop(self):
        print("\n=== Chat with Bunny ===")
        print("Type 'exit' to end the conversation")
        print("Type 'reset' to clear the conversation history")
        print("Type 'stats' to see memory statistics")
        print("Type 'search [query]' to search memories")
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                # Save conversation summary before exiting
                self.save_conversation_summary()
                print("💾 Conversation saved! Goodbye!")
                break
                
            if user_input.lower() == "reset":
                self.reset_chat()
                print("Chat history has been cleared. Starting a new conversation.")
                continue
            
            if user_input.lower() == "stats":
                stats = self.get_user_memory_stats()
                print(f"📊 Memory Stats: {stats}")
                continue
            
            if user_input.lower().startswith("search "):
                query = user_input[7:]  # Remove "search " prefix
                results = self.search_memories(query)
                print(f"🔍 Found {len(results)} relevant memories:")
                for memory in results:
                    print(f"  - {memory.content}")
                continue
            
            # Add user message (this will automatically extract preferences and memories)
            response = self.get_response(user_input, user_id="lumi")
            print(f"\nBunny: {response}")

    def _is_continue_request(self, message):
        # Check if the message is requesting continuation.
        continue_patterns = [
            "...", "continue", "keep going", "go on", "and?", 
            "tell me more", "what else", "more", "keep talking"
        ]
        message_lower = message.lower().strip()
        
        # Check if the message is exactly one of the continue patterns
        return message_lower in continue_patterns
    
    def _handle_continue_request(self, message, user_id):
        # Handle continuation requests by prompting the model to continue.
        # Add user message to chat history
        self.chat_history.add_user_message(message, user_id)
        
        # Create a continuation prompt
        continuation_prompt = f"""The user wants you to continue your previous thought. 
        They said: "{message}"
        
        Please continue naturally from where you left off, expanding on your previous response."""
        
        try:
            # Use the existing chat context to continue
            self.chat.add_user_message(continuation_prompt)
            
            response_text = ""
            for fragment in self.model.respond_stream(self.chat):
                response_text += fragment.content
                
        except Exception as e:
            print(f"Error in continue request: {e}")
            # Fallback response
            response_text = "I'd be happy to continue! What would you like me to elaborate on?"
        
        # Add assistant response to chat history
        self.chat_history.add_assistant_message(response_text)
        
        return response_text

    def _should_suggest_note_taking(self, message: str, context_data: Dict) -> Optional[str]:
        """
        Determine if the user wants to take a quick note/memo.
        Uses precise patterns to avoid false positives in casual conversation and gaming contexts.
        
        Returns:
            str: 'explicit_note' if note-taking is explicitly requested, None otherwise
        """
        message_lower = message.lower().strip()
        
        # Skip very short messages
        if len(message_lower.split()) < 3 and ':' not in message_lower:
            return None
            
        # Common gaming/false positive phrases
        gaming_phrases = [
            r'game (?:wants|tells|says)',
            r'(?:need|have|got) to (?:go|get|find|check|look|talk|speak|ask)',
            r'remember to (?:go|get|find|check|look|talk|speak|ask)',
            r'oh (?:i|you|we) (?:need|should|might|can)',
            r'i (?:think|guess|suppose|believe|feel|wonder)',
            r'write (?:this|that|it) (?:somewhere|down|in)',
            r'note (?:to self|that|this|the|down|in)',
            r'remind (?:me|you|us) (?:to|about|that|when|if)'
        ]
        
        for phrase in gaming_phrases:
            if re.search(phrase, message_lower):
                return None
        
        # More precise patterns with word boundaries
        note_triggers = [
            # Explicit note requests with clear intent
            r'^(?:write|jot) (?:this|that|it) down(?: for me)?$',
            r'^take (?:a )?note(?: of this| that| please)?$',
            r'^make a note(?: of this| that)?$',
            r'^note to self:',
            r'^remind me (?:about|that|to)',
            r'^add (?:this|that|it) to my (?:notes|list)',
            r'^save (?:this|that|it) (?:in|to) my (?:notes|list)',
            
            # Common memo patterns (only at start of message)
            '^(?:memo|note|reminder|todo|task|idea):',
            
            # Direct requests
            r'^can you (?:please )?(?:write|jot|note) (?:this|that|it) down\?$',
            r'^i want to (?:make a )?note (?:of|that) ', 
            r'^let me (?:make a )?note (?:of|that) ',
            r'^i should (?:write|jot) (?:this|that|it) down$'
        ]
        
        # Only check for note triggers if message starts with them
        for pattern in note_triggers:
            if re.match(pattern, message_lower):
                return 'explicit_note'
                
        return None

class BunnyChatMoodIntegration:
    def __init__(self, mood_system):
        self.mood_system = mood_system

    def get_mood_command_response(self, user_id):
        mood_summary_data = self.mood_system.get_user_mood_summary(user_id)
        if mood_summary_data:
            mood_score = mood_summary_data.get('intensity', 0.5)
            mood_summary = mood_summary_data.get('primary_mood', 'neutral')
            return f"📊 Current mood: {mood_summary} ({mood_score:.1f})"
        return "📊 No mood data available"

if __name__ == "__main__":
    bunny = BunnyChat()
    bunny.run_chat_loop()