from fastapi import Header, HTTPException
from app.config import settings

def verify_api_key(x_api_key: str = Header(None)) -> str:
    """
    Verify the API Key passed in the X-API-Key header.
    Returns the API key if valid, raising 401 otherwise.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>"
        )
    if x_api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>"
        )
    return x_api_key
