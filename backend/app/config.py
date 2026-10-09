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
    youtube_location_radius: str = os.getenv("YOUTUBE_LOCATION_RADIUS", "100km")
    twitch_client_id: str = os.getenv("TWITCH_CLIENT_ID", "")
    twitch_client_secret: str = os.getenv("TWITCH_CLIENT_SECRET", "")
    twitch_max_results: int = int(os.getenv("TWITCH_MAX_RESULTS", "10"))
    twitch_max_categories: int = int(os.getenv("TWITCH_MAX_CATEGORIES", "3"))
    twitch_embed_parent: str = os.getenv("TWITCH_EMBED_PARENT", "localhost")
    kick_client_id: str = os.getenv("KICK_CLIENT_ID", "")
    kick_client_secret: str = os.getenv("KICK_CLIENT_SECRET", "")
    kick_max_results: int = int(os.getenv("KICK_MAX_RESULTS", "25"))
    kick_max_categories: int = int(os.getenv("KICK_MAX_CATEGORIES", "3"))
    kick_embed_parent: str = os.getenv("KICK_EMBED_PARENT", "localhost")
    # Freshness thresholds (seconds since last_verified_at). See
    # services/freshness.py. Periodic revalidation lands in Sprint 4.3.
    freshness_fresh_seconds: int = int(os.getenv("FRESHNESS_FRESH_SECONDS", "300"))
    freshness_aging_seconds: int = int(os.getenv("FRESHNESS_AGING_SECONDS", "1800"))
    # Short-lived result cache (Sprint 4.1). Redis only if traffic justifies it.
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "60"))
    # Background refresh (Sprint 4.3): bounded, modest by default.
    refresh_enabled: bool = os.getenv("REFRESH_ENABLED", "1") == "1"
    refresh_interval_seconds: int = int(os.getenv("REFRESH_INTERVAL_SECONDS", "900"))
    refresh_batch_size: int = int(os.getenv("REFRESH_BATCH_SIZE", "10"))
    refresh_prune_days: int = int(os.getenv("REFRESH_PRUNE_DAYS", "30"))
    # Embedding prototype (Sprint 7.2, experimental — production search
    # never calls it; 7.3 decides if it ever should).
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embeddings_model: str = os.getenv("EMBEDDINGS_MODEL", "nomic-embed-text")
    # None = use the model's documented preset (app/search/embeddings.py).
    embeddings_query_prefix: str | None = os.getenv("EMBEDDINGS_QUERY_PREFIX")
    embeddings_doc_prefix: str | None = os.getenv("EMBEDDINGS_DOC_PREFIX")
    cors_origins: list[str] = _cors_origins()
    # Rate limiting + abuse protection (Sprint 10.2). In-memory, per process.
    rate_limit_search: int = int(os.getenv("RATE_LIMIT_SEARCH", "60"))
    rate_limit_search_window: int = int(os.getenv("RATE_LIMIT_SEARCH_WINDOW", "60"))
    rate_limit_refresh: int = int(os.getenv("RATE_LIMIT_REFRESH", "2"))
    rate_limit_refresh_window: int = int(os.getenv("RATE_LIMIT_REFRESH_WINDOW", "300"))


settings = Settings()
