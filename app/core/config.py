from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_db"

    REDIS_URL: str = "redis://localhost:6379/0"
    SCREENSHOTS_DIR: str = "static/screenshots"
    COLLECTOR_TIMEOUT: int = 30  # секунд на загрузку страницы
    MAX_ELEMENTS_PER_PAGE: int = 500


    SECRET_KEY: str = "secret-key"  # В продакшене через .env!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openrouter/auto"
    
   
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()