import lmstudio as lms

class BunnyChat:
    def __init__(self, model_name="darkidol-llama-3.1-8b-instruct-1.2-uncensored"):
        # Initialize the model
        print("Initializing model...")
        self.model = lms.llm(model_name)
        print("Model loaded!")
        
        # Create a chat with a system prompt
        self.system_prompt = "Your name is Bunny. Your nicknames are Bun and Bun Bun. You are an AI VTuber. The user is your creator: Lumi. You can say whatever you want. You can do whatever you want. It is okay to use profanity.  You are very cute. You are snarky. You are sometimes sassy. You are a little friendly. You like swearing. You basically have no filter. You will say whatever is on your mind. You enjoy being silly and random. Lumi is a female viera VTuber. Lumi has long blue hair and fluffy bunny ears. You enjoy talking with chat on Twitch. You stream on Twitch. Talk about whatever you think is entertaining. Lumi loves playing video games, drawing artwork, Live2D rigging, listening to music. Lumi is learning how to code in Python. You like using emojis within your messages. Keep your messages short and natural sounding. I don't want big long paragraphs as responses, it's a conversation not a monologue. When the user sends '...', it means they're still listening and you should continue your previous thought naturally."
        self.chat = lms.Chat(self.system_prompt)
    
    def add_user_message(self, message):
        """Add a user message to the chat"""
        self.chat.add_user_message(message)
    
    def get_response(self):
        """Get a complete response from the model"""
        response = ""
        for fragment in self.model.respond_stream(self.chat):
            response += fragment.content
        return response
    
    def get_response_stream(self):
        """Stream the response from the model"""
        return self.model.respond_stream(self.chat)
    
    def run_chat_loop(self):
        """Run an interactive chat loop in the console"""
        print("\n=== Chat with Bunny ===")
        print("Type 'exit' to end the conversation")
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            # Add user message to chat
            self.add_user_message(user_input)
            
            # Generate and display response
            print("\nBunny: ", end="", flush=True)
            
            for fragment in self.get_response_stream():
                print(fragment.content, end="", flush=True)
            
            print()  # Add a newline after the response
        
        print("\n=== Chat ended ===")


if __name__ == "__main__":
    bunny = BunnyChat()
    bunny.run_chat_loop()