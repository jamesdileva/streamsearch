"""Advanced event detection — measurement (Sprint 13.2).

A labeled fixture set decides whether this ever ships. Recall = do known
same-event groups form? Precision = do unrelated broadcasts stay apart?
The negative cases are chosen to reproduce Sprint 6.3's actual failure mode
(same-city, different-event merges).
"""

from datetime import datetime, timezone

from app.models.stream import Stream
from app.search.events import detect_events, linked

H = timezone.utc


def _s(id: str, title: str, place: str | None, hour: int, minute: int = 0) -> Stream:
    started = datetime(2026, 10, 10, hour, minute, tzinfo=H) if hour >= 0 else None
    return Stream(
        id=id,
        platform="youtube",
        platform_stream_id=id,
        channel_name=f"ch-{id}",
        title=title,
        live_status="live",
        location_text=place,
        started_at=started,
    )


LA = "Los Angeles, CA"

RELATED = {
    # one wildfire event, three broadcasts
    "wildfire-la": [
        _s("w1", "LA County Fire wildfire live", LA, 12),
        _s("w2", "Wildfire response downtown LA", LA, 13),
        _s("w3", "LA wildfire scanner", LA, 14),
    ],
    # one concert event, two broadcasts
    "concert-tokyo": [
        _s("c1", "Tokyo concert live", "Tokyo", 19),
        _s("c2", "Live from Tokyo Dome concert", "Tokyo", 19, 15),
    ],
}

UNRELATED = {
    # Sprint 6.3's failure: same city, one has an event term, the other none
    "la-fire-vs-traffic": [
        _s("f1", "LA County Fire scanner live", LA, 12),
        _s("t1", "LA traffic jam live", LA, 12, 10),
    ],
    # same city and minute, clearly different events
    "tokyo-storm-vs-concert": [
        _s("s1", "Hurricane storm Tokyo", "Tokyo", 19),
        _s("c3", "Concert Tokyo", "Tokyo", 19, 5),
    ],
    # same event term, different cities
    "wildfire-la-vs-tokyo": [
        _s("w4", "Wildfire Los Angeles", LA, 12),
        _s("w5", "Wildfire Tokyo", "Tokyo", 12),
    ],
    # one stream mixes two event terms; the other shares only one of them
    "conflicting-terms": [
        _s("m1", "Fire and storm coverage LA", LA, 12),
        _s("m2", "Storm warning LA", LA, 12, 30),
    ],
    # no shared event term at all
    "gaming-vs-news": [
        _s("g1", "Ranked Fortnite stream", None, 10),
        _s("n1", "Evening news bulletin", None, 23),
    ],
}


def _all_streams() -> list[Stream]:
    return [s for group in RELATED.values() for s in group] + [
        s for group in UNRELATED.values() for s in group
    ]


def test_related_groups_are_recalled():
    """Every known same-event group must be detected as one event."""
    for name, group in RELATED.items():
        proposals = detect_events(group)
        matched = [p for p in proposals if set(p.related_streams) == set(s.id for s in group)]
        assert matched, f"missed related group: {name} (got {proposals})"


def test_unrelated_broadcasts_stay_apart():
    """The Sprint 6.3 failure mode: no cross-event merges."""
    for name, group in UNRELATED.items():
        proposals = detect_events(group)
        assert not proposals, f"false merge for: {name} -> {proposals}"


def test_la_fire_and_la_traffic_do_not_merge():
    """The exact 6.3 regression: shared city words alone must not link."""
    fire, traffic = UNRELATED["la-fire-vs-traffic"]
    assert linked(fire, traffic) is None


def test_conflicting_event_terms_do_not_merge():
    mixed, storm_only = UNRELATED["conflicting-terms"]
    assert linked(mixed, storm_only) is None
    assert linked(storm_only, mixed) is None


def test_proposal_carries_roadmap_fields():
    group = RELATED["wildfire-la"]
    (proposal,) = detect_events(group)
    assert proposal.topic in {"wildfire", "fire", "la"}
    assert proposal.place == "los angeles"
    assert proposal.started_at == datetime(2026, 10, 10, 12, tzinfo=H)
    assert set(proposal.related_streams) == {"w1", "w2", "w3"}
    # Entities include the shared event terms and the place tokens.
    assert {"wildfire", "fire", "los", "angeles"} <= set(proposal.entities)
    assert proposal.platforms == ["youtube"]
    assert proposal.confidence == "medium"  # named place, so higher confidence


def test_cross_platform_group_is_medium_confidence():
    group = list(RELATED["concert-tokyo"])
    group[1] = group[1].model_copy(update={"platform": "twitch", "id": "c2t", "platform_stream_id": "c2t"})
    (proposal,) = detect_events(group)
    assert proposal.platforms == ["twitch", "youtube"]
    assert proposal.confidence == "medium"


def test_singletons_are_not_proposed_as_events():
    proposals = detect_events([RELATED["concert-tokyo"][0]])
    assert proposals == []


def test_measurement_suite_shape():
    """Keep the experiment honest: both halves must stay non-trivial."""
    related_pairs = sum(1 for g in RELATED.values() if len(g) >= 2)
    unrelated_pairs = sum(1 for g in UNRELATED.values() if len(g) >= 2)
    assert related_pairs == 2
    assert unrelated_pairs == 5
    # Recall: both known groups found; Precision: no unrelated group merged.
    proposals = detect_events(_all_streams())
    merged = {frozenset(p.related_streams) for p in proposals}
    for group in UNRELATED.values():
        ids = {s.id for s in group}
        assert not any(ids <= m for m in merged)
