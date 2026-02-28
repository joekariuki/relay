"""Application configuration loaded from environment variables."""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"

    # Agent settings
    agent_model: str = "anthropic:claude-sonnet-4-6"
    agent_max_tokens: int = 1024
    agent_max_tool_rounds: int = 5

    # Language detection settings
    language_detection_model: str = "anthropic:claude-haiku-4-5-20251001"
    language_detection_timeout_s: float = 2.0

    # Session settings
    session_ttl_minutes: int = 30
    session_max_history: int = 20

    # Eval judge model
    eval_model: str = "anthropic:claude-haiku-4-5-20251001"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def configure_logging(level: str | None = None) -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    log_level = level or settings.log_level
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
