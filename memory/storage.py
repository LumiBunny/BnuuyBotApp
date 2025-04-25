import numpy as np
from datetime import datetime
import json
import os
from sentence_transformers import SentenceTransformer

class MemoryStorage:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Initialize with a lightweight sentence transformer model
        # This is a small, fast model (80MB) that works well for semantic search
        self.model = SentenceTransformer(model_name)
        self.memories = []
        self.embeddings = []
        self.data_dir = os.path.join(os.path.dirname(__file__), '../data/memories')
        os.makedirs(self.data_dir, exist_ok=True)
        self._load_memories()
    
    def _load_memories(self):
        # Load existing memories from disk
        try:
            memory_file = os.path.join(self.data_dir, 'memories.json')
            if os.path.exists(memory_file):
                with open(memory_file, 'r') as f:
                    self.memories = json.load(f)
                    
                # Generate embeddings for loaded memories
                if self.memories:
                    texts = [m['content'] for m in self.memories]
                    self.embeddings = self.model.encode(texts)
        except Exception as e:
            print(f"Error loading memories: {e}")
            self.memories = []
            self.embeddings = []
    
    def _save_memories(self):
        try:
            memory_file = os.path.join(self.data_dir, 'memories.json')
            with open(memory_file, 'w') as f:
                json.dump(self.memories, f)
        except Exception as e:
            print(f"Error saving memories: {e}")
    
    def store(self, memory):
        # Add timestamp if not present
        if 'timestamp' not in memory:
            memory['timestamp'] = datetime.now().isoformat()
        
        # Add the memory to our list
        self.memories.append(memory)
        
        # Create and store embedding for the memory content
        content = memory.get('content', '')
        embedding = self.model.encode([content])[0]
        self.embeddings.append(embedding)
        
        # Save to disk (could be made more efficient with batch saves)
        self._save_memories()
        
        return memory
    
    def search(self, user_id, query, limit=5):
        if not self.memories or not query:
            return []
        
        # Filter memories by user_id
        user_indices = [i for i, m in enumerate(self.memories) 
                        if m.get('user_id') == user_id]
        
        if not user_indices:
            return []
        
        # Get embeddings for user's memories
        user_embeddings = np.array([self.embeddings[i] for i in user_indices])
        
        # Generate embedding for query
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity
        similarities = np.dot(user_embeddings, query_embedding) / (
            np.linalg.norm(user_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get indices of top matches
        top_indices = np.argsort(-similarities)[:limit]  # Negative for descending order
        
        # Return the matched memories
        return [self.memories[user_indices[i]] for i in top_indices]