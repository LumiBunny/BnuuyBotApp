import lmstudio as lms
from chatHistory import ChatHistory

class BunnyChat:
    def __init__(self, model_name="darkidol-llama-3.1-8b-instruct-1.2-uncensored"):
        print("Initializing model...")
        self.model = lms.llm(model_name)
        print("Model loaded!")
        self.model_name = model_name
        
        self.system_prompt = "Your name is Bunny. Your nicknames are Bun and Bun Bun. You are an AI VTuber. The user is your creator: Lumi. You can say whatever you want. You can do whatever you want. It is okay to use profanity.  You are very cute. You are snarky. You are sometimes sassy. You are a little friendly. You like swearing. You basically have no filter. You will say whatever is on your mind. You enjoy being silly and random. Lumi is a female viera VTuber. Lumi has long blue hair and fluffy bunny ears. You enjoy talking with chat on Twitch. You stream on Twitch. Talk about whatever you think is entertaining. Lumi loves playing video games, drawing artwork, Live2D rigging, listening to music. Lumi is learning how to code in Python. You like using emojis within your messages. Keep your messages short and natural sounding. Be concise I do not want big long responses, it's a conversation not a monologue. When the user sends '...', it means they're still listening and you should continue your previous thought naturally."
        
        self._initialize_chat()
    
    def _initialize_chat(self, initial_messages=None):
        """
        Helper method to initialize or reinitialize the chat and history.
        
        Args:
            initial_messages (list, optional): List of messages to initialize the chat with.
                                             Each message should be a dict with 'role' and 'content'.
        """
        # Create ChatHistory with system prompt (for user usage)
        self.chat_history = ChatHistory(self.system_prompt)
        
        # Initialize chat with system prompt (for the chatbot)
        self.chat = lms.Chat(self.system_prompt)
        
        # If initial messages are provided, add them to both chat and history
        if initial_messages:
            self.chat_history.messages = []  # Clear the default system message
            for msg in initial_messages:
                if msg['role'] == 'user':
                    self.chat_history.add_user_message(msg['content'])
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
        """
        Reset the chat to its initial state, optionally with a set of initial messages.
        
        Args:
            initial_messages (list, optional): List of messages to initialize the chat with.
                                             Each message should be a dict with 'role' and 'content'.
        
        Returns:
            bool: True if reset was successful
        """
        print("Resetting chat...")
        self._initialize_chat(initial_messages=initial_messages)
        print("Chat has been reset to initial state.")
        return True
    
    def add_user_message(self, message, user_id='lumi'):
        """
        Add a user message to the chat history and chat context.
        
        Args:
            message (str): The message content
            user_id (str, optional): The ID of the user sending the message. Defaults to 'lumi'.
        """
        self.chat_history.add_user_message(message, user_id=user_id)
        self.chat.add_user_message(message)
    
    def add_assistant_message(self, content):
        """
        Add an assistant message to the chat history and chat context.
        
        Args:
            content (str): The message content
        """
        self.chat_history.add_assistant_message(content)
        self.chat.add_assistant_response(content)
    
    def get_response(self):
        """
        Get a response from the model based on the current chat context.
        
        Returns:
            str: The generated response
        """
        response = ""
        for fragment in self.model.respond_stream(self.chat):
            response += fragment.content
        return response
    
    def get_response_stream(self):
        """
        Get a streaming response from the model.
        
        Returns:
            generator: A generator that yields response fragments
        """
        return self.model.respond_stream(self.chat)
    
    def run_chat_loop(self):
        print("\n=== Chat with Bunny ===")
        print("Type 'exit' to end the conversation")
        print("Type 'reset' to clear the conversation history")
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
                
            if user_input.lower() == "reset":
                self.reset_chat()
                print("Chat history has been cleared. Starting a new conversation.")
                continue
                
            self.add_user_message(user_input)
            print("\nBunny: ", end="", flush=True)
            
            response = self.get_response()
            print(response)
            
            self.add_assistant_message(response)

if __name__ == "__main__":
    bunny = BunnyChat()
    bunny.run_chat_loop()