"""Persistent live-stream index (Sprint 4.2): SQLite via stdlib only.

One row per (platform, platform_stream_id). Every upsert refreshes
`last_seen_at` and overwrites metadata; `first_seen_at` is preserved;
`ended_at` is set on the live→ended transition and cleared if the id goes
live again. Only ended records past the cutoff are pruned — unseen actives
stay until the refresh loop (4.3) can revalidate them first.
"""

import json
from datetime import datetime, timedelta, timezone

from app.models.stream import IndexedStream, Stream
from app.services.db import connect

_COLUMNS = (
    "platform, platform_stream_id, id, channel_id, channel_name, title,"
    " description, thumbnail_url, source_url, embed_url, embed_supported,"
    " live_status, freshness, score, started_at, discovered_at,"
    " last_verified_at, viewer_count, category, tags, latitude, longitude,"
    " location_text, metadata, first_seen_at, last_seen_at, ended_at"
)


def _ensure_table(conn) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS streams (
            platform TEXT NOT NULL,
            platform_stream_id TEXT NOT NULL,
            id TEXT NOT NULL,
            channel_id TEXT NOT NULL DEFAULT '',
            channel_name TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            thumbnail_url TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            embed_url TEXT,
            embed_supported INTEGER NOT NULL DEFAULT 0,
            live_status TEXT NOT NULL DEFAULT 'unknown',
            freshness TEXT,
            score REAL,
            started_at TEXT,
            discovered_at TEXT,
            last_verified_at TEXT,
            viewer_count INTEGER,
            category TEXT,
            tags TEXT NOT NULL DEFAULT '[]',
            latitude REAL,
            longitude REAL,
            location_text TEXT,
            metadata TEXT NOT NULL DEFAULT '{}',
            first_seen_at TEXT,
            last_seen_at TEXT,
            ended_at TEXT,
            PRIMARY KEY (platform, platform_stream_id)
        )"""
    )


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _row_to_indexed(row) -> IndexedStream:
    data = dict(row)
    data["embed_supported"] = bool(data["embed_supported"])
    data["tags"] = json.loads(data["tags"] or "[]")
    data["metadata"] = json.loads(data["metadata"] or "{}")
    for field in ("started_at", "discovered_at", "last_verified_at",
                  "first_seen_at", "last_seen_at", "ended_at"):
        data[field] = _parse(data[field])
    return IndexedStream(**data)


def upsert_stream(record: Stream, now: datetime | None = None) -> IndexedStream:
    at = now or datetime.now(timezone.utc)
    with connect() as conn:
        _ensure_table(conn)
        existing = get_stream(record.platform, record.platform_stream_id, conn)
        first_seen = existing.first_seen_at if existing else at
        ended_at = existing.ended_at if existing else None
        if record.live_status == "ended":
            if ended_at is None:
                ended_at = at
        else:
            ended_at = None
        conn.execute(
            f"INSERT OR REPLACE INTO streams ({_COLUMNS}) VALUES ("
            + ", ".join(["?"] * 27) + ")",
            (
                record.platform, record.platform_stream_id, record.id,
                record.channel_id, record.channel_name, record.title,
                record.description, record.thumbnail_url, record.source_url,
                record.embed_url, int(record.embed_supported),
                record.live_status, record.freshness, record.score,
                _iso(record.started_at), _iso(record.discovered_at),
                _iso(record.last_verified_at), record.viewer_count,
                record.category, json.dumps(record.tags or []),
                record.latitude, record.longitude, record.location_text,
                json.dumps(record.metadata or {}),
                _iso(first_seen), _iso(at), _iso(ended_at),
            ),
        )
        stored = get_stream(record.platform, record.platform_stream_id, conn)
        assert stored is not None
        return stored


def get_stream(
    platform: str, platform_stream_id: str, conn=None
) -> IndexedStream | None:
    own = conn is None
    conn = conn or connect()
    try:
        _ensure_table(conn)
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM streams"
            " WHERE platform = ? AND platform_stream_id = ?",
            (platform, platform_stream_id),
        ).fetchone()
        return _row_to_indexed(row) if row else None
    finally:
        if own:
            conn.close()


def list_streams(
    live_status: str | None = None, limit: int = 100, oldest_first: bool = False
) -> list[IndexedStream]:
    order = "ASC" if oldest_first else "DESC"
    with connect() as conn:
        _ensure_table(conn)
        if live_status:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM streams WHERE live_status = ?"
                f" ORDER BY last_seen_at {order} LIMIT ?",
                (live_status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM streams"
                f" ORDER BY last_seen_at {order} LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_indexed(r) for r in rows]


def index_counts() -> tuple[int, int]:
    with connect() as conn:
        _ensure_table(conn)
        total = conn.execute("SELECT COUNT(*) FROM streams").fetchone()[0]
        live = conn.execute(
            "SELECT COUNT(*) FROM streams WHERE live_status = 'live'"
        ).fetchone()[0]
        return total, live


def prune_ended_older_than(days: int, now: datetime | None = None) -> int:
    """Delete ended records unseen for longer than `days`. Returns count."""
    at = now or datetime.now(timezone.utc)
    cutoff = _iso(at - timedelta(days=days))
    with connect() as conn:
        _ensure_table(conn)
        cur = conn.execute(
            "DELETE FROM streams WHERE live_status = 'ended' AND last_seen_at < ?",
            (cutoff,),
        )
        return cur.rowcount or 0
