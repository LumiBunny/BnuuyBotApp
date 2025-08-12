import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class InnerThoughtsGenerator:
    # Generates inner thoughts and observations for AI responses.
    # This class creates internal observations based on context and enhances
    # message lists with thinking content for more contextually aware responses.
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Initialize the inner thoughts generator with configuration.
        self.config = config or {
            'enable_inner_thoughts': True,
            'observation_role': 'observation',  # Role name for inner thoughts in messages
            'thought_prefix': '[Internal Observation]',
            'max_thought_length': 200
        }
        
        logger.info("InnerThoughtsGenerator initialized")
    
    def generate_inner_thoughts(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate inner thoughts content based on provided context.
        
        Args:
            context: Dictionary containing context information such as:
                - mood_summary: Current mood analysis
                - mood_trend: Emotional trend (rising/falling/stable)
                - response_guidance: How to approach the response
                - has_mood_context: Whether mood context is available
        
        Returns:
            Generated inner thoughts string or None if no context available
        """
        if not self.config.get('enable_inner_thoughts', True):
            return None
            
        if not context.get('has_mood_context', False):
            return None
        
        mood_summary = context.get('mood_summary', '')
        trend = context.get('mood_trend', 'stable')
        guidance = context.get('response_guidance', {})
        
        if not mood_summary:
            return None
        
        # Generate inner thoughts based on mood context
        thoughts = f"{self.config['thought_prefix']} {mood_summary}. "
        
        if trend != "stable":
            thoughts += f"Emotional trend appears to be {trend}. "
        
        if guidance:
            response_tone = guidance.get('response_tone', '')
            empathy_level = guidance.get('empathy_level', '')
            
            if response_tone:
                thoughts += f"Response approach: {response_tone}. "
            if empathy_level:
                thoughts += f"Empathy level: {empathy_level}."
        
        # Truncate if too long
        max_length = self.config.get('max_thought_length', 200)
        if len(thoughts) > max_length:
            thoughts = thoughts[:max_length-3] + "..."
        
        return thoughts
    
    def create_context_aware_messages(self, base_messages: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        Add inner thoughts context to message list for LLM processing.
        
        Args:
            base_messages: Original message list
            context: Context information for generating inner thoughts
        
        Returns:
            Enhanced message list with inner thoughts inserted
        """
        inner_thoughts = self.generate_inner_thoughts(context)
        
        if not inner_thoughts:
            return base_messages
        
        # Create the inner thoughts message
        thought_message = {
            "role": self.config.get('observation_role', 'observation'),
            "content": inner_thoughts
        }
        
        # Insert before the last user message for better context
        if base_messages and base_messages[-1]["role"] == "user":
            return base_messages[:-1] + [thought_message] + [base_messages[-1]]
        else:
            return base_messages + [thought_message]
    
    def generate_contextual_thoughts(self, 
                                   user_message: str, 
                                   conversation_history: List[Dict],
                                   additional_context: Optional[Dict] = None) -> Optional[str]:
        """
        Generate inner thoughts based on user message and conversation context.
        
        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            additional_context: Any additional context information
        
        Returns:
            Generated contextual thoughts or None
        """
        if not self.config.get('enable_inner_thoughts', True):
            return None
        
        context = additional_context or {}
        
        # Analyze conversation for patterns or important elements
        thoughts_parts = []
        
        # Add message analysis
        if user_message:
            message_length = len(user_message.split())
            if message_length > 50:
                thoughts_parts.append("User provided detailed message")
            elif message_length < 5:
                thoughts_parts.append("User message is brief")
        
        # Add conversation context
        if len(conversation_history) > 10:
            thoughts_parts.append("Extended conversation context")
        elif len(conversation_history) < 3:
            thoughts_parts.append("Early in conversation")
        
        # Add any additional context
        if context:
            for key, value in context.items():
                if key.startswith('has_') and value:
                    thoughts_parts.append(f"{key.replace('has_', '').replace('_', ' ')} available")
        
        if not thoughts_parts:
            return None
        
        thoughts = f"{self.config['thought_prefix']} " + ". ".join(thoughts_parts) + "."
        
        # Truncate if needed
        max_length = self.config.get('max_thought_length', 200)
        if len(thoughts) > max_length:
            thoughts = thoughts[:max_length-3] + "..."
        
        return thoughts
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        # Update the configuration for the inner thoughts generator.
        self.config.update(new_config)
        logger.info(f"InnerThoughtsGenerator config updated: {new_config}")


# Example usage and testing
if __name__ == "__main__":
    # Test the inner thoughts generator
    generator = InnerThoughtsGenerator()
    
    # Test with mood context
    mood_context = {
        'has_mood_context': True,
        'mood_summary': 'User seems excited and enthusiastic',
        'mood_trend': 'rising',
        'response_guidance': {
            'response_tone': 'enthusiastic and supportive',
            'empathy_level': 'high'
        }
    }
    
    thoughts = generator.generate_inner_thoughts(mood_context)
    print(f"Generated thoughts: {thoughts}")
    
    # Test message enhancement
    base_messages = [
        {"role": "user", "content": "I'm so excited about this new project!"}
    ]
    
    enhanced_messages = generator.create_context_aware_messages(base_messages, mood_context)
    print(f"Enhanced messages: {enhanced_messages}")
