import threading
import time
from datetime import datetime
import json
from .storage import MemoryStorage

class MemoryManager:
    def __init__(self, profile_manager=None, storage=None):
        # profile_manager: Your existing UserProfileManager instance
        # storage: Optional custom storage implementation
        self.profile_manager = profile_manager
        self.storage = storage or MemoryStorage()
        self.processing_queue = []
        self._stop_requested = False
        self._worker_thread = None
        
    def start(self):
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_requested = False
            self._worker_thread = threading.Thread(target=self._process_memory_queue)
            self._worker_thread.daemon = True
            self._worker_thread.start()
            
    def stop(self):
        self._stop_requested = True
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
            
    def _process_memory_queue(self):
        # Background thread that processes memory operations.
        while not self._stop_requested:
            if self.processing_queue:
                # Get the next item to process
                task = self.processing_queue.pop(0)
                try:
                    operation = task.get('operation')
                    if operation == 'store_memory':
                        self._store_memory(task.get('memory'))
                    elif operation == 'extract_preferences':
                        self._extract_preferences(task.get('user_id'), task.get('text'))
                    elif operation == 'summarize_conversation':
                        self._summarize_conversation(task.get('conversation'))
                except Exception as e:
                    print(f"Error processing memory task: {e}")
            else:
                # Sleep a bit to avoid busy waiting
                time.sleep(0.1)
                
    def process_conversation(self, user_id, user_message, ai_response):
        # Process a conversation turn for memory extraction.
        
        # Queue extraction of preferences
        self.processing_queue.append({
            'operation': 'extract_preferences',
            'user_id': user_id,
            'text': user_message
        })
        
        # Store the conversation as a memory
        self.processing_queue.append({
            'operation': 'store_memory',
            'memory': {
                'type': 'conversation',
                'user_id': user_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    def _extract_preferences(self, user_id, text):
        # Extract preferences from text and store them in the user profile.
        if not self.profile_manager:
            return
            
        # Use your existing preference extractor
        # This assumes your profile_manager has a method to extract preferences
        preferences = self.profile_manager.extract_preferences(text, user_id)
        
        if preferences:
            for pref in preferences:
                category = self.profile_manager.categorize_preference(pref)
                self.profile_manager.add_preference(user_id, pref, category)
                
    def _store_memory(self, memory):
        # Store a memory in the storage backend.
        self.storage.store(memory)
        
    # Summarize the conversation if it's a conversation memory
    # Will implement this at a later date
    """def _summarize_conversation(self, conversation):
        # Summarize a conversation and store the summary.
        from .summarization import summarize_conversation
        
        summary = summarize_conversation(conversation)
        if summary:
            self.storage.store({
                'type': 'summary',
                'user_id': conversation.get('user_id'),
                'content': summary,
                'original_conversation_id': conversation.get('id'),
                'timestamp': datetime.now().isoformat()
            })"""

    def get_memory_context(self, user_id, recent_message, limit=3):
        # Get memories relevant to the current conversation topic
        relevant_memories = self.get_relevant_memories(user_id, recent_message, limit)
        
        # Get relevant user profile information
        profile_context = None
        if self.profile_manager:
            profile_context = self.profile_manager.get_profile_summary(user_id)
        
        if not relevant_memories and not profile_context:
            return None
        
        # Format the memories as context for the AI
        context_parts = ["I recall the following about this user:"]
        
        # Add profile information
        if profile_context:
            for category, items in profile_context.items():
                if items:
                    likes = [item for item in items if not item.startswith("doesn't like")]
                    dislikes = [item.replace("doesn't like ", "") for item in items if item.startswith("doesn't like")]
                    
                    if likes:
                        context_parts.append(f"- User likes {category}: {', '.join(likes)}")
                    if dislikes:
                        context_parts.append(f"- User dislikes {category}: {', '.join(dislikes)}")
        
        # Add memories
        for memory in relevant_memories:
            memory_type = memory.get('type', 'unknown')
            content = memory.get('content', '')
            timestamp = memory.get('timestamp', '')
            
            # Format based on memory type
            if memory_type == 'preference':
                context_parts.append(f"- User {content}")
            elif memory_type == 'conversation':
                context_parts.append(f"- From a previous conversation: {content}")
            elif memory_type == 'note':
                context_parts.append(f"- Note: {content}")
            else:
                context_parts.append(f"- {content}")
        
        return "\n".join(context_parts)
            
    def get_relevant_memories(self, user_id, query, limit=5):
        # Retrieve memories relevant to the current conversation.
        
        return self.storage.search(user_id, query, limit)
        
    def add_explicit_memory(self, user_id, content, memory_type="note", metadata=None):
        # Add an explicit memory requested by the user.
        memory = {
            'type': memory_type,
            'user_id': user_id,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        return self.storage.store(memory)