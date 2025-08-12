"""
Thinking Module - Inner Thoughts and Cognitive Processing

This module handles the AI's internal thought processes, including:
- Inner thoughts generation
- Speculative decoding for cognitive processing
- Message enhancement with thinking context
- Integration bridge with mood system
- Comprehensive integration with preferences, interests, and mood
"""

from .inner_thoughts import InnerThoughtsGenerator
from .speculative_thinking import SpeculativeThinking
from .mood_thinking_bridge import MoodThinkingBridge
from .thinking_bridge import ThinkingBridge

__all__ = [
    'InnerThoughtsGenerator', 
    'SpeculativeThinking', 
    'MoodThinkingBridge',
    'ThinkingBridge'
]
