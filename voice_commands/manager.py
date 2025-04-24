from .attention import AttentionHandler
from .commands import CommandProcessor

class VoiceCommandManager:
    def __init__(self):
        self.attention_handler = AttentionHandler()
        self.command_processor = CommandProcessor()
    
    def process_input(self, text):
        if not text or not text.strip():
            return None, False
       
        if len(text.strip()) < 2:
            return None, False
        
        processed_text = self.attention_handler.check_for_attention(text)
        command_result = self.command_processor.process_command(text)
        
        if command_result:
            return command_result, True
        else:
            return processed_text, False