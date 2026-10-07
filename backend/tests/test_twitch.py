"""Twitch adapter tests — all mocked, no network, no real credentials.

Dual-platform live verification is deferred until TWITCH_CLIENT_ID/SECRET
(and YOUTUBE_API_KEY) exist; see worklog Sprint 5.2 for the procedure.
"""

import httpx
import pytest

from app.adapters.base import AdapterConfigError, AdapterError
from app.adapters.twitch import TwitchAdapter
from app.config import settings
from app.models.stream import Stream
from app.services.search import SearchService, build_default_adapters

CATEGORIES = {
    "data": [
        {"id": "509658", "name": "Just Chatting"},
        {"id": "12345", "name": "Outdoors"},
    ]
}

STREAMS = {
    "data": [
        {
            "id": "42123456789",
            "user_id": "123456",
            "user_login": "rivercam",
            "user_name": "RiverCam",
            "game_id": "12345",
            "game_name": "Outdoors",
            "type": "live",
            "title": "River flood watch live",
            "viewer_count": 5231,
            "started_at": "2026-10-07T00:00:00Z",
            "language": "en",
            "thumbnail_url": "https://static-cdn/rivercam-{width}x{height}.jpg",
            "tags": ["English"],
            "is_mature": False,
        },
        {
            "id": "42123456790",
            "user_id": "789",
            "user_login": "cityhall",
            "user_name": "CityHall",
            "game_id": "509658",
            "game_name": "Just Chatting",
            "type": "live",
            "title": "City hall briefing",
            "viewer_count": 42,
            "started_at": "2026-10-07T01:00:00Z",
            "language": "en",
            "thumbnail_url": "https://static-cdn/cityhall-{width}x{height}.jpg",
            "tags": [],
            "is_mature": False,
        },
        {"id": "broken", "type": "live"},
    ]
}

TOKEN = {"access_token": "tok", "expires_in": 3600, "token_type": "bearer"}


def _client(handler, token_calls: list | None = None) -> httpx.Client:
    def route(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in request.url.path:
            if token_calls is not None:
                token_calls.append(1)
            return httpx.Response(200, json=TOKEN)
        if "search/categories" in request.url.path:
            return httpx.Response(200, json=CATEGORIES)
        if request.url.path.endswith("/streams"):
            return handler(request)
        return httpx.Response(404, json={})

    return httpx.Client(transport=httpx.MockTransport(route))


def _ok_client(token_calls: list | None = None) -> httpx.Client:
    return _client(lambda request: httpx.Response(200, json=STREAMS), token_calls)


def _creds(**over) -> dict:
    base = {"client_id": "id", "client_secret": "secret"}
    return {**base, **over}


def test_maps_streams_to_normalized_records():
    adapter = TwitchAdapter(**_creds(), client=_ok_client())
    records = adapter.search("flood")
    assert len(records) == 2  # malformed item skipped
    first = Stream(**records[0])
    assert first.platform == "twitch"
    assert first.platform_stream_id == "123456"
    assert first.id == "twitch-123456"
    assert first.channel_name == "RiverCam"
    assert first.title == "River flood watch live"
    assert first.viewer_count == 5231
    assert first.source_url == "https://www.twitch.tv/rivercam"
    assert first.thumbnail_url == "https://static-cdn/rivercam-640x360.jpg"
    assert first.category == "Outdoors"
    assert first.tags == ["English"]
    assert first.live_status == "live"
    assert first.location_text is None
    assert first.embed_supported is True
    assert "channel=rivercam" in (first.embed_url or "")
    assert first.metadata["user_login"] == "rivercam"
    assert first.metadata["twitch_stream_id"] == "42123456789"


def test_category_cap_and_fallback():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json={"data": []})

    adapter = TwitchAdapter(**_creds(max_categories=1), client=_client(handler))
    assert adapter.search("flood") == []
    assert seen.get("game_id") == "509658"


def test_no_categories_falls_back_to_top_live():
    seen: dict = {}

    def route(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in request.url.path:
            return httpx.Response(200, json=TOKEN)
        if "search/categories" in request.url.path:
            return httpx.Response(200, json={"data": []})
        seen.update(request.url.params)
        return httpx.Response(200, json=STREAMS)

    adapter = TwitchAdapter(
        **_creds(), client=httpx.Client(transport=httpx.MockTransport(route))
    )
    assert len(adapter.search("flood")) == 2
    assert "game_id" not in seen


def test_token_cached_across_searches():
    calls: list = []
    adapter = TwitchAdapter(**_creds(), client=_ok_client(calls))
    adapter.search("a")
    adapter.search("b")
    assert len(calls) == 1


def test_401_refreshes_token_and_retries():
    calls: list = []
    states = {"streams": 0}

    def route(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in request.url.path:
            calls.append(1)
            return httpx.Response(200, json=TOKEN)
        if "search/categories" in request.url.path:
            return httpx.Response(200, json=CATEGORIES)
        states["streams"] += 1
        if states["streams"] == 1:
            return httpx.Response(401, json={})
        return httpx.Response(200, json=STREAMS)

    adapter = TwitchAdapter(
        **_creds(), client=httpx.Client(transport=httpx.MockTransport(route))
    )
    assert len(adapter.search("flood")) == 2
    assert len(calls) == 2


def test_reverify_confirms_live_and_offline():
    adapter = TwitchAdapter(**_creds(), client=_ok_client())
    verdicts = adapter.reverify(["123456", "999"])
    assert verdicts["123456"] is not None
    assert verdicts["123456"]["platform_stream_id"] == "123456"
    assert verdicts["999"] is None


def test_missing_credentials_raise_config_error():
    with pytest.raises(AdapterConfigError):
        TwitchAdapter(client_id="", client_secret="s")
    with pytest.raises(AdapterConfigError):
        TwitchAdapter(client_id="id", client_secret="")


def test_http_500_raises_adapter_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    with pytest.raises(AdapterError, match="status 500"):
        TwitchAdapter(**_creds(), client=_client(handler)).search("x")


def test_factory_matrix(monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", "yt")
    monkeypatch.setattr(settings, "twitch_client_id", "id")
    monkeypatch.setattr(settings, "twitch_client_secret", "s")
    assert [a.platform for a in build_default_adapters()] == ["youtube", "twitch"]

    monkeypatch.setattr(settings, "youtube_api_key", "")
    assert [a.platform for a in build_default_adapters()] == ["twitch"]

    monkeypatch.setattr(settings, "twitch_client_id", "")
    monkeypatch.setattr(settings, "twitch_client_secret", "")
    assert [a.platform for a in build_default_adapters()] == ["fake", "twitch"]

    monkeypatch.setattr(settings, "youtube_api_key", "yt")
    assert [a.platform for a in build_default_adapters()] == ["youtube"]


def test_service_validates_twitch_records():
    service = SearchService(
        adapters=[TwitchAdapter(**_creds(), client=_ok_client())]
    )
    res = service.search("flood")
    assert res.count == 2
    assert {s.platform for s in res.results} == {"twitch"}
