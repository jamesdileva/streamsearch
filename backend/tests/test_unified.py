"""Unified cross-platform results (Sprint 5.3 verification).

One ranked set, no platform automatically dominating; platform / sort /
location filters behave; invalid sorts are rejected; filter variants don't
share cache entries.
"""

from fastapi.testclient import TestClient

from app.adapters.base import FakeAdapter
from app.adapters.fake_twitch import FakeTwitchAdapter
from app.main import app
from app.models.stream import Stream
from app.search.scoring import rank_streams, sort_streams
from app.services.cache import SearchCache
from app.services.search import SearchService

client = TestClient(app)


def _s(**over) -> Stream:
    base = {
        "id": "s",
        "platform": "fake",
        "platform_stream_id": "s",
        "live_status": "live",
        "freshness": "fresh",
    }
    return Stream(**{**base, **over})


def _mixed_service() -> SearchService:
    return SearchService(adapters=[FakeAdapter(), FakeTwitchAdapter()])


def test_no_platform_automatically_dominates():
    # Identical content on two platforms: same score, stable adapter order.
    a = _s(id="a", platform="fake", title="Wildfire update")
    b = _s(id="b", platform="twitch", title="Wildfire update")
    tied = rank_streams([a, b], "wildfire")
    assert tied[0].score == tied[1].score
    assert [s.id for s in tied] == ["a", "b"]

    ranked = _mixed_service().search("wildfire")
    assert ranked.count == 3
    assert {s.platform for s in ranked.results} == {"fake", "twitch"}


def test_platform_filter():
    service = _mixed_service()
    twitch = service.search("wildfire", platform="twitch")
    assert twitch.count == 2
    assert {s.platform for s in twitch.results} == {"twitch"}
    assert service.search("wildfire", platform="fake").count == 1
    assert service.search("wildfire", platform="TWITCH").count == 2
    assert service.search("wildfire", platform="nope").count == 0


def test_sort_newest_nulls_last_ended_lastest():
    old = _s(id="old", title="t", started_at="2026-10-01T00:00:00Z")
    new = _s(id="new", title="t", started_at="2026-10-06T00:00:00Z")
    none = _s(id="none", title="t", started_at=None)
    ended = _s(
        id="ended", title="t", live_status="ended",
        started_at="2026-10-07T00:00:00Z",
    )
    ordered = sort_streams([old, ended, none, new], "newest")
    assert [s.id for s in ordered] == ["new", "old", "none", "ended"]


def test_sort_viewers_nulls_last():
    big = _s(id="big", title="t", viewer_count=100)
    small = _s(id="small", title="t", viewer_count=5)
    none = _s(id="none", title="t", viewer_count=None)
    ordered = sort_streams([none, small, big], "viewers")
    assert [s.id for s in ordered] == ["big", "small", "none"]


def test_has_location_filter():
    service = _mixed_service()
    assert service.search("wildfire", has_location=True).count == 0
    loc = _s(id="loc", title="Wildfire update", location_text="Los Angeles, CA")
    noloc = _s(id="noloc", title="Wildfire update")
    ranked = rank_streams([noloc, loc], "wildfire")
    kept = [s for s in ranked if s.location_text]
    assert [s.id for s in kept] == ["loc"]


def test_filter_variants_use_separate_cache_entries():
    key_default = SearchCache.key(
        "wildfire", ("fake", "twitch"), "all", "relevance", False
    )
    assert SearchCache.key("wildfire", ("fake", "twitch")) == key_default
    assert (
        SearchCache.key("wildfire", ("fake", "twitch"), "twitch", "relevance", False)
        != key_default
    )
    assert (
        SearchCache.key("wildfire", ("fake", "twitch"), "all", "viewers", False)
        != key_default
    )


def test_api_platform_sort_location_params():
    assert {s["platform"] for s in client.get(
        "/api/search", params={"q": "wildfire", "platform": "twitch"}
    ).json()["results"]} == {"twitch"}
    viewers = client.get(
        "/api/search", params={"q": "wildfire", "sort": "viewers"}
    ).json()["results"]
    counts = [s["viewer_count"] for s in viewers]
    assert counts == sorted(
        [c for c in counts if c is not None], reverse=True
    ) + [c for c in counts if c is None]
    assert client.get(
        "/api/search", params={"q": "wildfire", "has_location": "true"}
    ).json()["count"] == 0


def test_api_unknown_sort_is_422():
    r = client.get("/api/search", params={"q": "wildfire", "sort": "bogus"})
    assert r.status_code == 422
