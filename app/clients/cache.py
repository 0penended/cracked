import time
import asyncio
from typing import Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with data and timestamp."""

    data: T
    timestamp: float
    ttl: float


class TokenDataCache:
    """In-memory cache for token data with TTL support."""

    def __init__(self, default_ttl: float = 900):  # 15 minutes default
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get data from cache if it exists and is not expired."""
        async with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if time.time() - entry.timestamp > entry.ttl:
                # Entry expired, remove it
                del self._cache[key]
                logger.debug(f"Cache entry expired for key: {key}")
                return None

            logger.debug(f"Cache hit for key: {key}")
            return entry.data

    def get_sync(self, key: str) -> Optional[Any]:
        """Synchronous version of get for use with sync clients."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() - entry.timestamp > entry.ttl:
            # Entry expired, remove it
            del self._cache[key]
            logger.debug(f"Cache entry expired for key: {key}")
            return None

        logger.debug(f"Cache hit for key: {key}")
        return entry.data

    async def set(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """Set data in cache with optional TTL override."""
        async with self._lock:
            cache_ttl = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(
                data=data, timestamp=time.time(), ttl=cache_ttl
            )
            logger.debug(f"Cache set for key: {key} with TTL: {cache_ttl}s")

    def set_sync(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """Synchronous version of set for use with sync clients."""
        cache_ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = CacheEntry(data=data, timestamp=time.time(), ttl=cache_ttl)
        logger.debug(f"Cache set for key: {key} with TTL: {cache_ttl}s")

    async def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache invalidated for key: {key}")

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    async def cleanup_expired(self) -> None:
        """Remove all expired entries from cache."""
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if current_time - entry.timestamp > entry.ttl
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        total_entries = len(self._cache)
        expired_entries = sum(
            1
            for entry in self._cache.values()
            if current_time - entry.timestamp > entry.ttl
        )

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "default_ttl": self._default_ttl,
            "cache_keys": list(self._cache.keys()),
        }


# Global cache instance
token_cache = TokenDataCache()
