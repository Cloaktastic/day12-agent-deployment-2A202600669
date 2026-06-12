import redis
import logging
from datetime import datetime
from fastapi import HTTPException, Depends
from app.config import settings
from app.auth import verify_api_key

logger = logging.getLogger(__name__)
r = redis.from_url(settings.redis_url, decode_responses=True)

# Price reference for GPT-4o-mini
PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

def check_budget(user_id: str = Depends(verify_api_key)) -> None:
    """
    FastAPI dependency: Check if the user has exceeded their monthly budget.
    Raises 402 if exceeded.
    """
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id[:8]}:{month_key}"
    
    try:
        current_spending = float(r.get(key) or 0.0)
    except Exception as e:
        logger.error(f"Redis cost guard check failed: {e}. Failing open.")
        current_spending = 0.0

    if current_spending >= settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget of ${settings.monthly_budget_usd} exceeded. Used: ${current_spending:.6f}"
        )

def record_cost(user_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate and record the cost of the LLM call in Redis.
    """
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id[:8]}:{month_key}"
    
    input_cost = (input_tokens / 1000.0) * PRICE_PER_1K_INPUT_TOKENS
    output_cost = (output_tokens / 1000.0) * PRICE_PER_1K_OUTPUT_TOKENS
    cost = input_cost + output_cost
    
    try:
        r.incrbyfloat(key, cost)
        r.expire(key, 32 * 24 * 3600)  # 32 days
    except Exception as e:
        logger.error(f"Redis cost guard recording failed: {e}")
        
    return cost
