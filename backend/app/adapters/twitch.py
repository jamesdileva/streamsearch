"""Twitch adapter (Sprint 5.2) — official Twitch Helix API only.

Topic search has no title-text primitive on Helix, so the flow is:
`search/categories` (topic → game ids) then `streams` (game ids → live
broadcasts), falling back to top-live overall when no category matches.
Client-credentials auth; the bearer token is cached until near-expiry and
refreshed once on 401.

Identity choice: `platform_stream_id` is the channel (user) id, not the
per-broadcast stream id — a channel is live at most once, so the id is
stable across broadcasts and reverify-by-channel works. The broadcast id
is preserved in metadata.

Live verification with real credentials is deferred until
TWITCH_CLIENT_ID/SECRET exist — same pattern as the YouTube key.
"""

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.adapters.base import AdapterConfigError, AdapterError, BasePlatformAdapter

_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_HELIX = "https://api.twitch.tv/helix"
_THUMB_WIDTH = 640
_THUMB_HEIGHT = 360


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class TwitchAdapter(BasePlatformAdapter):
    platform = "twitch"

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        max_results: int = 10,
        max_categories: int = 3,
        embed_parent: str = "localhost",
        client: httpx.Client | None = None,
    ) -> None:
        if not client_id or not client_secret:
            raise AdapterConfigError("TWITCH_CLIENT_ID/SECRET are not configured")
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_results = max(1, min(int(max_results), 50))
        self.max_categories = max(1, min(int(max_categories), 5))
        self.embed_parent = embed_parent
        self._client = client
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # -- HTTP -----------------------------------------------------------

    def _raw(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            if self._client is not None:
                return self._client.request(method, url, **kwargs)
            with httpx.Client(timeout=10.0) as client:
                return client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise AdapterError(f"twitch request failed: {exc}") from exc

    def _auth_headers(self) -> dict[str, str]:
        now = time.monotonic()
        if self._token is None or now >= self._token_expires_at:
            self._refresh_token()
        return {"Client-Id": self.client_id, "Authorization": f"Bearer {self._token}"}

    def _refresh_token(self) -> None:
        response = self._raw(
            "POST",
            _TOKEN_URL,
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        if response.status_code != 200:
            raise AdapterError(
                f"twitch auth failed (status {response.status_code})"
            )
        try:
            body = response.json()
            token = body["access_token"]
            lifetime = int(body.get("expires_in", 3600))
        except (ValueError, KeyError, TypeError) as exc:
            raise AdapterError("twitch auth returned malformed JSON") from exc
        self._token = str(token)
        self._token_expires_at = time.monotonic() + max(lifetime - 60, 60)

    def _helix(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._raw(
            "GET", f"{_HELIX}{path}", headers=self._auth_headers(), params=params
        )
        if response.status_code == 401:
            # Token may have been revoked early: refresh once and retry.
            self._token = None
            response = self._raw(
                "GET", f"{_HELIX}{path}", headers=self._auth_headers(), params=params
            )
        if response.status_code == 429:
            raise AdapterError("twitch rate limited (status 429)")
        if response.status_code != 200:
            raise AdapterError(f"twitch request failed (status {response.status_code})")
        try:
            body = response.json()
        except ValueError as exc:
            raise AdapterError("twitch returned malformed JSON") from exc
        if not isinstance(body, dict):
            raise AdapterError("twitch returned an unexpected payload")
        return body

    # -- Discovery ------------------------------------------------------

    def _category_ids(self, query: str) -> list[str]:
        body = self._helix(
            "/search/categories", {"query": query, "first": self.max_categories}
        )
        items = body.get("data")
        if not isinstance(items, list):
            raise AdapterError("twitch categories payload missing data")
        return [
            str(item["id"])
            for item in items[: self.max_categories]
            if isinstance(item, dict) and item.get("id")
        ]

    def _live_streams(self, game_ids: list[str]) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"type": "live", "first": self.max_results}
        if game_ids:
            params["game_id"] = game_ids
        body = self._helix("/streams", params)
        items = body.get("data")
        if not isinstance(items, list):
            raise AdapterError("twitch streams payload missing data")
        return [i for i in items if isinstance(i, dict) and i.get("type") == "live"]

    def _map(self, item: dict[str, Any]) -> dict[str, Any] | None:
        user_id = str(item.get("user_id", ""))
        login = str(item.get("user_login", ""))
        if not user_id or not login:
            return None
        thumb = str(item.get("thumbnail_url", "")).replace(
            "{width}x{height}", f"{_THUMB_WIDTH}x{_THUMB_HEIGHT}"
        )
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": f"twitch-{user_id}",
            "platform": self.platform,
            "platform_stream_id": user_id,
            "channel_id": user_id,
            "channel_name": str(item.get("user_name", "") or login),
            "title": str(item.get("title", "")),
            "description": "",
            "thumbnail_url": thumb,
            "source_url": f"https://www.twitch.tv/{login}",
            "embed_url": (
                f"https://player.twitch.tv/?channel={login}"
                f"&parent={self.embed_parent}"
            ),
            "embed_supported": True,
            "live_status": "live",
            "started_at": item.get("started_at"),
            "discovered_at": now,
            "last_verified_at": now,
            "viewer_count": _to_int(item.get("viewer_count")),
            "category": item.get("game_name") or None,
            "tags": list(item.get("tags") or []),
            "latitude": None,
            "longitude": None,
            "location_text": None,
            "metadata": {
                "twitch_stream_id": str(item.get("id", "")),
                "user_login": login,
                "language": item.get("language"),
                "is_mature": item.get("is_mature"),
            },
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        game_ids = self._category_ids(query.strip())
        # No matching category: fall back to top-live overall so arbitrary
        # topics still return candidates for ranking.
        streams = self._live_streams(game_ids)
        return [
            mapped for item in streams[: self.max_results] if (mapped := self._map(item))
        ]

    def reverify(
        self, platform_stream_ids: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        """Channel lookup (≤100 per call); missing channels are offline."""
        found: dict[str, dict[str, Any] | None] = {}
        for start in range(0, len(platform_stream_ids), 100):
            chunk = platform_stream_ids[start : start + 100]
            if not chunk:
                continue
            body = self._helix(
                "/streams",
                {"user_id": chunk, "type": "live", "first": 100},
            )
            items = body.get("data")
            if not isinstance(items, list):
                raise AdapterError("twitch streams payload missing data")
            for item in items:
                if not isinstance(item, dict) or item.get("type") != "live":
                    continue
                mapped = self._map(item)
                if mapped:
                    found[mapped["platform_stream_id"]] = mapped
        return {uid: found.get(uid) for uid in platform_stream_ids}
