from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_ANON_KEY: str
    OPENAI_API_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRO_PRICE_ID: str
    REDIS_URL: str = "redis://localhost:6379"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    FREE_TIER_LIMIT: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
