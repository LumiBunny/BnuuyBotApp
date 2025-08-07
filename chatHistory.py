import os
import json
import datetime

class ChatHistory:
    def __init__(self, system_prompt=None, history_file=None):
        # Create a default directory for chat histories
        history_dir = "chat_history"
        os.makedirs(history_dir, exist_ok=True)
        
        # Generate a timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.history_file = os.path.join(history_dir, f"chat_{timestamp}.json")
        
        self.messages = []
        
        # Initialize history file
        self._initialize_history_file()
        
        # Add system prompt if provided
        if system_prompt:
            self.add_system_message(system_prompt)
    
    def _initialize_history_file(self):
        # Create a new history file with an empty messages list.
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
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
    
    def add_user_message(self, content, user_id='lumi'):
        # Add a user message to the history.
        message = {
            'role': 'user',
            'user_id': user_id,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.messages.append(message)
        self._save_to_file()
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
        # Clear all messages except system prompt.
        system_prompts = [msg for msg in self.messages if msg['role'] == 'system']
        self.messages = system_prompts
        self._save_to_file()
        return self
    
    def get_last_n_messages(self, n=1):
        # Get the last n messages.
        return self.messages[-n:] if n <= len(self.messages) else self.messages

    @classmethod
    def load_from_file(cls, filename, system_prompt=None):
        """
        Load a chat history from a file and return a new ChatHistory instance.
        
        Args:
            filename (str): The name of the file to load (without path)
            system_prompt (str, optional): System prompt to use for the new chat
            
        Returns:
            ChatHistory: A new ChatHistory instance with the loaded messages
        """
        history_dir = "chat_history"
        filepath = os.path.join(history_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Chat history file not found: {filepath}")
            
        # Load the messages from the file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Create a new timestamp for the new history file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_history = cls(system_prompt=system_prompt)
        
        # Clear the default system message if we're loading from a file
        # (we'll add them back from the loaded messages)
        new_history.messages = []
        
        # Add all messages from the loaded file
        for msg in data.get('messages', []):
            new_history.messages.append(msg)
            
        # Save the loaded messages to the new history file
        new_history._save_to_file()
        
        return new_history