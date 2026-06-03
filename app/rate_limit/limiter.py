import time
from fastapi import Request, HTTPException
from app.cache.service import get_redis_client

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute

    async def __call__(self, request: Request):
        # In a real production setup (behind Nginx/Load Balancer), 
        # you'd extract the 'X-Forwarded-For' header. 
        # For local dev, we use request.client.host.
        client_ip = request.client.host if request.client else "unknown"
        
        # Use the current minute as part of the Redis key (Fixed Window)
        current_minute = int(time.time() / 60)
        redis_key = f"ratelimit:{client_ip}:{current_minute}"
        
        client = get_redis_client()
        
        # Increment the request count for this IP
        current_count = await client.incr(redis_key)
        
        # If it's the first request in this minute, set the key to expire in 60 seconds
        if current_count == 1:
            await client.expire(redis_key, 60)
            
        if current_count > self.requests_per_minute:
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests. Please slow down."
            )