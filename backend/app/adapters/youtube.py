"""YouTube adapter (Sprint 1.2) — official YouTube Data API v3 only.

Flow: `search.list` (eventType=live, type=video) for candidate video IDs,
then `videos.list` (snippet + liveStreamingDetails + recordingDetails) for
the metadata needed to build normalized records. Only broadcasts that are
verifiably live are returned.

Quota note: `search.list` costs ~100 units per call, so callers must pass a
small `max_results` budget and cache aggressively (Sprint 4.1).

Live verification with a real key is deferred until `YOUTUBE_API_KEY` is
configured — see worklog Sprint 1.2 for the smoke procedure.
"""

from datetime import datetime, timezone
from typing import Any

import httpx

from app.adapters.base import AdapterConfigError, AdapterError, BasePlatformAdapter
from app.search.location import parse_location, place_coords

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
WATCH_URL = "https://www.youtube.com/watch"
EMBED_URL = "https://www.youtube.com/embed"


def _language(snippet: dict[str, Any]) -> str | None:
    """BCP-47 primary subtag, e.g. "en". Absent stays absent."""
    raw = snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage")
    if not raw:
        return None
    return str(raw).strip().lower().split("-")[0] or None


def _thumb(snippet: dict[str, Any]) -> str:
    thumbs = snippet.get("thumbnails") or {}
    for quality in ("high", "medium", "default"):
        url = (thumbs.get(quality) or {}).get("url")
        if url:
            return str(url)
    return ""


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


class YouTubeAdapter(BasePlatformAdapter):
    platform = "youtube"

    def __init__(
        self,
        api_key: str = "",
        max_results: int = 10,
        client: httpx.Client | None = None,
        location_radius: str = "100km",
    ) -> None:
        if not api_key:
            raise AdapterConfigError("YOUTUBE_API_KEY is not configured")
        self.api_key = api_key
        self.max_results = max(1, min(int(max_results), 25))
        self._client = client
        self.location_radius = location_radius

    def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {**params, "key": self.api_key}
        try:
            if self._client is not None:
                response = self._client.get(url, params=params)
            else:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(url, params=params)
        except httpx.RequestError as exc:
            raise AdapterError(f"youtube request failed: {exc}") from exc
        if response.status_code == 403:
            raise AdapterError(
                "youtube access denied or quota exhausted (status 403)"
            )
        if response.status_code != 200:
            raise AdapterError(f"youtube request failed (status {response.status_code})")
        try:
            body = response.json()
        except ValueError as exc:
            raise AdapterError("youtube returned malformed JSON") from exc
        if not isinstance(body, dict):
            raise AdapterError("youtube returned an unexpected payload")
        return body

    def _candidate_ids(self, query: str) -> list[str]:
        params: dict[str, Any] = {
            "part": "snippet",
            "eventType": "live",
            "type": "video",
            "q": query,
            "maxResults": self.max_results,
        }
        # Platform geographic search where supported: known places carry
        # coordinates, so no external geocoding is needed. Unknown places
        # simply skip the geo bias (keyword matching still applies).
        parsed = parse_location(query)
        if parsed.place:
            coords = place_coords(parsed.place)
            if coords:
                params["location"] = f"{coords[0]},{coords[1]}"
                params["locationRadius"] = self.location_radius
        body = self._get(SEARCH_URL, params)
        ids: list[str] = []
        items = body.get("items")
        if not isinstance(items, list):
            raise AdapterError("youtube search payload missing items")
        for item in items:
            if not isinstance(item, dict):
                continue
            video_id = (item.get("id") or {}).get("videoId")
            if video_id:
                ids.append(str(video_id))
        return ids

    def _details(self, video_ids: list[str]) -> list[dict[str, Any]]:
        body = self._get(
            VIDEOS_URL,
            {
                "part": "snippet,liveStreamingDetails,recordingDetails",
                "id": ",".join(video_ids),
                "maxResults": len(video_ids),
            },
        )
        items = body.get("items")
        if not isinstance(items, list):
            raise AdapterError("youtube videos payload missing items")
        return [i for i in items if isinstance(i, dict)]

    def _map(self, item: dict[str, Any]) -> dict[str, Any] | None:
        video_id = str(item.get("id", ""))
        snippet = item.get("snippet") or {}
        live = item.get("liveStreamingDetails") or {}
        if not video_id or not live.get("actualStartTime"):
            return None  # not a verifiably live broadcast — skip
        recording = item.get("recordingDetails") or {}
        location = recording.get("location") or {}
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": f"youtube-{video_id}",
            "platform": self.platform,
            "platform_stream_id": video_id,
            "channel_id": str(snippet.get("channelId", "")),
            "channel_name": str(snippet.get("channelTitle", "")),
            "title": str(snippet.get("title", "")),
            "description": str(snippet.get("description", "")),
            "thumbnail_url": _thumb(snippet),
            "source_url": f"{WATCH_URL}?v={video_id}",
            "embed_url": f"{EMBED_URL}/{video_id}",
            "embed_supported": True,
            "live_status": "live",
            "started_at": live.get("actualStartTime"),
            "discovered_at": now,
            "last_verified_at": now,
            "viewer_count": _to_int(live.get("concurrentViewers")),
            "language": _language(snippet),
            "category": snippet.get("categoryId"),
            "tags": list(snippet.get("tags") or []),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "location_text": recording.get("locationDescription"),
            "metadata": {
                "liveBroadcastContent": snippet.get("liveBroadcastContent")
            },
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        ids = self._candidate_ids(query.strip())
        if not ids:
            return []
        return [
            mapped
            for item in self._details(ids)
            if (mapped := self._map(item)) is not None
        ]

    def reverify(
        self, platform_stream_ids: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        """Batch id lookup (50 per call); missing or unmappable → None (ended)."""
        found: dict[str, dict[str, Any] | None] = {}
        for start in range(0, len(platform_stream_ids), 50):
            chunk = platform_stream_ids[start : start + 50]
            if not chunk:
                continue
            for item in self._details(chunk):
                video_id = str(item.get("id", ""))
                if video_id:
                    found[video_id] = self._map(item)
        return {vid: found.get(vid) for vid in platform_stream_ids}
