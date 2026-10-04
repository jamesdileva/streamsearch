"""YouTube adapter tests — all mocked, no network, no real key (Sprint 1.2).

Real-query verification is deferred until YOUTUBE_API_KEY exists;
see worklog Sprint 1.2 for the smoke procedure.
"""

import httpx
import pytest

from app.adapters.base import AdapterConfigError, AdapterError, FakeAdapter
from app.adapters.youtube import YouTubeAdapter
from app.config import settings
from app.models.stream import Stream
from app.services.search import SearchService, build_default_adapters

SEARCH_FIXTURE = {
    "items": [
        {
            "id": {"videoId": "vid-live"},
            "snippet": {
                "channelTitle": "Live Channel",
                "title": "Wildfire live coverage",
                "liveBroadcastContent": "live",
            },
        },
        {
            "id": {"videoId": "vid-upcoming"},
            "snippet": {
                "channelTitle": "Later Channel",
                "title": "Upcoming show",
                "liveBroadcastContent": "upcoming",
            },
        },
        {
            "id": {"videoId": "vid-gone"},
            "snippet": {
                "channelTitle": "Gone Channel",
                "title": "Removed video",
                "liveBroadcastContent": "none",
            },
        },
    ]
}

VIDEOS_FIXTURE = {
    "items": [
        {
            "id": "vid-live",
            "snippet": {
                "channelId": "chan-live",
                "channelTitle": "Live Channel",
                "title": "Wildfire live coverage",
                "description": "Live from the ridge.",
                "thumbnails": {
                    "default": {"url": "https://img/default.jpg"},
                    "high": {"url": "https://img/high.jpg"},
                },
                "categoryId": "25",
                "tags": ["wildfire", "live"],
                "liveBroadcastContent": "live",
            },
            "liveStreamingDetails": {
                "actualStartTime": "2026-10-03T00:00:00Z",
                "concurrentViewers": "1234",
            },
            "recordingDetails": {
                "location": {"latitude": 34.05, "longitude": -118.24},
                "locationDescription": "Los Angeles, CA",
            },
        },
        {
            "id": "vid-upcoming",
            "snippet": {
                "channelId": "chan-later",
                "channelTitle": "Later Channel",
                "title": "Upcoming show",
                "description": "Starts soon.",
                "thumbnails": {},
                "liveBroadcastContent": "upcoming",
            },
        },
    ]
}


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _ok_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if "youtube/v3/search" in request.url.path:
            return httpx.Response(200, json=SEARCH_FIXTURE)
        if "youtube/v3/videos" in request.url.path:
            return httpx.Response(200, json=VIDEOS_FIXTURE)
        return httpx.Response(404, json={})

    return _client(handler)


def test_maps_live_broadcast_to_normalized_record():
    adapter = YouTubeAdapter(api_key="test-key", client=_ok_client())
    (raw,) = [r for r in adapter.search("wildfire") if r["platform_stream_id"] == "vid-live"]
    stream = Stream(**raw)  # must validate against the normalized model
    assert stream.platform == "youtube"
    assert stream.id == "youtube-vid-live"
    assert stream.channel_name == "Live Channel"
    assert stream.title == "Wildfire live coverage"
    assert stream.thumbnail_url == "https://img/high.jpg"
    assert stream.source_url == "https://www.youtube.com/watch?v=vid-live"
    assert stream.embed_url == "https://www.youtube.com/embed/vid-live"
    assert stream.embed_supported is True
    assert stream.live_status == "live"
    assert stream.viewer_count == 1234
    assert stream.category == "25"
    assert stream.tags == ["wildfire", "live"]
    assert stream.latitude == 34.05
    assert stream.longitude == -118.24
    assert stream.location_text == "Los Angeles, CA"
    assert stream.metadata == {"liveBroadcastContent": "live"}


def test_non_live_and_missing_details_filtered_out():
    adapter = YouTubeAdapter(api_key="test-key", client=_ok_client())
    results = adapter.search("wildfire")
    assert [r["platform_stream_id"] for r in results] == ["vid-live"]


def test_no_candidates_skips_videos_call():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"items": []})

    adapter = YouTubeAdapter(api_key="test-key", client=_client(handler))
    assert adapter.search("nothing") == []
    assert len(calls) == 1 and "search" in calls[0]


def test_missing_key_raises_config_error():
    with pytest.raises(AdapterConfigError):
        YouTubeAdapter(api_key="")
    assert issubclass(AdapterConfigError, AdapterError)


def test_http_500_raises_adapter_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    with pytest.raises(AdapterError, match="status 500"):
        YouTubeAdapter(api_key="k", client=_client(handler)).search("x")


def test_403_raises_quota_error_without_leaking_key():
    # The key travels as a `key=` query param by YouTube API design (over
    # HTTPS); it must never land in the raised error message.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={})

    with pytest.raises(AdapterError, match="403") as exc_info:
        YouTubeAdapter(api_key="secret-key", client=_client(handler)).search("x")
    assert "secret-key" not in str(exc_info.value)


def test_malformed_json_raises_adapter_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    with pytest.raises(AdapterError, match="malformed"):
        YouTubeAdapter(api_key="k", client=_client(handler)).search("x")


def test_max_results_clamped_to_budget():
    assert YouTubeAdapter(api_key="k", max_results=99).max_results == 25
    assert YouTubeAdapter(api_key="k", max_results=0).max_results == 1


def test_service_factory_uses_fake_without_key(monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", "")
    (adapter,) = build_default_adapters()
    assert isinstance(adapter, FakeAdapter)


def test_service_factory_uses_youtube_with_key(monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", "k")
    (adapter,) = build_default_adapters()
    assert isinstance(adapter, YouTubeAdapter)


def test_search_service_validates_adapter_records():
    service = SearchService(adapters=[YouTubeAdapter(api_key="k", client=_ok_client())])
    res = service.search("wildfire")
    assert res.query == "wildfire"
    assert res.count == 1
    assert res.results[0].platform == "youtube"


def test_youtube_raw_records_contain_only_normalized_fields():
    # No raw YouTube shapes may reach the API/UI boundary.
    adapter = YouTubeAdapter(api_key="k", client=_ok_client())
    records = adapter.search("wildfire")
    assert records, "expected at least one record to inspect"
    for raw in records:
        assert set(raw) <= set(Stream.model_fields)
        Stream(**raw)
