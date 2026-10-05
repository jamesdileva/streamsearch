"""Location-aware search tests (Sprint 3.3 verification).

Matrix: known location, unknown location, location with no matching
streams, location plus topic. All mocked — no network, no key.
"""

import httpx

from app.adapters.base import BasePlatformAdapter
from app.adapters.youtube import YouTubeAdapter
from app.models.stream import Stream
from app.search.location import MAX_PLACES, PLACES, parse_location, place_coords
from app.search.scoring import rank_streams
from app.services.search import SearchService


def _s(**over) -> Stream:
    base = {
        "id": "s",
        "platform": "fake",
        "platform_stream_id": "s",
        "live_status": "live",
        "freshness": "fresh",
    }
    return Stream(**{**base, **over})


def test_near_pattern_splits_topic_and_place():
    parsed = parse_location("wildfire near Los Angeles")
    assert parsed.topic == "wildfire"
    assert parsed.place == "los angeles"
    assert parsed.place_attempt is None


def test_in_pattern_and_suffix_forms():
    assert parse_location("storm in Florida").place == "florida"
    assert parse_location("storm florida").place == "florida"
    assert parse_location("concert Tokyo").place == "tokyo"
    assert parse_location("concert tokyo").topic == "concert"


def test_case_punctuation_and_synonyms_normalized():
    parsed = parse_location("STORMS near NYC!!")
    assert parsed.topic == "storm"
    assert parsed.place == "new york"


def test_unknown_location_stays_in_topic():
    parsed = parse_location("wildfire near nowhereville")
    assert parsed.place is None
    assert parsed.place_attempt == "nowhereville"
    assert parsed.topic == "wildfire near nowhereville"


def test_no_location_leaves_query_intact():
    parsed = parse_location("just a concert")
    assert parsed.place is None
    assert parsed.place_attempt is None
    assert parsed.topic == "just a concert"


def test_bare_place_gives_empty_topic():
    parsed = parse_location("near los angeles")
    assert parsed.place == "los angeles"
    assert parsed.topic == ""


def test_gazetteer_stays_small_with_coords():
    assert len(PLACES) <= MAX_PLACES
    assert place_coords("los angeles") == (34.05, -118.24)
    assert place_coords("nowhereville") is None


def test_place_match_outranks_same_text_without_it():
    la = _s(id="la", title="Wildfire update", location_text="Los Angeles, CA")
    tx = _s(id="tx", title="Wildfire update", location_text="Austin, Texas")
    none = _s(id="none", title="Wildfire update")
    ranked = rank_streams([tx, none, la], "wildfire", place="los angeles")
    assert [s.id for s in ranked] == ["la", "tx", "none"]


def test_location_with_no_matching_streams_keeps_order():
    a = _s(id="a", title="Wildfire update", location_text="Austin, Texas")
    b = _s(id="b", title="Wildfire update", location_text="Miami, Florida")
    ranked = rank_streams([a, b], "wildfire", place="tokyo")
    assert [s.id for s in ranked] == ["a", "b"]


class _StubAdapter(BasePlatformAdapter):
    platform = "stub"

    def __init__(self, records: list[dict]):
        self.records = records

    def search(self, query: str) -> list[dict]:
        return self.records


def test_service_prefers_place_match_end_to_end():
    records = [
        {"id": "tx", "platform": "stub", "platform_stream_id": "tx",
         "title": "Wildfire update", "location_text": "Austin, Texas",
         "live_status": "live"},
        {"id": "la", "platform": "stub", "platform_stream_id": "la",
         "title": "Wildfire update", "location_text": "Los Angeles, CA",
         "live_status": "live"},
    ]
    res = SearchService(adapters=[_StubAdapter(records)]).search(
        "wildfire near los angeles"
    )
    assert [s.id for s in res.results] == ["la", "tx"]


def _youtube_client(captured: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if "youtube/v3/search" in request.url.path:
            captured.update(dict(request.url.params))
            return httpx.Response(200, json={"items": []})
        return httpx.Response(404, json={})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_youtube_sends_geo_for_known_place():
    captured: dict = {}
    adapter = YouTubeAdapter(api_key="k", client=_youtube_client(captured))
    assert adapter.search("wildfire near los angeles") == []
    assert captured.get("location") == "34.05,-118.24"
    assert captured.get("locationRadius") == "100km"


def test_youtube_skips_geo_without_place():
    captured: dict = {}
    adapter = YouTubeAdapter(api_key="k", client=_youtube_client(captured))
    assert adapter.search("wildfire near nowhereville") == []
    assert "location" not in captured
