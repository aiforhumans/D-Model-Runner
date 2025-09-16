"""
Conversation Index Cache for optimized search and metadata operations.

This module provides in-memory caching of conversation metadata to dramatically
improve search performance and reduce file I/O operations.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class ConversationIndexCache:
    """
    In-memory cache of conversation metadata for fast search operations.
    
    Reduces search time from O(n*file_io) to O(n) by maintaining metadata
    in memory and using file system monitoring for cache invalidation.
    """
    
    def __init__(self, storage_dir: Path):
        """
        Initialize the conversation index cache.
        
        Args:
            storage_dir: Directory containing conversation JSON files
        """
        self.storage_dir = storage_dir
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._file_mtimes: Dict[str, float] = {}
        self._cache_file = storage_dir / '.conversation_index.json'
        self._lock = Lock()
        self._last_scan_time = 0
        
        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache or build new one
        self._load_or_build_cache()
    
    def _load_or_build_cache(self) -> None:
        """Load existing cache file or build new cache by scanning directory."""
        try:
            if self._cache_file.exists():
                logger.debug(f"Loading conversation index cache from {self._cache_file}")
                self._load_cache_file()
            else:
                logger.debug("No cache file found, building new index")
                self._build_cache_from_files()
        except Exception as e:
            logger.warning(f"Failed to load cache, rebuilding: {e}")
            self._build_cache_from_files()
    
    def _load_cache_file(self) -> None:
        """Load cache from the index file."""
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            self._metadata_cache = cache_data.get('metadata', {})
            self._file_mtimes = cache_data.get('mtimes', {})
            self._last_scan_time = cache_data.get('last_scan_time', 0)
            
            # Verify cache is still valid
            if self._is_cache_stale():
                logger.debug("Cache is stale, rebuilding")
                self._build_cache_from_files()
            else:
                logger.debug(f"Loaded {len(self._metadata_cache)} conversations from cache")
                
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Cache file corrupted, rebuilding: {e}")
            self._build_cache_from_files()
    
    def _is_cache_stale(self) -> bool:
        """Check if cache needs to be refreshed by comparing file modification times."""
        for conv_id, cached_mtime in self._file_mtimes.items():
            file_path = self.storage_dir / f"{conv_id}.json"
            if file_path.exists():
                current_mtime = file_path.stat().st_mtime
                if current_mtime > cached_mtime:
                    return True
            else:
                # File was deleted
                return True
        
        # Check for new files
        for file_path in self.storage_dir.glob("*.json"):
            if file_path.name == '.conversation_index.json':
                continue
            conv_id = file_path.stem
            if conv_id not in self._file_mtimes:
                return True
        
        return False
    
    def _build_cache_from_files(self) -> None:
        """Build cache by scanning all conversation files in the directory."""
        logger.debug(f"Scanning directory {self.storage_dir} for conversations")
        
        with self._lock:
            self._metadata_cache.clear()
            self._file_mtimes.clear()
            
            conversation_files = list(self.storage_dir.glob("*.json"))
            
            for file_path in conversation_files:
                # Skip the index cache file itself
                if file_path.name == '.conversation_index.json':
                    continue
                
                try:
                    conv_id = file_path.stem
                    metadata = self._extract_metadata_from_file(file_path)
                    if metadata:
                        self._metadata_cache[conv_id] = metadata
                        self._file_mtimes[conv_id] = file_path.stat().st_mtime
                        
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {e}")
                    continue
            
            self._last_scan_time = time.time()
            logger.debug(f"Built cache with {len(self._metadata_cache)} conversations")
            
            # Save cache to disk
            self._save_cache_file()
    
    def _extract_metadata_from_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a conversation JSON file without loading full content.
        
        Args:
            file_path: Path to the conversation JSON file
            
        Returns:
            Dictionary containing conversation metadata or None if invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract only the metadata we need for search/listing
            metadata = {
                'id': data['id'],
                'title': data['metadata']['title'],
                'model': data['metadata']['model'],
                'created_at': data['metadata']['created_at'],
                'updated_at': data['metadata']['updated_at'],
                'tags': data['metadata'].get('tags', []),
                'description': data['metadata'].get('description', ''),
                'message_count': len(data.get('messages', []))
            }
            
            return metadata
            
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to extract metadata from {file_path}: {e}")
            return None
    
    def _save_cache_file(self) -> None:
        """Save current cache state to disk."""
        try:
            cache_data = {
                'metadata': self._metadata_cache,
                'mtimes': self._file_mtimes,
                'last_scan_time': self._last_scan_time,
                'version': '1.0'
            }
            
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved cache with {len(self._metadata_cache)} conversations")
            
        except Exception as e:
            logger.warning(f"Failed to save cache file: {e}")
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all conversations.
        
        Returns:
            List of conversation metadata dictionaries
        """
        self._refresh_if_needed()
        
        with self._lock:
            # Sort by updated_at, most recent first
            conversations = list(self._metadata_cache.values())
            conversations.sort(key=lambda x: x['updated_at'], reverse=True)
            return conversations
    
    def search_metadata(self, query: str, search_content: bool = False) -> List[Dict[str, Any]]:
        """
        Search conversations by title, tags, or description.
        
        Args:
            query: Search query string
            search_content: If True, search message content (requires file I/O)
            
        Returns:
            List of matching conversation metadata
        """
        self._refresh_if_needed()
        query_lower = query.lower()
        results = []
        
        with self._lock:
            for conv_metadata in self._metadata_cache.values():
                # Search in title, tags, and description
                if (query_lower in conv_metadata['title'].lower() or
                    query_lower in conv_metadata.get('description', '').lower() or
                    any(query_lower in tag.lower() for tag in conv_metadata['tags'])):
                    results.append(conv_metadata.copy())
                    continue
                
                # Search in content if requested (requires loading file)
                if search_content:
                    if self._search_in_conversation_content(conv_metadata['id'], query_lower):
                        results.append(conv_metadata.copy())
        
        # Sort results by relevance (title match first, then updated_at)
        def sort_key(conv):
            title_match = query_lower in conv['title'].lower()
            return (not title_match, -time.mktime(time.strptime(conv['updated_at'], '%Y-%m-%dT%H:%M:%S.%f')))
        
        results.sort(key=sort_key)
        return results
    
    def _search_in_conversation_content(self, conv_id: str, query_lower: str) -> bool:
        """
        Search for query in conversation message content.
        
        Args:
            conv_id: Conversation ID
            query_lower: Lowercase search query
            
        Returns:
            True if query found in message content
        """
        try:
            file_path = self.storage_dir / f"{conv_id}.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for message in data.get('messages', []):
                if query_lower in message.get('content', '').lower():
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to search content in {conv_id}: {e}")
            return False
    
    def update_conversation_metadata(self, conv_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata for a conversation in the cache.
        
        Args:
            conv_id: Conversation ID
            metadata: Updated metadata dictionary
        """
        with self._lock:
            self._metadata_cache[conv_id] = metadata
            
            # Update file modification time
            file_path = self.storage_dir / f"{conv_id}.json"
            if file_path.exists():
                self._file_mtimes[conv_id] = file_path.stat().st_mtime
            
            # Save updated cache
            self._save_cache_file()
        
        logger.debug(f"Updated metadata for conversation {conv_id}")
    
    def remove_conversation(self, conv_id: str) -> None:
        """
        Remove a conversation from the cache.
        
        Args:
            conv_id: Conversation ID to remove
        """
        with self._lock:
            self._metadata_cache.pop(conv_id, None)
            self._file_mtimes.pop(conv_id, None)
            self._save_cache_file()
        
        logger.debug(f"Removed conversation {conv_id} from cache")
    
    def _refresh_if_needed(self) -> None:
        """Check if cache needs refresh and update if necessary."""
        # Only check periodically to avoid excessive file system calls
        current_time = time.time()
        if current_time - self._last_scan_time > 30:  # Check every 30 seconds
            if self._is_cache_stale():
                logger.debug("Cache is stale, refreshing")
                self._build_cache_from_files()
    
    def invalidate_cache(self) -> None:
        """Force a complete cache rebuild."""
        logger.debug("Manually invalidating conversation cache")
        self._build_cache_from_files()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                'conversation_count': len(self._metadata_cache),
                'last_scan_time': self._last_scan_time,
                'cache_file_exists': self._cache_file.exists(),
                'storage_dir': str(self.storage_dir)
            }