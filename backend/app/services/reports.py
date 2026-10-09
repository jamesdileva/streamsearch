"""Reports store (Sprint 2.3): SQLite persistence via stdlib only.

One small table in the PoC database file. Short-lived connections per call;
plenty for report volume.
"""

import sqlite3
from datetime import datetime, timezone

from app.models.report import Report, ReportCreate
from app.services.db import connect


def _connect() -> sqlite3.Connection:
    conn = connect()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id TEXT NOT NULL,
            platform TEXT NOT NULL DEFAULT '',
            reason TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )"""
    )
    return conn


def count_reports() -> int:
    """Total report volume for observability (Sprint 10.3)."""
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]


def save_report(data: ReportCreate) -> Report:
    created = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO reports (stream_id, platform, reason, detail, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                data.stream_id.strip(),
                data.platform.strip(),
                data.reason,
                data.detail.strip(),
                created,
            ),
        )
        report_id = cur.lastrowid or 0
    return Report(
        id=report_id,
        stream_id=data.stream_id.strip(),
        platform=data.platform.strip(),
        reason=data.reason,
        detail=data.detail.strip(),
        created_at=datetime.fromisoformat(created),
    )


def list_reports(stream_id: str = "") -> list[Report]:
    with _connect() as conn:
        if stream_id.strip():
            rows = conn.execute(
                "SELECT id, stream_id, platform, reason, detail, created_at"
                " FROM reports WHERE stream_id = ? ORDER BY id",
                (stream_id.strip(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, stream_id, platform, reason, detail, created_at"
                " FROM reports ORDER BY id"
            ).fetchall()
    return [
        Report(
            id=row[0],
            stream_id=row[1],
            platform=row[2],
            reason=row[3],
            detail=row[4],
            created_at=datetime.fromisoformat(row[5]),
        )
        for row in rows
    ]
