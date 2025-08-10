import logging
from typing import Dict, List, Optional, Any
import json
from .mood_detector import HybridMoodDetector
from .dynamic_mood_context import DynamicMoodContext

logger = logging.getLogger(__name__)

class IntegratedMoodSystem:
    # Complete mood system integrating detection and context management
    # Designed for seamless integration with BunnyChat
    def __init__(self, use_gpu: bool = True, transformer_model: str = "j-hartmann/emotion-english-distilroberta-base"):
        # Initialize mood detection
        self.detector = HybridMoodDetector(use_gpu=use_gpu, model_name=transformer_model)
        
        # Initialize dynamic context (per-user contexts)
        self.user_contexts: Dict[str, DynamicMoodContext] = {}
        
        # Configuration
        self.config = {
            'min_confidence_threshold': 0.3,  # Only use moods above this confidence
            'context_decay_hours': 2.0,       # How long mood context lasts
            'max_observations_per_user': 5,   # Max mood observations to keep
            'enable_inner_thoughts': True,    # Enable inner thoughts generation
            'enable_trend_analysis': True,    # Enable mood trend analysis
        }
        
        logger.info(f"IntegratedMoodSystem initialized - GPU: {use_gpu}")
    
    def _get_user_context(self, user_id: str) -> DynamicMoodContext:
        # Get or create mood context for a user
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = DynamicMoodContext(
                max_observations=self.config['max_observations_per_user'],
                decay_hours=self.config['context_decay_hours']
            )
        return self.user_contexts[user_id]
    
    def process_user_message(self, user_id: str, message: str) -> Optional[Dict[str, Any]]:
        # Process a user message for mood detection and context update
        # Returns mood information if detected
        if not message or not message.strip():
            return None
        
        # Detect mood using hybrid system
        mood_result = self.detector.detect_mood(message)
        
        if not mood_result or mood_result.confidence < self.config['min_confidence_threshold']:
            return None
        
        # Get user's mood context
        context = self._get_user_context(user_id)
        
        # Add observation to context
        context.add_observation(
            mood=mood_result.mood,
            intensity=mood_result.intensity,
            confidence=mood_result.confidence,
            context=f"Detected from: '{message[:50]}...'" if len(message) > 50 else f"Detected from: '{message}'"
        )
        
        # Return mood information for logging/debugging
        return {
            'detected_mood': mood_result.mood,
            'intensity': mood_result.intensity,
            'confidence': mood_result.confidence,
            'detection_method': mood_result.method,
            'raw_scores': mood_result.raw_scores,
            'context_updated': True
        }
    
    def get_mood_aware_messages(self, user_id: str, base_messages: List[Dict]) -> List[Dict]:
        # Enhance message list with mood context for LLM
        # This is the main integration point with BunnyChat
        if not self.config['enable_inner_thoughts']:
            return base_messages
        
        context = self._get_user_context(user_id)
        return context.create_mood_aware_messages(base_messages)
    
    def get_mood_context_for_system_prompt(self, user_id: str) -> str:
        # Get mood context as text for system prompt enhancement
        # Alternative to message-based integration
        context = self._get_user_context(user_id)
        mood_context = context.get_current_mood_context()
        
        if not mood_context['has_mood_context']:
            return ""
        
        guidance = mood_context['response_guidance']
        
        return f"""
Current User Emotional Context:
- {mood_context['mood_summary']}
- Emotional trend: {mood_context['mood_trend']}
- Recommended response tone: {guidance['response_tone']}
- Empathy approach: {guidance['empathy_level']}

Please feel free to adapt your responses accordingly.
"""
    
    def get_user_mood_summary(self, user_id: str) -> Dict[str, Any]:
        # Get comprehensive mood summary for a user
        context = self._get_user_context(user_id)
        return context.get_current_mood_context()
    
    def cleanup_user_context(self, user_id: str) -> int:
        # Clean up old mood observations for a user
        if user_id not in self.user_contexts:
            return 0
        
        context = self.user_contexts[user_id]
        return context.cleanup_old_observations()
    
    def cleanup_all_contexts(self) -> Dict[str, int]:
        # Clean up old observations for all users
        cleanup_results = {}
        for user_id, context in self.user_contexts.items():
            cleanup_results[user_id] = context.cleanup_old_observations()
        return cleanup_results
    
    def get_system_stats(self) -> Dict[str, Any]:
        # Get system-wide mood statistics
        detector_info = self.detector.get_model_info()
        
        user_stats = {}
        for user_id, context in self.user_contexts.items():
            user_stats[user_id] = {
                'observation_count': len(context.observations),
                'dominant_mood': context.get_current_mood_context()['dominant_mood'],
                'has_active_context': context.get_current_mood_context()['has_mood_context']
            }
        
        return {
            'detector_info': detector_info,
            'total_users': len(self.user_contexts),
            'active_users': sum(1 for stats in user_stats.values() if stats['has_active_context']),
            'user_stats': user_stats,
            'config': self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        # Update system configuration
        self.config.update(new_config)
        logger.info(f"Mood system config updated: {new_config}")
    
    def get_debug_info(self, user_id: str) -> Dict[str, Any]:
        # Get detailed debug information for a user
        if user_id not in self.user_contexts:
            return {'error': 'User not found'}
        
        context = self.user_contexts[user_id]
        return {
            'user_id': user_id,
            'context_debug': context.get_debug_info(),
            'detector_info': self.detector.get_model_info(),
            'system_config': self.config
        }

# Integration helper for BunnyChat
class BunnyChatMoodIntegration:
    # Helper class for integrating mood system with BunnyChat
    # Provides simple interface for existing BunnyChat methods
    def __init__(self, mood_system: IntegratedMoodSystem):
        self.mood_system = mood_system
    
    def enhance_get_response(self, user_id: str, message: str, base_messages: List[Dict]) -> List[Dict]:
        """
        Enhance BunnyChat's get_response method with mood awareness
        
        Usage in BunnyChat:
        messages = self.mood_integration.enhance_get_response(user_id, message, messages)
        """
        # Process the user message for mood
        mood_info = self.mood_system.process_user_message(user_id, message)
        
        if mood_info:
            logger.info(f"Mood detected for {user_id}: {mood_info['detected_mood']} "
                       f"(confidence: {mood_info['confidence']:.2f})")
        
        # Return mood-aware messages
        return self.mood_system.get_mood_aware_messages(user_id, base_messages)
    
    def get_mood_command_response(self, user_id: str) -> str:
        # Generate response for /mood command
        mood_summary = self.mood_system.get_user_mood_summary(user_id)
        
        if not mood_summary['has_mood_context']:
            return "😐 I haven't detected any particular mood from our recent conversation."
        
        dominant_mood = mood_summary['dominant_mood']
        mood_summary_text = mood_summary['mood_summary']
        trend = mood_summary['mood_trend']
        
        # Mood emojis
        mood_emojis = {
            'joy': '😊',
            'sadness': '😢',
            'anger': '😠',
            'fear': '😰',
            'surprise': '😲',
            'neutral': '😐'
        }
        
        emoji = mood_emojis.get(dominant_mood, '🤔')
        
        response = f"{emoji} **Current Mood Analysis:**\n"
        response += f"• {mood_summary_text}\n"
        response += f"• Emotional trend: {trend}\n"
        
        if trend == "improving":
            response += "• That's great to see! 🌟"
        elif trend == "declining":
            response += "• I'm here if you need support 💙"
        
        return response

# Example integration with BunnyChat
"""
# In bunnyChat.py, add to __init__:
from integrated_mood_system import IntegratedMoodSystem, BunnyChatMoodIntegration

self.mood_system = IntegratedMoodSystem(use_gpu=True)
self.mood_integration = BunnyChatMoodIntegration(self.mood_system)

# In get_response method, replace message building with:
messages = self.mood_integration.enhance_get_response(user_id, message, messages)

# Add new command in run_chat_loop:
elif user_input.lower() == '/mood':
    print(self.mood_integration.get_mood_command_response(user_id))
    continue
"""

# Future: Speculative Decoding Implementation Outline
class SpeculativeMoodDecoding:
    # Future implementation for speculative decoding with mood context
    # Uses a smaller "draft" model for inner thoughts and main model for responses
    def __init__(self, main_model_client, draft_model_client=None):
        self.main_model = main_model_client
        self.draft_model = draft_model_client  # Smaller, faster model for inner thoughts
        
        # This would integrate with LM Studio's speculative decoding when available
        self.speculative_enabled = draft_model_client is not None
    
    async def generate_with_inner_thoughts(self, messages: List[Dict], mood_context: str) -> Dict[str, str]:
        # Future method for generating responses with speculative inner thoughts
        if not self.speculative_enabled:
            # Fallback to regular generation
            return await self._generate_regular(messages)
        
        # Step 1: Generate inner thoughts with draft model (fast)
        inner_thoughts_prompt = f"Given this mood context: {mood_context}, what should I consider in my response?"
        inner_thoughts = await self._generate_draft_thoughts(inner_thoughts_prompt)
        
        # Step 2: Use inner thoughts to guide main model response
        enhanced_messages = messages + [
            {"role": "thinking", "content": inner_thoughts}
        ]
        
        main_response = await self._generate_main_response(enhanced_messages)
        
        return {
            "inner_thoughts": inner_thoughts,
            "response": main_response,
            "method": "speculative"
        }
    
    async def _generate_draft_thoughts(self, prompt: str) -> str:
        # Generate quick inner thoughts with draft model
        # Implementation would depend on LM Studio's API
        pass
    
    async def _generate_main_response(self, messages: List[Dict]) -> str:
        # Generate main response with full model
        # Implementation would depend on LM Studio's API
        pass
    
    async def _generate_regular(self, messages: List[Dict]) -> Dict[str, str]:
        # Fallback regular generation
        # Implementation would depend on LM Studio's API
        pass

if __name__ == "__main__":
    # Test the integrated system
    mood_system = IntegratedMoodSystem(use_gpu=False)  # CPU for testing
    integration = BunnyChatMoodIntegration(mood_system)
    
    print("🤖 Testing Integrated Mood System")
    print("=" * 50)
    
    # Simulate user interaction
    user_id = "test_user"
    
    # Test mood detection and context
    test_messages = [
        "I'm so excited about this new project!",
        "Ugh, this bug is really frustrating me",
        "Actually, I think I figured it out!",
        "Can you help me with the next step?"
    ]
    
    base_messages = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n--- Message {i+1}: '{message}' ---")
        
        # Process message and get enhanced messages
        enhanced_messages = integration.enhance_get_response(user_id, message, base_messages + [{"role": "user", "content": message}])
        
        # Show the mood-aware messages
        for msg in enhanced_messages:
            if msg["role"] == "observation":
                print(f"🧠 Inner thoughts: {msg['content']}")
        
        # Show mood command response
        mood_response = integration.get_mood_command_response(user_id)
        print(f"📊 Mood summary: {mood_response}")
    
    # Show system stats
    print(f"\n📈 System stats: {json.dumps(mood_system.get_system_stats(), indent=2, default=str)}")
