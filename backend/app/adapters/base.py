"""Adapter interface + fake adapter (Sprint 0.2). Real YouTube adapter lands in 1.2."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class BasePlatformAdapter(ABC):
    """Contract all platform adapters must implement.

    `search_quota_cost` is a best-effort estimate of platform quota consumed
    per search, for observability only (Sprint 10.3). YouTube's real unit
    cost is the model; request-limited platforms (Twitch, Kick) declare 0
    because they have no per-request unit budget.
    """

    platform: str = "base"
    search_quota_cost: int = 0

    @abstractmethod
    def search(self, query: str) -> list[dict[str, Any]]:
        """Return normalized stream dicts (see architecture §7)."""
        raise NotImplementedError

    def reverify(self, platform_stream_ids: list[str]) -> dict[str, dict[str, Any] | None]:
        """Re-check known broadcasts by platform id (Sprint 4.3).

        Returns id → normalized dict for still-live records, id → None for
        confirmed-ended/gone ones. Ids the adapter cannot judge are simply
        absent — the refresh pass leaves those records untouched.
        The default (unsupported) returns {} for everything.
        """
        return {}


class AdapterError(Exception):
    """Controlled adapter failure (timeout, quota, malformed, auth).

    Never carries secrets — safe to surface the message to logs/API errors.
    """


class AdapterConfigError(AdapterError):
    """Adapter is misconfigured (e.g. missing API key)."""


class FakeAdapter(BasePlatformAdapter):
    """Fixture adapter proving the normalization boundary.

    Returns one normalized stream dict per query (no platform SDK involved).
    Everything it knows stays live — useful for refresh-pass tests.
    """

    platform = "fake"

    def _record(
        self, id: str, platform_stream_id: str, title: str
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": id,
            "platform": self.platform,
            "platform_stream_id": platform_stream_id,
            "channel_id": "fake-channel-1",
            "channel_name": "Skeleton Channel",
            "title": title,
            "description": "Fixture stream proving adapter → model mapping.",
            "thumbnail_url": "",
            "source_url": "https://example.com/watch/fake-1",
            "embed_url": None,
            "embed_supported": False,
            "live_status": "live",
            "started_at": now,
            "discovered_at": now,
            "last_verified_at": now,
            "viewer_count": None,
            "language": "en",
            "category": None,
            "tags": ["skeleton"],
            "latitude": None,
            "longitude": None,
            "location_text": None,
            "metadata": {"adapter": "fake"},
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        return [self._record("fake-1", "fake-1", f"Skeleton live: {query.strip()}")]

    def reverify(
        self, platform_stream_ids: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        return {
            pid: self._record(pid, pid, "Skeleton live (reverified)")
            for pid in platform_stream_ids
        }
