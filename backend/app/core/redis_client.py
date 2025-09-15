# backend/app/core/redis_client.py
import os
import json
from typing import Optional, Any

import redis

from app.core.config import settings
from app.core.observability import get_logger

logger = get_logger(__name__)

class RedisClient:
    def __init__(self, url: str = None):
        self.url = url or settings.REDIS_URL
        self.client = redis.from_url(self.url, decode_responses=True)
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.client.ping()
            logger.info("Redis connection established")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set_nx(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set key only if it doesn't exist (atomic)"""
        try:
            result = self.client.set(
                key,
                json.dumps(value) if not isinstance(value, str) else value,
                nx=True,
                ex=ttl
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET NX failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e}")
            return False
    
    def acquire_lock(self, key: str, timeout: int = 10) -> bool:
        """Acquire a distributed lock"""
        lock_key = f"lock:{key}"
        return self.set_nx(lock_key, "1", ttl=timeout)
    
    def release_lock(self, key: str) -> bool:
        """Release a distributed lock"""
        lock_key = f"lock:{key}"
        return self.delete(lock_key)

# Global Redis client instance
class _InMemoryRedis:
    """Simple in-memory Redis-like client for tests.

    Provides minimal set of methods used by the application code.
    """

    def __init__(self):
        self._store = {}

    def set_nx(self, key: str, value: Any, ttl: int = None) -> bool:
        if key in self._store:
            return False
        self._store[key] = json.dumps(value) if not isinstance(value, str) else value
        # TTL is ignored in this minimal implementation
        return True

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    # Compatibility helpers
    def acquire_lock(self, key: str, timeout: int = 10) -> bool:
        return self.set_nx(f"lock:{key}", "1", ttl=timeout)

    def release_lock(self, key: str) -> bool:
        return self.delete(f"lock:{key}")


if os.environ.get("DISABLE_REDIS") == "1":
    logger.info("Redis disabled via DISABLE_REDIS=1; using in-memory stub")
    redis_client = _InMemoryRedis()
else:
    # Attempt to create a real client; fallback to in-memory if connection fails
    try:
        redis_client = RedisClient()
    except Exception:
        logger.warning("Redis connection failed; falling back to in-memory stub for this process")
        redis_client = _InMemoryRedis()
