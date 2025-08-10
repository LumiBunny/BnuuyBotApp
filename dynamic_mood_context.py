import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class MoodObservation:
    # Temporary mood observation for context
    mood: str
    intensity: float
    confidence: float
    context: str
    timestamp: datetime
    decay_factor: float = 1.0  # How much this observation should influence context
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'age_minutes': (datetime.now() - self.timestamp).total_seconds() / 60
        }

class DynamicMoodContext:
    # Manages temporary mood observations for LLM context
    # Observations naturally decay and are replaced by newer ones
    def __init__(self, max_observations: int = 5, decay_hours: float = 2.0):
        self.max_observations = max_observations
        self.decay_hours = decay_hours
        self.observations = deque(maxlen=max_observations)
        
        # Mood influence weights for different contexts
        self.mood_influences = {
            'joy': {
                'response_tone': 'enthusiastic and positive',
                'suggestions': 'encouraging and optimistic',
                'empathy_level': 'celebratory'
            },
            'sadness': {
                'response_tone': 'gentle and supportive',
                'suggestions': 'comforting and understanding',
                'empathy_level': 'compassionate'
            },
            'anger': {
                'response_tone': 'calm and validating',
                'suggestions': 'solution-focused and practical',
                'empathy_level': 'understanding but grounding'
            },
            'fear': {
                'response_tone': 'reassuring and steady',
                'suggestions': 'confidence-building and step-by-step',
                'empathy_level': 'protective and encouraging'
            },
            'surprise': {
                'response_tone': 'curious and engaging',
                'suggestions': 'exploratory and informative',
                'empathy_level': 'interested and supportive'
            },
            'neutral': {
                'response_tone': 'balanced and informative',
                'suggestions': 'practical and clear',
                'empathy_level': 'helpful and professional'
            }
        }
    
    def add_observation(self, mood: str, intensity: float, confidence: float, 
                       context: str, user_message: str = "") -> None:
        # Add a new mood observation
        observation = MoodObservation(
            mood=mood,
            intensity=intensity,
            confidence=confidence,
            context=context,
            timestamp=datetime.now()
        )
        
        # Add to observations (automatically removes oldest if at max capacity)
        self.observations.append(observation)
        
        # Update decay factors for all observations
        self._update_decay_factors()
    
    def _update_decay_factors(self) -> None:
        # Update decay factors based on age and intensity
        now = datetime.now()
        
        for observation in self.observations:
            age_hours = (now - observation.timestamp).total_seconds() / 3600
            
            # Exponential decay based on time
            time_decay = max(0.1, 1.0 - (age_hours / self.decay_hours))
            
            # High-intensity emotions decay slower
            intensity_factor = 0.5 + (observation.intensity * 0.5)
            
            # High-confidence observations decay slower
            confidence_factor = 0.5 + (observation.confidence * 0.5)
            
            observation.decay_factor = time_decay * intensity_factor * confidence_factor
    
    def get_current_mood_context(self) -> Dict[str, Any]:
        # Get current mood context for LLM prompt
        if not self.observations:
            return {
                'has_mood_context': False,
                'dominant_mood': 'neutral',
                'mood_summary': 'No recent mood observations',
                'response_guidance': self.mood_influences['neutral']
            }
        
        # Update decay factors
        self._update_decay_factors()
        
        # Calculate weighted mood scores
        mood_scores = {}
        total_weight = 0
        
        for obs in self.observations:
            weight = obs.decay_factor * obs.confidence
            mood_scores[obs.mood] = mood_scores.get(obs.mood, 0) + weight
            total_weight += weight
        
        # Find dominant mood
        if total_weight > 0:
            dominant_mood = max(mood_scores.keys(), key=lambda m: mood_scores[m])
            dominant_intensity = mood_scores[dominant_mood] / total_weight
        else:
            dominant_mood = 'neutral'
            dominant_intensity = 0.5
        
        # Generate mood summary
        mood_summary = self._generate_mood_summary(mood_scores, total_weight)
        
        return {
            'has_mood_context': True,
            'dominant_mood': dominant_mood,
            'dominant_intensity': dominant_intensity,
            'mood_summary': mood_summary,
            'response_guidance': self.mood_influences.get(dominant_mood, self.mood_influences['neutral']),
            'recent_observations': [obs.to_dict() for obs in list(self.observations)[-3:]],  # Last 3 for context
            'mood_trend': self._analyze_mood_trend()
        }
    
    def _generate_mood_summary(self, mood_scores: Dict[str, float], total_weight: float) -> str:
        # Generate a natural language mood summary
        if total_weight == 0:
            return "User's emotional state is unclear"
        
        # Sort moods by influence
        sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_moods) == 1:
            mood, score = sorted_moods[0]
            intensity = score / total_weight
            if intensity > 0.7:
                return f"User is clearly feeling {mood}"
            elif intensity > 0.4:
                return f"User seems to be feeling {mood}"
            else:
                return f"User shows mild {mood}"
        
        # Multiple moods
        primary_mood, primary_score = sorted_moods[0]
        secondary_mood, secondary_score = sorted_moods[1]
        
        primary_ratio = primary_score / total_weight
        secondary_ratio = secondary_score / total_weight
        
        if primary_ratio > 0.6:
            return f"User is primarily feeling {primary_mood} with some {secondary_mood}"
        elif primary_ratio > 0.4:
            if secondary_ratio > 0.2:
                return f"User shows mixed emotions: {primary_mood} and {secondary_mood}"
            else:
                return f"User is feeling {primary_mood} with minor other emotions"
        else:
            return f"User's emotional state is complex, showing {primary_mood}, {secondary_mood}, and other feelings"
    
    def _analyze_mood_trend(self) -> str:
        # Analyze if mood is improving, declining, or stable
        if len(self.observations) < 2:
            return "stable"
        
        # Compare recent vs older observations
        recent_obs = list(self.observations)[-2:]  # Last 2
        older_obs = list(self.observations)[:-2] if len(self.observations) > 2 else []
        
        if not older_obs:
            return "stable"
        
        # Simple trend analysis based on positive vs negative emotions
        positive_emotions = {'joy', 'surprise'}
        negative_emotions = {'sadness', 'anger', 'fear'}
        
        def mood_score(obs_list):
            if not obs_list:
                return 0
            total = 0
            for obs in obs_list:
                if obs.mood in positive_emotions:
                    total += obs.intensity * obs.confidence
                elif obs.mood in negative_emotions:
                    total -= obs.intensity * obs.confidence
            return total / len(obs_list)
        
        recent_score = mood_score(recent_obs)
        older_score = mood_score(older_obs)
        
        diff = recent_score - older_score
        
        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"
    
    def generate_inner_thoughts(self) -> Optional[str]:
        # Generate 'inner thoughts' content for LLM context
        context = self.get_current_mood_context()
        
        if not context['has_mood_context']:
            return None
        
        mood_summary = context['mood_summary']
        trend = context['mood_trend']
        guidance = context['response_guidance']
        
        # Generate inner thoughts based on mood context
        thoughts = f"[Internal Observation] {mood_summary}. "
        
        if trend != "stable":
            thoughts += f"Emotional trend appears to be {trend}. "
        
        thoughts += f"Response approach: {guidance['response_tone']}. "
        thoughts += f"Empathy level: {guidance['empathy_level']}."
        
        return thoughts
    
    def create_mood_aware_messages(self, base_messages: List[Dict]) -> List[Dict]:
        # Add mood context to message list for LLM
        inner_thoughts = self.generate_inner_thoughts()
        
        if not inner_thoughts:
            return base_messages
        
        # Insert inner thoughts as a special role
        mood_message = {
            "role": "observation",  # Custom role for mood context
            "content": inner_thoughts
        }
        
        # Insert before the last user message
        if base_messages and base_messages[-1]["role"] == "user":
            return base_messages[:-1] + [mood_message] + [base_messages[-1]]
        else:
            return base_messages + [mood_message]
    
    def cleanup_old_observations(self) -> int:
        # Remove observations older than decay_hours
        cutoff_time = datetime.now() - timedelta(hours=self.decay_hours)
        initial_count = len(self.observations)
        
        # Filter out old observations
        self.observations = deque(
            [obs for obs in self.observations if obs.timestamp > cutoff_time],
            maxlen=self.max_observations
        )
        
        return initial_count - len(self.observations)
    
    def get_debug_info(self) -> Dict:
        # Get debug information about current mood context
        context = self.get_current_mood_context()
        
        return {
            "observation_count": len(self.observations),
            "dominant_mood": context['dominant_mood'],
            "mood_summary": context['mood_summary'],
            "mood_trend": context['mood_trend'],
            "inner_thoughts": self.generate_inner_thoughts(),
            "observations": [obs.to_dict() for obs in self.observations]
        }

# Example usage
if __name__ == "__main__":
    mood_context = DynamicMoodContext()
    
    # Simulate mood observations over time
    import time
    
    print("🧠 Testing Dynamic Mood Context")
    print("=" * 50)
    
    # Add some mood observations
    mood_context.add_observation("joy", 0.8, 0.9, "User expressed excitement about project")
    print("Added: Joy observation")
    print(f"Inner thoughts: {mood_context.generate_inner_thoughts()}")
    print()
    
    time.sleep(1)
    mood_context.add_observation("sadness", 0.6, 0.7, "User mentioned feeling overwhelmed")
    print("Added: Sadness observation")
    print(f"Inner thoughts: {mood_context.generate_inner_thoughts()}")
    print()
    
    time.sleep(1)
    mood_context.add_observation("joy", 0.7, 0.8, "User solved the problem successfully")
    print("Added: Joy observation")
    print(f"Inner thoughts: {mood_context.generate_inner_thoughts()}")
    print()
    
    # Test message integration
    base_messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Can you help me with this code?"}
    ]
    
    mood_aware_messages = mood_context.create_mood_aware_messages(base_messages)
    print("Mood-aware messages:")
    for msg in mood_aware_messages:
        print(f"  {msg['role']}: {msg['content']}")
    
    print(f"\nDebug info: {json.dumps(mood_context.get_debug_info(), indent=2, default=str)}")
