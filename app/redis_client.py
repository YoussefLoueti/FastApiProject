import redis.asyncio as redis
import os
import json

# Redis URL from environment variable
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create Redis client
redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

class RedisManager:
    def __init__(self, client):
        self.client = client
    
    async def set_json(self, key: str, value: dict, expire: int = 3600):
        """Set JSON data with expiration"""
        return await self.client.set(key, json.dumps(value), ex=expire)
    
    async def get_json(self, key: str):
        """Get JSON data"""
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete(self, key: str):
        """Delete key"""
        return await self.client.delete(key)
    
    async def exists(self, key: str):
        """Check if key exists"""
        return await self.client.exists(key)

# Create Redis manager instance
redis_manager = RedisManager(redis_client)