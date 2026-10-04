import pytest
from fastapi.testclient import TestClient

from app.adapters.base import AdapterError, BasePlatformAdapter, FakeAdapter
from app.main import app
from app.models.stream import Stream
from app.services.search import SearchService, get_search_service

client = TestClient(app)


def test_search_returns_normalized_fake_stream():
    r = client.get("/api/search", params={"q": "wildfire"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "wildfire"
    assert body["count"] == 1
    (stream,) = body["results"]
    assert stream["platform"] == "fake"
    assert stream["live_status"] == "live"
    assert "wildfire" in stream["title"]
    assert stream["channel_name"] == "Skeleton Channel"
    assert stream["source_url"] == "https://example.com/watch/fake-1"


def test_search_empty_query_is_422_envelope():
    r = client.get("/api/search", params={"q": "   "})
    assert r.status_code == 422
    assert r.json() == {
        "error": {"code": 422, "message": "query must not be empty"}
    }


def test_unknown_route_is_framework_404():
    # Framework-level 404 keeps the Starlette default; the envelope in
    # errors.py covers errors raised by our routes (e.g. 422 above).
    r = client.get("/api/nope")
    assert r.status_code == 404


def test_fake_adapter_maps_to_stream_model():
    res = SearchService(adapters=[FakeAdapter()]).search("storm")
    assert res.query == "storm"
    assert res.count == 1
    assert res.results[0].platform == "fake"
    assert res.results[0].live_status == "live"


class _FailingAdapter(BasePlatformAdapter):
    platform = "failing"

    def search(self, query: str) -> list[dict]:
        raise AdapterError("boom")


def test_adapter_failure_is_502_envelope_without_internals():
    app.dependency_overrides[get_search_service] = lambda: SearchService(
        adapters=[_FailingAdapter()]
    )
    try:
        r = client.get("/api/search", params={"q": "wildfire"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 502
    assert r.json() == {
        "error": {"code": 502, "message": "live search temporarily unavailable"}
    }


@pytest.mark.parametrize("query", ["news", "wildfire", "storm", "gaming", "concert"])
def test_five_query_sweep_returns_normalized_shape(query: str):
    # Automated half of the roadmap 5-query check (mocked adapter).
    # Title/thumbnail/link-vs-source matching needs a real key — deferred.
    r = client.get("/api/search", params={"q": query})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == query
    assert body["count"] == len(body["results"])
    for stream in body["results"]:
        assert set(stream) <= set(Stream.model_fields)
        assert stream["platform"]
        assert isinstance(stream["metadata"], dict)


def test_search_response_contains_no_raw_platform_fields():
    body = client.get("/api/search", params={"q": "wildfire"}).json()
    assert body["results"], "expected at least one result to inspect"
    for stream in body["results"]:
        assert set(stream) <= set(Stream.model_fields)
        for marker in ("snippet", "liveStreamingDetails", "etag", "kind", "pageInfo"):
            assert marker not in stream
