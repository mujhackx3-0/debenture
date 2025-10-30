"""
Application configuration with environment variable management.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    APP_NAME: str = "Esoteric Loan Sales Assistant"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-use-strong-random-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALLOWED_ORIGINS: list[str] = ["*"]  # Configure properly in production
    
    # Groq LLM Settings
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str = "mixtral-8x7b-32768"
    GROQ_TEMPERATURE: float = 0.5
    GROQ_MAX_TOKENS: int = 1024
    GROQ_TIMEOUT: int = 30
    
    # Database Settings
    SQLITE_DB_PATH: str = "chat_memory_loan_sales.db"
    CHROMA_DB_PERSIST_DIR: str = "loan_sales_rag.db"
    
    # Redis Settings (for session management)
    REDIS_URL: Optional[str] = None
    REDIS_SESSION_TTL: int = 3600  # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Performance
    MAX_MESSAGE_HISTORY: int = 50
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 3
    
    # Loan Configuration
    MIN_CREDIT_SCORE: int = 650
    MAX_PERSONAL_LOAN: int = 500000
    MIN_LOAN_AMOUNT: int = 10000
    MAX_LOAN_TERM_MONTHS: int = 60
    MIN_LOAN_TERM_MONTHS: int = 12
    
    # Monitoring
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance to avoid reloading from environment on every call.
    """
    return Settings()


# Export settings instance
settings = get_settings()

