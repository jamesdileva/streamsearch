"""Manual event groups (Sprint 6.1): create/get/extend/close/list.

SQLite `events` + `event_streams` join table in the PoC database. Stream
refs are NOT foreign-keyed — a group may reference broadcasts the index
hasn't seen (e.g. reported by URL). Detection/clustering is 6.2/6.3 work.
"""

import sqlite3
from datetime import datetime, timezone

from app.models.event import Event, EventStreamRef, new_event_id
from app.services.db import connect


def _ensure_tables(conn) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            location TEXT,
            detected_at TEXT NOT NULL,
            active_until TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS event_streams (
            event_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            platform_stream_id TEXT NOT NULL,
            added_at TEXT NOT NULL,
            PRIMARY KEY (event_id, platform, platform_stream_id)
        )"""
    )


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _refs_for(conn, event_id: str) -> list[EventStreamRef]:
    rows = conn.execute(
        "SELECT platform, platform_stream_id FROM event_streams"
        " WHERE event_id = ? ORDER BY added_at, platform, platform_stream_id",
        (event_id,),
    ).fetchall()
    return [EventStreamRef(platform=r[0], platform_stream_id=r[1]) for r in rows]


def _row_to_event(row, refs: list[EventStreamRef]) -> Event:
    return Event(
        event_id=row[0],
        topic=row[1],
        location=row[2],
        detected_at=datetime.fromisoformat(row[3]),
        active_until=datetime.fromisoformat(row[4]) if row[4] else None,
        related_streams=refs,
    )


class UnknownEventError(ValueError):
    """Raised when an operation names an event that doesn't exist."""


def create_event(
    topic: str,
    location: str | None = None,
    stream_refs: list[EventStreamRef] | None = None,
    event_id: str | None = None,
    now: datetime | None = None,
) -> Event:
    at = now or datetime.now(timezone.utc)
    event = Event(
        event_id=event_id or new_event_id(),
        topic=topic,
        location=location.strip() if location and location.strip() else None,
        detected_at=at,
    )
    with connect() as conn:
        _ensure_tables(conn)
        try:
            conn.execute(
                "INSERT INTO events (event_id, topic, location, detected_at, active_until)"
                " VALUES (?, ?, ?, ?, ?)",
                (event.event_id, event.topic, event.location, _iso(at), None),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"event already exists: {event.event_id}") from exc
        for ref in stream_refs or []:
            conn.execute(
                "INSERT OR IGNORE INTO event_streams"
                " (event_id, platform, platform_stream_id, added_at)"
                " VALUES (?, ?, ?, ?)",
                (event.event_id, ref.platform, ref.platform_stream_id, _iso(at)),
            )
        event.related_streams = _refs_for(conn, event.event_id)
    return event


def get_event(event_id: str) -> Event | None:
    with connect() as conn:
        _ensure_tables(conn)
        row = conn.execute(
            "SELECT event_id, topic, location, detected_at, active_until"
            " FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_event(row, _refs_for(conn, event_id))


def add_streams(event_id: str, refs: list[EventStreamRef]) -> Event:
    at = datetime.now(timezone.utc)
    with connect() as conn:
        _ensure_tables(conn)
        exists = conn.execute(
            "SELECT 1 FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if exists is None:
            raise UnknownEventError(f"unknown event: {event_id}")
        for ref in refs:
            conn.execute(
                "INSERT OR IGNORE INTO event_streams"
                " (event_id, platform, platform_stream_id, added_at)"
                " VALUES (?, ?, ?, ?)",
                (event_id, ref.platform, ref.platform_stream_id, _iso(at)),
            )
        row = conn.execute(
            "SELECT event_id, topic, location, detected_at, active_until"
            " FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        assert row is not None
        return _row_to_event(row, _refs_for(conn, event_id))


def close_event(event_id: str, now: datetime | None = None) -> Event:
    at = now or datetime.now(timezone.utc)
    with connect() as conn:
        _ensure_tables(conn)
        cur = conn.execute(
            "UPDATE events SET active_until = ? WHERE event_id = ? AND active_until IS NULL",
            (_iso(at), event_id),
        )
        if cur.rowcount == 0:
            existing = get_event(event_id)
            if existing is None:
                raise UnknownEventError(f"unknown event: {event_id}")
            return existing
        row = conn.execute(
            "SELECT event_id, topic, location, detected_at, active_until"
            " FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        assert row is not None
        return _row_to_event(row, _refs_for(conn, event_id))


def list_events(active_only: bool = False, limit: int = 100) -> list[Event]:
    with connect() as conn:
        _ensure_tables(conn)
        if active_only:
            rows = conn.execute(
                "SELECT event_id, topic, location, detected_at, active_until"
                " FROM events WHERE active_until IS NULL"
                " ORDER BY detected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT event_id, topic, location, detected_at, active_until"
                " FROM events ORDER BY detected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_event(r, _refs_for(conn, r[0])) for r in rows]
