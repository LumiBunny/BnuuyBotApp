"""
Realistic Thinking Bridge

Works with LM Studio's actual API limitations by enhancing system prompts
instead of using custom message roles that aren't supported.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ThinkingBridge:
    """
    Thinking bridge that works with LM Studio's actual API capabilities.
    
    Instead of custom roles, this enhances the system prompt with context
    and creates "inner thoughts" as part of the conversation flow.
    """
    
    def __init__(self, 
                 memory_manager=None,
                 preference_extractor=None, 
                 interest_tracker=None,
                 mood_system=None):
        """
        Initialize the realistic thinking bridge.
        
        Args:
            memory_manager: MemoryManager instance
            preference_extractor: PreferenceExtractor instance
            interest_tracker: InterestTracker instance
            mood_system: IntegratedMoodSystem instance
        """
        self.memory_manager = memory_manager
        self.preference_extractor = preference_extractor
        self.interest_tracker = interest_tracker
        self.mood_system = mood_system
        
        logger.info("ThinkingBridge initialized")
    
    def gather_comprehensive_context(self, user_id: str, current_message: str = "") -> Dict[str, Any]:
        """Gather all available context about the user."""
        context = {
            'user_id': user_id,
            'current_message': current_message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Gather Preferences
        try:
            if self.memory_manager:
                preferences = self.memory_manager.get_preferences(user_id)
                context['preferences'] = preferences
                context['preference_summary'] = self._summarize_preferences(preferences)
        except Exception as e:
            logger.error(f"Error gathering preferences: {e}")
            context['preferences'] = {}
            context['preference_summary'] = "No known preferences"
        
        # Gather Interests
        try:
            if self.interest_tracker:
                top_interests = self.interest_tracker.get_top_interests(user_id, limit=3)
                context['interests'] = top_interests
                context['interest_summary'] = self._summarize_interests(top_interests)
        except Exception as e:
            logger.error(f"Error gathering interests: {e}")
            context['interests'] = []
            context['interest_summary'] = "No tracked interests"
        
        # Gather Mood Context
        try:
            context['mood_context'] = self._gather_mood_context(user_id)
        except Exception as e:
            logger.error(f"Error gathering mood context: {e}")
            context['mood_context'] = ""
        
        return context
    
    def _summarize_preferences(self, preferences: Dict) -> str:
        """Create a concise summary of user preferences."""
        if not preferences:
            return "No known preferences"
        
        summary_parts = []
        for category, prefs in preferences.items():
            if isinstance(prefs, dict):
                loves = prefs.get('loves', [])
                likes = prefs.get('likes', [])
                dislikes = prefs.get('dislikes', [])
                hates = prefs.get('hates', [])
                
                if loves:
                    summary_parts.append(f"loves {', '.join(loves[:2])}")
                if likes:
                    summary_parts.append(f"likes {', '.join(likes[:2])}")
                if dislikes:
                    summary_parts.append(f"dislikes {', '.join(dislikes[:2])}")
                if hates:
                    summary_parts.append(f"hates {', '.join(hates[:2])}")
        
        return "; ".join(summary_parts[:3])  # Keep it very concise
    
    def _summarize_interests(self, interests: List[Dict]) -> str:
        """Create a concise summary of user interests."""
        if not interests:
            return "No tracked interests"
        
        interest_strings = []
        for interest in interests[:3]:  # Top 3 only
            topic = interest['topic']
            score = interest['score']
            if score > 0.6:
                interest_strings.append(f"very interested in {topic}")
            elif score > 0.3:
                interest_strings.append(f"interested in {topic}")
        
        return "; ".join(interest_strings) if interest_strings else "No strong interests"
    
    def _gather_mood_context(self, user_id: str) -> str:
        """Gather current mood context for the user."""
        try:
            if hasattr(self.mood_system, 'get_mood_context_for_system_prompt'):
                return self.mood_system.get_mood_context_for_system_prompt(user_id)
            elif hasattr(self.mood_system, 'get_user_mood_summary'):
                mood_summary = self.mood_system.get_user_mood_summary(user_id)
                if mood_summary.get('has_mood_context', False):
                    return f"Current mood: {mood_summary.get('mood_summary', 'neutral')}"
            return ""
        except Exception as e:
            logger.error(f"Error gathering mood context: {e}")
            return ""
    
    def create_enhanced_system_prompt(self, base_system_prompt: str, user_id: str, current_message: str = "") -> str:
        """
        Create an enhanced system prompt with comprehensive context.
        
        This is the realistic approach that works with LM Studio's API.
        """
        context = self.gather_comprehensive_context(user_id, current_message)
        
        # Build context additions
        context_parts = []
        
        # Add mood context
        mood_context = context.get('mood_context', '')
        if mood_context:
            context_parts.append(mood_context)
        
        # Add preferences
        pref_summary = context.get('preference_summary', '')
        if pref_summary and pref_summary != "No known preferences":
            context_parts.append(f"User preferences: {pref_summary}")
        
        # Add interests
        interest_summary = context.get('interest_summary', '')
        if interest_summary and interest_summary != "No tracked interests":
            context_parts.append(f"User interests: {interest_summary}")
        
        # Create enhanced prompt
        if context_parts:
            context_text = " | ".join(context_parts)
            enhanced_prompt = f"{base_system_prompt}\n\n[Internal Context: {context_text}]\n\nUse this context naturally in your response. Don't explicitly mention you're using internal context."
        else:
            enhanced_prompt = base_system_prompt
        
        return enhanced_prompt
    
    def generate_inner_thoughts_as_text(self, user_id: str, current_message: str = "") -> str:
        """
        Generate inner thoughts as a text string that can be used in conversation.
        
        This creates a natural-sounding internal monologue that could be
        included in the conversation or used for logging/debugging.
        """
        context = self.gather_comprehensive_context(user_id, current_message)
        
        thoughts = []
        
        # Mood-based thoughts
        mood_context = context.get('mood_context', '')
        if mood_context:
            thoughts.append(f"I notice the user {mood_context.lower()}")
        
        # Preference-based thoughts
        pref_summary = context.get('preference_summary', '')
        if pref_summary and pref_summary != "No known preferences":
            thoughts.append(f"I remember they {pref_summary}")
        
        # Interest-based thoughts
        interest_summary = context.get('interest_summary', '')
        if interest_summary and interest_summary != "No tracked interests":
            thoughts.append(f"They seem to be {interest_summary}")
        
        if thoughts:
            return f"*thinking: {' and '.join(thoughts)}*"
        else:
            return "*thinking: Getting to know this user better*"


# Example usage showing the realistic approach
if __name__ == "__main__":
    print("ThinkingBridge - works with actual LM Studio API limitations")
