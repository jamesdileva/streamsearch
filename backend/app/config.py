"""Central config — env only, no secrets committed. See /.env.example."""

import os


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./streamsearch.db")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    youtube_max_results: int = int(os.getenv("YOUTUBE_MAX_RESULTS", "10"))
    # Freshness thresholds (seconds since last_verified_at). See
    # services/freshness.py. Periodic revalidation lands in Sprint 4.3.
    freshness_fresh_seconds: int = int(os.getenv("FRESHNESS_FRESH_SECONDS", "300"))
    freshness_aging_seconds: int = int(os.getenv("FRESHNESS_AGING_SECONDS", "1800"))
    cors_origins: list[str] = _cors_origins()


settings = Settings()
