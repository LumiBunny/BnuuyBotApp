"""
Speculative Thinking Module

Handles speculative decoding for generating responses with inner thoughts.
Uses a smaller "draft" model for quick inner thoughts and main model for responses.
Extracted from the mood module to create a dedicated thinking system.
"""

import logging
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

class SpeculativeThinking:
    """
    Implements speculative decoding with inner thoughts generation.
    
    Uses a smaller "draft" model for generating quick inner thoughts
    and a main model for generating the final response, guided by those thoughts.
    """
    
    def __init__(self, main_model_client, draft_model_client=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the speculative thinking system.
        
        Args:
            main_model_client: Primary model client for generating responses
            draft_model_client: Optional smaller/faster model for inner thoughts
            config: Configuration dictionary
        """
        self.main_model = main_model_client
        self.draft_model = draft_model_client
        
        # This would integrate with LM Studio's speculative decoding when available
        self.speculative_enabled = draft_model_client is not None
        
        self.config = config or {
            'enable_speculative_thinking': True,
            'thinking_role': 'thinking',  # Role name for inner thoughts in messages
            'max_thinking_tokens': 150,
            'thinking_temperature': 0.7,
            'response_temperature': 0.8,
            'fallback_to_regular': True
        }
        
        logger.info(f"SpeculativeThinking initialized - Speculative enabled: {self.speculative_enabled}")
    
    async def generate_with_inner_thoughts(self, messages: List[Dict], context: Optional[str] = None) -> Dict[str, str]:
        """
        Generate responses with speculative inner thoughts.
        
        Args:
            messages: List of conversation messages
            context: Optional context string (e.g., mood context)
        
        Returns:
            Dictionary containing inner_thoughts, response, and method used
        """
        if not self.config.get('enable_speculative_thinking', True):
            return await self._generate_regular(messages)
        
        if not self.speculative_enabled:
            # Fallback to regular generation
            if self.config.get('fallback_to_regular', True):
                return await self._generate_regular(messages)
            else:
                raise ValueError("Speculative thinking is disabled and fallback is not allowed")
        
        try:
            # Step 1: Generate inner thoughts with draft model (fast)
            inner_thoughts_prompt = self._create_thinking_prompt(messages, context)
            inner_thoughts = await self._generate_draft_thoughts(inner_thoughts_prompt)
            
            # Step 2: Use inner thoughts to guide main model response
            enhanced_messages = self._enhance_messages_with_thoughts(messages, inner_thoughts)
            main_response = await self._generate_main_response(enhanced_messages)
            
            return {
                "inner_thoughts": inner_thoughts,
                "response": main_response,
                "method": "speculative"
            }
            
        except Exception as e:
            logger.error(f"Error in speculative thinking: {e}")
            if self.config.get('fallback_to_regular', True):
                logger.info("Falling back to regular generation")
                return await self._generate_regular(messages)
            else:
                raise
    
    def _create_thinking_prompt(self, messages: List[Dict], context: Optional[str] = None) -> str:
        """
        Create a prompt for generating inner thoughts.
        
        Args:
            messages: Conversation messages
            context: Optional context information
        
        Returns:
            Formatted prompt for inner thoughts generation
        """
        # Get the last user message for context
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        prompt_parts = ["Think about how to respond to this message."]
        
        if context:
            prompt_parts.append(f"Context: {context}")
        
        if last_user_message:
            prompt_parts.append(f"User message: {last_user_message}")
        
        prompt_parts.append("What should I consider in my response? Keep it brief and focused.")
        
        return " ".join(prompt_parts)
    
    def _enhance_messages_with_thoughts(self, messages: List[Dict], inner_thoughts: str) -> List[Dict]:
        """
        Add inner thoughts to the message list.
        
        Args:
            messages: Original message list
            inner_thoughts: Generated inner thoughts
        
        Returns:
            Enhanced message list with thinking context
        """
        thinking_message = {
            "role": self.config.get('thinking_role', 'thinking'),
            "content": inner_thoughts
        }
        
        # Insert thinking before the last user message for better context
        if messages and messages[-1]["role"] == "user":
            return messages[:-1] + [thinking_message] + [messages[-1]]
        else:
            return messages + [thinking_message]
    
    async def _generate_draft_thoughts(self, prompt: str) -> str:
        """
        Generate quick inner thoughts with draft model.
        
        Args:
            prompt: Prompt for generating thoughts
        
        Returns:
            Generated inner thoughts string
        """
        if not self.draft_model:
            # If no draft model, use main model with different parameters
            return await self._generate_with_model(
                self.main_model, 
                prompt, 
                max_tokens=self.config.get('max_thinking_tokens', 150),
                temperature=self.config.get('thinking_temperature', 0.7)
            )
        
        # Use draft model for faster generation
        return await self._generate_with_model(
            self.draft_model,
            prompt,
            max_tokens=self.config.get('max_thinking_tokens', 150),
            temperature=self.config.get('thinking_temperature', 0.7)
        )
    
    async def _generate_main_response(self, messages: List[Dict]) -> str:
        """
        Generate main response with full model.
        
        Args:
            messages: Enhanced message list with thinking context
        
        Returns:
            Generated response string
        """
        # Convert messages to a format suitable for the model
        prompt = self._messages_to_prompt(messages)
        
        return await self._generate_with_model(
            self.main_model,
            prompt,
            temperature=self.config.get('response_temperature', 0.8)
        )
    
    async def _generate_regular(self, messages: List[Dict]) -> Dict[str, str]:
        """
        Fallback regular generation without speculative thinking.
        
        Args:
            messages: Message list
        
        Returns:
            Dictionary with response and method used
        """
        prompt = self._messages_to_prompt(messages)
        response = await self._generate_with_model(
            self.main_model,
            prompt,
            temperature=self.config.get('response_temperature', 0.8)
        )
        
        return {
            "inner_thoughts": None,
            "response": response,
            "method": "regular"
        }
    
    async def _generate_with_model(self, model_client, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.8) -> str:
        """
        Generate text with a specific model client.
        
        This is a placeholder method that should be implemented based on
        the specific LM Studio API or model client being used.
        
        Args:
            model_client: Model client to use
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        
        Returns:
            Generated text
        """
        # TODO: Implement actual model generation based on LM Studio API
        # This is a placeholder implementation
        logger.warning("_generate_with_model is not implemented - using placeholder")
        
        if "think" in prompt.lower() or "consider" in prompt.lower():
            return "I should respond thoughtfully and consider the user's emotional state."
        else:
            return "This is a placeholder response. Please implement the actual model generation."
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """
        Convert message list to a single prompt string.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "thinking":
                prompt_parts.append(f"[Thinking] {content}")
            elif role == "observation":
                prompt_parts.append(f"[Observation] {content}")
            else:
                prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the configuration for speculative thinking."""
        self.config.update(new_config)
        logger.info(f"SpeculativeThinking config updated: {new_config}")
    
    def set_draft_model(self, draft_model_client) -> None:
        """Set or update the draft model client."""
        self.draft_model = draft_model_client
        self.speculative_enabled = draft_model_client is not None
        logger.info(f"Draft model updated - Speculative enabled: {self.speculative_enabled}")


# Example usage and testing
if __name__ == "__main__":
    # Mock model clients for testing
    class MockModelClient:
        def __init__(self, name: str):
            self.name = name
    
    async def test_speculative_thinking():
        # Test with mock clients
        main_model = MockModelClient("main")
        draft_model = MockModelClient("draft")
        
        thinking = SpeculativeThinking(main_model, draft_model)
        
        # Test messages
        test_messages = [
            {"role": "user", "content": "I'm feeling really excited about this new project!"}
        ]
        
        # Test generation (will use placeholder implementation)
        result = await thinking.generate_with_inner_thoughts(
            test_messages, 
            context="User seems enthusiastic and energetic"
        )
        
        print(f"Method: {result['method']}")
        print(f"Inner thoughts: {result['inner_thoughts']}")
        print(f"Response: {result['response']}")
    
    # Run the test
    asyncio.run(test_speculative_thinking())
