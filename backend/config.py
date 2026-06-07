from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_ANON_KEY: str
    OPENAI_API_KEY: str
    STRIPE_SECRET_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"
    STRIPE_PRO_PRICE_ID: str = "price_placeholder"
    REDIS_URL: str = "redis://localhost:6379"
    ALLOWED_ORIGINS: str = "*"
    FREE_TIER_LIMIT: int = 5

    def get_allowed_origins(self) -> list[str]:
        import json
        v = self.ALLOWED_ORIGINS.strip()
        if not v or v == "*":
            return ["*"]
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except Exception:
            return [v]

    class Config:
        env_file = ".env"


settings = Settings()
