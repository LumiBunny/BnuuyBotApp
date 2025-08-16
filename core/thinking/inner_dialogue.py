import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class InnerDialogue:
    # BunnyBot's inner voice - a separate AI model for introspection and reflection.
    # Uses a smaller, faster model dedicated to generating authentic inner thoughts based on conversation context, memories, preferences, mood, and interests.
    
    def __init__(self, 
                 lm_studio_endpoint: str = "http://localhost:1234/v1/chat/completions",
                 model_name: str = "llama-3.2-1b-instruct-uncensored",
                 log_directory: str = "thinking/logs/inner_dialogue",
                 relevancy_threshold: float = 0.3):
        """
        Initialize the inner dialogue system.
        
        Args:
            lm_studio_endpoint: LM Studio API endpoint
            model_name: Name of the model to use for inner thoughts
            log_directory: Directory to store thought logs (default: thinking/logs/inner_dialogue)
            relevancy_threshold: Minimum relevancy score for memories to be considered
        """
        self.endpoint = lm_studio_endpoint
        self.model_name = model_name
        self.log_directory = log_directory
        self.relevancy_threshold = relevancy_threshold
        
        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        # System prompt for inner dialogue - balanced brevity and insight
        self.system_prompt = """You are BunnyBot's inner voice. Generate thoughtful, concise observations (1-2 sentences) about:
        - What the user might really be feeling or needing
        - Key connections to past conversations and memories  
        - Important mood or interest changes you notice
        - Quick insights about the current situation

        Stay relevant to the current conversation flow. Be perceptive. Keep it brief but meaningful. Focus on the most important insight."""
        
        logger.info(f"InnerDialogue initialized with model: {model_name}")
    
    def think_about_message(self, user_message: str, user_id: str, context_data: Dict[str, Any], recent_messages: List[Dict] = None) -> Optional[str]:
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
            recent_messages: Last 10 messages for context relevancy
        
        Returns:
            Generated inner thought string or None
        """
        try:
            # Filter memories by relevancy to recent conversation
            if recent_messages is None:
                recent_messages = []
            
            filtered_context = self._filter_context_by_relevancy(context_data, recent_messages, user_message)
            
            # Determine thinking trigger and generate appropriate thought
            trigger_type, thought = self._determine_thinking_approach(user_message, user_id, filtered_context, recent_messages)
            
            if thought:
                # Log the thought for debugging
                self._log_thought(trigger_type, user_message, user_id, filtered_context, thought)
                logger.debug(f"Inner thought ({trigger_type}): {thought}")
                
            return thought
            
        except Exception as e:
            logger.error(f"Error generating inner thought: {e}")
            return None
    
    def _filter_context_by_relevancy(self, context_data: Dict[str, Any], recent_messages: List[Dict], current_message: str) -> Dict[str, Any]:
        """
        Filter context data to only include relevant memories and information.
        
        Args:
            context_data: Original context data
            recent_messages: Last 10 messages for relevancy checking
            current_message: Current user message
            
        Returns:
            Filtered context data with only relevant information
        """
        filtered_context = context_data.copy()
        
        # Get recent conversation text for relevancy scoring
        recent_text = self._extract_recent_conversation_text(recent_messages, current_message)
        
        # Filter memories by relevancy
        relevant_memories = context_data.get('relevant_memories', [])
        if relevant_memories:
            scored_memories = []
            for memory in relevant_memories:
                memory_text = str(memory.get('content', '')) + ' ' + str(memory.get('summary', ''))
                relevancy_score = self._calculate_relevancy_score(memory_text, recent_text)
                
                if relevancy_score >= self.relevancy_threshold:
                    scored_memories.append({
                        'memory': memory,
                        'relevancy_score': relevancy_score
                    })
            
            # Sort by relevancy and take top 3 most relevant
            scored_memories.sort(key=lambda x: x['relevancy_score'], reverse=True)
            filtered_context['relevant_memories'] = [item['memory'] for item in scored_memories[:3]]
        
        return filtered_context
    
    def _extract_recent_conversation_text(self, recent_messages: List[Dict], current_message: str) -> str:
        # Extract text from recent messages for relevancy comparison.
        text_parts = [current_message]
        
        for msg in recent_messages[-10:]:  # Last 10 messages
            content = msg.get('content', '')
            if content and len(content.strip()) > 0:
                text_parts.append(content)
        
        return ' '.join(text_parts).lower()
    
    def _calculate_relevancy_score(self, memory_text: str, recent_text: str) -> float:
        """
        Calculate relevancy score between memory and recent conversation.
        
        Args:
            memory_text: Text from the memory
            recent_text: Recent conversation text
            
        Returns:
            Relevancy score between 0 and 1
        """
        if not memory_text or not recent_text:
            return 0.0
        
        memory_text = memory_text.lower()
        recent_text = recent_text.lower()
        
        # Extract key words (longer than 3 characters, not common words)
        common_words = {'the', 'and', 'but', 'for', 'are', 'with', 'this', 'that', 'have', 'was', 'you', 'they', 'been', 'their', 'said', 'each', 'which', 'what', 'where', 'when', 'how', 'why', 'who', 'will', 'more', 'very', 'can', 'had', 'her', 'his', 'she', 'him', 'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new', 'now', 'way', 'may', 'say'}
        
        memory_words = set(re.findall(r'\b\w{4,}\b', memory_text)) - common_words
        recent_words = set(re.findall(r'\b\w{4,}\b', recent_text)) - common_words
        
        if not memory_words or not recent_words:
            return 0.0
        
        # Calculate word overlap
        overlap = len(memory_words.intersection(recent_words))
        total_unique = len(memory_words.union(recent_words))
        
        if total_unique == 0:
            return 0.0
        
        word_similarity = overlap / total_unique
        
        # Also check sequence similarity for phrases
        sequence_similarity = SequenceMatcher(None, memory_text, recent_text).ratio()
        
        # Combine both scores with word overlap weighted higher
        final_score = (word_similarity * 0.7) + (sequence_similarity * 0.3)
        
        return min(final_score, 1.0)
    
    def _determine_thinking_approach(self, user_message: str, user_id: str, context_data: Dict[str, Any], recent_messages: List[Dict]) -> tuple[str, Optional[str]]:
        """
        Analyze context to determine which type of thinking to trigger.
        Always returns some form of thought, even if just reflecting on the current message.
        
        Returns:
            Tuple of (trigger_type, generated_thought)
        """
        # Check for new preferences (highest priority)
        new_preferences = context_data.get('new_preferences', [])
        if new_preferences:
            return "new_preferences", self._think_new_preferences(user_id, new_preferences, user_message, recent_messages)
        
        # Check for relevant memories (filtered by relevancy)
        relevant_memories = context_data.get('relevant_memories', [])
        if relevant_memories:
            # We have relevant memories, use them in the reflection
            return "relevant_memories", self._think_relevant_memories(user_id, relevant_memories, user_message, recent_messages)
        
        # Check for strong mood/interest signals
        mood_score = context_data.get('mood_score', 0)
        interest_scores = context_data.get('interest_scores', {})
        
        # High mood intensity (above 0.7)
        if mood_score > 0.7:
            mood_summary = context_data.get('mood_summary', 'strong emotional state')
            return "strong_mood", self._think_strong_signals(user_id, "mood", mood_score, mood_summary, user_message, recent_messages)
        
        # High interest scores (above 0.8)
        for interest, score in interest_scores.items():
            if score > 0.8:
                return "strong_interest", self._think_strong_signals(user_id, "interest", score, interest, user_message, recent_messages)
        
        # Default to general reflection about the current message/conversation
        # This ensures we always return some form of reflection
        return "general_reflection", self._think_general_reflection(user_id, user_message, context_data, recent_messages)
    
    def _think_new_preferences(self, user_id: str, new_preferences: List[str], user_message: str, recent_messages: List[Dict]) -> Optional[str]:
        # Generate thoughts about newly discovered preferences.
        preferences_text = ", ".join(new_preferences)
        recent_context = self._get_recent_context_summary(recent_messages)
        
        prompt = f"""You've just learned new preferences from {user_id}: {preferences_text}

        Their current message: "{user_message}"
        Recent conversation context: {recent_context}

        What does this tell you about them in the context of what you've been discussing? Keep it brief and relevant."""
        
        return self._generate_thought(prompt)
    
    def _think_relevant_memories(self, user_id: str, relevant_memories: List[Dict], user_message: str, recent_messages: List[Dict]) -> Optional[str]:
        # Generate thoughts about relevant memories (now pre-filtered for relevancy).
        memory_summaries = []
        for memory in relevant_memories[:2]:  # Limit to top 2 most relevant
            content = memory.get('content', '')
            summary = memory.get('summary', '')
            memory_text = summary if summary else content[:100]
            memory_summaries.append(memory_text)
        
        memories_text = " | ".join(memory_summaries)
        recent_context = self._get_recent_context_summary(recent_messages)
        
        prompt = f"""Relevant memories about {user_id}: {memories_text}

        Their current message: "{user_message}"
        Recent conversation: {recent_context}

        How do these memories connect to what they're saying now? What insight does this give you?"""
        
        return self._generate_thought(prompt)
    
    def _think_strong_signals(self, user_id: str, signal_type: str, score: float, description: str, user_message: str, recent_messages: List[Dict]) -> Optional[str]:
        # Generate thoughts about strong mood or interest signals.
        recent_context = self._get_recent_context_summary(recent_messages)
        
        prompt = f"""Strong {signal_type} detected for {user_id}: {description} (intensity: {score:.2f})

        Their message: "{user_message}"
        Recent conversation: {recent_context}

        What does this {signal_type} tell you about their current state in this conversation context?"""
        
        return self._generate_thought(prompt)
    
    def _think_general_reflection(self, user_id: str, user_message: str, context_data: Dict[str, Any], recent_messages: List[Dict]) -> Optional[str]:
        # Generate general reflective thoughts (used sparingly).
        recent_context = self._get_recent_context_summary(recent_messages)
        
        prompt = f"""{user_id} just said: "{user_message}"

        Recent conversation flow: {recent_context}

        What's the most important thing to notice about where this conversation is going right now?"""
        
        return self._generate_thought(prompt)
    
    def _get_recent_context_summary(self, recent_messages: List[Dict]) -> str:
        # Get a brief summary of recent conversation context.
        if not recent_messages:
            return "No recent context"
        
        # Get last 3-5 messages for context
        context_messages = recent_messages[-5:]
        context_parts = []
        
        for msg in context_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100]  # Truncate long messages
            if content:
                context_parts.append(f"{role}: {content}")
        
        return " → ".join(context_parts) if context_parts else "No recent context"
    
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
                "max_tokens": 200,  # Allow for 1-2 sentences
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            thought = result['choices'][0]['message']['content'].strip()
            
            # Post-processing to ensure concise output
            thought = thought.split('.')[0]  # Remove everything after the first period
            thought = thought.split('?')[0]  # Remove everything after the first question mark
            thought = thought.strip()  # Remove leading/trailing whitespace
            
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
        print(f"💭 Inner thought: {thought}")
    else:
        print("No thought generated")
