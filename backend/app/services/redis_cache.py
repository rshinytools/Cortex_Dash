# ABOUTME: Redis caching service for widget data with TTL support
# ABOUTME: Provides async caching operations for dashboard performance optimization

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis cache service for widget data"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis connection established")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._redis:
            return None
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (in seconds)"""
        if not self._redis:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self._redis.setex(key, ttl, serialized)
            return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._redis:
            return False
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._redis:
            return 0
        
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._redis:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except RedisError as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key (in seconds)"""
        if not self._redis:
            return None
        
        try:
            ttl = await self._redis.ttl(key)
            return ttl if ttl > 0 else None
        except RedisError as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return None
    
    async def invalidate_study_cache(self, study_id: str):
        """Invalidate all cache entries for a study"""
        pattern = f"widget_data:{study_id}:*"
        deleted = await self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache entries for study {study_id}")
    
    async def invalidate_widget_cache(self, study_id: str, widget_id: str):
        """Invalidate all cache entries for a specific widget"""
        pattern = f"widget_data:{study_id}:{widget_id}:*"
        deleted = await self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache entries for widget {widget_id} in study {study_id}")
    
    async def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics"""
        if not self._redis:
            return None
        
        try:
            info = await self._redis.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "total_keys": await self._redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except RedisError as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate as percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Get cache instance (for dependency injection)"""
    if not cache._redis:
        await cache.connect()
    return cache