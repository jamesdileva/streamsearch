"""Fake second platform (Sprint 5.1 contract review).

Behaves like Twitch where it matters for the interface, using fixture data:
numeric string ids, free-text game names instead of numeric category ids,
no location availability at all, one record with a missing thumbnail and no
embed, integer-or-absent viewers, live-or-nothing states. If the whole chain
(search → rank → cards → freshness → refresh → reports) works with this
next to the fake/YouTube adapters, the contract is genuinely platform
agnostic. The real Twitch adapter lands in Sprint 5.2.
"""

from datetime import datetime, timezone
from typing import Any

from app.adapters.base import BasePlatformAdapter

# parent=localhost is a dev-fixture value; 5.2 sets it from real config.
_EMBED_PARENT = "localhost"


class FakeTwitchAdapter(BasePlatformAdapter):
    platform = "twitch"

    def _record(
        self,
        pid: str,
        channel: str,
        title: str,
        game: str,
        viewers: int | None,
        thumbnail_url: str,
        embed_supported: bool,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": f"twitch-{pid}",
            "platform": self.platform,
            "platform_stream_id": pid,
            "channel_id": channel,
            "channel_name": channel,
            "title": title,
            "description": f"{game} stream on Twitch.",
            "thumbnail_url": thumbnail_url,
            "source_url": f"https://www.twitch.tv/{channel}",
            "embed_url": (
                f"https://player.twitch.tv/?channel={channel}&parent={_EMBED_PARENT}"
                if embed_supported
                else None
            ),
            "embed_supported": embed_supported,
            "live_status": "live",
            "started_at": "2026-10-01T12:00:00Z",
            "discovered_at": now,
            "last_verified_at": now,
            "viewer_count": viewers,
            "language": "en",
            "category": game,
            "tags": ["English", "Live"],
            "latitude": None,
            "longitude": None,
            "location_text": None,
            "metadata": {"adapter": "fake-twitch", "game_name": game},
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.strip()
        return [
            self._record(
                pid="48392157",
                channel="rivercam",
                title=f"River cam: {q} live",
                game="Outdoors",
                viewers=5231,
                thumbnail_url="https://static-cdn.twitch/rivercam-640x360.jpg",
                embed_supported=True,
            ),
            self._record(
                pid="987123",
                channel="cityhall",
                title=f"City hall {q} briefing",
                game="Just Chatting",
                viewers=None,
                thumbnail_url="",
                embed_supported=False,
            ),
        ]

    def reverify(
        self, platform_stream_ids: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        known = {
            r["platform_stream_id"]: r for r in self.search("reverify")
        }
        verdicts: dict[str, dict[str, Any] | None] = {}
        for pid in platform_stream_ids:
            if pid in known:
                verdicts[pid] = known[pid]
            elif pid == "555":
                verdicts[pid] = None  # retired channel: confirmed gone
            # Unknown ids: absent (can't judge) — records age honestly.
        return verdicts
