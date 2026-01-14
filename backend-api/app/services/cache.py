import redis.asyncio as redis
from typing import Optional, Any
import json
from app.core.config import settings

class RedisCache:
    """Redis cache service"""
    
    _client: Optional[redis.Redis] = None
    
    @classmethod
    async def initialize(cls):
        """Initialize Redis connection"""
        cls._client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._client:
            await cls._client.close()
    
    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not cls._client:
            return None
        
        value = await cls._client.get(key)
        if value:
            return json.loads(value)
        return None
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = settings.REDIS_CACHE_TTL):
        """Set value in cache"""
        if not cls._client:
            return
        
        await cls._client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl
        )
    
    @classmethod
    async def delete(cls, key: str):
        """Delete key from cache"""
        if not cls._client:
            return
        
        await cls._client.delete(key)
    
    @classmethod
    async def publish(cls, channel: str, message: Any):
        """Publish message to channel"""
        if not cls._client:
            return
        
        await cls._client.publish(
            channel,
            json.dumps(message, default=str)
        )
