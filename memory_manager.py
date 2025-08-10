import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Import your preference types
from preferences import PreferenceResult

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    # Represents a single memory entry with metadata.
    content: str
    timestamp: datetime
    importance: float  # 0.0 to 1.0
    category: str  # conversation, fact, preference, reminder, etc.
    tags: List[str]
    context: Optional[str] = None
    
    def to_dict(self) -> Dict:
        # Convert to dictionary for JSON serialization.
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        # Create from dictionary (JSON deserialization).
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class MemoryManager:
    """
    Manages user memory storage and retrieval using a per-user folder structure.
    
    File Structure:
    user_data/
    ├── {user_id}/
    │   ├── profile/
    │   │   ├── personal_info.json
    │   │   ├── preferences.json
    │   │   └── important_memories.json
    │   ├── conversations/
    │   │   ├── summaries/
    │   │   │   ├── 2024-08-08_summary.json
    │   │   │   └── weekly_2024-08-05.json
    │   │   └── raw_chats/
    │   │       └── 2024-08-08_chat.json
    │   └── agent_data/
    │       ├── reminders.json
    │       ├── notes.json
    │       └── mood_tracking.json
    """
    
    def __init__(self, base_data_dir: str = "user_data"):
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
        logger.info(f"MemoryManager initialized with base directory: {self.base_data_dir}")
    
    def _get_user_dir(self, user_id: str) -> Path:
        # Get the base directory for a specific user.
        return self.base_data_dir / user_id
    
    def _ensure_user_structure(self, user_id: str) -> None:
        # Create the directory structure for a user if it doesn't exist.
        user_dir = self._get_user_dir(user_id)
        
        # Create all necessary subdirectories
        directories = [
            user_dir / "profile",
            user_dir / "conversations" / "summaries",
            user_dir / "conversations" / "raw_chats", 
            user_dir / "agent_data"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty JSON files if they don't exist
        default_files = {
            user_dir / "profile" / "personal_info.json": {},
            user_dir / "profile" / "preferences.json": {
                "food": {"likes": [], "dislikes": [], "loves": [], "hates": []},
                "games": {"likes": [], "dislikes": [], "loves": [], "hates": []},
                "activities": {"likes": [], "dislikes": [], "loves": [], "hates": []},
                "colors": {"likes": [], "dislikes": [], "loves": [], "hates": []},
                "music": {"likes": [], "dislikes": [], "loves": [], "hates": []},
                "movies": {"likes": [], "dislikes": [], "loves": [], "hates": []},
                "other": {"likes": [], "dislikes": [], "loves": [], "hates": []}
            },
            user_dir / "profile" / "important_memories.json": [],
            user_dir / "agent_data" / "reminders.json": [],
            user_dir / "agent_data" / "notes.json": [],
            user_dir / "agent_data" / "mood_tracking.json": []
        }
        
        for file_path, default_content in default_files.items():
            if not file_path.exists():
                self._save_json(file_path, default_content)
                logger.info(f"Created default file: {file_path}")
    
    def _save_json(self, file_path: Path, data: Any) -> None:
        # Safely save data to JSON file.
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {e}")
            raise
    
    def _load_json(self, file_path: Path) -> Any:
        # Safely load data from JSON file.
        try:
            if not file_path.exists():
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading from {file_path}: {e}")
            return None
    
    # === PREFERENCE MANAGEMENT ===
    
    def save_preferences(self, user_id: str, preference_results: List[PreferenceResult]) -> None:
        # Save preference extraction results to user's preference file.
        self._ensure_user_structure(user_id)
        
        preferences_file = self._get_user_dir(user_id) / "profile" / "preferences.json"
        current_prefs = self._load_json(preferences_file) or {}
        
        # Group preferences by category and type
        for pref in preference_results:
            category = pref.preference_category
            pref_type = pref.preference_type
            value = pref.preference_value
            
            # Ensure category exists
            if category not in current_prefs:
                current_prefs[category] = {"likes": [], "dislikes": [], "loves": [], "hates": []}
            
            # Ensure preference type exists
            if pref_type not in current_prefs[category]:
                current_prefs[category][pref_type] = []
            
            # Add if not already present (avoid duplicates)
            if value not in current_prefs[category][pref_type]:
                current_prefs[category][pref_type].append(value)
                logger.info(f"Added preference: {user_id} {pref_type} {value} (category: {category})")
        
        self._save_json(preferences_file, current_prefs)
    
    def get_preferences(self, user_id: str, category: Optional[str] = None) -> Dict:
        # Get user preferences, optionally filtered by category.
        self._ensure_user_structure(user_id)
        
        preferences_file = self._get_user_dir(user_id) / "profile" / "preferences.json"
        prefs = self._load_json(preferences_file) or {}
        
        if category:
            return prefs.get(category, {"likes": [], "dislikes": [], "loves": [], "hates": []})
        return prefs
    
    # === MEMORY MANAGEMENT ===
    
    def add_memory(self, user_id: str, content: str, category: str, 
                   importance: float = 0.5, tags: List[str] = None, 
                   context: str = None) -> None:
        # Add a new memory entry.
        self._ensure_user_structure(user_id)
        
        memory = MemoryEntry(
            content=content,
            timestamp=datetime.now(),
            importance=importance,
            category=category,
            tags=tags or [],
            context=context
        )
        
        memories_file = self._get_user_dir(user_id) / "profile" / "important_memories.json"
        memories = self._load_json(memories_file) or []
        memories.append(memory.to_dict())
        
        self._save_json(memories_file, memories)
        logger.info(f"Added memory for {user_id}: {content[:50]}...")
    
    def get_memories(self, user_id: str, category: Optional[str] = None, 
                     min_importance: float = 0.0, days_back: Optional[int] = None) -> List[MemoryEntry]:
        # Retrieve memories with optional filtering.
        self._ensure_user_structure(user_id)
        
        memories_file = self._get_user_dir(user_id) / "profile" / "important_memories.json"
        memories_data = self._load_json(memories_file) or []
        
        memories = [MemoryEntry.from_dict(m) for m in memories_data]
        
        # Apply filters
        if category:
            memories = [m for m in memories if m.category == category]
        
        if min_importance > 0.0:
            memories = [m for m in memories if m.importance >= min_importance]
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            memories = [m for m in memories if m.timestamp >= cutoff_date]
        
        # Sort by importance and recency
        memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        return memories
    
    # === CONVERSATION MANAGEMENT ===
    
    def save_conversation_summary(self, user_id: str, summary: str, 
                                  main_topics: List[str], date: Optional[datetime] = None) -> None:
        # Save a conversation summary.
        self._ensure_user_structure(user_id)
        
        if date is None:
            date = datetime.now()
        
        summary_data = {
            "date": date.isoformat(),
            "summary": summary,
            "main_topics": main_topics,
            "created_at": datetime.now().isoformat()
        }
        
        summary_file = self._get_user_dir(user_id) / "conversations" / "summaries" / f"{date.strftime('%Y-%m-%d')}_summary.json"
        self._save_json(summary_file, summary_data)
        logger.info(f"Saved conversation summary for {user_id} on {date.strftime('%Y-%m-%d')}")
    
    def get_recent_summaries(self, user_id: str, days_back: int = 7) -> List[Dict]:
        # Get recent conversation summaries.
        self._ensure_user_structure(user_id)
        
        summaries_dir = self._get_user_dir(user_id) / "conversations" / "summaries"
        summaries = []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for summary_file in summaries_dir.glob("*_summary.json"):
            summary_data = self._load_json(summary_file)
            if summary_data:
                summary_date = datetime.fromisoformat(summary_data["date"])
                if summary_date >= cutoff_date:
                    summaries.append(summary_data)
        
        summaries.sort(key=lambda s: s["date"], reverse=True)
        return summaries
    
    # === AGENT DATA MANAGEMENT ===
    
    def add_reminder(self, user_id: str, reminder_text: str, 
                     due_date: Optional[datetime] = None, priority: str = "medium") -> None:
        # Add a reminder for the user.
        self._ensure_user_structure(user_id)
        
        reminder = {
            "id": len(self.get_reminders(user_id)) + 1,
            "text": reminder_text,
            "created_at": datetime.now().isoformat(),
            "due_date": due_date.isoformat() if due_date else None,
            "priority": priority,
            "completed": False
        }
        
        reminders_file = self._get_user_dir(user_id) / "agent_data" / "reminders.json"
        reminders = self._load_json(reminders_file) or []
        reminders.append(reminder)
        
        self._save_json(reminders_file, reminders)
        logger.info(f"Added reminder for {user_id}: {reminder_text}")
    
    def get_reminders(self, user_id: str, include_completed: bool = False) -> List[Dict]:
        # Get user reminders.
        self._ensure_user_structure(user_id)
        
        reminders_file = self._get_user_dir(user_id) / "agent_data" / "reminders.json"
        reminders = self._load_json(reminders_file) or []
        
        if not include_completed:
            reminders = [r for r in reminders if not r.get("completed", False)]
        
        return reminders
    
    def complete_reminder(self, user_id: str, reminder_id: int) -> bool:
        # Mark a reminder as completed.
        self._ensure_user_structure(user_id)
        
        reminders_file = self._get_user_dir(user_id) / "agent_data" / "reminders.json"
        reminders = self._load_json(reminders_file) or []
        
        for reminder in reminders:
            if reminder.get("id") == reminder_id:
                reminder["completed"] = True
                reminder["completed_at"] = datetime.now().isoformat()
                self._save_json(reminders_file, reminders)
                logger.info(f"Completed reminder {reminder_id} for {user_id}")
                return True
        
        return False
    
    # === NOTES MANAGEMENT ===
    
    def add_note(self, user_id: str, note_text: str, category: str = "general", 
                 tags: List[str] = None) -> None:
        # Add a note for the user.
        self._ensure_user_structure(user_id)
        
        note = {
            "id": len(self.get_notes(user_id)) + 1,
            "text": note_text,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        notes_file = self._get_user_dir(user_id) / "agent_data" / "notes.json"
        notes = self._load_json(notes_file) or []
        notes.append(note)
        
        self._save_json(notes_file, notes)
        logger.info(f"Added note for {user_id}: {note_text[:50]}...")
    
    def get_notes(self, user_id: str, category: Optional[str] = None) -> List[Dict]:
        # Get user notes, optionally filtered by category.
        self._ensure_user_structure(user_id)
        
        notes_file = self._get_user_dir(user_id) / "agent_data" / "notes.json"
        notes = self._load_json(notes_file) or []
        
        if category:
            notes = [n for n in notes if n.get("category") == category]
        
        return notes
    
    # === MOOD TRACKING ===
    
    def track_mood(self, user_id: str, mood: str, intensity: int = 5, 
                   context: str = None, tags: List[str] = None) -> None:
        # Track user's mood (1-10 scale).
        self._ensure_user_structure(user_id)
        
        mood_entry = {
            "mood": mood.lower(),
            "intensity": max(1, min(10, intensity)),  # Clamp to 1-10
            "context": context,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat()
        }
        
        mood_file = self._get_user_dir(user_id) / "agent_data" / "mood_tracking.json"
        mood_history = self._load_json(mood_file) or []
        mood_history.append(mood_entry)
        
        self._save_json(mood_file, mood_history)
        logger.info(f"Tracked mood for {user_id}: {mood} ({intensity}/10)")
    
    def get_mood_history(self, user_id: str, days_back: int = 7) -> List[Dict]:
        # Get user's mood history for the last N days.
        self._ensure_user_structure(user_id)
        
        mood_file = self._get_user_dir(user_id) / "agent_data" / "mood_tracking.json"
        mood_history = self._load_json(mood_file) or []
        
        if days_back > 0:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            mood_history = [
                m for m in mood_history 
                if datetime.fromisoformat(m["timestamp"]) >= cutoff_date
            ]
        
        return sorted(mood_history, key=lambda m: m["timestamp"], reverse=True)
    
    # === UTILITY METHODS ===
    
    def get_user_stats(self, user_id: str) -> Dict:
        # Get statistics about a user's data.
        self._ensure_user_structure(user_id)
        
        user_dir = self._get_user_dir(user_id)
        
        # Count preferences
        prefs = self.get_preferences(user_id)
        total_prefs = sum(len(category_prefs.get("likes", [])) + 
                         len(category_prefs.get("dislikes", [])) + 
                         len(category_prefs.get("loves", [])) + 
                         len(category_prefs.get("hates", []))
                         for category_prefs in prefs.values())
        
        # Count memories
        memories = self.get_memories(user_id)
        
        # Count reminders
        reminders = self.get_reminders(user_id)
        
        # Count conversation summaries
        summaries_dir = user_dir / "conversations" / "summaries"
        summary_count = len(list(summaries_dir.glob("*_summary.json")))
        
        return {
            "user_id": user_id,
            "total_preferences": total_prefs,
            "total_memories": len(memories),
            "active_reminders": len(reminders),
            "conversation_summaries": summary_count,
            "data_directory": str(user_dir)
        }
    
    def find_relevant_memories(self, user_id: str, query: str, max_results: int = 5) -> List[MemoryEntry]:
        # Simple keyword-based memory search (no vectors needed!).
        memories = self.get_memories(user_id)
        query_words = set(query.lower().split())
        
        # Score memories based on keyword overlap
        scored_memories = []
        for memory in memories:
            content_words = set(memory.content.lower().split())
            tag_words = set(' '.join(memory.tags).lower().split())
            
            # Calculate overlap score
            content_overlap = len(query_words.intersection(content_words))
            tag_overlap = len(query_words.intersection(tag_words)) * 2  # Tags are more important
            
            total_score = content_overlap + tag_overlap + memory.importance
            
            if total_score > 0:
                scored_memories.append((total_score, memory))
        
        # Sort by score and return top results
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for score, memory in scored_memories[:max_results]]

    def get_context_for_conversation(self, user_id: str, current_topic: str = None) -> Dict[str, Any]:
        # Get relevant context for current conversation including recent memories, preferences, and conversation patterns.
        self._ensure_user_structure(user_id)
        
        context = {
            "recent_memories": [],
            "relevant_preferences": {},
            "conversation_patterns": {},
            "active_reminders": [],
            "suggested_topics": []
        }
        
        # Get recent important memories
        context["recent_memories"] = self.get_memories(
            user_id, 
            min_importance=0.6, 
            days_back=7
        )[:3]
        
        # Get relevant preferences if topic is provided
        if current_topic:
            all_prefs = self.get_preferences(user_id)
            for category, prefs in all_prefs.items():
                if current_topic.lower() in category.lower():
                    context["relevant_preferences"][category] = prefs
        
        # Get active reminders
        context["active_reminders"] = self.get_reminders(user_id)[:3]
        
        # Analyze conversation patterns
        context["conversation_patterns"] = self._analyze_conversation_patterns(user_id)
        
        return context
    
    def _analyze_conversation_patterns(self, user_id: str) -> Dict[str, Any]:
        # Analyze user's conversation patterns and habits.
        summaries = self.get_recent_summaries(user_id, days_back=14)
        
        if not summaries:
            return {"frequent_topics": [], "conversation_frequency": "unknown"}
        
        # Extract frequent topics
        all_topics = []
        for summary in summaries:
            all_topics.extend(summary.get("main_topics", []))
        
        # Count topic frequency
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        frequent_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Determine conversation frequency
        days_with_conversations = len(summaries)
        if days_with_conversations >= 10:
            frequency = "daily"
        elif days_with_conversations >= 5:
            frequency = "regular"
        else:
            frequency = "occasional"
        
        return {
            "frequent_topics": [topic for topic, count in frequent_topics],
            "conversation_frequency": frequency,
            "total_conversations": days_with_conversations
        }
    
    def cleanup_old_data(self, user_id: str, days_to_keep: int = 90) -> Dict[str, int]:
        # Clean up old conversation data while preserving important memories.
        # Returns count of items cleaned up.
        self._ensure_user_structure(user_id)
        cleanup_stats = {"summaries_removed": 0, "raw_chats_removed": 0}
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Clean old summaries (but keep important ones)
        summaries_dir = self._get_user_dir(user_id) / "conversations" / "summaries"
        for summary_file in summaries_dir.glob("*_summary.json"):
            try:
                # Extract date from filename
                date_str = summary_file.stem.split('_')[0]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    summary_file.unlink()
                    cleanup_stats["summaries_removed"] += 1
            except (ValueError, IndexError):
                continue  # Skip files with unexpected naming
        
        # Clean old raw chats
        raw_chats_dir = self._get_user_dir(user_id) / "conversations" / "raw_chats"
        for chat_file in raw_chats_dir.glob("*_chat.json"):
            try:
                date_str = chat_file.stem.split('_')[0]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    chat_file.unlink()
                    cleanup_stats["raw_chats_removed"] += 1
            except (ValueError, IndexError):
                continue
        
        logger.info(f"Cleaned up old data for {user_id}: {cleanup_stats}")
        return cleanup_stats

# Example usage and testing
if __name__ == "__main__":
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Test with a sample user
    test_user = "test_user_123"
    
    # Add some sample memories
    memory_manager.add_memory(
        test_user, 
        "User mentioned they have a dentist appointment next week",
        "appointment",
        importance=0.8,
        tags=["dentist", "appointment", "health"]
    )
    
    # Add a reminder
    from datetime import datetime, timedelta
    memory_manager.add_reminder(
        test_user,
        "Ask about dentist appointment",
        due_date=datetime.now() + timedelta(days=7),
        priority="high"
    )
    
    # Test memory search
    relevant_memories = memory_manager.find_relevant_memories(test_user, "dentist health")
    print(f"Found {len(relevant_memories)} relevant memories")
    
    # Get user stats
    stats = memory_manager.get_user_stats(test_user)
    print(f"User stats: {stats}")
