# Configuration settings
import logging
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    debug: bool = False

    # App metadata
    app_name: str = "Production AI Agent"
    app_version: str = "1.0.0"

    # LLM configuration
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Security / API config
    agent_api_key: str = "dev-key-change-me"
    jwt_secret: str = "dev-jwt-secret"
    allowed_origins: str = "*"

    # Redis config
    redis_url: str = "redis://localhost:6379/0"

    # Required settings from instructions
    log_level: str = "INFO"
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate(self):
        logger = logging.getLogger(__name__)
        if self.environment == "production":
            if self.agent_api_key == "dev-key-change-me":
                raise ValueError("AGENT_API_KEY must be set in production!")
            if self.jwt_secret == "dev-jwt-secret":
                raise ValueError("JWT_SECRET must be set in production!")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set — using mock LLM")
        return self

settings = Settings()
try:
    settings.validate()
except Exception as e:
    import sys
    print(f"Configuration validation failed: {e}", file=sys.stderr)