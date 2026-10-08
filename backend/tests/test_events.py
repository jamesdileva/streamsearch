"""Event model tests (Sprint 6.1 verification).

Manual event groups: one event → many broadcasts across platforms.
No clustering, no endpoints in this sprint — the concept, persisted.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.config import settings
from app.models.event import Event, EventStreamRef
from app.services import events
from app.services.events import UnknownEventError

NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/e.db")


def _ref(platform: str, pid: str) -> EventStreamRef:
    return EventStreamRef(platform=platform, platform_stream_id=pid)


def test_manual_group_spans_platforms(isolated_db):
    event = events.create_event(
        topic="Downtown wildfire",
        location="los angeles",
        stream_refs=[_ref("youtube", "vid-1"), _ref("twitch", "123456")],
        event_id="evt-wildfire-1",
        now=NOW,
    )
    assert event.event_id == "evt-wildfire-1"
    assert event.topic == "Downtown wildfire"
    assert event.location == "los angeles"
    assert event.detected_at == NOW
    assert event.active_until is None
    assert event.is_active(NOW)

    stored = events.get_event("evt-wildfire-1")
    assert stored is not None
    assert [(r.platform, r.platform_stream_id) for r in stored.related_streams] == [
        ("twitch", "123456"),
        ("youtube", "vid-1"),
    ]


def test_auto_id_and_defaults(isolated_db):
    event = events.create_event(topic="Storm coverage")
    assert event.event_id.startswith("evt_")
    assert event.location is None
    assert event.related_streams == []
    assert events.get_event(event.event_id) is not None


def test_blank_topic_rejected(isolated_db):
    with pytest.raises(ValidationError):
        events.create_event(topic="   ")


def test_duplicate_event_id_rejected(isolated_db):
    events.create_event(topic="One", event_id="evt-dup")
    with pytest.raises(ValueError, match="already exists"):
        events.create_event(topic="Two", event_id="evt-dup")


def test_add_streams_is_idempotent(isolated_db):
    events.create_event(topic="T", event_id="evt-a", stream_refs=[_ref("youtube", "v1")])
    updated = events.add_streams(
        "evt-a", [_ref("youtube", "v1"), _ref("twitch", "9")]
    )
    # Insertion order; the duplicate v1 was ignored, not duplicated.
    assert [(r.platform, r.platform_stream_id) for r in updated.related_streams] == [
        ("youtube", "v1"),
        ("twitch", "9"),
    ]


def test_add_to_unknown_event_raises(isolated_db):
    with pytest.raises(UnknownEventError):
        events.add_streams("evt-nope", [_ref("youtube", "v1")])


def test_close_and_active_filter(isolated_db):
    events.create_event(topic="Open", event_id="evt-open")
    events.create_event(topic="Shut", event_id="evt-shut")
    closed = events.close_event("evt-shut", NOW)
    assert closed.active_until == NOW
    assert not closed.is_active(NOW)
    still_open = events.get_event("evt-open")
    assert still_open is not None and still_open.is_active(NOW)

    active = events.list_events(active_only=True)
    assert [e.event_id for e in active] == ["evt-open"]
    assert len(events.list_events()) == 2

    # Re-closing is a no-op returning current state.
    assert events.close_event("evt-shut", NOW).active_until == NOW


def test_close_unknown_event_raises(isolated_db):
    with pytest.raises(UnknownEventError):
        events.close_event("evt-nope")


def test_get_unknown_event_returns_none(isolated_db):
    assert events.get_event("evt-nope") is None


def test_model_active_boundary():
    event = Event(topic="T", active_until=NOW)
    assert not event.is_active(NOW)
    assert event.is_active(NOW.replace(year=2020))
