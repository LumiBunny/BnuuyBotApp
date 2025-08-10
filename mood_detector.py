import re
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

# Optional transformer imports
try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Transformers not available - using regex-only mode")

logger = logging.getLogger(__name__)

@dataclass
class MoodResult:
    mood: str
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    method: str  # "regex", "transformer", "hybrid"
    raw_scores: Optional[Dict] = None

class HybridMoodDetector:
    # Hybrid mood detection using enhanced regex + lightweight transformer
    def __init__(self, use_gpu: bool = True, model_name: str = "j-hartmann/emotion-english-distilroberta-base"):
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model_name = model_name
        self.transformer_pipeline = None
        
        # Initialize transformer if available
        if TRANSFORMERS_AVAILABLE:
            self._initialize_transformer()
        
        # Enhanced regex patterns with negation handling
        self._setup_enhanced_regex()
        
        logger.info(f"HybridMoodDetector initialized - GPU: {self.use_gpu}, Transformer: {self.transformer_pipeline is not None}")
    
    def _initialize_transformer(self):
        # Initialize the transformer model for sentiment analysis
        try:
            device = 0 if self.use_gpu else -1  # 0 for GPU, -1 for CPU
            
            self.transformer_pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                device=device,
                return_all_scores=True
            )
            
            # Test the model with a simple input
            test_result = self.transformer_pipeline("I am happy")
            logger.info(f"Transformer model loaded successfully on {'GPU' if self.use_gpu else 'CPU'}")
            
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}")
            self.transformer_pipeline = None
    
    def _setup_enhanced_regex(self):
        # Setup enhanced regex patterns with negation and context handling
        # Negation patterns
        self.negation_patterns = [
            r'\b(?:not|n\'t|never|no|none|neither|nor)\b',
            r'\b(?:don\'t|doesn\'t|didn\'t|won\'t|wouldn\'t|can\'t|couldn\'t)\b'
        ]
        
        # Intensity modifiers
        self.intensity_modifiers = {
            'high': ['extremely', 'incredibly', 'absolutely', 'totally', 'completely', 'utterly', 'very', 'really', 'so', 'super'],
            'medium': ['pretty', 'quite', 'fairly', 'rather', 'somewhat'],
            'low': ['a bit', 'slightly', 'kind of', 'sort of', 'a little', 'mildly']
        }
        
        # Enhanced emotion patterns with context
        self.emotion_patterns = {
            'joy': {
                'patterns': [
                    r'\b(?:happy|joy|joyful|cheerful|delighted|pleased|glad|content|elated|ecstatic|thrilled|excited)\b',
                    r'\b(?:love|adore|enjoy|like)\s+(?:this|it|that)',
                    r'\b(?:amazing|awesome|fantastic|wonderful|great|excellent|perfect|brilliant)\b'
                ],
                'base_intensity': 0.7
            },
            'sadness': {
                'patterns': [
                    r'\b(?:sad|unhappy|depressed|down|blue|miserable|heartbroken|devastated|crushed)\b',
                    r'\b(?:hate|dislike|despise)\s+(?:this|it|that)',
                    r'\b(?:awful|terrible|horrible|dreadful|disappointing)\b'
                ],
                'base_intensity': 0.6
            },
            'anger': {
                'patterns': [
                    r'\b(?:angry|mad|furious|enraged|irritated|annoyed|frustrated|pissed|livid)\b',
                    r'\b(?:hate|despise|loathe)\b',
                    r'\b(?:stupid|idiotic|ridiculous|absurd)\s+(?:bug|error|problem|issue)\b'
                ],
                'base_intensity': 0.7
            },
            'fear': {
                'patterns': [
                    r'\b(?:scared|afraid|frightened|terrified|worried|anxious|nervous|concerned)\b',
                    r'\b(?:panic|stress|overwhelm)\b'
                ],
                'base_intensity': 0.6
            },
            'surprise': {
                'patterns': [
                    r'\b(?:surprised|shocked|amazed|astonished|stunned|wow|whoa)\b',
                    r'\b(?:unexpected|sudden|out of nowhere)\b'
                ],
                'base_intensity': 0.5
            },
            'neutral': {
                'patterns': [
                    r'\b(?:okay|fine|alright|whatever|meh|normal|usual)\b',
                    r'\b(?:nothing|nothing much|not much)\b'
                ],
                'base_intensity': 0.3
            }
        }
    
    def detect_mood(self, text: str) -> Optional[MoodResult]:
        # Main mood detection method using hybrid approach
        if not text or not text.strip():
            return None
        
        text = text.strip()
        
        # Step 1: Try enhanced regex first (fast)
        regex_result = self._detect_with_enhanced_regex(text)
        
        # Step 2: Use transformer for complex cases or validation
        transformer_result = None
        if self.transformer_pipeline:
            # Use transformer if:
            # - Regex failed to detect anything
            # - Regex confidence is low
            # - Text contains complex patterns
            if (regex_result is None or 
                regex_result.confidence < 0.7 or 
                self._is_complex_text(text)):
                transformer_result = self._detect_with_transformer(text)
        
        # Step 3: Combine results intelligently
        return self._combine_results(regex_result, transformer_result, text)
    
    def _detect_with_enhanced_regex(self, text: str) -> Optional[MoodResult]:
        # Enhanced regex detection with negation and intensity handling
        text_lower = text.lower()
        
        # Check for negation
        has_negation = any(re.search(pattern, text_lower) for pattern in self.negation_patterns)
        
        # Find emotion matches
        best_match = None
        best_score = 0
        
        for emotion, config in self.emotion_patterns.items():
            for pattern in config['patterns']:
                matches = list(re.finditer(pattern, text_lower))
                if matches:
                    # Calculate intensity based on modifiers
                    intensity = config['base_intensity']
                    
                    # Check for intensity modifiers
                    for level, modifiers in self.intensity_modifiers.items():
                        for modifier in modifiers:
                            if modifier in text_lower:
                                if level == 'high':
                                    intensity = min(1.0, intensity + 0.2)
                                elif level == 'medium':
                                    intensity = min(1.0, intensity + 0.1)
                                elif level == 'low':
                                    intensity = max(0.1, intensity - 0.2)
                                break
                    
                    # Handle negation
                    if has_negation:
                        # Flip emotion or reduce intensity
                        if emotion in ['joy', 'surprise']:
                            emotion = 'sadness'
                        elif emotion == 'sadness':
                            emotion = 'joy'
                        intensity = max(0.1, intensity - 0.3)
                    
                    # Calculate confidence based on pattern specificity
                    confidence = min(1.0, len(matches) * 0.3 + intensity)
                    
                    if confidence > best_score:
                        best_match = MoodResult(
                            mood=emotion,
                            intensity=intensity,
                            confidence=confidence,
                            method="regex"
                        )
                        best_score = confidence
        
        return best_match
    
    def _detect_with_transformer(self, text: str) -> Optional[MoodResult]:
        # Use transformer model for mood detection
        if not self.transformer_pipeline:
            return None
        
        try:
            # Get predictions from transformer
            results = self.transformer_pipeline(text)
            
            if not results or not results[0]:
                return None
            
            # Find the highest scoring emotion
            best_result = max(results[0], key=lambda x: x['score'])
            
            # Map transformer labels to our emotion categories
            emotion_mapping = {
                'joy': 'joy',
                'happiness': 'joy',
                'sadness': 'sadness',
                'anger': 'anger',
                'fear': 'fear',
                'surprise': 'surprise',
                'neutral': 'neutral',
                'disgust': 'anger',  # Map disgust to anger
                'love': 'joy',       # Map love to joy
            }
            
            transformer_emotion = best_result['label'].lower()
            mapped_emotion = emotion_mapping.get(transformer_emotion, 'neutral')
            
            return MoodResult(
                mood=mapped_emotion,
                intensity=best_result['score'],
                confidence=best_result['score'],
                method="transformer",
                raw_scores={r['label']: r['score'] for r in results[0]}
            )
            
        except Exception as e:
            logger.error(f"Transformer mood detection failed: {e}")
            return None
    
    def _is_complex_text(self, text: str) -> bool:
        # Determine if text is complex and needs transformer analysis
        complexity_indicators = [
            'but', 'however', 'although', 'though', 'while',  # Contrasts
            'sarcasm', 'irony', 'kidding', 'joking',          # Sarcasm indicators
            '?', '!',                                          # Punctuation complexity
        ]
        
        text_lower = text.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in text_lower)
        
        # Also consider length and sentence structure
        word_count = len(text.split())
        has_multiple_sentences = text.count('.') > 1 or text.count('!') > 1 or text.count('?') > 1
        
        return complexity_score > 0 or word_count > 15 or has_multiple_sentences
    
    def _combine_results(self, regex_result: Optional[MoodResult], 
                        transformer_result: Optional[MoodResult], 
                        text: str) -> Optional[MoodResult]:
        # Intelligently combine regex and transformer results
        
        # If only one method succeeded, use it
        if regex_result is None and transformer_result is None:
            return None
        elif regex_result is None:
            return transformer_result
        elif transformer_result is None:
            return regex_result
        
        # Both methods succeeded - combine intelligently
        
        # If both agree on emotion, combine confidences
        if regex_result.mood == transformer_result.mood:
            combined_confidence = (regex_result.confidence + transformer_result.confidence) / 2
            combined_intensity = (regex_result.intensity + transformer_result.intensity) / 2
            
            return MoodResult(
                mood=regex_result.mood,
                intensity=combined_intensity,
                confidence=min(1.0, combined_confidence + 0.1),  # Bonus for agreement
                method="hybrid",
                raw_scores=transformer_result.raw_scores
            )
        
        # If they disagree, use the one with higher confidence
        if regex_result.confidence > transformer_result.confidence:
            regex_result.method = "hybrid_regex_preferred"
            return regex_result
        else:
            transformer_result.method = "hybrid_transformer_preferred"
            return transformer_result
    
    def get_model_info(self) -> Dict:
        # Get information about the loaded models
        return {
            "transformer_available": self.transformer_pipeline is not None,
            "transformer_model": self.model_name if self.transformer_pipeline else None,
            "using_gpu": self.use_gpu,
            "device": "cuda" if self.use_gpu else "cpu"
        }

# Example usage and testing
if __name__ == "__main__":
    detector = HybridMoodDetector()
    
    test_cases = [
        "I'm so happy today!",
        "I'm not happy at all",
        "Oh great, another bug",  # Sarcasm test
        "I love this but hate that part",  # Mixed emotions
        "I'm feeling pretty good about this project",
        "This is absolutely terrible",
        "I'm a bit worried about tomorrow",
    ]
    
    print("🧪 Testing Hybrid Mood Detection")
    print("=" * 50)
    
    for text in test_cases:
        result = detector.detect_mood(text)
        if result:
            print(f"'{text}'")
            print(f"  → {result.mood} (intensity: {result.intensity:.2f}, confidence: {result.confidence:.2f}, method: {result.method})")
        else:
            print(f"'{text}' → No mood detected")
        print()
    
    print(f"Model info: {detector.get_model_info()}")
