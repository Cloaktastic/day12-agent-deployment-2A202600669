# Main entry point
import json
import logging
import signal
from datetime import datetime, timezone
import redis
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_budget
from utils.mock_llm import ask as llm_ask

# Logging — JSON structured
logging.basicConfig(
    level=settings.log_level,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# Request/Response structures
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str

app = FastAPI(title=settings.app_name, version=settings.app_version)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        logger.error(json.dumps({"event": "readiness_check_failed", "error": str(e)}))
        raise HTTPException(status_code=503, detail="Redis connection failed")

@app.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    # 1. Get conversation history from Redis
    history_key = f"history:{user_id}"
    try:
        history_data = redis_client.get(history_key)
        history = json.loads(history_data) if history_data else []
    except Exception as e:
        logger.error(json.dumps({"event": "redis_error_load_history", "error": str(e)}))
        history = []

    # Append new user question
    history.append({"role": "user", "content": body.question})

    # 2. Call LLM
    input_tokens = len(body.question.split()) * 2
    answer = llm_ask(body.question)
    output_tokens = len(answer.split()) * 2

    # Record cost
    from app.cost_guard import record_cost
    record_cost(user_id, input_tokens, output_tokens)

    # Append assistant response
    history.append({"role": "assistant", "content": answer})

    # Limit history to 20 messages (10 turns)
    if len(history) > 20:
        history = history[-20:]

    # 3. Save to Redis (TTL 1 hour)
    try:
        redis_client.setex(history_key, 3600, json.dumps(history))
    except Exception as e:
        logger.error(json.dumps({"event": "redis_error_save_history", "error": str(e)}))

    # 4. Return response
    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

# Graceful Shutdown signal handler
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)