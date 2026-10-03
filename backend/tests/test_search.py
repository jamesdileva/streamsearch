from fastapi.testclient import TestClient

from app.adapters.base import FakeAdapter
from app.main import app
from app.services.search import SearchService

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
