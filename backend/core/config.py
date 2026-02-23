"""
Core configuration module for CliqUp backend.
Centralized configuration management with environment validation.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    MONGO_URL: str
    DB_NAME: str
    
    # Security
    JWT_SECRET: str = "cliqup-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    # App Info
    APP_NAME: str = "CliqUp"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Meet (Dating) Settings
    FREE_SQUAD_CAP: int = 3
    PLUS_SQUAD_CAP: int = 4
    ELITE_SQUAD_CAP: int = 5
    
    # Elo Rating Settings
    DEFAULT_ELO: int = 1200
    ELO_K_FACTOR: int = 32
    
    # Stories
    STORY_DURATION_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
