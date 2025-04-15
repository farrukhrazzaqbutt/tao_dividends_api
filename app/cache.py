import redis
import json
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)


class RedisCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None

    async def set(self, key: str, value: Any, expire: int = 120) -> bool:
        """Set value in cache with expiration in seconds."""
        try:
            self.redis_client.setex(
                key,
                timedelta(seconds=expire),
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False


# Create a global cache instance
cache = RedisCache()


async def get_cached_dividends(cache_key: str) -> Optional[List[Dict]]:
    """Get dividends from cache."""
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Error getting cached dividends: {str(e)}")
        return None


async def cache_dividends(cache_key: str, dividends: List[Dict], expire_seconds: int = 300) -> bool:
    """Cache dividends data."""
    try:
        redis_client.setex(
            cache_key,
            expire_seconds,
            json.dumps(dividends)
        )
        return True
    except Exception as e:
        logger.error(f"Error caching dividends: {str(e)}")
        return False


async def get_cached_sentiment(netuid: int, hotkey: str) -> Optional[float]:
    """Get sentiment score from cache."""
    try:
        cache_key = f"sentiment:{netuid}:{hotkey}"
        cached_score = redis_client.get(cache_key)
        return float(cached_score) if cached_score else None
    except Exception as e:
        logger.error(f"Error getting cached sentiment: {str(e)}")
        return None


async def cache_sentiment(netuid: int, hotkey: str, score: float, expire_seconds: int = 3600) -> bool:
    """Cache sentiment score."""
    try:
        cache_key = f"sentiment:{netuid}:{hotkey}"
        redis_client.setex(cache_key, expire_seconds, str(score))
        return True
    except Exception as e:
        logger.error(f"Error caching sentiment: {str(e)}")
        return False 