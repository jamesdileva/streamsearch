"""Second-platform contract proof (Sprint 5.1 verification).

A fake Twitch-shaped adapter — numeric ids, game-name categories, no
location, missing thumbnails, mixed embed support, int-or-absent viewers —
runs through the untouched chain: search, ranking, freshness, refresh,
index. No interface changes were needed; this module pins that.
"""

import pytest

from app.adapters.base import FakeAdapter
from app.adapters.fake_twitch import FakeTwitchAdapter
from app.config import settings
from app.models.stream import Stream
from app.services import index
from app.services.search import SearchService, build_default_adapters


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/p2.db")


def test_twitch_records_validate_despite_different_shapes():
    records = FakeTwitchAdapter().search("wildfire")
    assert len(records) == 2
    streams = [Stream(**r) for r in records]
    assert {s.platform for s in streams} == {"twitch"}
    # Numeric ids, game-name categories, no location anywhere.
    assert streams[0].platform_stream_id == "48392157"
    assert streams[0].category == "Outdoors"
    assert all(s.location_text is None for s in streams)
    # One full-featured, one sparse.
    assert streams[0].viewer_count == 5231
    assert streams[0].thumbnail_url != ""
    assert streams[0].embed_supported is True
    assert streams[1].viewer_count is None
    assert streams[1].thumbnail_url == ""
    assert streams[1].embed_supported is False


def test_mixed_search_ranks_across_platforms():
    service = SearchService(adapters=[FakeAdapter(), FakeTwitchAdapter()])
    res = service.search("wildfire")
    assert res.count == 3
    assert {s.platform for s in res.results} == {"fake", "twitch"}
    totals = [s.score or 0 for s in res.results]
    assert totals == sorted(totals, reverse=True)
    assert all(s.freshness == "fresh" for s in res.results)


def test_reverify_judges_known_retired_and_unknown():
    adapter = FakeTwitchAdapter()
    verdicts = adapter.reverify(["48392157", "555", "nope"])
    assert verdicts["48392157"] is not None
    assert verdicts["48392157"]["live_status"] == "live"
    assert verdicts["555"] is None
    assert "nope" not in verdicts


def test_refresh_pass_handles_mixed_platform_endings(isolated_db):
    live = Stream(**FakeTwitchAdapter().search("x")[0])
    gone = Stream(
        **{**FakeTwitchAdapter().search("x")[0],
           "id": "twitch-555", "platform_stream_id": "555"}
    )
    index.upsert_stream(live)
    index.upsert_stream(gone)
    from app.services.refresh import run_refresh_once

    report = run_refresh_once(adapters=[FakeTwitchAdapter()])
    assert (report.checked, report.refreshed, report.ended) == (2, 1, 1)
    stored = index.get_stream("twitch", "555")
    assert stored is not None and stored.live_status == "ended"


def test_factory_never_mixes_fake_with_real(monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", "k")
    assert [a.platform for a in build_default_adapters()] == ["youtube"]
    monkeypatch.setattr(settings, "youtube_api_key", "")
    assert [a.platform for a in build_default_adapters()] == ["fake", "twitch"]
