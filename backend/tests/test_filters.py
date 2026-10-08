"""Language + min-viewer filters (Sprint 8.1 verification).

Language is "where available": adapters report it when the platform does
and it stays absent otherwise. A viewer floor excludes records with no
viewer data rather than silently passing them.
"""

import httpx
from fastapi.testclient import TestClient

from app.adapters.base import BasePlatformAdapter
from app.adapters.youtube import YouTubeAdapter, _language
from app.main import app
from app.models.stream import Stream
from app.search.scoring import SORTS  # noqa: F401  (route guard reference)
from app.services.cache import SearchCache
from app.services.search import SearchService, get_search_service

client = TestClient(app)


def _s(**over) -> Stream:
    base = {
        "id": "s",
        "platform": "stub",
        "platform_stream_id": "s",
        "channel_id": "c",
        "channel_name": "Chan",
        "live_status": "live",
        "freshness": "fresh",
    }
    return Stream(**{**base, **over})


class _LangStub(BasePlatformAdapter):
    platform = "stub"

    def search(self, query: str) -> list[dict]:
        return [
            {"id": "en1", "platform": "stub", "platform_stream_id": "en1",
             "title": "English news", "language": "en", "viewer_count": 50,
             "live_status": "live"},
            {"id": "ja1", "platform": "stub", "platform_stream_id": "ja1",
             "title": "Japanese news", "language": "ja", "viewer_count": 5000,
             "live_status": "live"},
            {"id": "none1", "platform": "stub", "platform_stream_id": "none1",
             "title": "Unknown language", "language": None, "viewer_count": 900,
             "live_status": "live"},
        ]


# --- language --------------------------------------------------------------


def test_language_helper_extracts_primary_subtag():
    assert _language({"defaultAudioLanguage": "en-US"}) == "en"
    assert _language({"defaultLanguage": "JA"}) == "ja"
    assert _language({"defaultAudioLanguage": "--music"}) is None
    assert _language({}) is None


def test_youtube_adapter_populates_language():
    def handler(request: httpx.Request) -> httpx.Response:
        if "youtube/v3/search" in request.url.path:
            return httpx.Response(200, json={"items": [
                {"id": {"videoId": "v1"}, "snippet": {
                    "channelTitle": "C", "title": "T",
                    "liveBroadcastContent": "live",
                    "defaultAudioLanguage": "es-419"}}]})
        return httpx.Response(200, json={"items": [
            {"id": "v1", "snippet": {"channelId": "c", "channelTitle": "C",
                                     "title": "T", "defaultAudioLanguage": "es-419"},
             "liveStreamingDetails": {"actualStartTime": "2026-10-08T00:00:00Z",
                                      "concurrentViewers": "10"}}]})

    adapter = YouTubeAdapter(api_key="k", client=httpx.Client(
        transport=httpx.MockTransport(handler)))
    (record,) = adapter.search("x")
    assert record["language"] == "es"


def test_twitch_adapter_populates_language():
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in request.url.path:
            return httpx.Response(200, json={"access_token": "t",
                                             "expires_in": 3600})
        if "search/categories" in request.url.path:
            return httpx.Response(200, json={"data": [{"id": "1"}]})
        return httpx.Response(200, json={"data": [
            {"id": "9", "user_id": "u1", "user_login": "chan", "type": "live",
             "title": "T", "language": "DE", "game_name": "G",
             "viewer_count": 7}]})

    from app.adapters.twitch import TwitchAdapter

    adapter = TwitchAdapter(client_id="i", client_secret="s",
                            client=httpx.Client(transport=httpx.MockTransport(handler)))
    (record,) = adapter.search("x")
    assert record["language"] == "de"


def test_language_filter_matches_exact_and_case_insensitive():
    service = SearchService(adapters=[_LangStub()],
                            cache=SearchCache(ttl_seconds=60))
    en = service.search("news", language="en")
    assert [s.id for s in en.results] == ["en1"]
    assert service.search("news", language="EN").count == 1


def test_language_filter_excludes_unknown_by_default():
    # "where available": an unknown language must not masquerade as a match.
    service = SearchService(adapters=[_LangStub()],
                            cache=SearchCache(ttl_seconds=60))
    assert service.search("news", language="fr").count == 0
    assert service.search("news", language="ja").count == 1


def test_no_language_filter_returns_everything():
    service = SearchService(adapters=[_LangStub()],
                            cache=SearchCache(ttl_seconds=60))
    assert service.search("news").count == 3


# --- min viewers -----------------------------------------------------------


def test_min_viewers_filters_and_excludes_unknown():
    service = SearchService(adapters=[_LangStub()],
                            cache=SearchCache(ttl_seconds=60))
    kept = [s.id for s in service.search("news", min_viewers=100).results]
    # 50 excluded (below floor); None-viewer record excluded (can't verify);
    # 5000 and 900 kept, ranked with the 5000 viewer ahead only via sort.
    assert set(kept) == {"ja1", "none1"}
    assert service.search("news", min_viewers=10_000).count == 0
    assert service.search("news", min_viewers=0).count == 3


def test_min_viewers_combines_with_other_filters():
    service = SearchService(adapters=[_LangStub()],
                            cache=SearchCache(ttl_seconds=60))
    res = service.search("news", language="ja", min_viewers=1)
    assert [s.id for s in res.results] == ["ja1"]


# --- API + cache -----------------------------------------------------------


def test_api_language_and_min_viewers_params():
    service = SearchService(adapters=[_LangStub()],
                            cache=SearchCache(ttl_seconds=60))
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        assert {s["id"] for s in client.get(
            "/api/search", params={"q": "news", "language": "ja"}
        ).json()["results"]} == {"ja1"}
        assert {s["id"] for s in client.get(
            "/api/search", params={"q": "news", "min_viewers": "5000"}
        ).json()["results"]} == {"ja1"}
    finally:
        app.dependency_overrides.clear()


def test_api_negative_min_viewers_is_422_envelope():
    # Same envelope shape as every other search error, not FastAPI's native
    # validation payload.
    r = client.get("/api/search", params={"q": "news", "min_viewers": "-1"})
    assert r.status_code == 422
    assert r.json() == {
        "error": {"code": 422, "message": "min_viewers must be between 0 and 10000000"}
    }


def test_api_absurd_min_viewers_is_422():
    assert (
        client.get("/api/search", params={"q": "news", "min_viewers": "99999999"}).status_code
        == 422
    )


def test_filter_variants_use_separate_cache_entries():
    base = SearchCache.key("q", ("stub",))
    assert SearchCache.key("q", ("stub",)) == base
    assert SearchCache.key("q", ("stub",), language="ja") != base
    assert SearchCache.key("q", ("stub",), min_viewers=100) != base
