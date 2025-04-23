import os
import json

class UserProfileManager:
    def __init__(self, storage_path="user_profiles"):
        """Initialize the user profile manager with storage location."""
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
    def get_profile_path(self, user_id):
        """Get the file path for a user profile."""
        return os.path.join(self.storage_path, f"{user_id}.json")
        
    def get_profile(self, user_id):
        """Get a user profile or create if it doesn't exist."""
        profile_path = self.get_profile_path(user_id)
        
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                return json.load(f)
        else:
            # Create default profile structure
            profile = {
                "user_id": user_id,
                "preferences": {
                    "food": [],
                    "hobbies": [],
                    "interests": [],
                    "colors": [],
                    "music": [],
                    "movies": [],
                    "general": []
                },
                "important_dates": {},
                "reminders": [],
                "conversation_history": []
            }
            self._save_profile(user_id, profile)
            return profile
    
    def _save_profile(self, user_id, profile):
        """Save a user profile to disk."""
        with open(self.get_profile_path(user_id), 'w') as f:
            json.dump(profile, f, indent=2)
    
    def categorize_preference(self, preference):
        """Categorize a preference based on its content."""
        value = preference.get('preference_value', '').lower()
        category = preference.get('preference_category')
        
        # Return category if already provided and valid
        if category and category != 'general':
            return category
        
        # First check for food items to prevent them appearing in interests
        food_keywords = ['food', 'eat', 'eating', 'cuisine', 'meal', 'drink', 'pizza', 
                        'pasta', 'cheese', 'broccoli', 'vegetable', 'fruit', 'meat', 
                        'dessert', 'breakfast', 'lunch', 'dinner']
        
        # Check if any food keyword is in the preference value
        for keyword in food_keywords:
            if keyword in value:
                return "food"
        
        # Hobby-related keywords
        hobby_keywords = ['play', 'game', 'gaming', 'hobby', 'reading', 'swim', 
                         'swimming', 'run', 'running', 'cycling', 'bike', 'hike',
                         'draw', 'drawing', 'paint', 'painting', 'craft', 'crafting']
        
        # Interest-related keywords
        interest_keywords = ['interest', 'book', 'movie', 'show', 'tv', 'watch', 
                           'watching', 'science', 'history', 'art', 'technology', 'cooking']
        
        # Color-related keywords
        color_keywords = ['color', 'blue', 'red', 'green', 'yellow', 'purple', 'orange',
                         'black', 'white', 'pink', 'brown']
        
        # Music-related keywords
        music_keywords = ['music', 'song', 'band', 'artist', 'album', 'concert', 
                         'listen', 'listening', 'sing', 'singing', 'instrument', 'jazz']
        
        # Movie-related keywords
        movie_keywords = ['movie', 'film', 'cinema', 'show', 'series', 'episode', 
                         'actor', 'actress', 'director', 'watch', 'watching']
        
        # Game-related keywords
        game_keywords = ['rpg', 'game', 'gaming', 'play', 'playing', 'video game']
        
        # Check for whole words rather than partial matches
        words = value.split()
        
        # Special case for RPG games
        if 'rpg' in value or 'rpg games' in value:
            return "games"
        
        # Special case for music
        if 'jazz' in value or 'music' in value:
            return "music"
        
        # Check each word for category matches
        for word in words:
            if word in hobby_keywords:
                return "hobbies"
            if word in interest_keywords:
                return "interests"
            if word in color_keywords:
                return "colors"
            if word in music_keywords:
                return "music"
            if word in movie_keywords:
                return "movies"
            if word in game_keywords:
                return "games"
        
        # Check if the value contains specific activities
        activities = ['playing', 'listening', 'watching', 'reading']
        if any(activity in value for activity in activities):
            # Check what the activity is about
            if any(music_word in value for music_word in music_keywords):
                return "music"
            if any(game_word in value for game_word in game_keywords):
                return "games"
            if any(movie_word in value for movie_word in movie_keywords):
                return "movies"
        
        # Default category
        return "general"
    
    def add_preference(self, user_id, preference, category=None):
        """Add a preference to a user profile."""
        # First validate the preference
        is_valid, message = self.validate_preference(preference)
        if not is_valid:
            print(f"Skipping invalid preference: {message}")
            return False
        
        profile = self.get_profile(user_id)
        
        if not category:
            category = self.categorize_preference(preference)
        
        # Extract core data
        pref_type = preference.get('preference_type', 'likes')
        pref_value = preference.get('preference_value', '').lower()
        notes = preference.get('notes', '')
        
        # Clean up the value and preserve compound terms
        pref_value = pref_value.replace("rpg games final", "rpg games")
        pref_value = pref_value.replace("games final", "games")
        
        # Fix standalone activities without objects
        activities = ['playing', 'listening', 'watching', 'reading']
        if pref_value in activities:
            # Skip standalone activities without objects
            print(f"Skipping incomplete activity: {pref_value} (missing object)")
            return False
        
        # Fix standalone prepositions without verbs
        words = pref_value.split()
        if len(words) > 1 and words[0] in ['to', 'of', 'in', 'at', 'by', 'for']:
            # Check if the preposition is standalone (not part of a verb phrase)
            # If there's no verb before it (like "listening to"), remove it
            verbs = ['listening', 'talking', 'going', 'looking', 'playing', 'reading']
            if not any(verb in preference.get('context', '').lower() for verb in verbs):
                # Remove the preposition
                pref_value = ' '.join(words[1:])
        
        # Create primary preference entry with context
        if 'context' not in preference:
            context = f"{pref_type} {pref_value}"
        else:
            context = preference['context']
            # Also clean up the context if needed
            context_words = context.split()
            if len(context_words) > 2 and context_words[1] in ['to', 'of', 'in', 'at', 'by', 'for']:
                # If context is like "likes to jazz music" without a verb, fix it
                verbs = ['listening', 'talking', 'going', 'looking', 'playing', 'reading']
                if not any(verb in context.lower() for verb in verbs):
                    context = f"{context_words[0]} {' '.join(context_words[2:])}"
        
        pref_entry = {
            "type": pref_type,
            "value": pref_value,
            "notes": notes,
            "context": context
        }
        
        # Add to appropriate category
        if category not in profile["preferences"]:
            profile["preferences"][category] = []
        
        # Check if this preference already exists in ANY category (not just the current one)
        already_exists = False
        for cat, prefs in profile["preferences"].items():
            for existing in prefs:
                existing_value = existing.get("value", "").lower().strip()
                existing_type = existing.get("type", "")
                existing_context = existing.get("context", "").lower().strip() if "context" in existing else ""
                
                # Check for exact matches
                if existing_value == pref_value and existing_type == pref_type:
                    already_exists = True
                    break
                
                # Check for context matches
                if existing_context == context:
                    already_exists = True
                    break
            
            if already_exists:
                break
        
        if not already_exists:
            # Check if primary preference already exists in this category
            self._add_if_not_exists(profile["preferences"][category], pref_entry)
            
            # Save the updated profile
            self._save_profile(user_id, profile)
        
        return True
    
    def _add_if_not_exists(self, preference_list, new_entry):
        """Helper method to add a preference if it doesn't already exist or is too similar."""
        new_value = new_entry.get("value", "").lower().strip()
        new_type = new_entry.get("type", "")
        
        # Check for exact matches
        for existing in preference_list:
            existing_value = existing.get("value", "").lower().strip()
            existing_type = existing.get("type", "")
            
            # Check for exact match
            if existing_value == new_value and existing_type == new_type:
                return False  # Exact match found, don't add
            
            # Check for similar entries (one being a substring of the other)
            if (new_value in existing_value or existing_value in new_value) and new_type == existing_type:
                # If one is contained in the other, keep the more specific (longer) one
                if len(new_value) > len(existing_value):
                    # Replace the existing entry with the new one
                    existing.update(new_entry)
                return False
        
        # If we get here, no match was found
        preference_list.append(new_entry)
        return True
    
    def validate_preference(self, preference):
        """Validate a preference entry before adding it."""
        # Check if preference value exists and is meaningful
        value = preference.get('preference_value', '').strip().lower()
        if not value or len(value) < 2:
            return False, "Preference value is too short or empty"
            
        # Check if preference type is valid
        valid_types = ['likes', 'dislikes', 'neutral']
        pref_type = preference.get('preference_type', '').lower()
        if pref_type not in valid_types:
            return False, f"Invalid preference type: {pref_type}"
            
        # Check for nonsensical single-word preferences (common stopwords)
        stopwords = ['the', 'and', 'or', 'but', 'if', 'then', 'so', 'because', 'as']
        if value in stopwords:
            return False, f"'{value}' is too generic to be a meaningful preference"
            
        return True, "Valid preference"

    def get_profile_summary(self, user_id):
        """Get a summary of user preferences by category."""
        profile = self.get_profile(user_id)
        summary = {}
        
        for category, prefs in profile["preferences"].items():
            summary[category] = []
            for pref in prefs:
                prefix = "" if pref.get("type") == "likes" else "doesn't like "
                summary[category].append(f"{prefix}{pref.get('value')}")
        
        return summary