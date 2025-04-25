import os
import json

class UserProfileManager:
    def __init__(self, storage_path="user_profiles", preference_extractor=None, chat_logger=None):
        self.storage_path = storage_path
        self.cache = {}  # Profile cache
        self.indexes = {}  # Preference indexes
        self.preference_extractor = preference_extractor
        self.chat_logger = chat_logger
        os.makedirs(storage_path, exist_ok=True)

    def build_indexes(self, user_id):
        """Build indexes for faster preference lookups"""
        profile = self.get_profile(user_id)
        
        # Create a flat index of all preferences by value
        preference_by_value = {}
        
        for category, prefs in profile["preferences"].items():
            for pref in prefs:
                value = pref.get("value", "").lower()
                if value:
                    preference_by_value[value] = {
                        "category": category,
                        "preference": pref
                    }
        
        self.indexes[user_id] = {
            "by_value": preference_by_value
        }

    def has_preference(self, user_id, value):
        """Quickly check if a user has a specific preference"""
        # Build indexes if they don't exist
        if user_id not in self.indexes:
            self.build_indexes(user_id)
            
        # Check if preference exists
        return value.lower() in self.indexes[user_id]["by_value"]
    
    def extract_preferences(self, text, user_id):
        if self.preference_extractor:
            return self.preference_extractor.extract_preferences(text, user_id)
        return []

    def clear_cache(self):
        """Clear the profile cache"""
        self.cache = {}
        self.indexes = {}
        
    def get_profile_path(self, user_id):
        return os.path.join(self.storage_path, f"{user_id}.json")
    
    def _migrate_profile(self, profile, from_version, to_version):
        """Migrate profile from one version to another"""
        
        # Handle each version upgrade step by step
        current_version = from_version
        
        if current_version == 1 and to_version >= 2:
            # Migrate from v1 to v2
            self._apply_v2_changes(profile)
            current_version = 2
        
        if current_version == 2 and to_version >= 3:
            # Migrate from v2 to v3
            self._apply_v3_changes(profile)
            current_version = 3
        
        # Add more version steps as needed
        
        return current_version
    
    # _apply_v2_changes here is just a template/idea for future migrations as I update my app with new features
    def _apply_v2_changes(self, profile):
        """Apply changes for version 2 upgrade"""
        # Example: Merge "color" into "colors" category
        if "color" in profile["preferences"] and profile["preferences"]["color"]:
            if "colors" not in profile["preferences"]:
                profile["preferences"]["colors"] = []
            profile["preferences"]["colors"].extend(profile["preferences"]["color"])
            profile["preferences"]["color"] = []
        
        # Example: Add new fields
        if "settings" not in profile:
            profile["settings"] = {"theme": "default", "notifications": True}
        
    def get_profile(self, user_id):
        profile_path = self.get_profile_path(user_id)
        
        # Check if in cache first
        if user_id in self.cache:
            return self.cache[user_id]
        
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = json.load(f)

        else:
            profile = {
                "user_id": user_id,
                "version": 1,
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

        if "version" not in profile:
                profile["version"] = 1
                self._save_profile(user_id, profile)

        # Migrate if needed
        current_version = profile["version"]
        latest_version = 1  # Update this when adding new versions
        
        if current_version < latest_version:
            new_version = self._migrate_profile(profile, current_version, latest_version)
            profile["version"] = new_version
            self._save_profile(user_id, profile)
        
        # Add to cache
        self.cache[user_id] = profile
        
        # Build indexes immediately
        self.build_indexes(user_id)
        
        return profile
        
    def clean_profile_categories(self, user_id):
        profile = self.get_profile(user_id)
        
        # Remove ONLY these deprecated categories, will return to the idea later
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
        with open(self.get_profile_path(user_id), 'w') as f:
            json.dump(profile, f, indent=2)
        self.cache[user_id] = profile

    def create_backup(self, user_id):
        """Create a timestamped backup of a user profile"""
        import datetime
        
        profile = self.get_profile(user_id)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.storage_path}/backups/{user_id}_{timestamp}.json"
        
        # Ensure backup directory exists
        os.makedirs(f"{self.storage_path}/backups", exist_ok=True)
        
        # Save backup
        with open(backup_path, 'w') as f:
            json.dump(profile, f, indent=2)
        
        return backup_path
    
    def categorize_preference(self, preference):
        value = preference.get('preference_value', '').lower()
        category = preference.get('preference_category')
        
        if category and category != 'general':
            return category
        
        if value == "jazz" or value == "listening to jazz music":
            return "music"
        if value == "gaming" or value == "playing games":
            return "hobbies"
        if "reading" in value or "learning" in value or "studying" in value:
            return "interests"
        
        music_keywords = ['music', 'jazz', 'song', 'band', 'artist', 'album', 'concert', 
                         'sing', 'singing', 'instrument', 'rock', 'pop', 'classical', 
                         'hip hop', 'rap', 'blues', 'country', 'piano', 'guitar', 'drum', 
                         'violin', 'viola', 'cello', 'saxophone', 'flute', 'clarinet', 
                         'trombone', 'trumpet', 'soprano', 'alto', 'tenor', 'baritone',
                         'piano', 'piccolo', 'edm', 'dance', 'euro pop', 'euro dance',
                         'electro', 'electronic', 'electronic music', 'house', 'techno',
                         'indie', 'sheet music', 'chord', 'chords', 'chord progression']
        if any(keyword in value for keyword in music_keywords):
            return "music"
        
        game_keywords = ['rpg', 'game', 'final fantasy', 'video game', 'videogame']
        if any(keyword in value for keyword in game_keywords) and not (value == "gaming" or value == "playing games"):
            return "games"
        
        if 'playing' in value:
            for game_keyword in ['rpg', 'game', 'final fantasy', 'video game']:
                if game_keyword in value and not value == "playing games":
                    return "games"
            return "interests"
        
        food_keywords = ['food', 'eat', 'eating', 'cuisine', 'meal', 'drink', 'pizza', 
                        'pasta', 'cheese', 'broccoli', 'vegetable', 'fruit', 'meat', 
                        'dessert', 'breakfast', 'lunch', 'dinner', 'snack', 'sandwich',
                        'vegetarian', 'vegan', 'gluten free', 'gluten free food',
                        'meat', 'dairy', 'egg', 'butter', 'buttery', 'buttery food']
        if any(keyword in value for keyword in food_keywords):
            return "food"
        
        hobby_keywords = ['hobby', 'swimming', 'run', 'running', 
                         'cycling', 'bike', 'hike', 'draw', 'drawing', 'paint', 
                         'painting', 'craft', 'crafting', 'reading', 'learning',
                         'write', 'writing', 'cook', 'cooking', 'cookbook',
                         'playing music', 'programming', 'coding', 'streaming',
                         'vtubing', 'baking']
        if any(keyword in value for keyword in hobby_keywords):
            return "hobbies"
        
        color_keywords = ['color', 'blue', 'red', 'green', 'yellow', 'purple', 'orange',
                         'black', 'white', 'pink', 'brown', 'teal', 'maroon', 'navy',
                         'grey', 'silver', 'gold', 'gold color', 'turquoise', 'violet',
                         'magenta', 'cyan', 'indigo', 'lavender', 'lilac', 'lilac color',
                         'emerald', 'emerald green']
        if any(keyword in value for keyword in color_keywords):
            return "colors"
        
        entertainment_keywords = ['movie', 'film', 'cinema', 'series', 'episode', 
                                'actor', 'actress', 'director', 'watch', 'watching',
                                'podcast', 'concert', 'streaming', 'youtube', 'theatre',
                                'show', 'tv']
        if any(keyword in value for keyword in entertainment_keywords):
            return "entertainment"
        
        interest_keywords = ['interest', 'book', 'science', 'history', 'art', 
                            'technology', 'cooking', 'like', 'enjoy', 'love', 
                            'passionate', 'fan', 'enthusiast', 'collect', 'explore', 
                            'discover', 'follow', 'read', 'study']
        if any(keyword in value for keyword in interest_keywords):
            return "interests"
        
        print(f"  Defaulting to interests for: {value}")
        return "interests"
    
    def add_preference(self, user_id, preference, category=None):
        is_valid, message = self.validate_preference(preference)
        if not is_valid:
            return False
        
        profile = self.get_profile(user_id)
        
        pref_type = preference.get('preference_type', 'likes')
        pref_value = preference.get('preference_value', '').lower()
        context = preference.get('context', '')
        notes = preference.get('notes', '')
        
        if not category:
            category = self.categorize_preference(preference)
        
        if category in ["listening", "activity"]:
            if "listening" in pref_value:
                category = "music"
            else:
                category = "interests"
        
        entry = {
            "type": pref_type,
            "value": pref_value,
            "context": context,
            "notes": notes
        }
        
        if category not in profile["preferences"]:
            profile["preferences"][category] = []
        
        added = self._add_if_not_exists(profile["preferences"][category], entry)
        
        if added:
            self._save_profile(user_id, profile)
            # After saving the profile, rebuild the indexes
            self.build_indexes(user_id)
            
            # Log the preference to the chat log
            if self.chat_logger:
                log_message = f"[PREFERENCE ADDED] {pref_type} {category}: {pref_value}"
                self.chat_logger.append_to_log("system", log_message)
                
            return True
        
        return False
    
    def _add_if_not_exists(self, preference_list, new_entry):
        if new_entry.get("value", "").lower() == "listening to jazz music":
            new_entry["value"] = "jazz"

        new_value = new_entry.get("value", "").lower().strip()
        new_type = new_entry.get("type", "")
        
        for existing in preference_list:
            existing_value = existing.get("value", "").lower().strip()
            existing_type = existing.get("type", "")
            
            if existing_value == new_value and existing_type == new_type:
                return False
            
            if (new_value in existing_value or existing_value in new_value) and new_type == existing_type:
                if len(new_value) > len(existing_value):
                    existing.update(new_entry)
                return False
        
        preference_list.append(new_entry)
        return True
    
    def validate_preference(self, preference):
        value = preference.get('preference_value', '').strip().lower()
        if not value or len(value) < 2:
            return False, "Preference value is too short or empty"
            
        valid_types = ['likes', 'dislikes', 'neutral']
        pref_type = preference.get('preference_type', '').lower()
        if pref_type not in valid_types:
            return False, f"Invalid preference type: {pref_type}"
            
        stopwords = ['the', 'and', 'or', 'but', 'if', 'then', 'so', 'because', 'as']
        if value in stopwords:
            return False, f"'{value}' is too generic to be a meaningful preference"
            
        return True, "Valid preference"

    def get_profile_summary(self, user_id):
        profile = self.get_profile(user_id)
        summary = {}
        
        for category, prefs in profile["preferences"].items():
            summary[category] = []
            for pref in prefs:
                prefix = "" if pref.get("type") == "likes" else "doesn't like "
                summary[category].append(f"{prefix}{pref.get('value')}")
        
        return summary