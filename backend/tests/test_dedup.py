"""Duplicate detection tests (Sprint 6.2 verification).

Manually built duplicate set: obvious duplicates collapse (keeping the
best-ranked), while unrelated streams — including same-event titles from
different creators — survive. That second half is the point: 6.3 owns
event grouping, dedup must not do its job.
"""

from datetime import datetime, timezone

from app.adapters.base import BasePlatformAdapter
from app.models.stream import Stream
from app.search.dedup import are_duplicates, dedupe_streams
from app.services import index
from app.services.cache import SearchCache
from app.services.search import SearchService


def _s(**over) -> Stream:
    base = {
        "id": "s",
        "platform": "youtube",
        "platform_stream_id": "s",
        "channel_id": "chan-1",
        "channel_name": "News Channel",
        "live_status": "live",
        "freshness": "fresh",
    }
    return Stream(**{**base, **over})


def test_identical_ids_always_collapse():
    a = _s(id="youtube-v1", platform_stream_id="v1", title="Anything at all")
    b = _s(id="youtube-v1", platform_stream_id="v1", title="Totally different words here")
    survivors, removed = dedupe_streams([a, b])
    assert [s.id for s in survivors] == ["youtube-v1"]
    assert removed == 1


def test_same_channel_similar_titles_overlap_collapse():
    a = _s(
        id="a", platform_stream_id="a", title="Wildfire live coverage",
        started_at=datetime(2026, 10, 8, 12, tzinfo=timezone.utc),
    )
    b = _s(
        id="b", platform_stream_id="b", title="Wildfire live coverage!",
        started_at=datetime(2026, 10, 8, 14, tzinfo=timezone.utc),
    )
    assert are_duplicates(a, b)
    survivors, removed = dedupe_streams([a, b])
    assert [s.id for s in survivors] == ["a"]
    assert removed == 1


def test_cross_platform_simulcast_collapses():
    yt = _s(
        id="youtube-v1", platform="youtube", platform_stream_id="v1",
        channel_id="", channel_name="RiverCam",
        title="River flood watch live",
        started_at=datetime(2026, 10, 8, 12, tzinfo=timezone.utc),
    )
    tw = _s(
        id="twitch-9", platform="twitch", platform_stream_id="9",
        channel_id="", channel_name="rivercam",
        title="River flood watch live!",
        started_at=datetime(2026, 10, 8, 12, 30, tzinfo=timezone.utc),
    )
    assert are_duplicates(yt, tw)
    survivors, _ = dedupe_streams([yt, tw])
    assert [s.id for s in survivors] == ["youtube-v1"]


def test_same_channel_different_topics_survive():
    a = _s(id="a", platform_stream_id="a", title="Morning wildfire update")
    b = _s(id="b", platform_stream_id="b", title="Evening concert stream")
    assert not are_duplicates(a, b)
    survivors, removed = dedupe_streams([a, b])
    assert len(survivors) == 2 and removed == 0


def test_different_channels_same_event_title_survive():
    # Same event, different broadcasts — 6.3's job, not dedup's.
    a = _s(id="a", platform_stream_id="a", channel_id="c-a",
           channel_name="Alpha News", title="Wildfire live")
    b = _s(id="b", platform_stream_id="b", channel_id="c-b",
           channel_name="Beta News", title="Wildfire live")
    assert not are_duplicates(a, b)
    survivors, removed = dedupe_streams([a, b])
    assert len(survivors) == 2 and removed == 0


def test_same_channel_title_far_apart_in_time_survives():
    a = _s(id="a", platform_stream_id="a", title="Daily briefing",
           started_at=datetime(2026, 10, 1, 12, tzinfo=timezone.utc))
    b = _s(id="b", platform_stream_id="b", title="Daily briefing",
           started_at=datetime(2026, 10, 8, 12, tzinfo=timezone.utc))
    assert not are_duplicates(a, b)


def test_missing_times_do_not_block_obvious_dupe():
    a = _s(id="a", platform_stream_id="a", title="Wildfire live coverage")
    b = _s(id="b", platform_stream_id="b", title="Wildfire live coverage!")
    assert are_duplicates(a, b)


class _DupeAdapter(BasePlatformAdapter):
    platform = "dupe"

    def search(self, query: str) -> list[dict]:
        base = {
            "platform": "dupe", "channel_id": "c1", "channel_name": "Chan",
            "live_status": "live",
        }
        return [
            {**base, "id": "dupe-1", "platform_stream_id": "d1",
             "title": "Wildfire live coverage"},
            {**base, "id": "dupe-1", "platform_stream_id": "d1",
             "title": "Wildfire live coverage"},
            {**base, "id": "dupe-2", "platform_stream_id": "d2",
             "title": "Unrelated cooking show"},
        ]


def test_service_collapses_response_but_indexes_sightings():
    service = SearchService(
        adapters=[_DupeAdapter()], cache=SearchCache(ttl_seconds=60)
    )
    res = service.search("wildfire")
    assert res.count == 2
    assert res.duplicates_removed == 1
    assert [s.id for s in res.results] == ["dupe-1", "dupe-2"]
    # Index keeps what the platform reported (ids distinct → both stored).
    assert index.get_stream("dupe", "d1") is not None
    assert index.get_stream("dupe", "d2") is not None
