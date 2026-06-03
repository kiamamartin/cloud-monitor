import json
from typing import Optional, Dict, Any
import redis.asyncio as redis

from app.core.config import settings

# Global connection pool for high-performance reuse
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)

async def cache_monitor_status(monitor_id: str, payload: Dict[str, Any], ttl_seconds: int = 60):
    """Saves the latest monitor status to Redis with a TTL."""
    client = get_redis_client()
    key = f"monitor:status:{monitor_id}"
    
    # We store it as a JSON string
    await client.setex(key, ttl_seconds, json.dumps(payload))

async def get_cached_monitor_status(monitor_id: str) -> Optional[Dict[str, Any]]:
    """Fetches the monitor status from Redis."""
    client = get_redis_client()
    key = f"monitor:status:{monitor_id}"
    
    data = await client.get(key)
    if data:
        return json.loads(data)
    return None