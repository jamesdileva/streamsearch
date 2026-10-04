"""Normalization tests (Sprint 3.2 verification).

Equivalent queries must produce identical scores and order — the roadmap's
"run equivalent queries and compare result quality", automated. The synonym
map stays pinned small: no hand-built ontology.
"""

from app.models.stream import Stream
from app.search.normalize import MAX_SYNONYMS, SYNONYMS, normalized_text, tokens
from app.search.scoring import rank_streams, score_stream


def _s(**over) -> Stream:
    base = {
        "id": "s",
        "platform": "fake",
        "platform_stream_id": "s",
        "live_status": "live",
        "freshness": "fresh",
    }
    return Stream(**{**base, **over})


def test_case_punctuation_whitespace_equivalent():
    s = _s(title="Wildfire Los Angeles")
    variants = ["wildfire los angeles", "  WILDFIRE   los Angeles!! ", "Wildfire, Los Angeles"]
    totals = {score_stream(s, v).total for v in variants}
    assert len(totals) == 1


def test_plural_synonyms_equivalent():
    pairs = [
        ("wildfires", "wildfire"),
        ("earthquakes", "earthquake"),
        ("storms", "storm"),
    ]
    for plural, single in pairs:
        s = _s(title=f"{single.title()} response live")
        assert score_stream(s, plural).total == score_stream(s, single).total


def test_la_expands_to_los_angeles():
    s = _s(title="Fire near Los Angeles", location_text="Los Angeles, CA")
    assert score_stream(s, "la wildfire").total == score_stream(
        s, "los angeles wildfire"
    ).total


def test_normalized_text_form():
    assert normalized_text("  Wildfire!! NEAR   LA ") == "wildfire near la"


def test_empty_query_has_no_tokens():
    assert tokens("  !!!  ") == set()


def test_synonym_map_stays_small_and_explicit():
    assert len(SYNONYMS) <= MAX_SYNONYMS
    assert SYNONYMS["la"] == "los angeles"
    assert SYNONYMS["wildfires"] == "wildfire"


def test_equivalent_queries_rank_identically():
    streams = [
        _s(id="a", title="Wildfire Los Angeles live"),
        _s(id="b", title="Los Angeles morning news"),
        _s(id="c", title="Cooking show marathon"),
    ]
    first = [s.id for s in rank_streams(streams, "WILDFIRES near LA!!")]
    second = [s.id for s in rank_streams(streams, "wildfire near los angeles")]
    assert first == second == ["a", "b", "c"]


def test_no_stemming_rules_misfire():
    # "news" must not become "new": only explicit map entries expand.
    assert "new" not in tokens("news")
    assert tokens("news") == {"news"}
