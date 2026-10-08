"""Clustering experiment (Sprint 6.3 verification).

Hand-built set modeled on real-world patterns: a cross-platform wildfire
story, a concert, same-city distractors, plus edge pairs. Measures what the
union rule gets right, and — more valuably — exactly where it fails.
"""

from datetime import datetime, timezone

from app.models.stream import Stream
from app.search.clustering import (
    MAX_STOPWORDS,
    STOPWORDS,
    cluster_streams,
    linked,
    shared_entities,
)

D = datetime(2026, 10, 8, tzinfo=timezone.utc)


def _at(hour: int, minute: int = 0, day: int = 8) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=timezone.utc)


def _s(id: str, platform: str, channel: str, title: str,
       location: str | None, started: datetime | None) -> Stream:
    return Stream(
        id=id, platform=platform, platform_stream_id=id,
        channel_id=channel, channel_name=channel, title=title,
        live_status="live", freshness="fresh",
        location_text=location, started_at=started,
    )


def _scene() -> dict[str, Stream]:
    return {
        # Wildfire story: local news + Twitch watch + statewide roundup.
        "w1": _s("w1", "youtube", "la-news", "Downtown LA wildfire live coverage",
                 "Los Angeles, CA", _at(12)),
        "w2": _s("w2", "twitch", "lawatch", "LA fire watch", None, _at(12, 30)),
        "w3": _s("w3", "youtube", "nat-news", "California wildfires update",
                 "California", _at(10)),
        # Concert story: two wordings, same venue/city.
        "c1": _s("c1", "youtube", "venue", "Tokyo concert live", "Tokyo", _at(19)),
        "c2": _s("c2", "twitch", "fan", "Live from Tokyo Dome concert",
                 "Tokyo", _at(19, 5)),
        # Distractors: same places/times, different events.
        "d1": _s("d1", "youtube", "traffic", "LA traffic jam live",
                 "Los Angeles, CA", _at(12, 15)),
        "d2": _s("d2", "twitch", "weather", "California storm warning",
                 "California", _at(11)),
        "d3": _s("d3", "twitch", "gamer", "Tokyo gaming stream", "Tokyo", _at(20)),
    }


def _ids(cluster) -> set[str]:
    return {m.id for m in cluster.members}


def test_default_operating_point_groups_and_misfires():
    # Measured, not wished: at 0.4 the concert pair groups correctly, the
    # wildfire pair groups — but the same-city traffic distractor joins it
    # (shared city words alone clear the title gate on short titles).
    scene = _scene()
    groups = sorted(
        [sorted(_ids(c)) for c in cluster_streams(list(scene.values()))]
    )
    assert groups == [["c1", "c2"], ["d1", "w1", "w2"]]


def test_no_cross_story_or_other_distractor_merges():
    scene = _scene()
    clusters = cluster_streams(list(scene.values()))
    for cluster in clusters:
        ids = _ids(cluster)
        assert not ({"d2", "d3"} & ids)
        assert not ({"w1", "w2", "w3"} & ids and {"c1", "c2"} & ids)


def test_higher_threshold_fragments_everything():
    # The dilemma, measured: at 0.6 the false positive disappears — along
    # with both true groups. No threshold separates city-word overlap from
    # topic-word overlap on short titles; that needs lexical/semantic
    # equivalence (fire≈wildfire), i.e. 7.x work, not tuning here.
    scene = _scene()
    assert cluster_streams(list(scene.values()), title_threshold=0.6) == []


def test_statewide_roundup_stays_separate():
    # Ambiguous by design: a statewide roundup is arguably a different
    # (related) event from the local incident — and the lexical gap
    # (fire vs wildfire) plus region-vs-city wording keeps it apart.
    # Recorded here so the recall boundary is pinned, not silent.
    scene = _scene()
    clusters = cluster_streams(list(scene.values()))
    assert all("w3" not in _ids(c) for c in clusters)


def test_same_title_different_creators_cluster():
    a = _s("a", "youtube", "alpha", "Wildfire live", "Los Angeles, CA", _at(12))
    b = _s("b", "twitch", "beta", "Wildfire live", "Los Angeles, CA", _at(12, 20))
    assert linked(a, b)
    assert _ids(cluster_streams([a, b])[0]) == {"a", "b"}


def test_time_veto_splits_stale_rebroadcasts():
    a = _s("a", "youtube", "daily", "Daily briefing", "Chicago", _at(12, day=1))
    b = _s("b", "youtube", "daily", "Daily briefing", "Chicago", _at(12, day=4))
    assert not linked(a, b)
    assert cluster_streams([a, b]) == []


def test_cluster_notes_carry_topic_and_location():
    scene = _scene()
    clusters = cluster_streams(list(scene.values()))
    wildfire = next(c for c in clusters if "w1" in _ids(c))
    assert wildfire.topic_guess == ["angeles", "los", "downtown"]
    assert wildfire.location == "los angeles, ca"
    assert shared_entities(scene["w1"], scene["w3"]) == ["wildfire"]
    assert set(shared_entities(scene["w1"], scene["w2"])) >= {"los", "angeles"}


def test_stopwords_stay_small():
    assert len(STOPWORDS) <= MAX_STOPWORDS
