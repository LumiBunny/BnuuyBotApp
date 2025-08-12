"""
Mood-Thinking Bridge

Provides integration between the mood module and thinking module.
This bridge allows the thinking system to work with mood context
while keeping the modules cleanly separated.
"""

import logging
from typing import Dict, List, Optional, Any
from .inner_thoughts import InnerThoughtsGenerator

logger = logging.getLogger(__name__)

class MoodThinkingBridge:
    """
    Bridge between mood context and thinking functionality.
    
    This class provides a clean interface for using thinking capabilities
    with mood context while keeping the modules decoupled.
    """
    
    def __init__(self, inner_thoughts_generator: Optional[InnerThoughtsGenerator] = None):
        """
        Initialize the mood-thinking bridge.
        
        Args:
            inner_thoughts_generator: Optional custom inner thoughts generator
        """
        self.thoughts_generator = inner_thoughts_generator or InnerThoughtsGenerator()
        logger.info("MoodThinkingBridge initialized")
    
    def create_mood_aware_messages_with_thoughts(self, base_messages: List[Dict], mood_context: Dict[str, Any]) -> List[Dict]:
        """
        Create mood-aware messages enhanced with inner thoughts.
        
        This method combines mood context with thinking functionality
        to create messages that include both mood observations and inner thoughts.
        
        Args:
            base_messages: Original message list
            mood_context: Mood context from DynamicMoodContext.get_current_mood_context()
        
        Returns:
            Enhanced message list with both mood context and inner thoughts
        """
        # First add mood context
        mood_enhanced_messages = self._add_mood_context(base_messages, mood_context)
        
        # Then add inner thoughts based on the mood context
        thinking_enhanced_messages = self.thoughts_generator.create_context_aware_messages(
            mood_enhanced_messages, 
            mood_context
        )
        
        return thinking_enhanced_messages
    
    def _add_mood_context(self, base_messages: List[Dict], mood_context: Dict[str, Any]) -> List[Dict]:
        """
        Add basic mood context to messages (without inner thoughts).
        
        This replicates the simplified mood context functionality
        that remains in the mood module.
        
        Args:
            base_messages: Original message list
            mood_context: Mood context information
        
        Returns:
            Messages with mood context added
        """
        if not mood_context.get('has_mood_context', False):
            return base_messages
        
        mood_message = {
            "role": "observation",
            "content": f"Mood Context: {mood_context.get('mood_summary', '')}. Trend: {mood_context.get('mood_trend', 'stable')}."
        }
        
        # Insert before the last user message
        if base_messages and base_messages[-1]["role"] == "user":
            return base_messages[:-1] + [mood_message] + [base_messages[-1]]
        else:
            return base_messages + [mood_message]
    
    def generate_mood_based_thoughts(self, mood_context: Dict[str, Any]) -> Optional[str]:
        """
        Generate inner thoughts specifically based on mood context.
        
        Args:
            mood_context: Mood context from DynamicMoodContext
        
        Returns:
            Generated thoughts or None
        """
        return self.thoughts_generator.generate_inner_thoughts(mood_context)
    
    def update_thinking_config(self, new_config: Dict[str, Any]) -> None:
        """Update the thinking generator configuration."""
        self.thoughts_generator.update_config(new_config)


# Example usage
if __name__ == "__main__":
    # Test the bridge
    bridge = MoodThinkingBridge()
    
    # Mock mood context
    mood_context = {
        'has_mood_context': True,
        'mood_summary': 'User seems excited and enthusiastic',
        'mood_trend': 'rising',
        'response_guidance': {
            'response_tone': 'enthusiastic and supportive',
            'empathy_level': 'high'
        }
    }
    
    # Test message enhancement
    base_messages = [
        {"role": "user", "content": "I'm so excited about this new project!"}
    ]
    
    enhanced_messages = bridge.create_mood_aware_messages_with_thoughts(base_messages, mood_context)
    
    print("Enhanced messages with mood context and inner thoughts:")
    for i, msg in enumerate(enhanced_messages):
        print(f"{i+1}. {msg['role']}: {msg['content']}")
