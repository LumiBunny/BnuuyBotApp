from datetime import datetime, timedelta
from typing import Dict, List
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
        
        # Sentiment indicators
        self.positive_indicators = ['love', 'like', 'enjoy', 'adore', 'prefer', 'favorite', 'fond of']
        self.negative_indicators = ['hate', 'dislike', 'boring', 'annoying', 'terrible', 'awful', 'worst']
        self.negation_words = ['not', 'never', 'dont', "don't", 'doesnt', "doesn't"]
        
    def track_conversation_interests(self, user_id: str, conversation_text: str, 
                                   timestamp: datetime = None) -> Dict[str, float]:
        """
        Analyze conversation for interest signals and update interest scores.
        Returns dict of {topic: interest_score}
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        logger.info(f"Analyzing interests in: {conversation_text[:100]}...")
        
        # Extract topics mentioned (simple keyword approach)
        interests = self._extract_topics_from_text(conversation_text)
        logger.info(f"Extracted interests: {interests}")
        
        # Update interest scores based on frequency and recency
        updated_interests = {}
        for topic, mentions in interests.items():
            score = self._calculate_interest_score(user_id, topic, mentions, timestamp, conversation_text)
            updated_interests[topic] = score
            
            # Always save to interests storage (separate from important memories)
            if self.memory_manager and hasattr(self.memory_manager, 'add_interest'):
                try:
                    self.memory_manager.add_interest(
                        user_id=user_id,
                        topic=topic,
                        score=score,
                        context=conversation_text[:200]  # Save a snippet for context
                    )
                    logger.info(f"Updated interest score for {topic}: {score:.2f}")
                except Exception as e:
                    logger.error(f"Error updating interest for {topic}: {e}")
        
        return updated_interests
    
    def get_top_interests(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get user's top interests based on stored interest scores."""
        if not self.memory_manager or not hasattr(self.memory_manager, 'get_interests'):
            logger.warning("MemoryManager not available or missing get_interests method")
            return []
            
        try:
            # Get all interests with score > 0
            interests = self.memory_manager.get_interests(user_id, min_score=0.01)
            
            if not interests:
                logger.debug(f"No interests found for user {user_id}")
                return []
            
            # Convert to list of dicts and sort by score (descending)
            sorted_interests = [
                {'topic': topic, 'score': float(data['score']), 'last_updated': data['last_updated']}
                for topic, data in interests.items()
            ]
            sorted_interests.sort(key=lambda x: x['score'], reverse=True)
            
            logger.debug(f"Retrieved {len(sorted_interests)} interests for user {user_id}")
            return sorted_interests[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top interests for {user_id}: {e}")
            return []
    
    def _extract_topics_from_text(self, text: str) -> Dict[str, int]:
        """Extract topics and count mentions from conversation text."""
        # Simple topic extraction - you could enhance this with spaCy later
        topic_keywords = {
            'gaming': ['game', 'gaming', 'play', 'minecraft', 'zelda', 'steam', 'xbox', 'playstation'],
            'cooking': ['cook', 'recipe', 'food', 'kitchen', 'bake', 'meal', 'chef', 'ingredient', 'pasta'],
            'art': ['art', 'draw', 'paint', 'sketch', 'creative', 'design', 'canvas', 'brush'],
            'music': ['music', 'song', 'band', 'listen', 'album', 'concert', 'guitar', 'piano'],
            'fitness': ['workout', 'gym', 'exercise', 'run', 'fitness', 'health', 'training', 'cardio'],
            'travel': ['travel', 'trip', 'vacation', 'visit', 'explore', 'country', 'flight', 'hotel'],
            'technology': ['tech', 'computer', 'programming', 'code', 'software', 'app', 'website'],
            'movies': ['movie', 'film', 'cinema', 'series', 'show', 'episode', 'netflix'],
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
    
    def _detect_sentiment(self, text: str, topic: str) -> float:
        """Detect sentiment about a topic in the given text.
        Returns: 
            float: Sentiment score between -1.0 (negative) and 1.0 (positive)
        """
        text_lower = text.lower()
        sentiment = 0.0
        
        # Check for positive indicators
        for word in self.positive_indicators:
            if word in text_lower:
                # Check for negation (e.g., "don't like")
                if any(neg in text_lower.split(text_lower.split(word)[0])[-1].split()[:2] for neg in self.negation_words):
                    sentiment -= 0.2
                else:
                    sentiment += 0.3
        
        # Check for negative indicators
        for word in self.negative_indicators:
            if word in text_lower:
                # Check for negation (e.g., "not bad")
                if any(neg in text_lower.split(text_lower.split(word)[0])[-1].split()[:2] for neg in self.negation_words):
                    sentiment += 0.2
                else:
                    sentiment -= 0.3
        
        return max(-1.0, min(1.0, sentiment))  # Clamp between -1.0 and 1.0

    def _calculate_interest_score(self, user_id: str, topic: str, 
                                current_mentions: int, timestamp: datetime, 
                                conversation_text: str = "") -> float:
        """Calculate interest score based on frequency, recency, and history."""
        # Get existing interest score from MemoryManager
        existing_score = 0.0
        if self.memory_manager and hasattr(self.memory_manager, 'get_interests'):
            try:
                existing_interests = self.memory_manager.get_interests(user_id)
                if topic in existing_interests:
                    existing_score = float(existing_interests[topic].get('score', 0.0))
                    logger.debug(f"Found existing score for {topic}: {existing_score}")
            except Exception as e:
                logger.warning(f"Could not get existing interests: {e}")
        
        # Base score from current mentions (more generous scoring)
        base_score = min(current_mentions * 0.15, 0.4)  # Increased from 0.1 to 0.15
        
        # Get sentiment score for this mention
        sentiment = self._detect_sentiment(conversation_text, topic)
        
        # Adjust base score based on sentiment (more impactful)
        sentiment_boost = sentiment * 0.25  # Increased from 0.2 to 0.25
        base_score += sentiment_boost
        
        # Ensure base score is positive for any mention
        base_score = max(base_score, 0.1)  # Minimum score for any detected interest
        
        # Handle accumulation differently based on whether interest exists
        if existing_score > 0:
            # Existing interest: accumulate with decay to prevent runaway growth
            decay_factor = 0.85  # Slightly more aggressive decay
            combined_score = (existing_score * decay_factor) + base_score
            
            # Bonus for building on existing interest
            combined_score += 0.08  # Increased bonus
            
            logger.debug(f"Accumulating: {existing_score:.3f} * {decay_factor} + {base_score:.3f} + 0.08 = {combined_score:.3f}")
        else:
            # New interest: start with base score
            combined_score = base_score
            logger.debug(f"New interest: starting with {combined_score:.3f}")
        
        # Ensure score is between 0 and 1, never negative
        final_score = max(0.0, min(1.0, combined_score))
        
        logger.debug(f"Interest score calculation for {topic}: existing={existing_score:.3f}, "
                    f"base={base_score:.3f}, sentiment={sentiment:.3f}, final={final_score:.3f}")
        
        return final_score

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
