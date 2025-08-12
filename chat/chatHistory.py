import json
import datetime
from pathlib import Path
from typing import Optional
from .summarization import ChatSummarizer

class ChatHistory:
    def __init__(self, user_id: str = "lumi", system_prompt=None, history_file=None, base_data_dir: str = "user_data"):
        """
        Initialize ChatHistory with user-specific directory structure.
        
        Args:
            user_id: User identifier for directory structure
            system_prompt: Optional system prompt to add
            history_file: Optional specific history file (legacy support)
            base_data_dir: Base directory for user data
        """
        self.user_id = user_id
        self.base_data_dir = Path(base_data_dir)
        
        # Setup user directory structure (matches memory_manager.py)
        self.user_dir = self.base_data_dir / user_id
        self.raw_chats_dir = self.user_dir / "conversations" / "raw_chats"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Generate timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.history_file = self.raw_chats_dir / f"chat_{timestamp}.json"
        
        self.messages = []
        
        # Initialize chat summarizer
        self.summarizer = ChatSummarizer(user_id, base_data_dir)
        
        # Initialize history file
        self._initialize_history_file()
        
        # Add system prompt if provided
        if system_prompt:
            self.add_system_message(system_prompt)
    
    def _ensure_directories(self):
        """Create necessary directory structure."""
        self.raw_chats_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_history_file(self):
        # Create a new history file with an empty messages list.
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump({'messages': []}, f, indent=2)
        self.messages = []
    
    def add_system_message(self, content):
        # Add a system message to the history.
        message = {
            'role': 'system',
            'user_id': 'system',
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.messages.append(message)
        self._save_to_file()
        return self
    
    def add_user_message(self, content, user_id=None):
        # Add a user message to the history.
        if user_id is None:
            user_id = self.user_id
            
        message = {
            'role': 'user',
            'user_id': user_id,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.messages.append(message)
        self._save_to_file()
        
        # Check if periodic summarization is needed
        summary = self.summarizer.check_and_summarize(self.messages)
        if summary:
            print(f"📝 Generated periodic summary: {summary}")
        
        return self
    
    def add_assistant_message(self, content):
        # Add an assistant message to the history.
        message = {
            'role': 'assistant',
            'user_id': 'assistant',
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.messages.append(message)
        self._save_to_file()
        
        # Check if periodic summarization is needed
        summary = self.summarizer.check_and_summarize(self.messages)
        if summary:
            print(f"📝 Generated periodic summary: {summary}")
        
        return self
    
    def _save_to_file(self):
        # Save the current messages to the history file.
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump({'messages': self.messages}, f, indent=2)
    
    def get_messages(self):
        # Get all messages in the history.
        return self.messages
    
    def get_formatted_history(self):
        # Get history formatted for LLM context.
        # Convert our format to the format expected by LM Studio
        formatted_messages = []
        for msg in self.messages:
            formatted_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        return formatted_messages
    
    def clear(self):
        """Clear all messages except system prompt and generate reset summary."""
        if len(self.messages) > 1:  # More than just system prompt
            summary = self.summarizer.end_session(self.get_formatted_history(), "reset")
            print("📖 Chat log summarized! (Session reset)")
        
        # Clear messages (keep system prompts)
        system_prompts = [msg for msg in self.messages if msg['role'] == 'system']
        self.messages = system_prompts
        self._save_to_file()
        
        # Reset summarizer for new session
        self.summarizer.reset_session()
        
        return self
    
    def end_session(self):
        """End the current chat session and generate final summary."""
        if len(self.messages) > 1:  # More than just system prompt
            summary = self.summarizer.end_session(self.get_formatted_history(), "session_ended")
            print("📖 Chat log summarized! (Session ended)")
        
        # Reset summarizer
        self.summarizer.reset_session()
        
        return self

    def get_last_n_messages(self, n=1):
        # Get the last n messages.
        return self.messages[-n:] if n <= len(self.messages) else self.messages

    @classmethod
    def load_from_file(cls, filename, user_id: str = "lumi", system_prompt=None, base_data_dir: str = "user_data"):
        """Load a chat history from a file and return a new ChatHistory instance.
        Args:
            filename (str): The name of the file to load (without path)
            user_id (str): User identifier for directory structure
            system_prompt (str, optional): System prompt to use for the new chat
            base_data_dir (str): Base directory for user data
        Returns:
            ChatHistory: A new ChatHistory instance with the loaded messages
        """
        # Use new directory structure
        raw_chats_dir = Path(base_data_dir) / user_id / "conversations" / "raw_chats"
        filepath = raw_chats_dir / filename
        
        if not filepath.exists():
            # Fallback to old location for backward compatibility
            old_filepath = Path("chat_history") / filename
            if old_filepath.exists():
                filepath = old_filepath
            else:
                raise FileNotFoundError(f"Chat history file not found: {filepath}")
            
        # Load the messages from the file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Create a new instance with loaded data
        new_history = cls(user_id=user_id, system_prompt=system_prompt, base_data_dir=base_data_dir)
        
        # Clear the default system message if we're loading from a file
        # (we'll add them back from the loaded messages)
        new_history.messages = []
        
        # Add all messages from the loaded file
        for msg in data.get('messages', []):
            new_history.messages.append(msg)
            
        # Save the loaded messages to the new history file
        new_history._save_to_file()
        
        return new_history