"""
Application configuration loaded from environment variables / .env file.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "DCDeepTech API Gateway"
    app_env: str = "development"

    # Security
    secret_key: str = "change_me"
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/dcdeeptech"

    # CORS — stored as comma-separated string in env, parsed to list
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Billing
    default_currency: str = "USD"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call once per process."""
    return Settings()


settings = get_settings()
