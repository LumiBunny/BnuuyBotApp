import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .models import Note

logger = logging.getLogger(__name__)

class NoteManager:
    """Manages note storage and retrieval for a single user."""
    
    def __init__(self, user_data_dir: Path):
        """
        Initialize NoteManager for a user.
        
        Args:
            user_data_dir: Path to the user's data directory
        """
        self.notes_file = user_data_dir / "agent_data" / "notes.json"
        self.notes_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_notes_file()
    
    def _ensure_notes_file(self) -> None:
        """Ensure the notes file exists with an empty list if it doesn't exist."""
        if not self.notes_file.exists():
            self.notes_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_notes([])
    
    def _load_notes(self) -> List[Dict]:
        """Load all notes from the JSON file."""
        try:
            if not self.notes_file.exists():
                return []
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading notes from {self.notes_file}: {e}")
            return []
    
    def _save_notes(self, notes_data: List[Dict]) -> None:
        """Save notes to the JSON file."""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Error saving notes to {self.notes_file}: {e}")
            raise
    
    def create_note(self, title: str, content: str, category: str = "general", 
                   tags: Optional[List[str]] = None, context: Optional[Dict] = None) -> Note:
        """Create a new note."""
        note = Note(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            category=category.lower(),
            tags=[t.lower() for t in (tags or [])],
            context=context
        )
        
        notes = self._load_notes()
        notes.append(note.to_dict())
        self._save_notes(notes)
        
        logger.info(f"Created note: {note.id} - {note.title}")
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """Retrieve a note by ID."""
        notes = [Note.from_dict(n) for n in self._load_notes()]
        return next((n for n in notes if n.id == note_id), None)
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes, sorted by most recently updated."""
        notes = [Note.from_dict(n) for n in self._load_notes()]
        return sorted(notes, key=lambda x: x.updated_at, reverse=True)
    
    def update_note(self, note_id: str, **updates) -> Optional[Note]:
        """Update an existing note."""
        notes_data = self._load_notes()
        
        for i, note_data in enumerate(notes_data):
            if note_data.get('id') == note_id:
                # Update fields
                for key, value in updates.items():
                    if key in note_data and key not in ['id', 'created_at']:
                        note_data[key] = value
                
                # Always update the updated_at timestamp
                note_data['updated_at'] = datetime.now().isoformat()
                
                # Save the changes
                self._save_notes(notes_data)
                
                logger.info(f"Updated note: {note_id}")
                return Note.from_dict(note_data)
        
        return None
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID. Returns True if deleted, False if not found."""
        notes_data = self._load_notes()
        initial_count = len(notes_data)
        
        # Filter out the note to delete
        notes_data = [n for n in notes_data if n.get('id') != note_id]
        
        if len(notes_data) < initial_count:
            self._save_notes(notes_data)
            logger.info(f"Deleted note: {note_id}")
            return True
        return False
    
    def search_notes(self, query: str = "", category: Optional[str] = None, 
                    tags: Optional[List[str]] = None, limit: int = 10) -> List[Note]:
        """Search notes with flexible filtering."""
        notes = self.get_all_notes()
        
        # Filter by category if specified
        if category:
            category = category.lower()
            notes = [n for n in notes if n.category.lower() == category]
        
        # Filter by tags if specified
        if tags:
            tags = {t.lower() for t in tags}
            notes = [n for n in notes if tags.intersection(t.lower() for t in n.tags)]
        
        # Full-text search if query provided
        if query:
            query = query.lower()
            def score_note(note: Note) -> int:
                score = 0
                score += note.title.lower().count(query) * 5
                score += note.content.lower().count(query) * 1
                score += sum(tag.lower().count(query) * 3 for tag in note.tags)
                return score
            
            # Score and sort notes by relevance
            scored_notes = [(note, score_note(note)) for note in notes]
            scored_notes.sort(key=lambda x: x[1], reverse=True)
            notes = [note for note, score in scored_notes if score > 0][:limit]
        
        return notes[:limit]
    
    def get_categories(self) -> Dict[str, int]:
        """Get all categories with note counts."""
        notes = self.get_all_notes()
        categories = {}
        for note in notes:
            categories[note.category] = categories.get(note.category, 0) + 1
        return categories
    
    def get_tags(self) -> Dict[str, int]:
        """Get all tags with note counts."""
        notes = self.get_all_notes()
        tags = {}
        for note in notes:
            for tag in note.tags:
                tags[tag] = tags.get(tag, 0) + 1
        return tags