import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdapFit API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
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
    
    # ML Engine
    ML_MIN_TRAINING_SAMPLES: int = 14
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
