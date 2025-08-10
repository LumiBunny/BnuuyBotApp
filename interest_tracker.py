from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class InterestTracker:
    """
    Tracks user interests over time and identifies patterns.
    Works alongside PreferenceExtractor and MemoryManager to build a dynamic interest profile.
    """
    
    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.interest_decay_days = 30  # How long before interests start fading
        self.mention_threshold = 3     # How many mentions to consider "strong interest"
        
    def track_conversation_interests(self, user_id: str, conversation_text: str, 
                                   timestamp: datetime = None) -> Dict[str, float]:
        """
        Analyze conversation for interest signals and update interest scores.
        Returns dict of {topic: interest_score}
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # Extract topics mentioned (simple keyword approach)
        interests = self._extract_topics_from_text(conversation_text)
        
        # Update interest scores based on frequency and recency
        updated_interests = {}
        for topic, mentions in interests.items():
            score = self._calculate_interest_score(user_id, topic, mentions, timestamp)
            updated_interests[topic] = score
            
            # Store in memory if significant
            if score > 0.6:
                if self.memory_manager:
                    self.memory_manager.add_memory(
                        user_id,
                        f"Showed strong interest in {topic} (score: {score:.2f})",
                        "interest",
                        importance=score,
                        tags=[topic, "interest", "conversation"],
                        context=conversation_text[:100] + "..."
                    )
        
        return updated_interests
    
    def _extract_topics_from_text(self, text: str) -> Dict[str, int]:
        """Extract topics and count mentions from conversation text."""
        # Simple topic extraction - you could enhance this with spaCy later
        topic_keywords = {
            'gaming': ['game', 'gaming', 'play', 'minecraft', 'zelda', 'steam', 'xbox', 'playstation'],
            'cooking': ['cook', 'recipe', 'food', 'kitchen', 'bake', 'meal', 'chef', 'ingredient'],
            'art': ['art', 'draw', 'paint', 'sketch', 'creative', 'design', 'canvas', 'brush'],
            'music': ['music', 'song', 'band', 'listen', 'album', 'concert', 'guitar', 'piano'],
            'fitness': ['workout', 'gym', 'exercise', 'run', 'fitness', 'health', 'training', 'cardio'],
            'travel': ['travel', 'trip', 'vacation', 'visit', 'explore', 'country', 'flight', 'hotel'],
            'technology': ['tech', 'computer', 'programming', 'code', 'software', 'app', 'website'],
            'movies': ['movie', 'film', 'watch', 'cinema', 'netflix', 'series', 'show', 'episode'],
            'reading': ['book', 'read', 'novel', 'author', 'chapter', 'library', 'story', 'literature'],
            'pets': ['dog', 'cat', 'pet', 'puppy', 'kitten', 'animal', 'vet', 'walk']
        }
        
        text_lower = text.lower()
        topic_mentions = {}
        
        for topic, keywords in topic_keywords.items():
            mentions = sum(text_lower.count(keyword) for keyword in keywords)
            if mentions > 0:
                topic_mentions[topic] = mentions
                
        return topic_mentions
    
    def _calculate_interest_score(self, user_id: str, topic: str, 
                                current_mentions: int, timestamp: datetime) -> float:
        """Calculate interest score based on frequency, recency, and history."""
        # Base score from current mentions
        base_score = min(current_mentions * 0.2, 1.0)
        
        # Get historical interest if memory manager available
        if self.memory_manager:
            # Look for past interest memories
            past_memories = self.memory_manager.find_relevant_memories(user_id, topic, max_results=10)
            interest_memories = [m for m in past_memories if m.category == "interest"]
            
            # Boost score based on consistent interest
            if len(interest_memories) >= self.mention_threshold:
                base_score *= 1.5  # 50% boost for consistent interest
                
            # Apply recency decay
            recent_mentions = sum(1 for m in interest_memories 
                                if (timestamp - m.timestamp).days <= self.interest_decay_days)
            if recent_mentions > 0:
                base_score *= (1 + recent_mentions * 0.1)
        
        return min(base_score, 1.0)
    
    def get_top_interests(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get user's top interests based on memory analysis."""
        if not self.memory_manager:
            return []
            
        # Get all interest memories
        interest_memories = self.memory_manager.get_memories(user_id, category="interest")
        
        # Count and score interests
        interest_scores = {}
        for memory in interest_memories:
            for tag in memory.tags:
                if tag != "interest" and tag != "conversation":
                    current_score = interest_scores.get(tag, 0)
                    # Weight by importance and recency
                    days_old = (datetime.now() - memory.timestamp).days
                    recency_factor = max(0.1, 1 - (days_old / self.interest_decay_days))
                    interest_scores[tag] = current_score + (memory.importance * recency_factor)
        
        # Sort and return top interests
        sorted_interests = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"topic": topic, "score": score} for topic, score in sorted_interests[:limit]]
    
    def suggest_conversation_topics(self, user_id: str) -> List[str]:
        """Suggest conversation topics based on user's interests."""
        top_interests = self.get_top_interests(user_id, limit=3)
        
        suggestions = []
        for interest in top_interests:
            topic = interest["topic"]
            # Create natural conversation starters
            topic_starters = {
                'gaming': f"How's your gaming going lately? Still playing?",
                'cooking': f"Have you tried any new recipes recently?",
                'art': f"Working on any art projects these days?",
                'music': f"Discovered any good music lately?",
                'fitness': f"How's your workout routine going?",
                'travel': f"Any travel plans coming up?",
                'technology': f"Seen any cool tech stuff recently?",
                'movies': f"Watched any good movies or shows lately?",
                'reading': f"Read any interesting books recently?",
                'pets': f"How's your pet doing?"
            }
            
            starter = topic_starters.get(topic, f"How's your {topic} going lately?")
            suggestions.append(starter)
            
        if not suggestions:
            suggestions = [
                "What have you been up to lately?", 
                "Any new hobbies or interests?",
                "How was your day?"
            ]
            
        return suggestions
    
    def detect_interest_changes(self, user_id: str, days_back: int = 30) -> Dict[str, str]:
        """
        Detect changes in user interests over time.
        Returns dict of {topic: 'increasing'/'decreasing'/'stable'}
        """
        if not self.memory_manager:
            return {}
            
        # Get interest memories from different time periods
        recent_memories = self.memory_manager.get_memories(
            user_id, category="interest", days_back=days_back//2
        )
        older_memories = self.memory_manager.get_memories(
            user_id, category="interest", days_back=days_back
        )
        
        # Count recent vs older mentions
        recent_topics = {}
        older_topics = {}
        
        cutoff_date = datetime.now() - timedelta(days=days_back//2)
        
        for memory in older_memories:
            for tag in memory.tags:
                if tag not in ["interest", "conversation"]:
                    if memory.timestamp >= cutoff_date:
                        recent_topics[tag] = recent_topics.get(tag, 0) + 1
                    else:
                        older_topics[tag] = older_topics.get(tag, 0) + 1
        
        # Analyze changes
        changes = {}
        all_topics = set(recent_topics.keys()) | set(older_topics.keys())
        
        for topic in all_topics:
            recent_count = recent_topics.get(topic, 0)
            older_count = older_topics.get(topic, 0)
            
            if recent_count > older_count * 1.5:
                changes[topic] = "increasing"
            elif older_count > recent_count * 1.5:
                changes[topic] = "decreasing"
            else:
                changes[topic] = "stable"
        
        return changes


# Example usage and testing
if __name__ == "__main__":
    # This would normally be imported and used with MemoryManager
    print("InterestTracker module - import this into your main application")
    
    # Example of how to use it:
    # from memory_manager import MemoryManager
    # from interest_tracker import InterestTracker
    # 
    # memory_manager = MemoryManager()
    # interest_tracker = InterestTracker(memory_manager)
    # 
    # interests = interest_tracker.track_conversation_interests(
    #     "user123", 
    #     "I love playing Minecraft and cooking pasta!"
    # )
    # print(f"Detected interests: {interests}")
