import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    database_url: str = _normalize_database_url(
        os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'regulatory_intel.db'}")
    )
    gmail_address: str = os.getenv("GMAIL_ADDRESS", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    default_digest_email: str = os.getenv("DEFAULT_DIGEST_EMAIL", "")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    public_url: str = os.getenv("PUBLIC_URL", "")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    ingest_lookback_days: int = int(os.getenv("INGEST_LOOKBACK_DAYS", "30"))
    user_agent: str = os.getenv(
        "USER_AGENT", "RegulatoryIntelBot/1.0 (+https://regulatory-intelligence)"
    )
    ingest_cron_hour: int = int(os.getenv("INGEST_CRON_HOUR", "6"))
    digest_cron_hour: int = int(os.getenv("DIGEST_CRON_HOUR", "7"))
    run_initial_ingest: bool = os.getenv("RUN_INITIAL_INGEST", "").lower() in ("1", "true", "yes")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
