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