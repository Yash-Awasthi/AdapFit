import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdapFit API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Skips JWT validation and injects a fixed development user. The auth
    # middleware ignores this whenever ENVIRONMENT is "production".
    AUTH_DISABLED: bool = os.getenv("AUTH_DISABLED", "").lower() in {"1", "true", "yes"}
    DEV_USER_ID: str = os.getenv("DEV_USER_ID", "default")

    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    # Groq retires model ids without notice; a retired id answers 404.
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    # Comma-separated models tried in order after GROQ_MODEL fails or returns nothing.
    GROQ_FALLBACK_MODELS: str = os.getenv("GROQ_FALLBACK_MODELS", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    
    # Postgres (asyncpg pool; empty keeps the in-memory fallback active)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_POOL_MAX_SIZE: int = int(os.getenv("DB_POOL_MAX_SIZE", "4"))

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_POOL_MODE: str = os.getenv("SUPABASE_POOL_MODE", "transaction")  # transaction | session
    SUPABASE_POOL_SIZE: int = int(os.getenv("SUPABASE_POOL_SIZE", "10"))
    
    # Algorithmic Defaults
    DEFAULT_BASELINE_HRV_RMSSD: float = 50.0
    DEFAULT_BASELINE_HRV_STD: float = 10.0
    DEFAULT_BASELINE_RHR: float = 65.0
    DEFAULT_BASELINE_SLEEP_HOURS: float = 8.0
    DEFAULT_CHRONIC_LOAD: float = 500.0
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMITING_ENABLED: bool = os.getenv("RATE_LIMITING_ENABLED", "").lower() not in {"0", "false", "no"}
    
    # ML Engine
    ML_MIN_TRAINING_SAMPLES: int = 14
    
    # Read by app.core.auth at import time; declared here so a .env carrying it
    # does not fail validation.
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")

    # Outgoing mail (guardian consent). Without SMTP_HOST the link is logged, which only suits development.
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "no-reply@adapfit.app")
    # Base URL links in emails point at, e.g. https://api.adapfit.app
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    # Bearer token Prometheus sends to /metrics. Unset in production means /metrics answers 404.
    METRICS_TOKEN: str = os.getenv("METRICS_TOKEN", "")

    class Config:
        case_sensitive = True
        env_file = ".env"
        # .env.example ships keys no setting declares. Rejecting unknown keys
        # turns copying it into a boot failure.
        extra = "ignore"

settings = Settings()
