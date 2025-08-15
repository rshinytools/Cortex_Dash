# ABOUTME: Redis cache implementation for widget data and query results
# ABOUTME: Provides caching layer with TTL management and invalidation strategies

import json
import hashlib
import pickle
from typing import Any, Optional, Union, List, Dict
from datetime import datetime, timedelta
import redis
from redis import Redis
from redis.exceptions import RedisError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis cache for the application"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client: Optional[Redis] = None
        self.connect()
    
    def connect(self):
        """Establish connection to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if hasattr(settings, 'REDIS_PASSWORD') else None,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except (RedisError, Exception) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _generate_key(self, namespace: str, identifier: str) -> str:
        """Generate a cache key with namespace"""
        return f"{settings.CACHE_PREFIX}:{namespace}:{identifier}"
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            # Try JSON first (more portable)
            return json.dumps(data).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        if not data:
            return None
        
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            try:
                return pickle.loads(data)
            except:
                return None
    
    def get(self, namespace: str, identifier: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected():
            return None
        
        try:
            key = self._generate_key(namespace, identifier)
            data = self.redis_client.get(key)
            
            if data:
                # Update access time in statistics
                self._update_stats(namespace, 'hits')
                return self._deserialize(data)
            else:
                self._update_stats(namespace, 'misses')
                return None
                
        except RedisError as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self, 
        namespace: str, 
        identifier: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self.is_connected():
            return False
        
        try:
            key = self._generate_key(namespace, identifier)
            serialized = self._serialize(value)
            
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            
            self._update_stats(namespace, 'sets')
            return True
            
        except RedisError as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, identifier: str) -> bool:
        """Delete value from cache"""
        if not self.is_connected():
            return False
        
        try:
            key = self._generate_key(namespace, identifier)
            result = self.redis_client.delete(key)
            self._update_stats(namespace, 'deletes')
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.is_connected():
            return 0
        
        try:
            full_pattern = f"{settings.CACHE_PREFIX}:{pattern}"
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except RedisError as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all cache entries in a namespace"""
        pattern = f"{namespace}:*"
        return self.delete_pattern(pattern)
    
    def invalidate_study(self, study_id: str) -> int:
        """Invalidate all cache entries for a study"""
        count = 0
        namespaces = ['widget', 'query', 'dataset', 'mapping']
        
        for ns in namespaces:
            pattern = f"{ns}:*{study_id}*"
            count += self.delete_pattern(pattern)
        
        return count
    
    def invalidate_widget(self, widget_id: str) -> int:
        """Invalidate all cache entries for a widget"""
        pattern = f"widget:*{widget_id}*"
        return self.delete_pattern(pattern)
    
    def get_ttl(self, namespace: str, identifier: str) -> Optional[int]:
        """Get remaining TTL for a key"""
        if not self.is_connected():
            return None
        
        try:
            key = self._generate_key(namespace, identifier)
            ttl = self.redis_client.ttl(key)
            return ttl if ttl > 0 else None
            
        except RedisError as e:
            logger.error(f"Cache TTL error: {e}")
            return None
    
    def extend_ttl(self, namespace: str, identifier: str, ttl: int) -> bool:
        """Extend TTL for an existing key"""
        if not self.is_connected():
            return False
        
        try:
            key = self._generate_key(namespace, identifier)
            return bool(self.redis_client.expire(key, ttl))
            
        except RedisError as e:
            logger.error(f"Cache extend TTL error: {e}")
            return False
    
    def _update_stats(self, namespace: str, operation: str):
        """Update cache statistics"""
        if not self.is_connected():
            return
        
        try:
            stats_key = f"{settings.CACHE_PREFIX}:stats:{namespace}:{operation}"
            self.redis_client.hincrby(stats_key, str(datetime.utcnow().date()), 1)
            
            # Set TTL for stats (keep for 30 days)
            self.redis_client.expire(stats_key, 30 * 24 * 3600)
            
        except RedisError:
            pass  # Don't fail on stats update
    
    def get_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_connected():
            return {}
        
        try:
            pattern = f"{settings.CACHE_PREFIX}:stats:"
            if namespace:
                pattern += f"{namespace}:"
            pattern += "*"
            
            stats = {}
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                key_str = key.decode('utf-8')
                parts = key_str.split(':')
                
                if len(parts) >= 4:
                    ns = parts[-2]
                    op = parts[-1]
                    
                    if ns not in stats:
                        stats[ns] = {}
                    
                    # Get all date entries for this stat
                    data = self.redis_client.hgetall(key)
                    total = sum(int(v) for v in data.values())
                    
                    stats[ns][op] = total
            
            # Calculate hit rate
            for ns in stats:
                if 'hits' in stats[ns] and 'misses' in stats[ns]:
                    total_requests = stats[ns]['hits'] + stats[ns]['misses']
                    if total_requests > 0:
                        stats[ns]['hit_rate'] = round(
                            stats[ns]['hits'] / total_requests * 100, 2
                        )
            
            return stats
            
        except RedisError as e:
            logger.error(f"Cache stats error: {e}")
            return {}


class WidgetCache:
    """Specialized cache for widget data"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.namespace = "widget"
    
    def get_widget_data(
        self, 
        widget_id: str, 
        study_id: str,
        config_hash: str
    ) -> Optional[Dict]:
        """Get cached widget data"""
        identifier = f"{study_id}:{widget_id}:{config_hash}"
        return self.cache.get(self.namespace, identifier)
    
    def set_widget_data(
        self, 
        widget_id: str, 
        study_id: str,
        config_hash: str,
        data: Dict,
        ttl: int = 3600
    ) -> bool:
        """Cache widget data"""
        identifier = f"{study_id}:{widget_id}:{config_hash}"
        return self.cache.set(self.namespace, identifier, data, ttl)
    
    def invalidate_widget(self, widget_id: str) -> int:
        """Invalidate all cache for a widget"""
        return self.cache.invalidate_widget(widget_id)
    
    def get_config_hash(self, config: Dict) -> str:
        """Generate hash for widget configuration"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()


class QueryCache:
    """Specialized cache for query results"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.namespace = "query"
    
    def get_query_result(
        self, 
        query_hash: str, 
        study_id: str
    ) -> Optional[List[Dict]]:
        """Get cached query result"""
        identifier = f"{study_id}:{query_hash}"
        return self.cache.get(self.namespace, identifier)
    
    def set_query_result(
        self, 
        query_hash: str, 
        study_id: str,
        result: List[Dict],
        ttl: int = 1800
    ) -> bool:
        """Cache query result"""
        identifier = f"{study_id}:{query_hash}"
        return self.cache.set(self.namespace, identifier, result, ttl)
    
    def get_query_hash(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate hash for query"""
        query_data = {
            'query': query,
            'params': params or {}
        }
        query_str = json.dumps(query_data, sort_keys=True)
        return hashlib.sha256(query_str.encode()).hexdigest()[:16]


# Global cache instance
cache_manager = CacheManager()
widget_cache = WidgetCache(cache_manager)
query_cache = QueryCache(cache_manager)