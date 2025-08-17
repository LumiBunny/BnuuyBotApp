from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import json
import logging
import re
from uuid import uuid4

from ..memory_manager import MemoryManager
from .models import Note

logger = logging.getLogger(__name__)

class NoteManager:
    """
    Manages notes using the application's MemoryManager for storage.
    """
    
    def __init__(self, memory_manager: MemoryManager, nlp_processor=None):
        """
        Initialize the NoteManager with a MemoryManager instance.
        
        Args:
            memory_manager: Instance of MemoryManager for storage
            nlp_processor: Optional NLP processor for text analysis
        """
        self.memory_manager = memory_manager
        self.nlp = nlp_processor
        self._ensure_default_categories()
    
    def _ensure_default_categories(self):
        """Ensure default note categories exist in the memory manager."""
        # This is a no-op since MemoryManager handles its own categories
        pass
    
    def create_note_from_message(self, message: str, user_id: str, 
                               category: str = "general", 
                               tags: List[str] = None,
                               context: Dict = None) -> Note:
        """
        Create a note from a user message.
        
        Args:
            message: The note content
            user_id: ID of the user creating the note
            category: Note category
            tags: List of tags for the note
            context: Additional context for the note
            
        Returns:
            The created Note object
        """
        # Clean and process the message
        message = message.strip()
        if not message:
            raise ValueError("Cannot create an empty note")
        
        # Extract title from first sentence or first 50 chars
        title = (message[:50] + '...') if len(message) > 50 else message
        title = title.split('.')[0]  # First sentence as title
        
        # Create the note using MemoryManager
        self.memory_manager.add_note(
            user_id=user_id,
            note_text=message,
            category=category,
            tags=tags or []
        )
        
        # Return a Note object for the rest of the system to use
        return Note(
            id=str(uuid4()),
            title=title,
            content=message,
            category=category,
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def create_note(self, user_id: str, title: str, content: str, 
                   category: str = "general", tags: List[str] = None) -> Note:
        """
        Create a note with explicit title and content.
        
        Args:
            user_id: ID of the user creating the note
            title: Note title
            content: Note content
            category: Note category
            tags: List of tags for the note
            
        Returns:
            The created Note object
            
        Raises:
            ValueError: If content is empty
        """
        if not content.strip():
            raise ValueError("Cannot create an empty note")
        
        # Create the note using MemoryManager
        self.memory_manager.add_note(
            user_id=user_id,
            note_text=content,
            title=title,
            category=category,
            tags=tags or []
        )
        
        # Create and return a Note object
        return Note(
            id=str(uuid4()),
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def get_notes(self, user_id: str, 
                 category: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 limit: int = 10,
                 offset: int = 0) -> List[Note]:
        """
        Get notes for a user with optional filtering.
        
        Args:
            user_id: ID of the user
            category: Optional category filter
            tags: Optional list of tags to filter by
            limit: Maximum number of notes to return
            offset: Offset for pagination
            
        Returns:
            List of Note objects
        """
        # Get notes from MemoryManager
        notes_data = self.memory_manager.get_notes(user_id, category=category)
        
        # Convert to Note objects
        notes = []
        for i, note_data in enumerate(notes_data[offset:offset+limit], 1):
            try:
                note = Note(
                    id=note_data.get('id', str(uuid4())),  # Use stored ID or generate new one
                    title=note_data.get('title', note_data.get('text', '')[:50]),
                    content=note_data.get('text', ''),
                    category=note_data.get('category', 'general'),
                    tags=note_data.get('tags', []),
                    created_at=datetime.fromisoformat(note_data.get('created_at', datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(note_data.get('updated_at', datetime.now().isoformat()))
                )
                
                # Apply tag filtering if specified
                if tags and not any(tag in note.tags for tag in tags):
                    continue
                    
                notes.append(note)
            except Exception as e:
                logger.error(f"Error parsing note {i}: {e}")
                continue
                
        return notes
    
    def search_notes(self, user_id: str, query: str, limit: int = 5, threshold: float = 0.3) -> List[Tuple[Note, float]]:
        """
        Enhanced note search with semantic similarity using spaCy.
        
        Args:
            user_id: ID of the user
            query: Search query
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0-1) for a match
            
        Returns:
            List of tuples containing (Note, similarity_score) sorted by score
        """
        if not self.nlp:
            return self._basic_search(user_id, query, limit)
            
        # Get all notes
        all_notes = self.get_notes(user_id)
        if not all_notes:
            return []
            
        # Process query
        query_doc = self.nlp(query.lower())
        
        # Calculate similarity for each note
        results = []
        for note in all_notes:
            # Combine note fields for comparison
            note_text = f"{note.title} {note.content} {' '.join(note.tags)}"
            note_doc = self.nlp(note_text.lower())
            
            # Calculate similarity score
            similarity = query_doc.similarity(note_doc)
            
            if similarity >= threshold:
                results.append((note, similarity))
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def _basic_search(self, user_id: str, query: str, limit: int) -> List[Tuple[Note, float]]:
        """Fallback search without spaCy"""
        query_terms = [term.lower().strip() for term in query.split() if term.strip()]
        if not query_terms:
            return []
            
        all_notes = self.get_notes(user_id)
        matches = []
        
        for note in all_notes:
            note_text = f"{note.title} {note.content} {' '.join(note.tags)}".lower()
            match_count = sum(1 for term in query_terms if term in note_text)
            
            if match_count > 0:
                # Simple score based on term frequency
                score = match_count / len(query_terms)
                matches.append((note, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def edit_note(self, user_id: str, note_id: str, 
                 title: str = None, content: str = None, 
                 category: str = None, tags: List[str] = None) -> Note:
        """
        Edit an existing note.
        
        Args:
            user_id: ID of the user who owns the note
            note_id: ID of the note to edit
            title: New title (optional)
            content: New content (optional)
            category: New category (optional)
            tags: New tags (optional)
           
        Returns:
            The updated Note object
            
        Raises:
            ValueError: If note doesn't exist or user doesn't have permission
        """
        # Get existing note
        notes = self.get_notes(user_id)
        note = next((n for n in notes if n.id == note_id), None)
        
        if not note:
            raise ValueError("Note not found or access denied")
        
        # Update fields if provided
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if category is not None:
            note.category = category
        if tags is not None:
            note.tags = tags
        
        note.updated_at = datetime.now()
        
        # Save the updated note using add_note (which handles both create and update)
        self.memory_manager.add_note(
            user_id=user_id,
            note_id=note_id,
            note_text=note.content,
            category=note.category,
            tags=note.tags
        )
        
        return note
    
    def delete_note(self, user_id: str, note_id: str, confirmation_required: bool = True) -> Dict[str, Any]:
        """
        Delete a note by its ID.
        
        Args:
            user_id: ID of the user who owns the note
            note_id: ID of the note to delete
            confirmation_required: If True, will return a confirmation request
                                 instead of deleting immediately
            
        Returns:
            Dict containing:
            - status: 'success', 'confirmation_required', or 'error'
            - message: Human-readable status message
            - confirmation_prompt: If status is 'confirmation_required',
                                contains the prompt to show user
        """
        # Get the note to confirm it exists and show details in confirmation
        notes = self.get_notes(user_id)
        note = next((n for n in notes if n.id == note_id), None)
        
        if not note:
            return {
                'status': 'error',
                'message': f"Note {note_id} not found"
            }
            
        if confirmation_required:
            return {
                'status': 'confirmation_required',
                'message': 'Note deletion requires confirmation',
                'confirmation_prompt': (
                    f"Are you sure you want to delete the note '{note.title}'?\n"
                    f"Preview: {note.content[:100]}{'...' if len(note.content) > 100 else ''}\n\n"
                    "Type 'CONFIRM DELETE' to proceed, or 'cancel' to abort."
                )
            }
        
        # If we get here, confirmation is not required or has been given
        success = self.memory_manager.delete_note(user_id, note_id)
        
        if success:
            return {
                'status': 'success',
                'message': f"Successfully deleted note: {note.title}"
            }
        else:
            return {
                'status': 'error',
                'message': f"Failed to delete note: {note.title}"
            }
    
    def bulk_delete_notes(self, user_id: str, category: str = None, 
                        confirmation_required: bool = True) -> Dict[str, Any]:
        """
        Delete multiple notes, optionally filtered by category, with confirmation.
        
        Args:
            user_id: ID of the user who owns the notes
            category: If provided, only delete notes in this category
            confirmation_required: If True, will return a confirmation request
                                 instead of deleting immediately
                                 
        Returns:
            Dict containing:
            - status: 'success', 'confirmation_required', 'cancelled', or 'error'
            - message: Human-readable status message
            - confirmation_prompt: If status is 'confirmation_required',
                                contains the prompt to show user
            - stats: Dictionary with deletion statistics
        """
        # Get notes that would be deleted
        notes = self.memory_manager.get_notes(user_id)
        if category:
            notes = [n for n in notes if n.get('category') == category]
        
        if not notes:
            return {
                'status': 'error',
                'message': f"No notes found{f' in category: {category}' if category else ''}",
                'stats': {
                    'total': 0,
                    'deleted': 0,
                    'skipped': 0
                }
            }
            
        # Prepare stats and previews
        stats = {
            'total': len(notes),
            'sample_size': min(3, len(notes)),
            'categories': {},
            'sample_notes': []
        }
        
        # Count by category and collect sample notes
        for note in notes:
            cat = note.get('category', 'uncategorized')
            stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
            
            if len(stats['sample_notes']) < 3:
                stats['sample_notes'].append({
                    'id': note.get('id'),
                    'title': note.get('title', 'Untitled'),
                    'preview': note.get('text', '')[:50] + ('...' if len(note.get('text', '')) > 50 else '')
                })
        
        if confirmation_required:
            # Build confirmation message
            category_msg = f" in category: {category}" if category else ""
            confirmation_msg = [
                f"You are about to delete {stats['total']} notes{category_msg}.",
                f"Categories affected: {', '.join(f'{k} ({v})' for k, v in stats['categories'].items())}",
                "",
                "Sample of notes to be deleted:"
            ]
            
            for i, note in enumerate(stats['sample_notes'], 1):
                confirmation_msg.append(f"{i}. {note['title']} - {note['preview']}")
                
            if stats['total'] > 3:
                confirmation_msg.append(f"...and {stats['total'] - 3} more")
                
            confirmation_msg.extend([
                "",
                "This action cannot be undone!",
                "Type 'CONFIRM BULK DELETE' to proceed, or 'cancel' to abort."
            ])
            
            return {
                'status': 'confirmation_required',
                'message': 'Bulk deletion requires confirmation',
                'confirmation_prompt': '\n'.join(confirmation_msg),
                'stats': stats
            }
            
        # If we get here, confirmation is not required or has been given
        deleted_count = 0
        for note in notes:
            if self.memory_manager.delete_note(user_id, note['id']):
                deleted_count += 1
        
        return {
            'status': 'success',
            'message': f"Successfully deleted {deleted_count} of {len(notes)} notes",
            'stats': {
                'total': len(notes),
                'deleted': deleted_count,
                'skipped': len(notes) - deleted_count
            }
        }
    
    def detect_note_intent(self, message: str) -> Optional[Dict]:
        """
        Enhanced note detection supporting both 'note' and 'memo' keywords,
        plus STT-friendly tag detection.
        """
        lower_msg = message.lower()
        
        # Enhanced note-taking phrases including 'memo'
        note_phrases = [
            "add a note", "make a note", "create a note", "save a note",
            "add a memo", "make a memo", "create a memo", "save a memo",
            "remember that", "remember this", "save this", "jot down", 
            "write down", "take a note", "note to self", "memo to self",
            "i need to remember", "don't let me forget"
        ]
        
        # Check for explicit note-taking intent
        explicit_intent = any(phrase in lower_msg for phrase in note_phrases)
        
        # Check for implicit note-taking (contextual clues)
        implicit_patterns = [
            r"i need to (research|study|learn|remember|check|look up)",
            r"remind me to",
            r"(todo|to do|task).*:",
            r"important.*remember"
        ]
        implicit_intent = any(re.search(pattern, lower_msg) for pattern in implicit_patterns)
        
        if explicit_intent or implicit_intent:
            # Extract content
            content = self._extract_note_content(message, note_phrases)
            
            # Extract tags (both hashtags and spoken tags)
            tags = self._extract_tags(message)
            
            # Determine category using spaCy if available
            category = self._determine_category(content) if self.nlp else None
            
            # Check if content is clear enough
            is_clear = self._is_content_clear(content)
            
            return {
                "intent": "create_note",
                "content": content,
                "category": category,
                "tags": tags,
                "is_clear": is_clear,
                "needs_followup": not is_clear
            }
        
        return None
    
    def _extract_note_content(self, message: str, note_phrases: List[str]) -> str:
        """Extract the actual note content from the message."""
        lower_msg = message.lower()
        content = message
        
        # Find the trigger phrase and extract content after it
        for phrase in note_phrases:
            if phrase in lower_msg:
                start_idx = lower_msg.index(phrase) + len(phrase)
                content = message[start_idx:].strip()
                # Remove common connecting words
                content = re.sub(r'^(to|that|about|:)\s*', '', content, flags=re.IGNORECASE)
                break
        
        return content
    
    def _extract_tags(self, message: str) -> List[str]:
        """Extract tags from both hashtags and spoken tag patterns."""
        tags = []
        
        # Extract hashtags (#tag)
        hashtags = re.findall(r'#(\w+)', message)
        tags.extend(hashtags)
        
        # Extract spoken tags patterns
        spoken_patterns = [
            r'tags?\s+([^.!?]+)',  # "tag python and learning"
            r'tagged?\s+as\s+([^.!?]+)',  # "tagged as python and learning"
            r'categories?\s+([^.!?]+)',  # "category work"
        ]
        
        for pattern in spoken_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                # Split on common separators
                tag_words = re.split(r'[,\s]+and\s+|[,\s]+', match.strip())
                tags.extend([tag.strip() for tag in tag_words if tag.strip()])
        
        return list(set(tags))  # Remove duplicates
    
    def _determine_category(self, content: str) -> Optional[str]:
        """Use spaCy to determine note category from content."""
        if not self.nlp:
            return None
            
        doc = self.nlp(content.lower())
        
        # Category keywords mapping
        category_keywords = {
            "work": ["meeting", "project", "deadline", "task", "client", "colleague"],
            "learning": ["research", "study", "learn", "tutorial", "course", "book"],
            "personal": ["buy", "grocery", "appointment", "call", "family", "friend"],
            "health": ["doctor", "exercise", "medication", "workout", "diet"],
            "finance": ["budget", "payment", "bill", "investment", "money"],
            "travel": ["flight", "hotel", "vacation", "trip", "booking"]
        }
        
        # Score categories based on keyword matches
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for token in doc if token.lemma_ in keywords)
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def _is_content_clear(self, content: str) -> bool:
        """Determine if note content is clear enough or needs follow-up."""
        if len(content.strip()) < 10:
            return False
        
        # Check for vague words that might need clarification
        vague_indicators = [
            "about", "regarding", "concerning", "that thing", "the meeting",
            "the project", "it", "this", "that"
        ]
        
        content_lower = content.lower()
        vague_count = sum(1 for indicator in vague_indicators if indicator in content_lower)
        
        # If more than 30% of content is vague indicators, needs follow-up
        word_count = len(content.split())
        return vague_count / max(word_count, 1) < 0.3
    
    def _clean_content(self, message: str) -> str:
        """Clean message content by removing hashtags and tag indicators."""
        # Remove hashtags
        content = re.sub(r'#\w+', '', message)
        
        # Remove spoken tag patterns
        content = re.sub(r'tags?\s+[^.!?]+', '', content, flags=re.IGNORECASE)
        content = re.sub(r'tagged?\s+as\s+[^.!?]+', '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _generate_title(self, content: str) -> str:
        """Generate an intelligent title from content."""
        # Use first sentence or first 50 characters
        title = (content[:50] + '...') if len(content) > 50 else content
        title = title.split('.')[0]  # First sentence as title
        
        return title
    
    def generate_followup_question(self, vague_content: str) -> str:
        """Generate a follow-up question for unclear note content."""
        if "meeting" in vague_content.lower():
            return "What would you like me to note about the meeting?"
        elif "project" in vague_content.lower():
            return "What specific details about the project should I save?"
        elif len(vague_content.strip()) < 10:
            return "Could you provide more details for the note?"
        else:
            return f"What additional details would you like me to include about '{vague_content}'?"
    
    def _get_thinking_context(self, operation: str, note_data: Dict = None, 
                            user_id: str = None, additional_context: Dict = None) -> Dict:
        """
        Generate thinking context for LLM to maintain awareness during note operations.
        
        Args:
            operation: The operation being performed (create, edit, delete, etc.)
            note_data: The note data being operated on
            user_id: ID of the user performing the operation
            additional_context: Any additional context to include
            
        Returns:
            Dict containing thinking context for the LLM
        """
        context = {
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'thinking': []
        }
        
        if user_id:
            context['user_id'] = user_id
            
        if note_data:
            context['note'] = {
                'id': note_data.get('id'),
                'title': note_data.get('title', 'Untitled'),
                'category': note_data.get('category', 'general'),
                'tags': note_data.get('tags', []),
                'preview': note_data.get('text', '')[:100] + ('...' if len(note_data.get('text', '')) > 100 else '')
            }
            
            # Add operation-specific thinking
            if operation == 'create':
                context['thinking'].extend([
                    f"Creating a new note titled: {context['note']['title']}",
                    f"Category: {context['note']['category']}",
                    f"Tags: {', '.join(context['note']['tags']) if context['note']['tags'] else 'None'}",
                    "Considering how this note relates to user's existing knowledge..."
                ])
            elif operation == 'edit':
                context['thinking'].extend([
                    f"Editing note: {context['note']['title']}",
                    "Analyzing changes and their implications...",
                    "Checking for related notes that might need updating..."
                ])
            elif operation == 'delete':
                context['thinking'].extend([
                    f"Preparing to delete note: {context['note']['title']}",
                    "Assessing impact and related content...",
                    "Verifying this is the intended action..."
                ])
                
        if additional_context:
            context.update(additional_context)
            
        # Add a final thinking step
        context['thinking'].append("Ensuring user intent is properly understood and executed...")
        
        return context