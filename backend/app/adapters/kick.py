"""Kick adapter (Sprint 9.2) — official Kick Public API only.

See `docs/kick-feasibility.md` for the decision record. Discovery has no
title-text primitive on Kick either, so the flow mirrors Twitch:

  GET /public/v1/categories?q={topic}     -> category ids (real text search)
  GET /public/v2/livestreams?category_id= -> live broadcasts (<=25 ids)
  GET /public/v2/livestreams  (no filter) -> top-live fallback

Re-verification goes through `GET /public/v1/users/livestreams` by
broadcaster user id.

Endpoint-shape honesty: Kick's published livestream payload varies across
API revisions, so every mapping read goes through `_first` (first present
key wins) instead of assuming one exact shape. A rename on Kick's side
degrades to fewer results, not a crash. Confirm field names against the
live API when credentials exist — the deferred verification procedure is
in the worklog for Sprint 9.2.

Identity: `platform_stream_id` is the channel (broadcaster user) id, not
the per-broadcast stream id — a channel is live at most once, so the id is
stable across broadcasts and reverify works.
"""

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.adapters.base import AdapterConfigError, AdapterError, BasePlatformAdapter

_TOKEN_URL = "https://id.kick.com/oauth2/token"
_API = "https://api.kick.com"
_EMBED_PARENT = "localhost"


def _first(item: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """First present, non-None value among `keys`, else `default`."""
    for key in keys:
        value = item.get(key)
        if value is not None:
            return value
    return default


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _nested(item: dict[str, Any], *path: str) -> dict[str, Any]:
    """Walk a dict path, returning {} the moment any level is missing."""
    node = item
    for key in path:
        if not isinstance(node, dict):
            return {}
        node = node.get(key)
        if not isinstance(node, dict):
            return {}
    return node


class KickAdapter(BasePlatformAdapter):
    platform = "kick"

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        max_results: int = 25,
        max_categories: int = 3,
        embed_parent: str = "",
        client: httpx.Client | None = None,
    ) -> None:
        if not client_id or not client_secret:
            raise AdapterConfigError("KICK_CLIENT_ID/SECRET are not configured")
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_results = max(1, min(int(max_results), 100))
        self.max_categories = max(1, min(int(max_categories), 25))
        self.embed_parent = (embed_parent or _EMBED_PARENT).strip()
        self._client = client
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # -- HTTP -----------------------------------------------------------

    def _request(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        try:
            if self._client is not None:
                return self._client.request(method, url, **kwargs)
            with httpx.Client(timeout=10.0) as client:
                return client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise AdapterError(f"kick request failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        if self._token is None or time.monotonic() >= self._token_expires_at:
            self._refresh_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    def _refresh_token(self) -> None:
        response = self._request(
            "POST",
            _TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code != 200:
            raise AdapterError(f"kick auth failed (status {response.status_code})")
        try:
            body = response.json()
            token = body["access_token"]
            lifetime = int(body.get("expires_in", 3600))
        except (ValueError, KeyError, TypeError) as exc:
            raise AdapterError("kick auth returned malformed JSON") from exc
        self._token = str(token)
        # Refresh a minute early so a slow request can't cross the boundary.
        self._token_expires_at = time.monotonic() + max(lifetime - 60, 60)

    def _get(
        self, path: str, params: dict[str, Any], retry_on_401: bool = True
    ) -> dict[str, Any]:
        response = self._request(
            "GET", f"{_API}{path}", headers=self._headers(), params=params
        )
        if response.status_code == 401 and retry_on_401:
            # Token may have been revoked early — refresh once and retry.
            self._token = None
            return self._get(path, params, retry_on_401=False)
        if response.status_code == 429:
            raise AdapterError("kick rate limited (status 429)")
        if response.status_code != 200:
            raise AdapterError(f"kick request failed (status {response.status_code})")
        try:
            body = response.json()
        except ValueError as exc:
            raise AdapterError("kick returned malformed JSON") from exc
        if not isinstance(body, dict):
            raise AdapterError("kick returned an unexpected payload")
        return body

    # -- Discovery ------------------------------------------------------

    def _category_ids(self, query: str) -> list[int]:
        body = self._get("/public/v1/categories", {"q": query})
        data = body.get("data")
        if not isinstance(data, list):
            raise AdapterError("kick categories payload missing data")
        ids: list[int] = []
        for item in data[: self.max_categories]:
            if not isinstance(item, dict):
                continue
            category_id = _to_int(_first(item, "id", "category_id"))
            if category_id is not None:
                ids.append(category_id)
        return ids

    def _livestreams(
        self, category_ids: list[int] | None = None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": self.max_results}
        if category_ids:
            params["category_id"] = list(category_ids)
        body = self._get("/public/v2/livestreams", params)
        data = body.get("data")
        if not isinstance(data, list):
            raise AdapterError("kick livestreams payload missing data")
        return [i for i in data if isinstance(i, dict)]

    def _map(self, item: dict[str, Any]) -> dict[str, Any] | None:
        channel = _nested(item, "channel") or _nested(item, "broadcaster_user")
        user_id = _to_int(
            _first(item, "broadcaster_user_id", "channel_id")
            or _first(channel, "id", "broadcaster_user_id")
        )
        slug = _first(
            item, "slug", "channel_slug", "user_login", "username", default=""
        ) or _first(channel, "slug", "username", "user_login", default="")
        if not user_id or not slug:
            return None  # cannot build a stable identity or a usable URL
        category = _nested(item, "category")
        thumb = _first(item, "thumbnail", "stream_thumbnail", default="")
        title = _first(item, "session_title", "title", "stream_title", default="")
        # Category may be nested (`category.name`) or flat (`category_name`).
        category_name = _first(
            category, "name", "category_name", default=""
        ) or _first(item, "category_name", "game_name", default="")
        if category_name:
            category_name = str(category_name)
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": f"kick-{user_id}",
            "platform": self.platform,
            "platform_stream_id": str(user_id),
            "channel_id": str(user_id),
            "channel_name": str(slug),
            "title": str(title),
            "description": "",
            "thumbnail_url": str(thumb or ""),
            "source_url": f"https://kick.com/{slug}",
            "embed_url": (
                f"https://player.kick.com/{slug}?parent={self.embed_parent}"
            ),
            "embed_supported": True,
            "live_status": "live",
            "started_at": _first(item, "start_time", "started_at", "created_at"),
            "discovered_at": now,
            "last_verified_at": now,
            "viewer_count": _to_int(_first(item, "viewer_count", "viewers")),
            # First-class field since Sprint 8.1 so the language filter works.
            "language": _first(item, "language", "language_code"),
            "category": category_name,
            "tags": [
                str(t) for t in (_first(item, "custom_tags", "tags", default=[]) or [])
            ],
            "latitude": None,
            "longitude": None,
            "location_text": None,
            "metadata": {
                "is_mature": _first(item, "is_mature"),
                "category_id": _to_int(_first(category, "id", "category_id")),
            },
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        category_ids = self._category_ids(query.strip())
        # No matching category: fall back to top-live overall so arbitrary
        # topics still return candidates for ranking.
        streams = self._livestreams(category_ids)
        return [
            mapped for item in streams[: self.max_results] if (mapped := self._map(item))
        ]

    def reverify(
        self, platform_stream_ids: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        """Channel lookup; missing channels mean offline (ended)."""
        found: dict[str, dict[str, Any] | None] = {}
        ids = [pid for pid in platform_stream_ids if pid]
        for start in range(0, len(ids), 100):
            chunk = ids[start : start + 100]
            if not chunk:
                continue
            body = self._get(
                "/public/v1/users/livestreams",
                {"broadcaster_user_id": chunk},
            )
            data = body.get("data")
            if not isinstance(data, list):
                raise AdapterError("kick users/livestreams payload missing data")
            for item in data:
                if not isinstance(item, dict):
                    continue
                mapped = self._map(item)
                if mapped:
                    found[mapped["platform_stream_id"]] = mapped
        return {pid: found.get(pid) for pid in platform_stream_ids}
