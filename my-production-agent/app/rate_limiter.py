import redis
import time
import logging
from fastapi import HTTPException, Depends
from app.config import settings
from app.auth import verify_api_key

logger = logging.getLogger(__name__)
r = redis.from_url(settings.redis_url, decode_responses=True)

def check_rate_limit(user_id: str = Depends(verify_api_key)) -> None:
    """
    Sliding window rate limiter using Redis sorted sets (ZSET).
    """
    now = time.time()
    # Use first 8 characters of user_id (API key) for the rate limit bucket
    key = f"rate_limit:{user_id[:8]}"
    window = 60
    limit = settings.rate_limit_per_minute

    try:
        # Remove timestamps outside the sliding window
        r.zremrangebyscore(key, 0, now - window)
        
        # Count requests in the current window
        request_count = r.zcard(key)
        
        if request_count >= limit:
            oldest = r.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(oldest_time + window - now) + 1
            else:
                retry_after = 60
            
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} req/min. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record request timestamp
        member_id = f"{now}-{time.time_ns()}"
        r.zadd(key, {member_id: now})
        r.expire(key, window + 10)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redis rate limiter error: {e}. Failing open.")
