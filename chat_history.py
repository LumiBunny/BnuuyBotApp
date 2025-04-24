import os
import json
import datetime

class ChatLogger:
    def __init__(self, logs_directory="chat_logs"):
        self.logs_directory = logs_directory
        os.makedirs(logs_directory, exist_ok=True)
        self.current_log_file = None
        self.initialize_new_log()
    
    def initialize_new_log(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(self.logs_directory, f"chat_log_{timestamp}.json")
        
        # Initialize with empty conversations array
        with open(self.current_log_file, 'w') as f:
            json.dump({"conversations": []}, f, indent=2)
    
    def append_to_log(self, from_role, message_value):
        if not self.current_log_file:
            self.initialize_new_log()
        
        try:
            # Read current log content
            with open(self.current_log_file, 'r') as f:
                log_data = json.load(f)
            
            # Append new message
            log_data["conversations"].append({
                "from": from_role,
                "value": message_value
            })
            
            # Write updated content back to file
            with open(self.current_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error appending to log: {str(e)}")
            return False
    
    def get_current_log(self):
        if not self.current_log_file or not os.path.exists(self.current_log_file):
            return {"conversations": []}
        
        with open(self.current_log_file, 'r') as f:
            return json.load(f)

class ChatHistory:
    
    def __init__(self, system_prompt=None):
        self.messages = []
        if system_prompt:
            self.add_system_message(system_prompt)
    
    def add_system_message(self, content):
        self.messages.append({"role": "system", "content": content})
        return self
    
    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})
        return self
    
    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})
        return self
    
    def get_history(self):
        return {"messages": self.messages}
    
    def clear(self):
        self.messages = []
        return self
    
    def get_last_n_messages(self, n=1):
        return self.messages[-n:] if n <= len(self.messages) else self.messages
    
    @classmethod
    def from_messages(cls, messages):
        chat_history = cls()
        chat_history.messages = messages
        return chat_history