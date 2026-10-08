"""Normalized Stream domain model (architecture §7).

Platform-agnostic. Platform extras live in `metadata`.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

LiveStatus = Literal["live", "ended", "unknown"]

# How much the live flag can be trusted (computed by the service layer,
# never set by adapters). See services/freshness.py for thresholds.
Freshness = Literal["fresh", "aging", "stale", "ended"]


class Stream(BaseModel):
    id: str
    platform: str
    platform_stream_id: str
    channel_id: str = ""
    channel_name: str = ""
    title: str = ""
    description: str = ""
    thumbnail_url: str = ""
    source_url: str = ""
    embed_url: str | None = None
    embed_supported: bool = False
    live_status: LiveStatus = "unknown"
    freshness: Freshness | None = None
    started_at: datetime | None = None
    discovered_at: datetime | None = None
    last_verified_at: datetime | None = None
    viewer_count: int | None = None
    # Broadcast language where the platform reports one (Sprint 8.1).
    # YouTube: defaultAudioLanguage/defaultLanguage; Twitch: language.
    # Absent means unknown — never guessed. Normalized lowercase (BCP-47
    # primary subtag, e.g. "en", "ja").
    language: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    location_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Query-relative enrichment stamped by the service layer (Sprint 3.1).
    # None until ranked; not set by adapters.
    score: float | None = None


class IndexedStream(Stream):
    """A Stream as stored in the persistent index (Sprint 4.2).

    Index bookkeeping only — never set by adapters, never part of the
    search ranking contract.
    """

    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    ended_at: datetime | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[Stream] = Field(default_factory=list)
    count: int = 0
    # Collapsed by dedup (Sprint 6.2); the index keeps every sighting.
    duplicates_removed: int = 0
