class CommandProcessor:
    def __init__(self):
        self.commands = {
            "clear history": self.clear_history,
            "stop listening": self.stop_listening,
            "pause music": self.pause_music,
            "volume up": self.volume_up,
            "volume down": self.volume_down,
            # Add more commands as needed
        }
    
    def process_command(self, text):
        text_lower = text.lower()
        
        for command, handler in self.commands.items():
            if command in text_lower:
                return handler()
        
        return None
    
    # Voice command functions and ideas to develop later

    def clear_history(self):
        # Implementation would connect to your chat history module, to develop
        return "COMMAND:CLEAR_HISTORY"
    
    def stop_listening(self):
        # Implementation would connect to your STT module
        return "COMMAND:STOP_LISTENING"
    
    def pause_music(self):
        # Implementation for pausing music
        return "COMMAND:PAUSE_MUSIC"
    
    def volume_up(self):
        # Implementation for increasing volume
        return "COMMAND:VOLUME_UP"
    
    def volume_down(self):
        # Implementation for decreasing volume
        return "COMMAND:VOLUME_DOWN"