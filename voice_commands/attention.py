class AttentionHandler:
    def __init__(self):
        self.attention_phrases = [
            "bunny", "bun", "bun bun", 
            "hey bunny", "hey bun", "hey bun bun",
            "okay bunny", "okay bun bun", "okay bun"
        ]
    
    def check_for_attention(self, text):
        text_lower = text.lower().strip()
        cleaned_text = text_lower.strip(",.!?")
        
        # Check if the cleaned text matches any attention phrase exactly
        if cleaned_text in self.attention_phrases:
            return "[Lumi wants your attention]"
            
        return text