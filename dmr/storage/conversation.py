"""
Conversation storage system for D-Model-Runner.

This module provides conversation data models and management functionality
for saving, loading, and managing conversation history.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field

from ..utils.helpers import safe_get_nested
from .index_cache import ConversationIndexCache
from ..utils.performance import measure_performance, track_cache_performance

try:
    from openai.types.chat import ChatCompletionMessageParam
    OPENAI_TYPES_AVAILABLE = True
except ImportError:
    OPENAI_TYPES_AVAILABLE = False
    ChatCompletionMessageParam = Dict[str, str]  # Fallback type


@dataclass
class Message:
    """Individual message in a conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        data = data.copy()
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ConversationMetadata:
    """Metadata for a conversation."""
    title: str
    model: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    model_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMetadata':
        """Create metadata from dictionary."""
        data = data.copy()
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class Conversation:
    """Represents a conversation with messages and metadata."""
    
    def __init__(self, id: Optional[str] = None, metadata: Optional[ConversationMetadata] = None):
        self.id = id or str(uuid.uuid4())
        self.metadata = metadata or ConversationMetadata(title="New Conversation", model="ai/gemma3")
        self.messages: List[Message] = []
        self._auto_save = False
        self._storage_path: Optional[Path] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a message to the conversation."""
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        self.metadata.updated_at = datetime.now()
        
        if self._auto_save and self._storage_path:
            self.save(self._storage_path)
        
        return message
    
    def get_messages(self, role: Optional[str] = None) -> List[Message]:
        """Get messages, optionally filtered by role."""
        if role:
            return [msg for msg in self.messages if msg.role == role]
        return self.messages.copy()
    
    def get_openai_messages(self) -> List[Dict[str, Any]]:
        """Get messages in OpenAI API format."""
        messages = []
        for msg in self.messages:
            if msg.role in ['user', 'assistant', 'system']:
                message_dict = {"role": msg.role, "content": msg.content}
                messages.append(message_dict)
        return messages
    
    def update_metadata(self, **kwargs) -> None:
        """Update conversation metadata."""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.metadata.updated_at = datetime.now()
        
        if self._auto_save and self._storage_path:
            self.save(self._storage_path)
    
    def set_auto_save(self, enabled: bool, storage_path: Optional[Path] = None) -> None:
        """Enable or disable auto-save functionality."""
        self._auto_save = enabled
        if storage_path:
            self._storage_path = storage_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            'id': self.id,
            'metadata': self.metadata.to_dict(),
            'messages': [msg.to_dict() for msg in self.messages],
            'version': '1.0'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary."""
        conversation = cls(
            id=data['id'],
            metadata=ConversationMetadata.from_dict(data['metadata'])
        )
        conversation.messages = [Message.from_dict(msg) for msg in data.get('messages', [])]
        return conversation
    
    def save(self, file_path: Path) -> None:
        """Save conversation to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        self._storage_path = file_path
    
    @classmethod
    def load(cls, file_path: Path) -> 'Conversation':
        """Load conversation from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        conversation = cls.from_dict(data)
        conversation._storage_path = file_path
        return conversation


class ConversationManager:
    """Manages multiple conversations and provides storage operations."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.cwd() / "dmr" / "storage" / "data" / "conversations"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._conversations: Dict[str, Conversation] = {}
        self._current_conversation: Optional[Conversation] = None
        
        # Initialize conversation index cache for optimized operations
        self._index_cache = ConversationIndexCache(self.storage_dir)
    
    def create_conversation(self, title: str, model: str, **metadata_kwargs) -> Conversation:
        """Create a new conversation."""
        metadata = ConversationMetadata(title=title, model=model, **metadata_kwargs)
        conversation = Conversation(metadata=metadata)
        self._conversations[conversation.id] = conversation
        self._current_conversation = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        if conversation_id in self._conversations:
            return self._conversations[conversation_id]
        
        # Try to load from disk
        file_path = self.storage_dir / f"{conversation_id}.json"
        if file_path.exists():
            conversation = Conversation.load(file_path)
            self._conversations[conversation.id] = conversation
            return conversation
        
        return None
    
    @measure_performance("conversation_save", include_args=True)
    def save_conversation(self, conversation: Conversation) -> Path:
        """Save a conversation to disk."""
        file_path = self.storage_dir / f"{conversation.id}.json"
        conversation.save(file_path)
        
        # Update index cache with new metadata
        metadata = {
            'id': conversation.id,
            'title': conversation.metadata.title,
            'model': conversation.metadata.model,
            'created_at': conversation.metadata.created_at.isoformat(),
            'updated_at': conversation.metadata.updated_at.isoformat(),
            'tags': conversation.metadata.tags,
            'description': conversation.metadata.description,
            'message_count': len(conversation.messages)
        }
        self._index_cache.update_conversation_metadata(conversation.id, metadata)
        
        return file_path
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from disk."""
        file_path = self.storage_dir / f"{conversation_id}.json"
        if not file_path.exists():
            return None
        
        conversation = Conversation.load(file_path)
        self._conversations[conversation.id] = conversation
        return conversation
    
    @track_cache_performance("conversation_list")
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all available conversations with metadata using optimized index cache."""
        return self._index_cache.get_all_metadata()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        file_path = self.storage_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
        
        if self._current_conversation and self._current_conversation.id == conversation_id:
            self._current_conversation = None
        
        # Remove from index cache
        self._index_cache.remove_conversation(conversation_id)
        
        return True
    
    def set_current_conversation(self, conversation: Conversation) -> None:
        """Set the current active conversation."""
        self._current_conversation = conversation
        self._conversations[conversation.id] = conversation
    
    def get_current_conversation(self) -> Optional[Conversation]:
        """Get the current active conversation."""
        return self._current_conversation
    
    @measure_performance("conversation_search", include_args=True)
    def search_conversations(self, query: str, search_content: bool = False) -> List[Dict[str, Any]]:
        """Search conversations using optimized index cache."""
        return self._index_cache.search_metadata(query, search_content)
    
    def enable_auto_save(self, conversation: Conversation) -> None:
        """Enable auto-save for a conversation."""
        file_path = self.storage_dir / f"{conversation.id}.json"
        conversation.set_auto_save(True, file_path)
    
    def invalidate_cache(self) -> None:
        """Force a rebuild of the conversation index cache."""
        self._index_cache.invalidate_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the conversation cache."""
        return self._index_cache.get_cache_stats()