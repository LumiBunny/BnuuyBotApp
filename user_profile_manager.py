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
                    "entertainment": [],
                    "games": [],
                    "general": [],
                    "color": []
                },
                "important_dates": {},
                "reminders": [],
                "conversation_history": []
            }
            self._save_profile(user_id, profile)
            return profile
        
    def clean_profile_categories(self, user_id):
        """Remove deprecated categories and ensure profile has current structure."""
        profile = self.get_profile(user_id)
        
        # Remove ONLY these deprecated categories
        categories_to_remove = ["listening", "activity"]
        for category in categories_to_remove:
            if category in profile["preferences"]:
                del profile["preferences"][category]
        
        # Ensure all current categories exist
        current_categories = ["food", "hobbies", "interests", "colors", "music", 
                             "movies", "entertainment", "games", "general", "color"]
        for category in current_categories:
            if category not in profile["preferences"]:
                profile["preferences"][category] = []
        
        # Save the updated profile
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
        
        # Debug output
        print(f"Categorizing: '{value}'")
        
        # Return category if already provided and valid
        if category and category != 'general':
            print(f"  Using provided category: {category}")
            return category
        
        # Handle specific cases first
        if value == "jazz" or value == "listening to jazz music":
            print("  Explicitly categorizing jazz as music")
            return "music"
        
        # Handle specific hobby cases
        if value == "gaming" or value == "playing games":
            print("  Explicitly categorizing as hobbies")
            return "hobbies"
        
        # Check for reading/learning activities - explicitly as interests
        if "reading" in value or "learning" in value or "studying" in value:
            print("  Explicitly categorizing as interests")
            return "interests"
        
        # Check for music-related content
        music_keywords = ['music', 'jazz', 'song', 'band', 'artist', 'album', 'concert', 
                         'sing', 'singing', 'instrument', 'rock', 'pop', 'classical', 
                         'hip hop', 'rap', 'blues', 'country', 'piano', 'guitar', 'drum', 
                         'violin', 'viola', 'cello', 'saxophone', 'flute', 'clarinet', 
                         'trombone', 'trumpet', 'soprano', 'alto', 'tenor', 'baritone',
                         'piano', 'piccolo', 'edm', 'dance', 'euro pop', 'euro dance',
                         'electro', 'electronic', 'electronic music', 'house', 'techno',
                         'indie', 'sheet music', 'chord', 'chords', 'chord progression']
        if any(keyword in value for keyword in music_keywords):
            print(f"  Categorizing as music (matched keyword)")
            return "music"
        
        # Check for game-related content
        game_keywords = ['rpg', 'game', 'final fantasy', 'video game', 'videogame']
        if any(keyword in value for keyword in game_keywords) and not (value == "gaming" or value == "playing games"):
            print(f"  Categorizing as games (matched keyword)")
            return "games"
        
        # Check for playing activities - prioritize games if it contains game keywords
        if 'playing' in value:
            for game_keyword in ['rpg', 'game', 'final fantasy', 'video game']:
                if game_keyword in value and not value == "playing games":
                    print(f"  Categorizing as games (contains playing + game keyword)")
                    return "games"
            # If it's playing but not game-related, it's an interest
            print(f"  Categorizing as interests (playing activity not game-related)")
            return "interests"
        
        # Then check for food items
        food_keywords = ['food', 'eat', 'eating', 'cuisine', 'meal', 'drink', 'pizza', 
                        'pasta', 'cheese', 'broccoli', 'vegetable', 'fruit', 'meat', 
                        'dessert', 'breakfast', 'lunch', 'dinner', 'snack', 'sandwich',
                        'vegetarian', 'vegan', 'gluten free', 'gluten free food',
                        'meat', 'dairy', 'egg', 'butter', 'buttery', 'buttery food']
        if any(keyword in value for keyword in food_keywords):
            print(f"  Categorizing as food (matched keyword)")
            return "food"
        
        # Hobby-related keywords
        hobby_keywords = ['hobby', 'swimming', 'run', 'running', 
                         'cycling', 'bike', 'hike', 'draw', 'drawing', 'paint', 
                         'painting', 'craft', 'crafting', 'reading', 'learning',
                         'write', 'writing', 'cook', 'cooking', 'cookbook',
                         'playing music', 'programming', 'coding', 'streaming',
                         'vtubing', 'baking']
        if any(keyword in value for keyword in hobby_keywords):
            print(f"  Categorizing as hobbies (matched keyword)")
            return "hobbies"
        
        # Color-related keywords
        color_keywords = ['color', 'blue', 'red', 'green', 'yellow', 'purple', 'orange',
                         'black', 'white', 'pink', 'brown', 'teal', 'maroon', 'navy',
                         'grey', 'silver', 'gold', 'gold color', 'turquoise', 'violet',
                         'magenta', 'cyan', 'indigo', 'lavender', 'lilac', 'lilac color',
                         'emerald', 'emerald green']
        if any(keyword in value for keyword in color_keywords):
            print(f"  Categorizing as colors (matched keyword)")
            return "colors"
        
        # Entertainment category
        entertainment_keywords = ['movie', 'film', 'cinema', 'series', 'episode', 
                                'actor', 'actress', 'director', 'watch', 'watching',
                                'podcast', 'concert', 'streaming', 'youtube', 'theatre',
                                'show', 'tv']
        if any(keyword in value for keyword in entertainment_keywords):
            print(f"  Categorizing as entertainment (matched keyword)")
            return "entertainment"
        
        # Interest-related keywords - expanded to capture more
        interest_keywords = ['interest', 'book', 'science', 'history', 'art', 
                            'technology', 'cooking', 'like', 'enjoy', 'love', 
                            'passionate', 'fan', 'enthusiast', 'collect', 'explore', 
                            'discover', 'follow', 'read', 'study']
        if any(keyword in value for keyword in interest_keywords):
            print(f"  Categorizing as interests (matched keyword)")
            return "interests"
        
        # Default to interests for anything else
        print(f"  Defaulting to interests for: {value}")
        return "interests"
    
    def add_preference(self, user_id, preference, category=None):
        """Add a preference to a user profile."""
        # First validate the preference
        is_valid, message = self.validate_preference(preference)
        if not is_valid:
            print(f"Skipping invalid preference: {message}")
            return False
        
        profile = self.get_profile(user_id)
        
        # Extract core data first so we can use it for category decisions
        pref_type = preference.get('preference_type', 'likes')
        pref_value = preference.get('preference_value', '').lower()
        context = preference.get('context', '')
        notes = preference.get('notes', '')
        
        if not category:
            category = self.categorize_preference(preference)
        
        # Make sure we never use deprecated categories
        if category in ["listening", "activity"]:
            if "listening" in pref_value:  # Use pref_value instead of undefined value
                category = "music"
            else:
                category = "interests"
        
        # Create the preference entry
        entry = {
            "type": pref_type,
            "value": pref_value,
            "context": context,
            "notes": notes
        }
        
        # Ensure the category exists in the profile
        if category not in profile["preferences"]:
            profile["preferences"][category] = []
        
        # Add the preference if it doesn't already exist
        added = self._add_if_not_exists(profile["preferences"][category], entry)
        
        # Save the updated profile
        if added:
            self._save_profile(user_id, profile)
            return True
        
        return False
    
    def _add_if_not_exists(self, preference_list, new_entry):
        """Helper method to add a preference if it doesn't already exist or is too similar."""
        # Special handling for "listening to jazz music"
        if new_entry.get("value", "").lower() == "listening to jazz music":
            print("Converting 'listening to jazz music' to just 'jazz'")
            new_entry["value"] = "jazz"

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