"""Deterministic relevance tests (Sprint 3.1 verification).

Small manually labeled set for query "wildfire los angeles":
- relevant: exact title match, live + fresh
- partially relevant: token/description/tag/location matches
- irrelevant: no textual overlap
Plus: freshness tiebreaks, ended demotion, viewers as tiebreak-only,
configurable weights, stable ties, empty query.
"""

from app.adapters.base import BasePlatformAdapter
from app.models.stream import Stream
from app.search.scoring import (
    DEFAULT_WEIGHTS,
    Weights,
    rank_streams,
    score_stream,
)
from app.services.search import SearchService

Q = "wildfire los angeles"


def _s(**over) -> Stream:
    base = {
        "id": "s",
        "platform": "fake",
        "platform_stream_id": "s",
        "live_status": "live",
        "freshness": "fresh",
    }
    return Stream(**{**base, **over})


def test_exact_title_beats_token_beats_irrelevant():
    exact = _s(id="exact", title="Wildfire Los Angeles")
    token = _s(id="token", title="Los Angeles morning news")
    # Shares "los angeles" tokens but not the full phrase.
    assert "wildfire" not in token.title.lower()
    off = _s(id="off", title="Cooking show marathon")
    ranked = rank_streams([off, token, exact], Q)
    assert [s.id for s in ranked] == ["exact", "token", "off"]
    assert ranked[0].score and ranked[0].score > ranked[1].score > ranked[2].score


def test_description_only_match_beats_nothing():
    desc = _s(id="desc", title="Evening news", description="Wildfire crews respond")
    off = _s(id="off", title="Evening news", description="Weather and sports")
    ranked = rank_streams([off, desc], Q)
    assert [s.id for s in ranked] == ["desc", "off"]


def test_tag_and_category_match_lifts():
    tagged = _s(id="tagged", title="Evening news", tags=["wildfire"])
    cat = _s(id="cat", title="Evening news", category="wildfire")
    off = _s(id="off", title="Evening news")
    ranked = rank_streams([off, tagged, cat], Q)
    assert ranked[0].id in ("tagged", "cat")
    assert ranked[-1].id == "off"


def test_location_match_lifts():
    local = _s(id="local", title="Evening news", location_text="Wildfire County")
    off = _s(id="off", title="Evening news")
    assert score_stream(local, Q).total > score_stream(off, Q).total


def test_freshness_breaks_text_ties():
    fresh = _s(id="fresh", title="Evening news", freshness="fresh")
    stale = _s(id="stale", title="Evening news", freshness="stale")
    ranked = rank_streams([stale, fresh], Q)
    assert [s.id for s in ranked] == ["fresh", "stale"]


def test_ended_exact_match_demoted_below_live_weak_match():
    ended = _s(
        id="ended",
        title="Wildfire",
        live_status="ended",
        freshness="ended",
    )
    weak = _s(id="weak", title="Evening news", description="wildfire update")
    ranked = rank_streams([ended, weak], Q)
    assert [s.id for s in ranked] == ["weak", "ended"]


def test_viewers_break_ties_but_never_beat_title():
    popular = _s(id="popular", title="Evening news", viewer_count=100000)
    niche = _s(id="niche", title="Evening news", viewer_count=3)
    assert score_stream(popular, Q).total > score_stream(niche, Q).total

    exact_niche = _s(id="exact", title="Wildfire Los Angeles", viewer_count=1)
    off_popular = _s(id="off", title="Cooking show", viewer_count=1000000)
    ranked = rank_streams([off_popular, exact_niche], Q)
    assert [s.id for s in ranked] == ["exact", "off"]


def test_custom_weights_respected():
    s = _s(id="s", title="Wildfire Los Angeles")
    full = score_stream(s, Q).total
    muted = score_stream(s, Q, Weights(title_exact=0.0)).total
    assert muted < full
    assert Weights() == DEFAULT_WEIGHTS


def test_stable_order_for_ties():
    a = _s(id="a", title="Evening news")
    b = _s(id="b", title="Evening news")
    assert [s.id for s in rank_streams([a, b], Q)] == ["a", "b"]


def test_empty_query_scores_zero():
    s = _s(id="s", title="Wildfire")
    assert score_stream(s, "   ").total == 0.0


class _StubAdapter(BasePlatformAdapter):
    platform = "stub"

    def __init__(self, records: list[dict]):
        self.records = records

    def search(self, query: str) -> list[dict]:
        return self.records


def test_service_ranks_across_adapters():
    records = [
        {"id": "weak", "platform": "stub", "platform_stream_id": "w",
         "title": "Evening news", "live_status": "live", "freshness": "fresh"},
        {"id": "exact", "platform": "stub", "platform_stream_id": "e",
         "title": "Wildfire", "live_status": "live", "freshness": "fresh"},
    ]
    res = SearchService(adapters=[_StubAdapter(records)]).search("wildfire")
    assert [s.id for s in res.results] == ["exact", "weak"]
    assert res.results[0].score and res.results[0].score > 0
