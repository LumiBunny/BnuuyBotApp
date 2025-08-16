import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from enum import Enum
import logging

try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("spaCy not available - using simple extraction only")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractionMethod(Enum):
    # Enum for tracking which method extracted a preference
    REGEX_PATTERN = "regex_pattern"
    SPACY_ENTITY = "spacy_entity"
    SPACY_DEPENDENCY = "spacy_dependency"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

class PreferenceType(Enum):
    # Enum for preference types
    LIKES = "likes"
    DISLIKES = "dislikes"
    LOVES = "loves"
    HATES = "hates"
    NEUTRAL = "neutral"

@dataclass
class PreferenceResult:
    # Structured result for preference extraction
    user_id: str
    preference_type: str  # likes, dislikes, loves, hates
    preference_category: str  # food, games, activities, etc.
    preference_value: str  # the actual item/activity
    confidence: float  # 0.0 to 1.0
    extraction_method: str  # which method found this
    context: str  # surrounding context
    original_input: str  # original text
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        # Convert to dictionary for JSON serialization
        return asdict(self)


class PreferenceExtractor:
    # Enhanced preference extraction with confidence scoring and validation.
    # Supports a hybrid approach of both simple regex and spaCy.
    
    def __init__(self, use_spacy: bool = True, min_confidence: float = 0.6):
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.min_confidence = min_confidence
        
        # Initialize spaCy if available and requested
        self.nlp = None
        self.matcher = None
        if self.use_spacy:
            try:
                self.nlp = spacy.load("en_core_web_lg")
                logger.info("Loaded spaCy large model")
            except OSError:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Loaded spaCy small model")
                except OSError:
                    logger.warning("No spaCy model found, falling back to simple extraction")
                    self.use_spacy = False
            
            if self.nlp:
                self._setup_spacy_patterns()
        
        # Initialize regex patterns (used by both approaches)
        self._setup_regex_patterns()
        
        # Known entities for categorization
        self.entity_categories = {
            'food': ['pizza', 'sushi', 'pasta', 'burger', 'salad', 'soup', 'bread', 'cheese', 'chocolate'],
            'games': ['minecraft', 'zelda', 'mario', 'final fantasy', 'pokemon', 'fortnite'],
            'colors': ['red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'pink', 'orange'],
            'activities': ['running', 'swimming', 'reading', 'cooking', 'gaming', 'hiking', 'dancing'],
            'music': ['rock', 'pop', 'jazz', 'classical', 'hip hop', 'country'],
            'movies': ['action', 'comedy', 'drama', 'horror', 'sci-fi', 'romance']
        }
        
        # Stopwords and invalid terms
        self.stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        logger.info(f"PreferenceExtractor initialized - spaCy: {self.use_spacy}, min_confidence: {min_confidence}")
    
    def _setup_regex_patterns(self):
        # Setup high-confidence regex patterns
        self.regex_patterns = {
            # Explicit favorites - very high confidence (treat as love)
            'favorite_explicit': {
                'pattern': r'my favorite\s+(?:(?:type of|kind of)\s+)?\w+(?:\s+\w+)*\s+is\s+([^,.!?]+?)(?:\s*[,.!?]|$)',
                'confidence': 0.9,
                'sentiment': PreferenceType.LOVES
            },
            # Strong positive expressions.
            'love_pattern': {
                'pattern': r'i\s+(?:really\s+|absolutely\s+)?love\s+([^,.!?]+?)(?:\s*[,.!?]|$)',
                'confidence': 0.85,
                'sentiment': PreferenceType.LOVES
            },
            # Strong negative expressions.
            'hate_pattern': {
                'pattern': r'i\s+(?:really\s+|absolutely\s+)?hate\s+([^,.!?]+?)(?:\s*[,.!?]|$)',
                'confidence': 0.85,
                'sentiment': PreferenceType.HATES
            },
            # Clear dislikes.
            'dislike_pattern': {
                'pattern': r'i\s+(?:don\'t|do not)\s+like\s+([^,.!?]+?)(?:\s*[,.!?]|$)',
                'confidence': 0.8,
                'sentiment': PreferenceType.DISLIKES
            },
            # Moderate likes.
            'like_pattern': {
                'pattern': r'i\s+(?:really\s+)?like\s+([^,.!?]+?)(?:\s*[,.!?]|$)',
                'confidence': 0.75,
                'sentiment': PreferenceType.LIKES
            },
            # Enjoyment.
            'enjoy_pattern': {
                'pattern': r'i\s+(?:really\s+)?enjoy\s+([^,.!?]+?)(?:\s*[,.!?]|$)',
                'confidence': 0.75,
                'sentiment': PreferenceType.LIKES
            }
        }
        
        # Compound noun patterns (for things like "chocolate ice cream")
        self.compound_nouns = {
            'food': [
                'ice cream', 'chocolate ice cream', 'vanilla ice cream',
                'hot dog', 'french fries', 'pizza slice',
                'chicken breast', 'beef steak', 'pork chop'
            ],
            'games': [
                'final fantasy', 'super mario', 'legend of zelda',
                'call of duty', 'grand theft auto'
            ],
            'movies': [
                'horror movies', 'action movies', 'comedy movies',
                'sci fi movies', 'romantic comedies'
            ]
        }
    
    def _setup_spacy_patterns(self):
        # Setup spaCy matcher patterns
        if not self.nlp:
            return
            
        self.matcher = Matcher(self.nlp.vocab)
        
        self.matcher.add("LOVE_PATTERN", [
            [{"LOWER": "i"}, {"LOWER": {"IN": ["really", "absolutely"]}, "OP": "?"}, {"LOWER": "love"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}],
            [{"LOWER": "i"}, {"LOWER": "love"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}]
        ])
        
        self.matcher.add("LIKE_PATTERN", [
            [{"LOWER": "i"}, {"LOWER": {"IN": ["really", "absolutely"]}, "OP": "?"}, {"LOWER": "like"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}],
            [{"LOWER": "i"}, {"LOWER": "like"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}]
        ])
        
        self.matcher.add("ENJOY_PATTERN", [
            [{"LOWER": "i"}, {"LOWER": {"IN": ["really", "absolutely"]}, "OP": "?"}, {"LOWER": "enjoy"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}],
            [{"LOWER": "i"}, {"LOWER": "enjoy"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}]
        ])
        
        # High-confidence explicit patterns
        self.matcher.add("FAVORITE_THING", [
            [{"LOWER": "my"}, {"LOWER": "favorite"}, {"POS": {"IN": ["NOUN", "PROPN"]}}],
            [{"LOWER": {"IN": ["i", "we"]}}, {"LOWER": "love"}, {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}]
        ])
        
        self.matcher.add("STRONG_PREFERENCE", [
            [{"LOWER": {"IN": ["i", "we"]}}, {"LOWER": "really"}, {"LOWER": {"IN": ["like", "love", "enjoy"]}}, {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}],
            [{"LOWER": {"IN": ["i", "we"]}}, {"LOWER": "absolutely"}, {"LOWER": {"IN": ["like", "love", "enjoy"]}}, {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}]
        ])
        
        self.matcher.add("NEGATIVE_PREFERENCE", [
            [{"LOWER": {"IN": ["i", "we"]}}, {"LOWER": {"IN": ["hate", "dislike"]}}, {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}],
            [{"LOWER": {"IN": ["i", "we"]}}, {"LOWER": {"IN": ["don't", "do"]}}, {"LOWER": {"IN": ["not", "n't"]}, "OP": "?"}, {"LOWER": "like"}, {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}]
        ])

    def extract_preferences(self, text: str, user_id: str = "user") -> List[PreferenceResult]:
        # Main extraction method that combines all approaches.
        if not text or not text.strip():
            return []
        
        logger.debug(f"Extracting preferences from: '{text[:50]}...'")
        
        all_results = []
        
        # Handle compound sentences with "but" first
        if " but " in text.lower():
            parts = self._split_compound_sentence(text)
            for part in parts:
                part_results = self.extract_preferences(part.strip(), user_id)
                all_results.extend(part_results)
            
            # Filter and return early for compound sentences
            filtered_results = [r for r in all_results if r.confidence >= self.min_confidence]
            validated_results = self._validate_and_deduplicate(filtered_results)
            # Apply sentiment hierarchy
            hierarchy_results = self._apply_sentiment_hierarchy(validated_results)
            if hierarchy_results:
                print(f"💞 Found {len(hierarchy_results)} preferences: {', '.join([f'{p.preference_type}={p.preference_value}' for p in hierarchy_results])}")
            else:
                print(f"💞 No new preferences detected")
            logger.info(f"Extracted {len(hierarchy_results)} preferences (from {len(all_results)} candidates)")
            return hierarchy_results
        
        # Method 1: Regex-based extraction (always runs)
        regex_results = self._extract_with_regex(text, user_id)
        all_results.extend(regex_results)
        
        # Method 2: spaCy-based extraction (if available)
        if self.use_spacy and self.nlp:
            spacy_results = self._extract_with_spacy(text, user_id)
            all_results.extend(spacy_results)
        
        # Method 3: Simple sentiment analysis (with higher threshold)
        sentiment_results = self._extract_with_sentiment(text, user_id)
        all_results.extend(sentiment_results)
        
        # Filter by confidence
        filtered_results = [r for r in all_results if r.confidence >= self.min_confidence]
        
        # Validate and deduplicate
        validated_results = self._validate_and_deduplicate(filtered_results)
        
        # Apply sentiment hierarchy
        hierarchy_results = self._apply_sentiment_hierarchy(validated_results)
        
        if hierarchy_results:
            print(f"💞 Found {len(hierarchy_results)} preferences: {', '.join([f'{p.preference_type}={p.preference_value}' for p in hierarchy_results])}")
        else:
            print(f"💞 No new preferences detected")
        logger.info(f"Extracted {len(hierarchy_results)} preferences (from {len(all_results)} candidates)")
        
        return hierarchy_results
    
    def _split_compound_sentence(self, text: str) -> List[str]:
        # Split compound sentences on 'but' and handle sentiment properly.
        parts = []
        
        # Split on "but" (case insensitive)
        raw_parts = re.split(r'\s+but\s+', text, flags=re.IGNORECASE)
        
        for i, part in enumerate(raw_parts):
            part = part.strip()
            if not part:
                continue
                
            # For parts after "but", we need to check if they have a subject
            if i > 0:
                # If the part doesn't start with "I" or "we", add it
                if not re.match(r'^(i|we)\s', part, re.IGNORECASE):
                    part = f"I {part}"
            
            parts.append(part)
        
        return parts
    
    def _extract_with_regex(self, text: str, user_id: str) -> List[PreferenceResult]:
        results = []
        text_lower = text.lower().strip()
        
        for pattern_name, pattern_info in self.regex_patterns.items():
            matches = re.finditer(pattern_info['pattern'], text_lower, re.IGNORECASE)
            
            for match in matches:
                preference_text = match.group(1).strip()
                # Parse compound objects (like "pizza and pasta")
                preference_objects = self._parse_compound_objects(preference_text)
                
                for preference_value in preference_objects:
                    # Basic validation
                    if not self._is_valid_preference_value(preference_value):
                        continue
                    
                    # Additional validation: skip if too long or contains sentiment words
                    if len(preference_value.split()) > 4:
                        continue
                    
                    category = self._categorize_preference(preference_value)
                    
                    result = PreferenceResult(
                        user_id=user_id,
                        preference_type=pattern_info['sentiment'].value,
                        preference_category=category,
                        preference_value=preference_value,
                        confidence=pattern_info['confidence'],
                        extraction_method=ExtractionMethod.REGEX_PATTERN.value,
                        context=match.group(0),
                        original_input=text,
                        notes=f"Extracted via regex pattern: {pattern_name}"
                    )
                    
                    results.append(result)
        
        return results

    def _parse_compound_objects(self, text: str) -> List[str]:
        # Parse compound objects like 'pizza and pasta' into individual items
        if not text or not text.strip():
            return []
        
        # Split on 'and' and comma-separated lists
        objects = []
        
        # First split on 'and'
        and_parts = re.split(r'\s+and\s+', text, flags=re.IGNORECASE)
        
        for part in and_parts:
            # Then split each part on commas
            comma_parts = [p.strip() for p in part.split(',') if p.strip()]
            objects.extend(comma_parts)
        
        # Clean up and validate each object
        cleaned_objects = []
        for obj in objects:
            obj = obj.strip().lower()
            if obj and len(obj) > 1:  # Basic validation
                cleaned_objects.append(obj)
        
        return cleaned_objects if cleaned_objects else [text.strip().lower()]

    def _is_valid_preference_value(self, value: str) -> bool:
        # Validate if a preference value is meaningful and not just noise
        if not value or not value.strip():
            return False
        
        value = value.strip().lower()
        
        # Skip if too short or too long
        if len(value) < 2 or len(value) > 50:
            return False
        
        # Skip if it's just sentiment words
        sentiment_words = {'love', 'hate', 'like', 'dislike', 'enjoy', 'prefer', 'favorite', 'really', 'absolutely'}
        if value in sentiment_words:
            return False
        
        # Skip if it contains only stop words or pronouns
        stop_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
                     'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 
                     'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                     'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
                     'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                     'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
                     'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
                     'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
                     'further', 'then', 'once'}
        
        words = value.split()
        if all(word in stop_words for word in words):
            return False
        
        # Skip if it looks like a sentence fragment or contains too many function words
        if len(words) > 1:
            function_word_count = sum(1 for word in words if word in stop_words)
            if function_word_count / len(words) > 0.6:  # More than 60% function words
                return False
        
        return True

    def _categorize_preference(self, preference_value: str) -> str:
        # Categorize a preference value into a general category
        if not preference_value:
            return "general"
        
        value_lower = preference_value.lower()
        
        # Check against known categories
        for category, keywords in self.entity_categories.items():
            if value_lower in keywords or any(keyword in value_lower for keyword in keywords):
                return category
        
        # Default fallback
        return "general"

    def _extract_with_spacy(self, text: str, user_id: str) -> List[PreferenceResult]:
        # Extract preferences using spaCy NLP
        if not self.nlp or not self.matcher:
            return []
        
        results = []
        doc = self.nlp(text)
        
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            pattern_name = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            # Find the object part of the sentence (usually after the sentiment word)
            preference_value = None
            
            # Look for noun chunks (compound nouns) in the span
            for chunk in doc.noun_chunks:
                # Check if this noun chunk overlaps with our matched span
                if chunk.start >= start and chunk.end <= end:
                    # Skip if it's just a pronoun or sentiment word
                    if chunk.root.pos_ in ["NOUN", "PROPN"] and chunk.text.lower() not in ['i', 'me', 'my', 'we', 'our']:
                        # Special handling for FAVORITE_THING pattern
                        if pattern_name == "FAVORITE_THING" and "favorite" in chunk.text.lower():
                            # Extract only the noun after "favorite"
                            tokens = chunk.text.lower().split()
                            if "favorite" in tokens:
                                favorite_idx = tokens.index("favorite")
                                if favorite_idx + 1 < len(tokens):
                                    # Get the noun(s) after "favorite"
                                    preference_value = " ".join(tokens[favorite_idx + 1:])
                                else:
                                    continue  # No noun after "favorite"
                            else:
                                preference_value = chunk.text.lower()
                        else:
                            preference_value = chunk.text.lower()
                        break
            
            # Fallback: if no noun chunk found, look for the last noun/proper noun sequence
            if not preference_value:
                noun_tokens = []
                for token in reversed(span):  # Go backwards to get the object
                    if token.pos_ in ["NOUN", "PROPN"]:
                        noun_tokens.insert(0, token.text.lower())
                    elif noun_tokens:  # Stop when we hit a non-noun after collecting nouns
                        break
                
                if noun_tokens:
                    preference_value = " ".join(noun_tokens)
            
            if not preference_value:
                continue
            
            # Parse compound objects (like "pizza and pasta") - but preserve compound nouns
            preference_objects = self._parse_compound_objects(preference_value)
            
            for pref_val in preference_objects:
                if not self._is_valid_preference_value(pref_val):
                    continue
                
                # Determine sentiment based on pattern - IMPROVED logic
                sentiment = PreferenceType.LIKES
                confidence = 0.8
                
                if pattern_name in ["LOVE_PATTERN", "FAVORITE_THING"]:
                    sentiment = PreferenceType.LOVES
                    confidence = 0.9
                elif pattern_name in ["LIKE_PATTERN", "ENJOY_PATTERN"]:
                    sentiment = PreferenceType.LIKES
                    confidence = 0.8
                elif pattern_name == "STRONG_PREFERENCE":
                    # Check if it's actually a love pattern
                    if "love" in span.text.lower():
                        sentiment = PreferenceType.LOVES
                        confidence = 0.85
                    else:
                        sentiment = PreferenceType.LIKES
                        confidence = 0.8
                elif pattern_name == "NEGATIVE_PREFERENCE":
                    sentiment = PreferenceType.DISLIKES
                    confidence = 0.8
                
                category = self._categorize_preference(pref_val)
                
                result = PreferenceResult(
                    user_id=user_id,
                    preference_type=sentiment.value,
                    preference_category=category,
                    preference_value=pref_val,
                    confidence=confidence,
                    extraction_method=ExtractionMethod.SPACY_ENTITY.value,
                    context=span.text,
                    original_input=text,
                    notes=f"Extracted via spaCy pattern: {pattern_name}"
                )
                
                results.append(result)
        
        # Method 2: Named Entity Recognition - also for compound nouns
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "WORK_OF_ART", "ORG", "PERSON"]:
                # Look for sentiment words near the entity
                sentiment_info = self._find_sentiment_near_entity(doc, ent)
                if sentiment_info:
                    category = self._categorize_preference(ent.text)
                    
                    result = PreferenceResult(
                        user_id=user_id,
                        preference_type=sentiment_info['type'].value,
                        preference_category=category,
                        preference_value=ent.text.lower(),
                        confidence=sentiment_info['confidence'],
                        extraction_method=ExtractionMethod.SPACY_ENTITY.value,
                        context=ent.sent.text,
                        original_input=text,
                        notes=f"Extracted via spaCy NER: {ent.label_}"
                    )
                    
                    results.append(result)
        
        # Filter out overlapping/partial entities - keep only the longest ones
        results = self._filter_overlapping_entities(results)
        
        return results

    def _extract_with_sentiment(self, text: str, user_id: str) -> List[PreferenceResult]:
        # Extract preferences using simple sentiment analysis.
        # This is a fallback method with higher confidence threshold.
        results = []
        
        # Simple sentiment patterns for fallback
        simple_patterns = {
            r'\b(love|adore)\s+([a-zA-Z\s]+)': (PreferenceType.LOVES, 0.7),
            r'\b(like|enjoy)\s+([a-zA-Z\s]+)': (PreferenceType.LIKES, 0.65),
            r'\b(hate|despise)\s+([a-zA-Z\s]+)': (PreferenceType.HATES, 0.7),
            r'\b(dislike|don\'t\s+like)\s+([a-zA-Z\s]+)': (PreferenceType.DISLIKES, 0.65)
        }
        
        for pattern, (sentiment, confidence) in simple_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                preference_value = match.group(2).strip().lower()
                
                # Basic validation
                if not self._is_valid_preference_value(preference_value):
                    continue
                
                # Skip if too long
                if len(preference_value.split()) > 3:
                    continue
                
                # Skip compound objects with "and" - let _parse_compound_objects handle them
                if " and " in preference_value:
                    continue
                
                category = self._categorize_preference(preference_value)
                
                result = PreferenceResult(
                    user_id=user_id,
                    preference_type=sentiment.value,
                    preference_category=category,
                    preference_value=preference_value,
                    confidence=confidence,
                    extraction_method=ExtractionMethod.SENTIMENT_ANALYSIS.value,
                    context=match.group(0),
                    original_input=text,
                    notes="Extracted via simple sentiment analysis"
                )
                
                results.append(result)
        
        return results

    def _find_sentiment_near_entity(self, doc, entity):
        # Find sentiment words near a named entity.
        sentiment_words = {
            'love': (PreferenceType.LOVES, 0.85),
            'adore': (PreferenceType.LOVES, 0.8),
            'like': (PreferenceType.LIKES, 0.75),
            'enjoy': (PreferenceType.LIKES, 0.75),
            'hate': (PreferenceType.HATES, 0.85),
            'despise': (PreferenceType.HATES, 0.8),
            'dislike': (PreferenceType.DISLIKES, 0.75)
        }
        
        # Look for sentiment words in the same sentence
        for token in entity.sent:
            if token.lemma_.lower() in sentiment_words:
                sentiment_type, confidence = sentiment_words[token.lemma_.lower()]
                return {'type': sentiment_type, 'confidence': confidence}
        
        return None

    def _validate_and_deduplicate(self, results: List[PreferenceResult]) -> List[PreferenceResult]:
        # Validate and remove duplicate preferences.
        if not results:
            return []
        
        # Group by preference value for deduplication
        grouped = {}
        for result in results:
            key = result.preference_value.lower()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)
        
        # For each group, keep the highest confidence result
        final_results = []
        for preference_value, group in grouped.items():
            # Sort by confidence (descending) and extraction method priority
            method_priority = {
                ExtractionMethod.REGEX_PATTERN.value: 3,
                ExtractionMethod.SPACY_ENTITY.value: 2,
                ExtractionMethod.SENTIMENT_ANALYSIS.value: 1
            }
            
            group.sort(key=lambda x: (x.confidence, method_priority.get(x.extraction_method, 0)), reverse=True)
            final_results.append(group[0])
        
        return final_results

    def _apply_sentiment_hierarchy(self, results: List[PreferenceResult]) -> List[PreferenceResult]:
        # Apply sentiment hierarchy - stronger sentiments imply weaker ones
        hierarchy_results = []
        
        # Create a mapping of sentiment implications
        sentiment_implications = {
            PreferenceType.LOVES.value: [PreferenceType.LIKES.value],  # love implies like
            PreferenceType.HATES.value: [PreferenceType.DISLIKES.value]  # hate implies dislike
        }
        
        for result in results:
            # Add the original result
            hierarchy_results.append(result)
            
            # Add implied sentiments
            if result.preference_type in sentiment_implications:
                for implied_sentiment in sentiment_implications[result.preference_type]:
                    # Create a new result with the implied sentiment
                    implied_result = PreferenceResult(
                        user_id=result.user_id,
                        preference_type=implied_sentiment,
                        preference_category=result.preference_category,
                        preference_value=result.preference_value,
                        confidence=max(0.6, result.confidence - 0.1),  # Slightly lower confidence
                        extraction_method=result.extraction_method,
                        context=result.context,
                        original_input=result.original_input,
                        notes=f"Implied from {result.preference_type}: {result.notes}"
                    )
                    hierarchy_results.append(implied_result)
        
        return hierarchy_results

    def _filter_overlapping_entities(self, results: List[PreferenceResult]) -> List[PreferenceResult]:
        # Filter out overlapping/partial entities - keep only the longest ones
        # For example, from 'chocolate ice cream', keep only 'chocolate ice cream' 
        # and remove 'chocolate' and 'chocolate ice'
        if not results:
            return []
        
        # Sort results by preference value length (longest first)
        sorted_results = sorted(results, key=lambda x: len(x.preference_value), reverse=True)
        
        filtered_results = []
        
        for result in sorted_results:
            current_value = result.preference_value.lower().strip()
            
            # Check if this entity is a substring of any already accepted longer entity
            is_substring = False
            for accepted_result in filtered_results:
                accepted_value = accepted_result.preference_value.lower().strip()
                
                # If current entity is contained within an accepted longer entity, skip it
                if current_value != accepted_value and current_value in accepted_value:
                    is_substring = True
                    break
            
            # Only add if it's not a substring of a longer entity
            if not is_substring:
                filtered_results.append(result)
        
        return filtered_results

    def get_extraction_stats(self, results: List[PreferenceResult]) -> dict:
        # Get statistics about the extraction results
        if not results:
            return {
                'total_preferences': 0,
                'by_sentiment': {},
                'by_method': {},
                'by_category': {},
                'avg_confidence': 0.0
            }
        
        # Count by sentiment type
        sentiment_counts = {}
        for result in results:
            sentiment = result.preference_type
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Count by extraction method
        method_counts = {}
        for result in results:
            method = result.extraction_method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Count by category
        category_counts = {}
        for result in results:
            category = result.preference_category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return {
            'total_preferences': len(results),
            'by_sentiment': sentiment_counts,
            'by_method': method_counts,
            'by_category': category_counts,
            'avg_confidence': round(avg_confidence, 3)
        }


# Example usage and testing
if __name__ == "__main__":
    # Test both approaches
    test_texts = [
        "I love pizza and pasta but I hate olives",
        "My favorite game is Final Fantasy, I really enjoy RPGs",
        "I don't like running but I love swimming",
        "I absolutely love chocolate ice cream",
        "I hate horror movies but I enjoy comedies"
    ]
    
    print("=== Testing Simple Approach ===")
    extractor_simple = PreferenceExtractor(use_spacy=False, min_confidence=0.6)
    
    for text in test_texts:
        results = extractor_simple.extract_preferences(text)
        print(f"\nInput: {text}")
        for result in results:
            print(f"  {result.preference_type}: {result.preference_value} "
                  f"({result.confidence:.2f}, {result.extraction_method})")
    
    if SPACY_AVAILABLE:
        print("\n\n=== Testing spaCy-Enhanced Approach ===")
        extractor_spacy = PreferenceExtractor(use_spacy=True, min_confidence=0.6)
        
        for text in test_texts:
            results = extractor_spacy.extract_preferences(text)
            print(f"\nInput: {text}")
            for result in results:
                print(f"  {result.preference_type}: {result.preference_value} "
                      f"({result.confidence:.2f}, {result.extraction_method})")
            
            # Show extraction stats
            stats = extractor_spacy.get_extraction_stats(results)
            if stats:
                print(f"  Stats: {stats}")