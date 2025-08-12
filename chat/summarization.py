import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ChatSummarizer:
    """
    Handles chat history summarization with incremental approach:
    - One JSON file per chat session
    - Brief summary appended every 20 messages
    - Session start/end timestamps
    - Final summary of remaining messages on session end/reset
    """
    
    def __init__(self, 
                 user_id: str,
                 base_data_dir: str = "user_data",
                 lm_studio_endpoint: str = "http://localhost:1234/v1/chat/completions",
                 model_name: str = "llama-3.2-1b-instruct-uncensored",
                 messages_per_summary: int = 20):
        """
        Initialize the chat summarizer.
        
        Args:
            user_id: User identifier for directory structure
            base_data_dir: Base directory for user data
            lm_studio_endpoint: LM Studio API endpoint
            model_name: Model name for summarization
            messages_per_summary: Number of messages before auto-summary
        """
        self.user_id = user_id
        self.base_data_dir = Path(base_data_dir)
        self.lm_studio_endpoint = lm_studio_endpoint
        self.model_name = model_name
        self.messages_per_summary = messages_per_summary
        
        # Setup user directory structure
        self.user_dir = self.base_data_dir / user_id
        self.summaries_dir = self.user_dir / "conversations" / "summaries"
        self.raw_chats_dir = self.user_dir / "conversations" / "raw_chats"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Track current session
        self.session_start_time = datetime.now()
        self.message_count = 0
        self.last_summary_count = 0
        self.session_file = None
        self.session_data = None
        
        # Initialize session file
        self._initialize_session_file()
        
    def _ensure_directories(self):
        """Create necessary directory structure."""
        for directory in [self.summaries_dir, self.raw_chats_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _initialize_session_file(self):
        """Initialize the session summary file."""
        # Create filename with session start timestamp
        filename = f"session_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.session_file = self.summaries_dir / filename
        
        # Initialize session data structure
        self.session_data = {
            "session_start": self.session_start_time.isoformat(),
            "session_end": None,
            "user_id": self.user_id,
            "total_messages": 0,
            "status": "active",
            "periodic_summaries": [],
            "final_summary": None
        }
        
        # Save initial file
        self._save_session_file()
        logger.info(f"Initialized session file: {self.session_file}")
    
    def _save_session_file(self):
        """Save the current session data to file."""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving session file: {e}")
    
    def _call_lm_studio(self, prompt: str, max_tokens: int = 150) -> str:
        """
        Call LM Studio API for summarization.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens for response (reduced for brevity)
            
        Returns:
            Generated summary text
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates very brief, concise summaries. Keep summaries to 1-2 sentences maximum. Focus only on the most important topics and key information."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
                "stream": False
            }
            
            response = requests.post(self.lm_studio_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Error calling LM Studio for summarization: {e}")
            return f"[Summary generation failed: {str(e)}]"
    
    def _create_brief_summary_prompt(self, messages: List[Dict]) -> str:
        """
        Create a prompt for brief periodic summaries.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt for summarization
        """
        # Format messages for the prompt
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role in ['user', 'assistant']:
                formatted_messages.append(f"{role.capitalize()}: {content}")
        
        messages_text = "\n".join(formatted_messages)
        
        prompt = f"""Create a very brief summary (1-2 sentences maximum) of these recent messages:

{messages_text}

Focus only on the most important topics discussed. Be extremely concise:"""
        
        return prompt
    
    def check_and_summarize(self, current_messages: List[Dict]) -> Optional[str]:
        """
        Check if summarization is needed and append to session file.
        
        Args:
            current_messages: Current list of chat messages
            
        Returns:
            Summary text if created, None otherwise
        """
        self.message_count = len(current_messages)
        messages_since_last_summary = self.message_count - self.last_summary_count
        
        if messages_since_last_summary >= self.messages_per_summary:
            # Get messages since last summary
            messages_to_summarize = current_messages[self.last_summary_count:]
            
            # Generate brief summary
            summary = self._generate_brief_summary(messages_to_summarize)
            
            # Append to session data
            summary_entry = {
                "timestamp": datetime.now().isoformat(),
                "message_range": f"{self.last_summary_count + 1}-{self.message_count}",
                "summary": summary
            }
            
            self.session_data["periodic_summaries"].append(summary_entry)
            self.session_data["total_messages"] = self.message_count
            
            # Update tracking
            self.last_summary_count = self.message_count
            
            # Save updated session file
            self._save_session_file()
            
            logger.info(f"Appended periodic summary at {self.message_count} messages")
            return summary
        
        return None
    
    def _generate_brief_summary(self, messages: List[Dict]) -> str:
        """
        Generate a brief summary for the given messages.
        
        Args:
            messages: Messages to summarize
            
        Returns:
            Generated brief summary text
        """
        prompt = self._create_brief_summary_prompt(messages)
        return self._call_lm_studio(prompt, max_tokens=100)  # Very brief
    
    def end_session(self, all_messages: List[Dict], end_reason: str = "session_ended") -> str:
        """
        End the session and finalize the summary file.
        
        Args:
            all_messages: All messages from the session
            end_reason: Reason for ending ("session_ended" or "reset")
            
        Returns:
            Final summary text
        """
        # Handle any remaining unsummarized messages
        messages_since_last = all_messages[self.last_summary_count:]
        
        if messages_since_last:
            # Generate summary for remaining messages
            remaining_summary = self._generate_brief_summary(messages_since_last)
            
            # Add to periodic summaries
            summary_entry = {
                "timestamp": datetime.now().isoformat(),
                "message_range": f"{self.last_summary_count + 1}-{len(all_messages)}",
                "summary": remaining_summary,
                "type": "final_chunk"
            }
            
            self.session_data["periodic_summaries"].append(summary_entry)
        
        # Generate overall session summary if we have multiple chunks
        if len(self.session_data["periodic_summaries"]) > 1:
            all_summaries = [entry["summary"] for entry in self.session_data["periodic_summaries"]]
            combined_text = " ".join(all_summaries)
            
            final_prompt = f"""Create a brief overall summary (2-3 sentences) of this entire chat session based on these periodic summaries:

{combined_text}

Provide a cohesive overview of the main topics and outcomes:"""
            
            final_summary = self._call_lm_studio(final_prompt, max_tokens=150)
        elif len(self.session_data["periodic_summaries"]) == 1:
            final_summary = self.session_data["periodic_summaries"][0]["summary"]
        else:
            # No periodic summaries - summarize all messages directly
            final_summary = self._generate_brief_summary(all_messages)
        
        # Finalize session data
        self.session_data["session_end"] = datetime.now().isoformat()
        self.session_data["total_messages"] = len(all_messages)
        self.session_data["status"] = f"ended_{end_reason}"
        self.session_data["final_summary"] = final_summary
        
        # Save final session file
        self._save_session_file()
        
        logger.info(f"Session ended: {end_reason}")
        return final_summary
    
    def reset_session(self):
        """Reset for a new chat session."""
        self.session_start_time = datetime.now()
        self.message_count = 0
        self.last_summary_count = 0
        
        # Initialize new session file
        self._initialize_session_file()
        
        logger.info("Chat summarizer reset for new session")

    def get_session_summary(self) -> Dict:
        """Get current session summary data."""
        return self.session_data.copy() if self.session_data else {}

# Example usage
if __name__ == "__main__":
    # Test the summarizer
    summarizer = ChatSummarizer("test_user", messages_per_summary=3)  # Low threshold for testing
    
    # Simulate some messages
    test_messages = [
        {"role": "user", "content": "Hello! I love pizza", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "Hi! Pizza is great! What's your favorite topping?", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "I really enjoy pepperoni and mushrooms", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "Great choice! Those are classic toppings", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "Do you have any cooking tips?", "timestamp": datetime.now().isoformat()},
    ]
    
    # Test periodic summarization
    for i in range(len(test_messages)):
        current_batch = test_messages[:i+1]
        summary = summarizer.check_and_summarize(current_batch)
        if summary:
            print(f"Periodic summary at message {i+1}: {summary}")
    
    # Test session end
    final_summary = summarizer.end_session(test_messages, "test_ended")
    print(f"Final summary: {final_summary}")
    
    print(f"Session file created: {summarizer.session_file}")
