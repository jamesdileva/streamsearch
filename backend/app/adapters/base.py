"""Adapter interface + fake adapter (Sprint 0.2). Real YouTube adapter lands in 1.2."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class BasePlatformAdapter(ABC):
    """Contract all platform adapters must implement.

    Search/business logic must depend on this, never on
    platform-specific response shapes.
    """

    platform: str = "base"

    @abstractmethod
    def search(self, query: str) -> list[dict[str, Any]]:
        """Return normalized stream dicts (see architecture §7)."""
        raise NotImplementedError


class FakeAdapter(BasePlatformAdapter):
    """Fixture adapter proving the normalization boundary.

    Returns one normalized stream dict per query (no platform SDK involved).
    """

    platform = "fake"

    def search(self, query: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "id": "fake-1",
                "platform": self.platform,
                "platform_stream_id": "fake-1",
                "channel_id": "fake-channel-1",
                "channel_name": "Skeleton Channel",
                "title": f"Skeleton live: {query.strip()}",
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
                "category": None,
                "tags": ["skeleton"],
                "latitude": None,
                "longitude": None,
                "location_text": None,
                "metadata": {"adapter": "fake"},
            }
        ]
