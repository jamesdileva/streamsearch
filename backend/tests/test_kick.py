"""Kick adapter tests — all mocked, no network, no real credentials.

Live verification is deferred until KICK_CLIENT_ID/SECRET exist; the
procedure is in the worklog for Sprint 9.2. Field-shape drift is covered
explicitly because Kick's payload varies across API revisions.
"""

import httpx
import pytest

from app.adapters.base import AdapterConfigError
from app.adapters.kick import KickAdapter
from app.config import settings
from app.models.stream import Stream
from app.services.search import SearchService, build_default_adapters

TOKEN = {"access_token": "tok", "expires_in": 3600, "token_type": "bearer"}

CATEGORIES = {"data": [{"id": 27, "name": "Just Chatting"}, {"id": 12, "name": "Games"}]}

LIVESTREAMS = {
    "data": [
        {
            "broadcaster_user_id": 123456,
            "slug": "riverwatch",
            "session_title": "Flood watch live",
            "category": {"id": 27, "name": "Just Chatting"},
            "viewer_count": 4821,
            "language": "en",
            "start_time": "2026-10-08T00:00:00Z",
            "thumbnail": "https://kick.com/thumb/river-640x360.jpg",
            "is_mature": False,
            "custom_tags": ["irl", "news"],
        },
        {
            "broadcaster_user_id": 789,
            "slug": "cityhall",
            "session_title": "City briefing",
            "category": {"id": 12, "name": "Games"},
            "viewer_count": 42,
            "language": "en",
        },
        {"broadcaster_user_id": 1, "slug": ""},  # unusable: no identity
    ],
    "pagination": {"next_cursor": "abc"},
}


def _creds(**over) -> dict:
    base = {"client_id": "id", "client_secret": "secret"}
    return {**base, **over}


def _client(
    categories: dict | None = None,
    streams: dict | None = None,
    seen: list | None = None,
    token_hook=None,
) -> httpx.Client:
    """Transport stub. Everything routes through `seen` so tests can assert
    on request params, and `token_hook` can count/inspect token refreshes."""

    def route(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if seen is not None:
            seen.append((path, request.url.params))
        if path.endswith("/oauth2/token"):
            if token_hook is not None:
                token_hook()
            return httpx.Response(200, json=TOKEN)
        if path.endswith("/public/v1/categories"):
            body = CATEGORIES if categories is None else categories
            return httpx.Response(200, json=body)
        if path.endswith("/public/v2/livestreams"):
            body = LIVESTREAMS if streams is None else streams
            return httpx.Response(200, json=body)
        if path.endswith("/public/v1/users/livestreams"):
            body = LIVESTREAMS if streams is None else streams
            return httpx.Response(200, json=body)
        return httpx.Response(404, json={})

    return httpx.Client(transport=httpx.MockTransport(route))


def test_maps_streams_to_normalized_records():
    adapter = KickAdapter(**_creds(client=_client()))
    records = adapter.search("just chatting")
    assert len(records) == 2  # identity-less item dropped
    first = Stream(**records[0])
    assert first.platform == "kick"
    assert first.platform_stream_id == "123456"
    assert first.id == "kick-123456"
    assert first.channel_name == "riverwatch"
    assert first.title == "Flood watch live"
    assert first.viewer_count == 4821
    assert first.category == "Just Chatting"
    # First-class field since Sprint 8.1 so the language filter works.
    assert first.language == "en"
    assert first.tags == ["irl", "news"]
    assert first.thumbnail_url == "https://kick.com/thumb/river-640x360.jpg"
    assert first.live_status == "live"
    # Embed parent is explicit and configurable, never guessed at runtime.
    assert first.embed_url == "https://player.kick.com/riverwatch?parent=localhost"
    assert first.embed_supported is True
    assert first.source_url == "https://kick.com/riverwatch"
    # Geo is absent from Kick entirely — see docs/kick-feasibility.md.
    assert first.location_text is None
    assert first.latitude is None


def test_search_uses_category_q_then_livestreams():
    seen: list = []
    adapter = KickAdapter(
        **_creds(max_categories=2), client=_client(seen=seen)
    )
    assert len(adapter.search("flood")) == 2
    categories = next(p for path, p in seen if path.endswith("categories"))
    streams = next(p for path, p in seen if path.endswith("livestreams"))
    assert categories.get("q") == "flood"
    assert streams.get_list("category_id") == ["27", "12"]


def test_no_categories_falls_back_to_top_live():
    seen: list = []
    adapter = KickAdapter(**_creds(), client=_client(categories={"data": []}, seen=seen))
    assert len(adapter.search("zzzznothing")) == 2
    streams = next(p for path, p in seen if path.endswith("livestreams"))
    assert "category_id" not in streams


def test_reverify_confirms_live_and_offline():
    adapter = KickAdapter(**_creds(), client=_client())
    verdicts = adapter.reverify(["123456", "999"])
    assert verdicts["123456"] is not None
    assert verdicts["123456"]["platform_stream_id"] == "123456"
    assert verdicts["999"] is None


def test_token_cached_across_searches():
    refreshes = {"n": 0}
    adapter = KickAdapter(
        **_creds(), client=_client(token_hook=lambda: refreshes.__setitem__("n", refreshes["n"] + 1))
    )
    adapter.search("a")
    adapter.search("b")
    assert refreshes["n"] == 1


def test_401_refreshes_and_retries():
    refreshes = {"n": 0}
    states = {"streams": 0}

    def route(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/oauth2/token"):
            refreshes["n"] += 1
            return httpx.Response(200, json=TOKEN)
        if path.endswith("/public/v1/categories"):
            return httpx.Response(200, json=CATEGORIES)
        if path.endswith("/public/v2/livestreams"):
            states["streams"] += 1
            if states["streams"] == 1:
                return httpx.Response(401, json={})
            return httpx.Response(200, json=LIVESTREAMS)
        return httpx.Response(404, json={})

    adapter = KickAdapter(
        **_creds(), client=httpx.Client(transport=httpx.MockTransport(route))
    )
    assert len(adapter.search("x")) == 2
    assert refreshes["n"] == 2


def test_rate_limit_raises_controlled_error():
    def route(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/oauth2/token"):
            return httpx.Response(200, json=TOKEN)
        return httpx.Response(429, json={})

    adapter = KickAdapter(
        **_creds(), client=httpx.Client(transport=httpx.MockTransport(route))
    )
    with pytest.raises(Exception, match="429"):
        adapter.search("x")


def test_missing_credentials_raise_config_error():
    with pytest.raises(AdapterConfigError):
        KickAdapter(client_id="", client_secret="s")
    with pytest.raises(AdapterConfigError):
        KickAdapter(client_id="id", client_secret="")


def test_field_shape_variants_still_map():
    """Older/newer revisions: title key and nested identity differ."""
    legacy = {
        "channel_id": 555,
        "user_login": "legacy",
        "title": "Legacy key titles",
        "stream_thumbnail": "https://kick.com/legacy.jpg",
        "viewers": 10,
        "tags": ["legacy"],
        "language_code": "en",
        "category_name": "IRL",
    }
    adapter = KickAdapter(**_creds(client=_client()))
    stream = Stream(**adapter._map(legacy))
    assert stream.platform_stream_id == "555"
    assert stream.channel_name == "legacy"
    assert stream.title == "Legacy key titles"
    assert stream.viewer_count == 10
    assert stream.category == "IRL"
    assert stream.language == "en"
    assert stream.tags == ["legacy"]
    assert stream.thumbnail_url == "https://kick.com/legacy.jpg"


def test_factory_matrix(monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", "yt")
    monkeypatch.setattr(settings, "twitch_client_id", "id")
    monkeypatch.setattr(settings, "twitch_client_secret", "s")
    monkeypatch.setattr(settings, "kick_client_id", "kid")
    monkeypatch.setattr(settings, "kick_client_secret", "ks")
    assert [a.platform for a in build_default_adapters()] == [
        "youtube",
        "twitch",
        "kick",
    ]

    monkeypatch.setattr(settings, "youtube_api_key", "")
    monkeypatch.setattr(settings, "twitch_client_id", "")
    monkeypatch.setattr(settings, "twitch_client_secret", "")
    assert [a.platform for a in build_default_adapters()] == ["kick"]

    monkeypatch.setattr(settings, "kick_client_id", "")
    monkeypatch.setattr(settings, "kick_client_secret", "")
    assert [a.platform for a in build_default_adapters()] == ["fake", "twitch"]


def test_service_validates_kick_records():
    service = SearchService(adapters=[KickAdapter(**_creds(), client=_client())])
    res = service.search("flood")
    assert res.count == 2
    assert {s.platform for s in res.results} == {"kick"}


def test_embed_parent_is_configurable():
    record = KickAdapter(
        client_id="id", client_secret="s", embed_parent="streamsearch.example"
    )._map({"broadcaster_user_id": 1, "slug": "chan", "session_title": "T"})
    assert "parent=streamsearch.example" in record["embed_url"]
