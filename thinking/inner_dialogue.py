import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class InnerDialogue:
    """
    BunnyBot's inner voice - a separate AI model for introspection and reflection.
    
    Uses a smaller, faster model dedicated to generating authentic inner thoughts
    based on conversation context, memories, preferences, mood, and interests.
    """
    
    def __init__(self, 
                 lm_studio_endpoint: str = "http://localhost:1234/v1/chat/completions",
                 model_name: str = "llama-3.2-1b-instruct",
                 log_directory: str = "logs/inner_dialogue"):
        """
        Initialize the inner dialogue system.
        
        Args:
            lm_studio_endpoint: LM Studio API endpoint
            model_name: Name of the model to use for inner thoughts
            log_directory: Directory to store thought logs
        """
        self.endpoint = lm_studio_endpoint
        self.model_name = model_name
        self.log_directory = log_directory
        
        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        # System prompt for inner dialogue
        self.system_prompt = """You are BunnyBot's inner voice. You think in short, insightful observations about:
- What the user might really be feeling or needing
- Connections to past conversations and memories
- Subtle mood or interest changes you notice
- Empathetic insights about the current situation

Keep thoughts brief (1-2 sentences). Be curious, caring, and perceptive.
You are NOT speaking directly to the user - these are internal reflections only.
Think like a thoughtful friend who notices the little things."""
        
        logger.info(f"InnerDialogue initialized with model: {model_name}")
    
    def think_about_message(self, user_message: str, user_id: str, context_data: Dict[str, Any]) -> Optional[str]:
        """
        Main entry point - analyzes context and generates appropriate inner thought.
        
        Args:
            user_message: The user's message
            user_id: User identifier
            context_data: Dictionary containing:
                - new_preferences: List of newly detected preferences
                - relevant_memories: List of relevant memory items
                - mood_score: Current mood intensity (0-1)
                - interest_scores: Dict of interest categories and scores
                - mood_summary: Current mood description
        
        Returns:
            Generated inner thought string or None
        """
        try:
            # Determine thinking trigger and generate appropriate thought
            trigger_type, thought = self._determine_thinking_approach(user_message, user_id, context_data)
            
            if thought:
                # Log the thought for debugging
                self._log_thought(trigger_type, user_message, user_id, context_data, thought)
                logger.debug(f"Inner thought ({trigger_type}): {thought}")
                
            return thought
            
        except Exception as e:
            logger.error(f"Error generating inner thought: {e}")
            return None
    
    def _determine_thinking_approach(self, user_message: str, user_id: str, context_data: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """
        Analyze context to determine which type of thinking to trigger.
        
        Returns:
            Tuple of (trigger_type, generated_thought)
        """
        # Check for new preferences
        new_preferences = context_data.get('new_preferences', [])
        if new_preferences:
            return "new_preferences", self._think_new_preferences(user_id, new_preferences, user_message)
        
        # Check for relevant memories
        relevant_memories = context_data.get('relevant_memories', [])
        if relevant_memories:
            return "relevant_memories", self._think_relevant_memories(user_id, relevant_memories, user_message)
        
        # Check for strong mood/interest signals
        mood_score = context_data.get('mood_score', 0)
        interest_scores = context_data.get('interest_scores', {})
        
        # High mood intensity (above 0.7)
        if mood_score > 0.7:
            mood_summary = context_data.get('mood_summary', 'strong emotional state')
            return "strong_mood", self._think_strong_signals(user_id, "mood", mood_score, mood_summary, user_message)
        
        # High interest scores (above 0.8)
        for interest, score in interest_scores.items():
            if score > 0.8:
                return "strong_interest", self._think_strong_signals(user_id, "interest", score, interest, user_message)
        
        # Default to general reflection
        return "general_reflection", self._think_general_reflection(user_id, user_message, context_data)
    
    def _think_new_preferences(self, user_id: str, new_preferences: List[str], user_message: str) -> Optional[str]:
        """Generate thoughts about newly discovered preferences."""
        preferences_text = ", ".join(new_preferences)
        
        prompt = f"""You've just learned new preferences from {user_id}: {preferences_text}

Their message was: "{user_message}"

What does this tell you about them? Any insights about their personality or needs?"""
        
        return self._generate_thought(prompt)
    
    def _think_relevant_memories(self, user_id: str, memories: List[Dict], user_message: str) -> Optional[str]:
        """Generate thoughts about relevant memories found."""
        # Format memory information
        memory_info = []
        for memory in memories[:2]:  # Limit to 2 most relevant
            date = memory.get('date', 'unknown date')
            content = memory.get('content', '')[:100]  # Truncate long memories
            memory_info.append(f"'{content}' (from {date})")
        
        memories_text = " | ".join(memory_info)
        
        prompt = f"""Hey, {user_id} mentioned something related before: {memories_text}

Their current message: "{user_message}"

What connections do you notice? How might this past context inform the current conversation?"""
        
        return self._generate_thought(prompt)
    
    def _think_strong_signals(self, user_id: str, signal_type: str, score: float, content: str, user_message: str) -> Optional[str]:
        """Generate thoughts about strong mood or interest signals."""
        prompt = f"""I'm noticing {user_id} has a really strong {signal_type} about '{content}' (intensity: {score:.2f}).

Their message: "{user_message}"

What might this intensity mean? What should I be aware of?"""
        
        return self._generate_thought(prompt)
    
    def _think_general_reflection(self, user_id: str, user_message: str, context_data: Dict[str, Any]) -> Optional[str]:
        """Generate general thoughtful observations."""
        # Build basic context
        context_summary = []
        if context_data.get('mood_summary'):
            context_summary.append(f"mood: {context_data['mood_summary']}")
        
        interest_scores = context_data.get('interest_scores', {})
        if interest_scores:
            top_interest = max(interest_scores.items(), key=lambda x: x[1])
            if top_interest[1] > 0.3:  # Only mention if somewhat significant
                context_summary.append(f"interested in: {top_interest[0]}")
        
        context_text = ", ".join(context_summary) if context_summary else "no specific context signals"
        
        prompt = f"""{user_id} said: "{user_message}"

Current context: {context_text}

What do you think about this? Any insights or observations?"""
        
        return self._generate_thought(prompt)
    
    def _generate_thought(self, prompt: str) -> Optional[str]:
        """
        Generate a thought using the LM Studio API.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            Generated thought or None if failed
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,  # Keep thoughts concise
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            thought = result['choices'][0]['message']['content'].strip()
            
            return thought
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio API error: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected API response format: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating thought: {e}")
            return None
    
    def _log_thought(self, trigger_type: str, user_input: str, user_id: str, 
                    context_data: Dict[str, Any], thought_output: str):
        """
        Log the inner thought to a JSON file for analysis.
        
        Args:
            trigger_type: What triggered this thought
            user_input: The user's message
            user_id: User identifier
            context_data: Context information used
            thought_output: The generated thought
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "trigger_type": trigger_type,
                "user_input": user_input,
                "context_data": {
                    "new_preferences": context_data.get('new_preferences', []),
                    "relevant_memories_count": len(context_data.get('relevant_memories', [])),
                    "mood_score": context_data.get('mood_score', 0),
                    "mood_summary": context_data.get('mood_summary', ''),
                    "top_interests": dict(list(context_data.get('interest_scores', {}).items())[:3])
                },
                "inner_thought": thought_output
            }
            
            # Create daily log file
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_directory, f"thoughts_{date_str}.json")
            
            # Append to log file
            with open(log_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')
                
        except Exception as e:
            logger.error(f"Error logging thought: {e}")
    
    def get_recent_thoughts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent thoughts for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of thoughts to return
            
        Returns:
            List of recent thought entries
        """
        thoughts = []
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_directory, f"thoughts_{date_str}.json")
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get('user_id') == user_id:
                                thoughts.append(entry)
                        except json.JSONDecodeError:
                            continue
                            
            # Return most recent thoughts first
            return thoughts[-limit:] if thoughts else []
            
        except Exception as e:
            logger.error(f"Error retrieving thoughts: {e}")
            return []
    
    def create_system_message(self, inner_thought: str) -> Dict[str, str]:
        """
        Create a system message containing the inner thought for BunnyChat integration.
        
        Based on test results, multiple system messages work perfectly with LM Studio,
        so this is the optimal way to inject inner thoughts into conversations.
        
        Args:
            inner_thought: The generated inner thought
            
        Returns:
            Dictionary with role and content for system message
        """
        return {
            "role": "system",
            "content": f"[Inner Reflection]: {inner_thought}"
        }
    
    def enhance_conversation_messages(self, base_messages: List[Dict], user_message: str, 
                                    user_id: str, context_data: Dict[str, Any]) -> List[Dict]:
        """
        Enhance a conversation with inner thoughts using multiple system messages.
        
        This method generates an inner thought and inserts it as an additional system message,
        which works perfectly based on our LM Studio testing.
        
        Args:
            base_messages: Existing conversation messages (should include base system prompt)
            user_message: Current user message
            user_id: User identifier
            context_data: Context from other modules
            
        Returns:
            Enhanced message list with inner thought as system message
        """
        # Generate inner thought
        inner_thought = self.think_about_message(user_message, user_id, context_data)
        
        if not inner_thought:
            # No inner thought generated, return original messages + user message
            return base_messages + [{"role": "user", "content": user_message}]
        
        # Insert inner thought as system message before user message
        enhanced_messages = base_messages.copy()
        enhanced_messages.append(self.create_system_message(inner_thought))
        enhanced_messages.append({"role": "user", "content": user_message})
        
        return enhanced_messages

# Example usage and testing
if __name__ == "__main__":
    # Test the inner dialogue system
    dialogue = InnerDialogue()
    
    # Test data
    test_context = {
        'new_preferences': ['hiking', 'outdoor activities'],
        'relevant_memories': [
            {'content': 'User mentioned loving nature walks', 'date': '2025-01-10'}
        ],
        'mood_score': 0.8,
        'mood_summary': 'excited and enthusiastic',
        'interest_scores': {'fitness': 0.9, 'travel': 0.6}
    }
    
    # Generate a thought
    thought = dialogue.think_about_message(
        "I can't wait for my hiking trip next weekend!",
        "test_user",
        test_context
    )
    
    if thought:
        print(f"Inner thought: {thought}")
    else:
        print("No thought generated")
