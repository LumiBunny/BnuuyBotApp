import spacy
import re
from spacy.matcher import Matcher

GAME_TITLES = ["final fantasy", "zelda", "mario", "minecraft"]

class EnhancedPreferenceExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            print("Large model not found, falling back to small model")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Create matcher for specific patterns
        self.matcher = Matcher(self.nlp.vocab)
        
        # Create matcher for specific patterns
        self.matcher = Matcher(self.nlp.vocab)
        
        # Pattern for "X is my favorite color"
        self.matcher.add("FAVORITE_COLOR_PATTERN", [
            [{"LOWER": {"IN": ["blue", "red", "green", "yellow", "black", "white", "purple", "pink", "orange", "brown"]}}, 
             {"LEMMA": "be"}, 
             {"LOWER": "my"}, 
             {"LOWER": "favorite"}, 
             {"LOWER": "color"}]
        ])
        
        # Pattern for "X is my favorite food"
        self.matcher.add("FAVORITE_FOOD_PATTERN", [
            [{"POS": {"IN": ["NOUN", "PROPN"]}}, 
             {"LEMMA": "be"}, 
             {"LOWER": "my"}, 
             {"LOWER": "favorite"}, 
             {"LOWER": "food"}]
        ])
        
        # Pattern for "X is my favorite game"
        self.matcher.add("FAVORITE_GAME_PATTERN", [
            [{"POS": {"IN": ["NOUN", "PROPN"]}}, 
             {"LEMMA": "be"}, 
             {"LOWER": "my"}, 
             {"LOWER": "favorite"}, 
             {"LOWER": {"IN": ["game", "videogame", "video game"]}}]
        ])
        
        # Pattern for "I love X" (generic)
        self.matcher.add("LOVE_PATTERN", [
            [{"LOWER": {"IN": ["i", "we"]}}, 
             {"LEMMA": "love"}, 
             {"POS": {"IN": ["NOUN", "PROPN"]}}]
        ])

        # Pattern for "I enjoy X" (positive preference)
        self.matcher.add("ENJOY_PATTERN", [
            [{"LOWER": {"IN": ["i", "we"]}}, 
             {"LEMMA": "enjoy"}, 
             {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}]
        ])
        
        # Pattern for "I don't like X" (negative preference)
        self.matcher.add("DISLIKE_PATTERN", [
            [
                {"LOWER": {"IN": ["i", "we"]}},
                {"LOWER": "don't"},
                {"LEMMA": "like"},
                {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}}
            ],
            # Add an alternative pattern that might match better
            [
                {"LOWER": {"IN": ["i", "we"]}},
                {"LOWER": "don't"},
                {"LOWER": "like"},
                {"TEXT": {"REGEX": ".*ing$"}}  # Match words ending with "ing"
            ]
        ])

        # Also add a pattern for "I hate X" or "I dislike X"
        self.matcher.add("HATE_PATTERN", [
            [
                {"LOWER": "i"},
                {"LOWER": {"IN": ["hate", "dislike"]}},
                {"POS": "VERB", "OP": "?"}, # Optional verb like "eating"
                {"POS": {"IN": ["NOUN", "PROPN"]}} # Required object
            ],
            
            [
                {"LOWER": "i"},
                {"LOWER": {"IN": ["hate", "dislike"]}},
                {"LEMMA": {"IN": ["eat", "cook", "drink"]}}, # Specific verbs that need objects
                {"POS": {"IN": ["NOUN", "PROPN"]}} # Required object
            ]
        ])
        
        # Pattern for "I don't like X"
        self.matcher.add("DONT_LIKE_PATTERN", [
            [
                {"LOWER": "i"},
                {"LOWER": "do"},
                {"LOWER": "n't"},
                {"LOWER": "like"},
                {"POS": "VERB"}  # This should match "running" which is tagged as VERB
            ]
        ])

        # Pattern for "I don't enjoy X"
        self.matcher.add("DONT_ENJOY_PATTERN", [
            [
                {"LOWER": "i"},
                {"LOWER": "do"},
                {"LOWER": "n't"},
                {"LOWER": "enjoy"},
                {"POS": "VERB"}  # This should match "running" which is tagged as VERB
            ]
        ])
        
        # Pattern for "I love X"
        self.matcher.add("LOVE_PATTERN", [
            [
                {"LOWER": "i"},
                {"LOWER": "love"},
                {"POS": {"IN": ["NOUN", "VERB"]}}  # This should match "cycling"
            ]
        ])

        self.game_titles = GAME_TITLES

    def extract_preferences(self, text, user_id="user"):
        doc = self.nlp(text)
        results = []
        
        # Split compound sentences with "but"
        if "but" in text.lower():
            parts = text.lower().split("but")
            for part in parts:
                part_results = self.extract_preferences(part.strip(), user_id)
                results.extend(part_results)
            return results
        
        # Handle "and" conjunctions for preferences
        elif " and " in text.lower() and ("like" in text.lower() or "love" in text.lower() or 
                                        "enjoy" in text.lower() or "hate" in text.lower() or 
                                        "don't like" in text.lower()):
            # Split the sentence on "and"
            parts = text.split(" and ")
            
            # Find the subject and sentiment in the first part
            first_doc = self.nlp(parts[0])
            subject = None
            sentiment = None
            
            for token in first_doc:
                if token.pos_ in ["PRON", "PROPN", "NOUN"] and token.dep_ == "nsubj":
                    subject = token.text
                    break
            
            if "like" in parts[0].lower():
                sentiment = "likes"
            elif "love" in parts[0].lower():
                sentiment = "likes"  # Treat love as likes
            elif "enjoy" in parts[0].lower():
                sentiment = "likes"
            elif "hate" in parts[0].lower() or "don't like" in parts[0].lower():
                sentiment = "dislikes"
            
            if subject and sentiment:
                # Process the first part as is
                first_results = self.extract_preferences(parts[0], user_id)
                results.extend(first_results)
                
                # For the second part, create a complete sentence with the same sentiment
                second_sentence = f"{subject} {sentiment} {parts[1]}"
                second_results = self.extract_preferences(second_sentence, user_id)
                results.extend(second_results)
                
                return results
        
        # Process patterns normally for the current text
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            pattern_name = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            if pattern_name == "FAVORITE_COLOR_PATTERN":
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "likes",
                    "preference_category": "color",
                    "preference_value": doc[start].text.lower(),
                    "notes": f"User expressed that {doc[start].text} is their favorite color",
                    "context": f"likes the color {doc[start].text.lower()}"  # Added context
                })
            
            elif pattern_name == "FAVORITE_FOOD_PATTERN":
                food_name = doc[start].text.lower()
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "likes",
                    "preference_category": "food",
                    "preference_value": food_name,
                    "notes": f"User expressed that {food_name} is their favorite food",
                    "context": f"likes {food_name}"  # Added context
                })
            
            elif pattern_name == "FAVORITE_GAME_PATTERN":
                game_name = doc[start].text.lower()
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "likes",
                    "preference_category": "games",
                    "preference_value": game_name,
                    "notes": f"User expressed that {game_name} is their favorite game",
                    "context": f"likes {game_name}"  # Added context
                })
            
            elif pattern_name == "LOVE_PATTERN":
                object_name = doc[start+2].text.lower()
                category = self.categorize_object(object_name)
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "likes",
                    "preference_category": category,
                    "preference_value": object_name,
                    "notes": f"User expressed that they love {object_name}",
                    "context": f"likes {object_name}"  # Added context
                })

            elif pattern_name == "ENJOY_PATTERN":
                activity = doc[start+2].text.lower()  # Get the activity being enjoyed
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "likes",
                    "preference_value": activity,
                    "notes": f"User expressed likes towards {activity}",
                    "context": f"likes {activity}"
                })
            
            elif pattern_name == "DISLIKE_PATTERN":
                activity = doc[start+3].text.lower()  # Get the activity being disliked
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "dislikes",
                    "preference_value": activity,
                    "notes": f"User expressed dislikes towards {activity}",
                    "context": f"dislikes {activity}"
                })
            
            elif pattern_name == "HATE_PATTERN":
                activity = doc[start+2].text.lower()  # Get the activity being hated
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "dislikes",
                    "preference_value": activity,
                    "notes": f"User expressed dislikes towards {activity}",
                    "context": f"dislikes {activity}"
                })

            elif pattern_name == "DONT_LIKE_PATTERN":
                activity = doc[start+4].text.lower()  # Note: index is now +4 because of the split tokens
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "dislikes",
                    "preference_value": activity,
                    "notes": f"User expressed dislikes towards {activity}",
                    "context": f"dislikes {activity}"
                })

            elif pattern_name == "DONT_ENJOY_PATTERN":
                activity = doc[start+4].text.lower()  # Index is +4 because of the split tokens
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "dislikes",
                    "preference_value": activity,
                    "notes": f"User expressed dislikes towards {activity}",
                    "context": f"dislikes {activity}"
                })
            
            elif pattern_name == "LOVE_PATTERN":
                activity = doc[start+2].text.lower()
                results.append({
                    "original_input": text,
                    "user_id": user_id,
                    "preference_type": "likes",
                    "preference_value": activity,
                    "notes": f"User expressed likes towards {activity}",
                    "context": f"likes {activity}"
                })
        
        # Define sentiment words
        positive_words = ["love", "like", "enjoy", "favorite", "prefer", "adore", "appreciate", "fond", "cherish"]
        negative_words = ["hate", "dislike", "detest", "avoid", "despise", "loathe", "can't stand", "don't like"]
        
        # Define activity verbs for categorization
        activity_verbs = {
            "entertainment": ["play", "gaming", "game"],
            "viewing": ["watch", "see", "view"],
            "listening": ["listen", "hear"],
            "food": ["eat", "drink", "consume", "taste", "cook", "bake"],
            "reading": ["read", "study"],
            "creation": ["make", "create", "build", "draw", "paint", "write"]
        }
    
        # Track negations
        negated = [False] * len(doc)
        for i, token in enumerate(doc):
            if token.lower_ in ["not", "n't", "no", "never"]:
                # Mark the next few tokens as negated
                for j in range(i+1, min(i+5, len(doc))):
                    negated[j] = True
        
        # Process sentences
        for sent in doc.sents:
            # Check for named entities first (like "Final Fantasy")
            for ent in sent.ents:
                # If it's a game title or product name
                if ent.label_ in ["PRODUCT", "WORK_OF_ART", "ORG"] or (
                    ent.text.lower() in ["final fantasy", "zelda", "mario", "minecraft"]):
                    # Look for sentiment indicators nearby
                    sentiment_type = None
                    for token in sent:
                        # Check if within 5 tokens of the entity
                        if abs(token.i - ent.start) <= 5:
                            if token.lemma_.lower() in positive_words:
                                sentiment_type = "dislikes" if negated[token.i] else "likes"
                                break
                            elif token.lemma_.lower() in negative_words:
                                sentiment_type = "likes" if negated[token.i] else "dislikes"
                                break
                    
                    # If we found a sentiment, add as a game preference
                    if sentiment_type:
                        results.append({
                            "original_input": text,
                            "user_id": user_id,
                            "preference_type": sentiment_type,
                            "preference_category": "games",
                            "preference_value": ent.text.lower(),  # Ensure lowercase
                            "notes": f"User expressed {sentiment_type} towards {ent.text}",
                            "context": f"{sentiment_type} {ent.text.lower()}"
                        })
    
            for token in sent:
                # Check if token is a sentiment word (verb or otherwise)
                if token.lemma_.lower() in positive_words + negative_words:
                    # Determine sentiment type, accounting for negation
                    sentiment_type = None
                    if token.lemma_.lower() in positive_words:
                        sentiment_type = "dislikes" if negated[token.i] else "likes"
                    elif token.lemma_.lower() in negative_words:
                        sentiment_type = "likes" if negated[token.i] else "dislikes"
                    else:
                        continue  # Not a sentiment word
                
                    # Find objects related to this sentiment
                    for obj in token.children:
                        # Case 1: Direct objects (nouns) - "I like cheese"
                        if obj.dep_ in ["dobj", "attr", "conj", "pobj"] and obj.pos_ not in ["VERB"]:
                            # Get the full noun phrase if possible
                            phrase = ""
                            if obj.pos_ in ["NOUN", "PROPN"]:
                                # Check for compound nouns and modifiers
                                compounds = []
                                for child in obj.subtree:
                                    if (child.dep_ in ["compound", "amod"] and child.i < obj.i) or child == obj:
                                        compounds.append((child.i, child.text))
                                
                                # Sort by position and join
                                compounds.sort()
                                phrase = " ".join([c[1] for c in compounds])
                            
                            if not phrase:
                                phrase = obj.text
                                
                            # Clean up "rpg games final" to just "rpg games"
                            if "rpg games final" in phrase.lower():
                                phrase = phrase.lower().replace("rpg games final", "rpg games")
                                
                            # After getting the phrase and before adding it to results:
                            # Try to determine category
                            category = self.categorize_object(phrase)
                            
                            # Add the preference with context
                            results.append({
                                "original_input": text,
                                "user_id": user_id,
                                "preference_type": sentiment_type,
                                "preference_category": category,
                                "preference_value": phrase.lower(),
                                "notes": f"User expressed {sentiment_type} towards {phrase}",
                                "context": f"{sentiment_type} {phrase.lower()}"
                            })
                            
                            # Check if this is a specific game title
                            self.game_titles = ["final fantasy", "zelda", "mario", "minecraft"]
                            if any(title.lower() in phrase.lower() for title in self.game_titles):
                                # Extract just the game title
                                for title in self.game_titles:
                                    if title.lower() in phrase.lower():
                                        # Add the game title as a separate preference
                                        results.append({
                                            "original_input": text,
                                            "user_id": user_id,
                                            "preference_type": sentiment_type,
                                            "preference_category": "games",
                                            "preference_value": title,
                                            "notes": f"User expressed {sentiment_type} towards {title}",
                                            "context": f"{sentiment_type} {title}"
                                        })
                                        # Don't remove from phrase - just add as additional result
                        
                        # Case 2: Activity objects (verbs) - "I enjoy swimming"
                        elif (obj.dep_ in ["dobj", "xcomp", "ccomp"] and obj.pos_ == "VERB"):
                            # Get the verb context (objects and modifiers)
                            verb_context = self._get_verb_context(obj)
                            
                            # Skip if verb_context is None (verb without proper objects)
                            if verb_context is None:
                                continue
                            
                            # Check for specific game titles in the sentence text
                            self.game_titles = ["final fantasy", "zelda", "mario", "minecraft"]
                            sent_text = " ".join([token.text for token in obj.sent]).lower()
                            
                            for title in self.game_titles:
                                if title.lower() in (verb_context.lower() if verb_context else ""):
                                    # Add the game title as a separate preference
                                    proper_title = title.title()
                                    results.append({
                                        "original_input": text,
                                        "user_id": user_id,
                                        "preference_type": sentiment_type,
                                        "preference_category": "games",
                                        "preference_value": title,
                                        "notes": f"User expressed {sentiment_type} towards {title}",
                                        "context": f"{sentiment_type} {title}"
                                    })
                            
                            # If we have a context with objects
                            if verb_context and len(verb_context.split()) > 1:
                                # The first word is the verb
                                parts = verb_context.split()
                                verb = parts[0]
                                object_phrase = " ".join(parts[1:])
                                
                                # Clean up "rpg games final" to just "rpg games"
                                if "rpg games final" in object_phrase.lower():
                                    object_phrase = object_phrase.lower().replace("rpg games final", "rpg games")
                                    verb_context = f"{verb} {object_phrase}"
                                
                                # Determine the activity category based on the verb
                                activity_category = "activity"  # Default category
                                for category, verbs in activity_verbs.items():
                                    if verb.lower() in verbs or any(v in verb.lower() for v in verbs):
                                        activity_category = category
                                        break
                                
                                # Add the full activity
                                results.append({
                                    "original_input": text,
                                    "user_id": user_id,
                                    "preference_type": sentiment_type,
                                    "preference_category": activity_category,
                                    "preference_value": verb_context.lower(),
                                    "notes": f"User expressed {sentiment_type} towards {verb_context}",
                                    "context": f"{sentiment_type} {verb_context.lower()}"  # Added context
                                })
                                
                                # Check if object_phrase starts with a preposition
                                words = object_phrase.split()
                                prepositions = ['in', 'at', 'on', 'by', 'for', 'with', 'to', 'from', 'about']
                                
                                # Only add the object as a separate preference if it's not just a prepositional phrase
                                if not (words and words[0].lower() in prepositions):
                                    obj_category = self.categorize_object(object_phrase)
                                    results.append({
                                        "original_input": text,
                                        "user_id": user_id,
                                        "preference_type": sentiment_type,
                                        "preference_category": obj_category,
                                        "preference_value": object_phrase.lower(),
                                        "notes": f"User expressed {sentiment_type} towards {object_phrase} (via {verb})",
                                        "context": f"{sentiment_type} {object_phrase.lower()}"  # Added context
                                    })
                                
                                # Always add the verb itself as a preference (e.g., "swimming")
                                results.append({
                                    "original_input": text,
                                    "user_id": user_id,
                                    "preference_type": sentiment_type,
                                    "preference_category": "activity",
                                    "preference_value": verb.lower(),
                                    "notes": f"User expressed {sentiment_type} towards {verb}",
                                    "context": f"{sentiment_type} {verb.lower()}"
                                })
                            else:
                                # Only add if verb_context exists (we already checked for None above)
                                if verb_context:
                                    # Just the verb itself (e.g., "I enjoy swimming")
                                    results.append({
                                        "original_input": text,
                                        "user_id": user_id,
                                        "preference_type": sentiment_type,
                                        "preference_category": "activity",
                                        "preference_value": obj.text.lower(),
                                        "notes": f"User expressed {sentiment_type} towards {obj.text}",
                                        "context": f"{sentiment_type} {obj.text.lower()}"  # Added context
                                    })
                        
                        # Case 3: Clausal complements - "I love how you designed this"
                        elif obj.dep_ in ["ccomp", "xcomp"] and obj.pos_ == "VERB":
                            results.append({
                                "original_input": text,
                                "user_id": user_id,
                                "preference_type": sentiment_type,
                                "preference_category": "general",
                                "preference_value": f"{obj.text}",
                                "notes": f"User expressed {sentiment_type} towards {obj.text}",
                                "context": f"{sentiment_type} {obj.text.lower()}"  # Added context
                            })
    
        # Add this special pass right after the main sentence loop ends
        # Special pass for "especially" phrases
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            # Check for phrases like "especially Final Fantasy"
            especial_markers = ["especially", "particularly", "specifically", "mainly", "notably"]
            for marker in especial_markers:
                if marker in sent_text:
                    # Find the marker position
                    marker_pos = sent_text.find(marker)
                    # Check what follows the marker
                    following_text = sent_text[marker_pos + len(marker):].strip()
                    
                    # Check if a game title follows
                    for title in ["final fantasy", "zelda", "mario", "minecraft"]:
                        if title in following_text:
                            # Find sentiment
                            sentiment_type = None
                            for token in sent:
                                if token.lemma_.lower() in positive_words:
                                    sentiment_type = "dislikes" if negated[token.i] else "likes"
                                    break
                                elif token.lemma_.lower() in negative_words:
                                    sentiment_type = "likes" if negated[token.i] else "dislikes"
                                    break
                            
                            if sentiment_type:
                                proper_title = title.title()
                                results.append({
                                    "original_input": text,
                                    "user_id": user_id,
                                    "preference_type": sentiment_type,
                                    "preference_category": "games",
                                    "preference_value": proper_title,
                                    "notes": f"User expressed {sentiment_type} towards {proper_title}",
                                    "context": f"{sentiment_type} {proper_title}"
                                })
        
        # NEW SECTION: Look for activity-game relationships (at the same level as the "especially" section)
        for sent in doc.sents:
            # Example: "I enjoy playing Final Fantasy"
            for token in sent:
                # Find activity verbs (playing, watching, etc.)
                if token.lemma_.lower() in ["play", "playing"]:
                    # Look for game titles in the same sentence
                    self.game_titles = ["final fantasy", "zelda", "mario", "minecraft"]
                    sent_text = sent.text.lower()
                    
                # If a game title is mentioned with the play verb
                for title in self.game_titles:
                    if title in sent_text:
                        # Determine sentiment
                        sentiment_type = "likes"  # Default to likes
                        for word in sent:
                            if word.lemma_.lower() in positive_words and word.i < token.i:
                                sentiment_type = "dislikes" if negated[word.i] else "likes"
                                break
                            elif word.lemma_.lower() in negative_words and word.i < token.i:
                                sentiment_type = "likes" if negated[word.i] else "dislikes"
                                break
                        
                        # Add both the activity and the game as preferences
                        results.append({
                            "original_input": text,
                            "user_id": user_id,
                            "preference_type": sentiment_type,
                            "preference_category": "entertainment",
                            "preference_value": f"playing {title}",
                            "notes": f"User expressed {sentiment_type} towards playing {title.title()}",
                            "context": f"{sentiment_type} playing {title}"
                        })
    
        # Ensure all preferences have context
        for pref in results:
            if "context" not in pref or not pref["context"]:
                pref_type = pref.get("preference_type", "likes")
                pref_value = pref.get("preference_value", "")
                pref["context"] = f"{pref_type} {pref_value}"

        # Right before returning the results, add this filtering:
        filtered_results = []
        prepositions = ['in', 'at', 'on', 'by', 'for', 'with', 'to', 'from']
        
        # These verbs are too generic to stand alone
        generic_verbs = ['eat', 'eating', 'play', 'playing', 'read', 'reading', 'watch', 'watching']
        
        # These are valid hobby verbs that can stand alone
        valid_hobby_verbs = ['cook', 'cooking', 'bake', 'baking', 'draw', 'drawing', 'paint', 'painting', 
                            'write', 'writing', 'dance', 'dancing', 'sing', 'singing']
        
        # First, deduplicate results based on preference_value and preference_type
        unique_preferences = {}
        for pref in results:
            key = (pref['preference_value'].lower(), pref['preference_type'])
            # Keep the preference with the most detailed notes (usually longer)
            if key not in unique_preferences or len(pref['notes']) > len(unique_preferences[key]['notes']):
                unique_preferences[key] = pref
        
        # Process the deduplicated results
        for pref in unique_preferences.values():
            value = pref['preference_value'].lower()
            words = value.split()
            
            # Fix verb conjugation (read -> reading)
            if 'read' in words:
                # Replace 'read' with 'reading' in all relevant fields
                pref['preference_value'] = pref['preference_value'].replace('read ', 'reading ')
                if 'notes' in pref:
                    pref['notes'] = pref['notes'].replace(' read ', ' reading ').replace('towards read', 'towards reading')
                if 'context' in pref:
                    pref['context'] = pref['context'].replace(' read ', ' reading ').replace('read ', 'reading ')
            
            # After fixing conjugation, update value and words
            value = pref['preference_value'].lower()
            words = value.split()
            
            # Skip preferences that are just prepositional phrases without verb context
            if (len(words) > 1 and words[0] in prepositions and 
                not any(verb in pref.get('context', '').lower() for verb in 
                    ['enjoy', 'like', 'love', 'hate', 'playing', 'swimming', 'reading', 'watching'])):
                continue
            
            # Skip standalone generic verbs, but keep hobby verbs
            if len(words) == 1 and words[0] in generic_verbs and words[0] not in valid_hobby_verbs:
                continue
            
            # Only filter out prepositional phrases that are subsets
            is_subset_to_filter = False
            if words and words[0] in prepositions:  # Only check prepositional phrases
                for other_key, other_pref in unique_preferences.items():
                    if (pref != other_pref and 
                        pref['preference_value'] in other_pref['preference_value'] and
                        pref['preference_type'] == other_pref['preference_type']):
                        is_subset_to_filter = True
                        break
            
            if not is_subset_to_filter:
                filtered_results.append(pref)
        
        # Now, let's add the basic verbs as separate preferences if they're not already included
        activity_verbs = ['reading', 'cooking', 'swimming', 'cycling', 'running', 'drawing', 'painting', 'writing', 'dancing', 'singing']
        added_verbs = set()
        
        for pref in list(filtered_results):  # Use a copy to avoid modification during iteration
            value = pref['preference_value'].lower()
            words = value.split()
            
            # If this preference contains an activity verb
            for verb in activity_verbs:
                if verb in words and verb not in added_verbs:
                    # Check if we already have this verb as a standalone preference
                    if not any(p['preference_value'] == verb for p in filtered_results):
                        # Add the verb as a standalone preference
                        filtered_results.append({
                            "original_input": pref.get('original_input', ''),
                            "user_id": pref.get('user_id', 'user'),
                            "preference_type": pref['preference_type'],
                            "preference_category": "activity",
                            "preference_value": verb,
                            "notes": f"User expressed {pref['preference_type']} towards {verb}",
                            "context": f"{pref['preference_type']} {verb}"
                        })
                        added_verbs.add(verb)
        
        # Special case for RPG games and implied preferences
        text_lower = text.lower()
        if "rpg games" in text_lower or "rpg game" in text_lower:
            # First, handle the rpg/rpg games conversion
            has_rpg = any(result["preference_value"] == "rpg" for result in filtered_results)
            has_rpg_games = any(result["preference_value"] == "rpg games" for result in filtered_results)
            
            if has_rpg and has_rpg_games:
                # If both exist, remove the "rpg" entries
                filtered_results = [result for result in filtered_results if result["preference_value"] != "rpg"]
            elif has_rpg:
                # If only "rpg" exists, convert it to "rpg games"
                for result in filtered_results:
                    if result["preference_value"] == "rpg":
                        result["preference_value"] = "rpg games"
                        result["notes"] = re.sub(r'\brpg\b', "rpg games", result["notes"], flags=re.IGNORECASE)
                        if "context" in result:
                            result["context"] = re.sub(r'\brpg\b', "rpg games", result["context"], flags=re.IGNORECASE)
            
            # Now add implied preferences if they don't already exist
            
            # Check for "games" preference
            has_games = any(result["preference_value"] == "games" for result in filtered_results)
            if not has_games:
                # Add implied "games" preference
                games_pref = {
                    "preference_type": "likes",
                    "preference_value": "games",
                    "notes": "User expressed likes towards games (implied by rpg games)",
                    "context": "likes games (implied by likes rpg games)"
                }
                filtered_results.append(games_pref)
            
            # Check for "playing games" if "playing rpg games" exists
            has_playing_rpg_games = any(result["preference_value"] == "playing rpg games" for result in filtered_results)
            has_playing_games = any(result["preference_value"] == "playing games" for result in filtered_results)
            
            if has_playing_rpg_games and not has_playing_games:
                # Add implied "playing games" preference
                playing_games_pref = {
                    "preference_type": "likes",
                    "preference_value": "playing games",
                    "notes": "User expressed likes towards playing games (implied by playing rpg games)",
                    "context": "likes playing games (implied by likes playing rpg games)"
                }
                filtered_results.append(playing_games_pref)
            
            # Check for "gaming" preference
            has_gaming = any(result["preference_value"] == "gaming" for result in filtered_results)
            if not has_gaming and has_playing_rpg_games:
                # Add implied "gaming" preference
                gaming_pref = {
                    "preference_type": "likes",
                    "preference_value": "gaming",
                    "notes": "User expressed likes towards gaming (implied by playing rpg games)",
                    "context": "likes gaming (implied by likes playing rpg games)"
                }
                filtered_results.append(gaming_pref)
        
        # Handle "with" phrases to maintain precision
        for i, result in enumerate(filtered_results):
            pref_value = result["preference_value"]
            
            # Check if this preference has a "with" phrase in the original text
            if " with " in text_lower:
                # Look for patterns like "[pref_value] with [something]"
                with_pattern = rf"\b{re.escape(pref_value)}\s+with\s+([a-z\s]+)"
                match = re.search(with_pattern, text_lower)
                
                if match:
                    # Found a "with" phrase that includes this preference
                    with_object = match.group(1).strip()
                    new_value = f"{pref_value} with {with_object}"
                    
                    # Update the preference value to include the "with" phrase
                    filtered_results[i]["preference_value"] = new_value
                    
                    # Update notes and context
                    if "notes" in filtered_results[i]:
                        filtered_results[i]["notes"] = filtered_results[i]["notes"].replace(
                            pref_value, new_value)
                    
                    if "context" in filtered_results[i]:
                        filtered_results[i]["context"] = filtered_results[i]["context"].replace(
                            pref_value, new_value)
            
            # Also check for verb+object with something patterns
            if " with " in text_lower and " " in pref_value:  # Only for multi-word preferences
                verb_obj_pattern = rf"\b{re.escape(pref_value)}\s+with\s+([a-z\s]+)"
                match = re.search(verb_obj_pattern, text_lower)
                
                if match:
                    with_object = match.group(1).strip()
                    new_value = f"{pref_value} with {with_object}"
                    
                    # Update the preference
                    filtered_results[i]["preference_value"] = new_value
                    
                    if "notes" in filtered_results[i]:
                        filtered_results[i]["notes"] = filtered_results[i]["notes"].replace(
                            pref_value, new_value)
                    
                    if "context" in filtered_results[i]:
                        filtered_results[i]["context"] = filtered_results[i]["context"].replace(
                            pref_value, new_value)
        
        # Handle "listening to X music" patterns
        for i, result in enumerate(filtered_results):
            pref_value = result["preference_value"]
            
            # Check for "listening to X music" pattern
            if pref_value.startswith("listening to ") and pref_value.endswith(" music"):
                # Extract the music genre
                genre = pref_value.replace("listening to ", "").replace(" music", "")
                
                # Add the music genre as a separate preference
                music_pref = {
                    "preference_type": "likes",
                    "preference_value": genre,
                    "notes": f"User expressed likes towards {genre} music",
                    "context": result.get("context", f"likes {genre}")
                }
                
                # Only add if it doesn't already exist
                if not any(r["preference_value"] == genre for r in filtered_results):
                    filtered_results.append(music_pref)

        # Fix incomplete activities
        for i, result in enumerate(filtered_results):
            if result["preference_value"] == "listening":
                # Look for a more complete "listening to X" preference
                complete_listening = next(
                    (r for r in filtered_results if r["preference_value"].startswith("listening to ")), 
                    None
                )
                
                if complete_listening:
                    # Replace the incomplete "listening" with the complete version
                    filtered_results[i]["preference_value"] = complete_listening["preference_value"]
                    if "notes" in filtered_results[i]:
                        filtered_results[i]["notes"] = filtered_results[i]["notes"].replace(
                            "listening", complete_listening["preference_value"])
                    if "context" in filtered_results[i]:
                        filtered_results[i]["context"] = complete_listening.get("context", 
                            filtered_results[i]["context"].replace("listening", complete_listening["preference_value"]))
        
        # Debug print after all processing
        print("DEBUG: Final results:", [(r["preference_value"], r.get("context", "")) for r in filtered_results])
        
        return filtered_results
    
    def categorize_object(self, object_phrase):
        """Categorize an object based on keywords"""
        phrase_lower = object_phrase.lower()

        # Check for specific game titles first
        if any(title in phrase_lower for title in self.game_titles):
            return "games"
        
        # Check for compound phrases
        if "rpg games" in phrase_lower or "video games" in phrase_lower:
            return "games"
        
        # Check for individual keywords
        if any(word in phrase_lower for word in ["game", "gaming", "video game", "rpg"]):
            return "games"
        elif any(word in phrase_lower for word in ["movie", "film", "show", "series"]):
            return "movies"
        elif any(word in phrase_lower for word in ["music", "song", "album", "band", "artist"]):
            return "music"
        elif any(word in phrase_lower for word in ["book", "novel", "story", "read"]):
            return "books"
        elif any(word in phrase_lower for word in ["food", "eat", "meal", "dish", "cuisine", "dinner", "lunch", "breakfast"]):
            return "food"
        elif any(word in phrase_lower for word in ["color", "colour", "blue", "red", "green", "yellow", "purple", "orange", "black", "white"]):
            return "colors"
        elif any(word in phrase_lower for word in ["sport", "exercise", "workout", "fitness", "running", "swimming", "cycling"]):
            return "sports"
        elif any(word in phrase_lower for word in ["travel", "trip", "vacation", "destination", "country", "city"]):
            return "travel"
        else:
            return "interests"
        
    def _get_verb_context(self, verb_token):
        """Get the context of a verb including its objects and modifiers."""
        print(f"\nDEBUG: Processing verb: {verb_token.text}")
        
        # Start with the verb itself
        context_parts = [verb_token.text]

        # Print the entire sentence for context
        print(f"DEBUG: Full sentence: {verb_token.sent.text}")
        
        # Print all children of the verb
        print(f"DEBUG: Verb children: {[f'{c.text}({c.dep_})' for c in verb_token.children]}")
        
        # Check for specific game titles in the sentence
        sent_text = " ".join([token.text for token in verb_token.sent]).lower()
        if "rpg games" in sent_text and verb_token.lemma_ == "play":
            return f"{verb_token.text} rpg games"

        # If playing/play is mentioned with a game title, handle specially
        if verb_token.lemma_.lower() in ["play"] and any(title in sent_text for title in self.game_titles):
            # Find which game title is mentioned
            for title in self.game_titles:
                if title in sent_text:
                    # Don't include the game title in the verb context
                    # Just return the verb + "games" as context
                    return f"{verb_token.text} games"
        
        # Add direct objects and modifiers
        has_object = False  # Track if we found any objects
        
        for child in verb_token.children:
            if child.dep_ in ["dobj", "pobj", "advmod", "prep"]:
                has_object = True  # We found an object
                
                # For prepositions, include their objects too
                if child.dep_ == "prep":
                    prep_phrase = [child.text]
                    for grandchild in child.children:
                        if grandchild.dep_ in ["pobj"]:
                            # Get the full noun phrase
                            if grandchild.pos_ in ["NOUN", "PROPN"]:
                                compounds = []
                                for gc_child in grandchild.subtree:
                                    if gc_child.dep_ in ["compound", "amod", "det"] or gc_child == grandchild:
                                        compounds.append((gc_child.i, gc_child.text))
                                
                                compounds.sort()
                                prep_phrase.extend([c[1] for c in compounds])
                            else:
                                prep_phrase.append(grandchild.text)
                    
                    context_parts.append(" ".join(prep_phrase))
                else:
                    # For direct objects, get the full noun phrase
                    if child.pos_ in ["NOUN", "PROPN"]:
                        # Debug print to see what's happening
                        print(f"DEBUG: Processing noun: {child.text}")
                        
                        # Get the entire subtree as one phrase
                        subtree_text = " ".join([token.text for token in child.subtree])
                        
                        # Special case for "RPG games"
                        if "rpg" in subtree_text.lower() and "game" in subtree_text.lower():
                            context_parts.append("rpg games")
                        else:
                            context_parts.append(subtree_text)
                    else:
                        context_parts.append(child.text)
        
        # If no objects were found, this verb phrase is incomplete
        if not has_object:
            return None  # Return None for standalone verbs without objects
        
        # Fix grammatical issues for specific verbs
        if verb_token.lemma_.lower() in ["listen", "listening"]:
            # If "to" is not already in the context
            context_str = " ".join(context_parts).lower()
            if " to " not in context_str and not any(p.lower() == "to" for p in context_parts[1:]):
                # Insert "to" after the verb
                context_parts.insert(1, "to")
        
        # Clean up "rpg games final" to just "rpg games" if it appears
        context_str = " ".join(context_parts).lower()
        if "rpg games final" in context_str:
            context_str = context_str.replace("rpg games final", "rpg games")
            return context_str
        
        # At the end, print what's being returned
        result = " ".join(context_parts)
        print(f"DEBUG: Final verb context: {result}")
        return result