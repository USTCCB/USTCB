"""Configuration Management"""
from typing import Optional
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Application Configuration"""
    
    # API Configuration
    API_TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    
    # Data Source Configuration
    A_STOCK_API: str = "https://api.example.com"
    US_STOCK_API: str = "https://api.example.com"
    HK_STOCK_API: str = "https://api.example.com"
    NEWS_API: str = "https://newsapi.example.com"
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # seconds
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Log Configuration
    LOG_LEVEL: str = "INFO"
    
    # Data Directory
    DATA_DIR: str = "data"
    CACHE_DIR: str = "data/cache"
    RESULTS_DIR: str = "data/results"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()