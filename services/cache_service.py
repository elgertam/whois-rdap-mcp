"""
Caching service for storing Whois and RDAP lookup results.
Implements in-memory LRU cache with TTL support.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple
import structlog

from config import Config

logger = structlog.get_logger(__name__)


class CacheEntry:
    """Cache entry with data and expiration time."""
    
    def __init__(self, data: Any, ttl: int):
        self.data = data
        self.expires_at = time.time() + ttl
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """Access cache entry and update statistics."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data


class CacheService:
    """Asynchronous LRU cache service with TTL support."""
    
    def __init__(self, config: Config):
        self.config = config
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        
        # Start background cleanup task
        if config.cache_cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                logger.debug("Cache miss", key=key)
                return None
            
            if entry.is_expired():
                logger.debug("Cache entry expired", key=key)
                await self._remove_entry(key)
                return None
            
            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            logger.debug("Cache hit", key=key, 
                        access_count=entry.access_count)
            
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        if ttl is None:
            ttl = self.config.cache_ttl
        
        async with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                await self._remove_entry(key)
            
            # Check if cache is full
            if len(self._cache) >= self.config.cache_max_size:
                await self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(value, ttl)
            self._cache[key] = entry
            self._access_order.append(key)
            
            logger.debug("Cache set", key=key, ttl=ttl,
                        cache_size=len(self._cache))
    
    async def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        async with self._lock:
            if key in self._cache:
                await self._remove_entry(key)
                logger.debug("Cache delete", key=key)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logger.info("Cache cleared")
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() 
                                if entry.is_expired())
            total_accesses = sum(entry.access_count 
                               for entry in self._cache.values())
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'valid_entries': total_entries - expired_entries,
                'total_accesses': total_accesses,
                'cache_hit_ratio': 0.0 if total_accesses == 0 else 
                                 (total_accesses / max(1, total_entries)),
                'max_size': self.config.cache_max_size
            }
    
    async def _remove_entry(self, key: str) -> None:
        """Remove entry from cache and access order."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        # Find the least recently used entry that's not recently accessed
        lru_key = self._access_order[0]
        await self._remove_entry(lru_key)
        
        logger.debug("Cache LRU eviction", evicted_key=lru_key)
    
    async def _cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            await self._remove_entry(key)
        
        if expired_keys:
            logger.debug("Cache cleanup completed", 
                        expired_count=len(expired_keys))
        
        return len(expired_keys)
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired entries."""
        try:
            while True:
                await asyncio.sleep(self.config.cache_cleanup_interval)
                
                async with self._lock:
                    await self._cleanup_expired()
                    
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
        except Exception as e:
            logger.error("Cache cleanup task error", error=str(e))
    
    async def close(self) -> None:
        """Close cache service and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.clear()
        logger.info("Cache service closed")
