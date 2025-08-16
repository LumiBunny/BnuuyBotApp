from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class Note:
    # Represents a single note with metadata and content.
    id: str
    title: str
    content: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        # Convert note to dictionary for JSON serialization.
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Note':
        # Create Note from dictionary (JSON deserialization).
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)