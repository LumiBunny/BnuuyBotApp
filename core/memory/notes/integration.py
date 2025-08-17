"""
Notes Integration Handler for BunnyChat

This module handles the integration between the notes system and the main chat system,
using the thinking module for natural conversational flow instead of pre-scripted responses.
"""

import logging
from typing import Dict, Optional, List, Any
from .manager import NoteManager
import uuid
import spacy

logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

class NotesIntegrationHandler:
    """
    Handles integration of notes functionality with the chat system.
    Manages note-taking intents, follow-ups, and note-related commands.
    """
    
    def __init__(self, note_manager: NoteManager, thinking_module=None):
        """
        Initialize the NotesIntegrationHandler.
        
        Args:
            note_manager: Instance of NoteManager for note operations
            thinking_module: Optional thinking module for inner dialogue
        """
        self.note_manager = note_manager
        self.thinking_module = thinking_module
        self.pending_notes = {}  # user_id -> pending note data
        self.pending_searches = {}  # search_id -> search data
        self.pending_edits = {}  # edit_id -> edit data
        self.pending_deletions = {}  # delete_id -> deletion data
        self.pending_bulk_actions = {}  # bulk_action_id -> bulk action data
    
    def process_message_for_notes(self, user_message: str, user_id: str, 
                                conversation_context: List[Dict] = None,
                                user_context: Dict = None) -> Dict:
        """
        Process a user message for note-taking intents and actions.
        
        Args:
            user_message: The user's message text
            user_id: ID of the user
            conversation_context: Current conversation context
            user_context: Additional user context
            
        Returns:
            Dict containing note-related context and actions
        """
        # Check if this is a response to a previous note action
        if user_id in self.pending_notes:
            pending = self.pending_notes[user_id]
            if pending.get('action') == 'no_matches' and user_message.lower() in ['no', 'n', 'no thanks']:
                del self.pending_notes[user_id]
                return {
                    'action': 'note_creation_declined',
                    'query': pending.get('query', ''),
                    'note_context': {
                        'action': 'note_creation_declined',
                        'query': pending.get('query', '')
                    }
                }
            return self._handle_note_followup(user_id, user_message, conversation_context)

        # Check for explicit note-taking intent
        note_intent = self.note_manager.detect_note_intent(user_message)
        if note_intent:
            return self._handle_explicit_note_intent(note_intent, user_message, user_id, user_context)
        
        # Check if we're in a note-taking flow
        if user_id in self.pending_notes:
            return self._handle_note_followup(user_id, user_message, conversation_context)
        
        # Check for note-related commands (search, list, etc.)
        note_command = self._detect_note_commands(user_message)
        if note_command:
            if note_command['command'] == 'search':
                result = self.handle_note_search(user_id, note_command['query'])
                # Store the search query in case user declines to create a note
                if result.get('action') == 'no_matches':
                    self.pending_notes[user_id] = {
                        'action': 'no_matches',
                        'query': result.get('query', '')
                    }
                return result
            elif note_command['command'] == 'list':
                return self._handle_note_command(note_command, user_id, user_message)
        
        # Check for implicit note-taking opportunities
        if self._is_implicit_note_opportunity(user_message, conversation_context):
            return self._handle_implicit_note_opportunity(user_message, user_id, user_context)
        
        # No note-related actions
        return {}
    
    def _handle_explicit_note_intent(self, intent: Dict, message: str, 
                                   user_id: str, user_context: Dict) -> Dict:
        """Handle explicit note-taking intents."""
        # Extract note content (remove command words)
        content = message.lower()
        for trigger in ['note', 'memo', 'remind me', 'remember that']:
            if trigger in content:
                content = content.split(trigger, 1)[-1].strip()
        
        # If content is too vague, ask for clarification
        if not self.note_manager._is_content_clear(content):
            question = self.note_manager.generate_followup_question(content)
            self.pending_notes[user_id] = {
                'partial_content': content,
                'state': 'awaiting_clarification',
                'attempts': 1
            }
            return {
                'action': 'note_followup',
                'question': question,
                'note_context': {
                    'action': 'note_followup',
                    'question': question
                }
            }
        
        # Create the note
        note = self.note_manager.create_note_from_message(
            message=content,
            user_id=user_id
        )
        
        return {
            'action': 'note_created',
            'note': note,
            'note_context': {
                'action': 'note_created',
                'note': note
            }
        }
    
    def _handle_note_followup(self, user_id: str, message: str, 
                             conversation_context: List[Dict]) -> Dict:
        """Handle follow-up responses in note-taking flows."""
        pending = self.pending_notes[user_id]
        
        if pending['state'] == 'awaiting_clarification':
            # Combine the original content with the clarification
            combined_content = f"{pending['partial_content']} {message}".strip()
            
            # If still too vague after multiple attempts, give up
            if (not self.note_manager._is_content_clear(combined_content) and 
                pending.get('attempts', 0) >= 2):
                del self.pending_notes[user_id]
                return {
                    'action': 'note_cancelled',
                    'reason': 'too_vague',
                    'note_context': {
                        'action': 'note_cancelled',
                        'reason': 'too_vague'
                    }
                }
            
            # If still vague, ask another question
            if not self.note_manager._is_content_clear(combined_content):
                question = self.note_manager.generate_followup_question(combined_content)
                pending['partial_content'] = combined_content
                pending['attempts'] = pending.get('attempts', 0) + 1
                
                return {
                    'action': 'note_followup',
                    'question': question,
                    'note_context': {
                        'action': 'note_followup',
                        'question': question
                    }
                }
            
            # We have enough information, create the note
            del self.pending_notes[user_id]
            note = self.note_manager.create_note_from_message(
                message=combined_content,
                user_id=user_id
            )
            
            return {
                'action': 'note_created',
                'note': note,
                'note_context': {
                    'action': 'note_created',
                    'note': note
                }
            }
        
        # Unknown follow-up state
        del self.pending_notes[user_id]
        return {}
    
    def _detect_note_commands(self, message: str) -> Optional[Dict]:
        """Detect note-related commands in a message."""
        message_lower = message.lower()
        
        if any(cmd in message_lower for cmd in ['search my notes', 'find in my notes']):
            query = message_lower.split('notes', 1)[-1].strip()
            return {'command': 'search', 'query': query}
            
        elif any(cmd in message_lower for cmd in ['list my notes', 'show my notes']):
            return {'command': 'list'}
            
        return None
    
    def _handle_note_command(self, command: Dict, user_id: str, 
                            original_message: str) -> Dict:
        """Handle note-related commands."""
        if command['command'] == 'list':
            notes = self.note_manager.get_notes(user_id=user_id, limit=5)
            
            return {
                'action': 'note_list',
                'notes': notes,
                'note_context': {
                    'action': 'note_list',
                    'notes': notes
                }
            }
            
        return {}
    
    def _is_implicit_note_opportunity(self, message: str, 
                                     conversation_context: List[Dict]) -> bool:
        """Detect if a message contains an implicit note-taking opportunity."""
        # Check for phrases that might indicate something to remember
        note_indicators = [
            'don\'t forget', 'make sure to', 'remember to', 
            'i need to', 'we should', 'let\'s not forget',
            'remind me to', 'i should', 'i must', 'i have to'
        ]
        
        message_lower = message.lower()
        if any(indicator in message_lower for indicator in note_indicators):
            return True
            
        # Check for future-oriented statements
        future_indicators = ['tomorrow', 'later', 'next week', 'when i get home']
        if any(indicator in message_lower for indicator in future_indicators):
            return True
            
        return False
    
    def _handle_implicit_note_opportunity(self, message: str, user_id: str,
                                         user_context: Dict) -> Dict:
        """Handle implicit note-taking opportunities."""
        # Use inner dialogue to determine if this should be a note
        if self.thinking_module:
            thought = self.thinking_module.think_about_notes(message, user_context)
            if thought.get('should_create_note', False):
                note = self.note_manager.create_note_from_message(
                    message=message,
                    user_id=user_id,
                    category=thought.get('category', 'general'),
                    tags=thought.get('tags', [])
                )
                
                return {
                    'action': 'proactive_note_created',
                    'note': note,
                    'note_context': {
                        'action': 'proactive_note_created',
                        'note': note,
                        'reason': thought.get('reason', 'implicit_opportunity')
                    }
                }
        
        # Default: just return an opportunity without creating a note
        return {
            'action': 'proactive_opportunity',
            'note_context': {
                'action': 'proactive_opportunity',
                'message': message
            }
        }
    
    def handle_note_search(self, user_id: str, query: str, threshold: float = 0.5) -> Dict:
        """
        Handle note search with interactive confirmation flow.
        
        Args:
            user_id: ID of the user
            query: Search query
            threshold: Minimum similarity score (0-1) for a match
            
        Returns:
            Dict with search results and next action
        """
        # Perform semantic search
        search_results = self.note_manager.search_notes(
            user_id=user_id,
            query=query,
            limit=5,
            threshold=threshold  # Use the provided threshold
        )
        
        if not search_results:
            # No matches found - consider creating a new note
            return {
                'action': 'no_matches',
                'query': query,
                'suggest_create': True,
                'note_context': {
                    'action': 'no_matches',
                    'query': query,
                    'suggest_create': True,
                    'thinking': 'No matching notes found. Would you like me to create a new one?'
                }
            }
        
        # Store the search for follow-up actions
        search_id = str(uuid.uuid4())
        self.pending_searches[search_id] = {
            'results': search_results,
            'query': query,
            'current_index': 0
        }
        
        # Get the first result
        note, score = search_results[0]
        
        return {
            'action': 'confirm_note',
            'search_id': search_id,
            'note': note,
            'score': score,
            'remaining': len(search_results) - 1,
            'note_context': {
                'action': 'confirm_note',
                'search_id': search_id,
                'note': note,
                'score': score,
                'remaining': len(search_results) - 1,
                'thinking': f'Found a note with {score*100:.1f}% match. Is this what you\'re looking for?'
            }
        }
    
    def handle_search_confirmation(self, user_id: str, search_id: str, is_confirmed: bool) -> Dict:
        """
        Handle user confirmation of a search result.
        
        Args:
            user_id: ID of the user
            search_id: ID of the search session
            is_confirmed: Whether the user confirmed the note is what they wanted
            
        Returns:
            Dict with next action or final result
        """
        if search_id not in self.pending_searches:
            return {
                'action': 'error',
                'message': 'Search session expired or invalid',
                'note_context': {
                    'action': 'error',
                    'message': 'Search session expired or invalid'
                }
            }
            
        search_data = self.pending_searches[search_id]
        results = search_data['results']
        current_index = search_data['current_index']
        
        if is_confirmed:
            # User confirmed this is the note they wanted
            note = results[current_index][0]
            del self.pending_searches[search_id]
            
            return {
                'action': 'note_found',
                'note': note,
                'note_context': {
                    'action': 'note_found',
                    'note': note,
                    'thinking': 'Found the note you were looking for!'
                }
            }
        else:
            # Try the next result
            next_index = current_index + 1
            if next_index < len(results):
                search_data['current_index'] = next_index
                note, score = results[next_index]
                
                return {
                    'action': 'confirm_note',
                    'search_id': search_id,
                    'note': note,
                    'score': score,
                    'remaining': len(results) - next_index - 1,
                    'note_context': {
                        'action': 'confirm_note',
                        'search_id': search_id,
                        'note': note,
                        'score': score,
                        'remaining': len(results) - next_index - 1,
                        'thinking': f'How about this one? ({score*100:.1f}% match)'
                    }
                }
            else:
                # No more results
                query = search_data['query']
                del self.pending_searches[search_id]
                
                return {
                    'action': 'no_matches',
                    'query': query,
                    'suggest_create': True,
                    'note_context': {
                        'action': 'no_matches',
                        'query': query,
                        'suggest_create': True,
                        'thinking': 'No more matching notes found. Would you like me to create a new one?'
                    }
                }

    def handle_edit_note(self, user_id: str, note_id: str, updates: Dict[str, Any]) -> Dict:
        """
        Handle editing a note with confirmation.
        
        Args:
            user_id: ID of the user
            note_id: ID of the note to edit
            updates: Dictionary of fields to update
        
        Returns:
            Dict with result of the operation
        """
        try:
            # Get the note first to verify ownership
            notes = self.note_manager.get_notes(user_id)
            note = next((n for n in notes if n.id == note_id), None)
            
            if not note:
                return {
                    'action': 'error',
                    'message': 'Note not found or access denied',
                    'note_context': {
                        'thinking': 'Failed to find the requested note to edit.'
                    }
                }
            
            # Store the edit for confirmation
            edit_id = str(uuid.uuid4())
            self.pending_edits[edit_id] = {
                'user_id': user_id,
                'note_id': note_id,
                'updates': updates,
                'original_note': note
            }
            
            # Generate a summary of changes
            changes = []
            for field, new_value in updates.items():
                old_value = getattr(note, field, '')
                changes.append(f"{field}: '{old_value}' → '{new_value}'")
            
            return {
                'action': 'confirm_edit',
                'edit_id': edit_id,
                'changes': '\n'.join(changes),
                'note_context': {
                    'action': 'confirm_edit',
                    'edit_id': edit_id,
                    'changes': changes,
                    'thinking': f'Confirm these changes to note "{note.title}":\n' + '\n'.join(changes)
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling edit: {str(e)}")
            return {
                'action': 'error',
                'message': str(e),
                'note_context': {
                    'thinking': f'Error processing edit: {str(e)}'
                }
            }

    def confirm_edit(self, edit_id: str, confirm: bool = False) -> Dict:
        """
        Confirm or cancel a pending edit.
        
        Args:
            edit_id: ID of the edit to confirm/cancel
            confirm: Whether to apply the edit
        
        Returns:
            Dict with result of the operation
        """
        if edit_id not in self.pending_edits:
            return {
                'action': 'error',
                'message': 'Edit session expired or invalid',
                'note_context': {
                    'thinking': 'Edit session expired. Please try again.'
                }
            }
        
        edit = self.pending_edits.pop(edit_id)
        
        if not confirm:
            return {
                'action': 'edit_cancelled',
                'note_context': {
                    'thinking': 'Edit was cancelled by user.'
                }
            }
        
        try:
            # Apply the edit
            updated_note = self.note_manager.edit_note(
                user_id=edit['user_id'],
                note_id=edit['note_id'],
                **edit['updates']
            )
            
            return {
                'action': 'edit_confirmed',
                'note': updated_note,
                'note_context': {
                    'thinking': f'Successfully updated note "{updated_note.title}"',
                    'note': updated_note
                }
            }
            
        except Exception as e:
            logger.error(f"Error confirming edit: {str(e)}")
            return {
                'action': 'error',
                'message': str(e),
                'note_context': {
                    'thinking': f'Error applying edit: {str(e)}'
                }
            }

    def handle_delete_request(self, user_id: str, note_id: str) -> Dict:
        """
        Handle a request to delete a note.
        
        Args:
            user_id: ID of the user
            note_id: ID of the note to delete
        
        Returns:
            Dict with confirmation request
        """
        try:
            # Verify the note exists and belongs to the user
            notes = self.note_manager.get_notes(user_id)
            note = next((n for n in notes if n.id == note_id), None)
            
            if not note:
                return {
                    'action': 'error',
                    'message': 'Note not found or access denied',
                    'note_context': {
                        'thinking': 'Could not find the specified note to delete.'
                    }
                }
            
            # Create a deletion request
            delete_id = str(uuid.uuid4())
            self.pending_deletions[delete_id] = {
                'user_id': user_id,
                'note_id': note_id,
                'note_title': note.title
            }
            
            return {
                'action': 'confirm_delete',
                'delete_id': delete_id,
                'note_title': note.title,
                'note_context': {
                    'action': 'confirm_delete',
                    'delete_id': delete_id,
                    'note_title': note.title,
                    'thinking': f'Are you sure you want to delete the note "{note.title}"? This cannot be undone.'
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing delete request: {str(e)}")
            return {
                'action': 'error',
                'message': str(e),
                'note_context': {
                    'thinking': f'Error processing delete request: {str(e)}'
                }
            }

    def confirm_deletion(self, delete_id: str, confirm: bool = False) -> Dict:
        """
        Confirm or cancel a pending deletion.
        
        Args:
            delete_id: ID of the deletion to confirm/cancel
            confirm: Whether to proceed with deletion
        
        Returns:
            Dict with result of the operation
        """
        if delete_id not in self.pending_deletions:
            return {
                'action': 'error',
                'message': 'Deletion session expired or invalid',
                'note_context': {
                    'thinking': 'Deletion session expired. Please try again.'
                }
            }
        
        deletion = self.pending_deletions.pop(delete_id)
        
        if not confirm:
            return {
                'action': 'deletion_cancelled',
                'note_context': {
                    'thinking': 'Deletion was cancelled.'
                }
            }
        
        try:
            # Delete the note
            success = self.note_manager.delete_note(
                user_id=deletion['user_id'],
                note_id=deletion['note_id']
            )
            
            if not success:
                raise Exception("Failed to delete note")
            
            return {
                'action': 'deletion_confirmed',
                'note_title': deletion['note_title'],
                'note_context': {
                    'thinking': f'Successfully deleted note "{deletion["note_title"]}"'
                }
            }
            
        except Exception as e:
            logger.error(f"Error confirming deletion: {str(e)}")
            return {
                'action': 'error',
                'message': str(e),
                'note_context': {
                    'thinking': f'Error deleting note: {str(e)}'
                }
            }

    def handle_bulk_action(self, user_id: str, action: str, **kwargs) -> Dict:
        """
        Handle bulk actions like delete all notes or delete by category.
        
        Args:
            user_id: ID of the user
            action: Action to perform (e.g., 'delete_all', 'delete_by_category')
            **kwargs: Additional parameters for the action
        
        Returns:
            Dict with result or confirmation request
        """
        try:
            if action == 'delete_all':
                notes = self.note_manager.get_notes(user_id)
                if not notes:
                    return {
                        'action': 'no_notes',
                        'note_context': {
                            'thinking': 'No notes found to delete.'
                        }
                    }
                
                # Create a bulk deletion request
                delete_id = str(uuid.uuid4())
                self.pending_bulk_actions[delete_id] = {
                    'user_id': user_id,
                    'action': 'delete_all',
                    'count': len(notes)
                }
                
                return {
                    'action': 'confirm_bulk_delete',
                    'delete_id': delete_id,
                    'count': len(notes),
                    'note_context': {
                        'action': 'confirm_bulk_delete',
                        'delete_id': delete_id,
                        'count': len(notes),
                        'thinking': f'Are you sure you want to delete all {len(notes)} notes? This cannot be undone.'
                    }
                }
                
            elif action == 'delete_by_category':
                category = kwargs.get('category')
                if not category:
                    raise ValueError("Category is required for delete_by_category")
                
                notes = [n for n in self.note_manager.get_notes(user_id) 
                        if n.category == category]
                
                if not notes:
                    return {
                        'action': 'no_notes',
                        'category': category,
                        'note_context': {
                            'thinking': f'No notes found in category "{category}" to delete.'
                        }
                    }
                
                # Create a bulk deletion request
                delete_id = str(uuid.uuid4())
                self.pending_bulk_actions[delete_id] = {
                    'user_id': user_id,
                    'action': 'delete_by_category',
                    'category': category,
                    'count': len(notes)
                }
                
                return {
                    'action': 'confirm_bulk_delete',
                    'delete_id': delete_id,
                    'category': category,
                    'count': len(notes),
                    'note_context': {
                        'action': 'confirm_bulk_delete',
                        'delete_id': delete_id,
                        'category': category,
                        'count': len(notes),
                        'thinking': f'Are you sure you want to delete {len(notes)} notes in category "{category}"? This cannot be undone.'
                    }
                }
                
            else:
                raise ValueError(f"Unknown bulk action: {action}")
                
        except Exception as e:
            logger.error(f"Error processing bulk action: {str(e)}")
            return {
                'action': 'error',
                'message': str(e),
                'note_context': {
                    'thinking': f'Error processing bulk action: {str(e)}'
                }
            }

    def confirm_bulk_action(self, bulk_action_id: str, confirm: bool = False) -> Dict:
        """
        Confirm or cancel a pending bulk action.
        
        Args:
            bulk_action_id: ID of the bulk action to confirm/cancel
            confirm: Whether to proceed with the action
        
        Returns:
            Dict with result of the operation
        """
        if bulk_action_id not in self.pending_bulk_actions:
            return {
                'action': 'error',
                'message': 'Bulk action session expired or invalid',
                'note_context': {
                    'thinking': 'Bulk action session expired. Please try again.'
                }
            }
        
        action = self.pending_bulk_actions.pop(bulk_action_id)
        
        if not confirm:
            return {
                'action': 'bulk_action_cancelled',
                'note_context': {
                    'thinking': 'Bulk action was cancelled.'
                }
            }
        
        try:
            if action['action'] == 'delete_all':
                count = self.note_manager.bulk_delete_notes(
                    user_id=action['user_id']
                )
                return {
                    'action': 'bulk_delete_completed',
                    'count': count,
                    'note_context': {
                        'thinking': f'Successfully deleted {count} notes.'
                    }
                }
                
            elif action['action'] == 'delete_by_category':
                count = self.note_manager.bulk_delete_notes(
                    user_id=action['user_id'],
                    category=action['category']
                )
                return {
                    'action': 'bulk_delete_completed',
                    'count': count,
                    'category': action['category'],
                    'note_context': {
                        'thinking': f'Successfully deleted {count} notes in category "{action["category"]}".'
                    }
                }
                
            else:
                raise ValueError(f"Unknown bulk action: {action['action']}")
                
        except Exception as e:
            logger.error(f"Error confirming bulk action: {str(e)}")
            return {
                'action': 'error',
                'message': str(e),
                'note_context': {
                    'thinking': f'Error processing bulk action: {str(e)}'
                }
            }
