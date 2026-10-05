"""Background refresh (Sprint 4.3): bounded revalidation, not a crawler.

One pass: take up to `batch_size` known-live records (stalest first),
reverify each by platform id, upsert the still-live ones (advancing
last_seen/last_verified), transition confirmed-gone ones to ended, then
prune long-ended records. Adapters that can't judge ids are skipped —
their records age honestly into stale. Per-adapter failures are recorded,
never raised. New-query discovery is deliberately excluded (unjustified
without traffic); the pass only tends records users already found.
"""

import logging
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.stream import Stream
from app.services import index

logger = logging.getLogger(__name__)


class RefreshReport(BaseModel):
    checked: int = 0
    refreshed: int = 0
    ended: int = 0
    pruned: int = 0
    errors: list[str] = Field(default_factory=list)


def run_refresh_once(
    adapters=None,
    batch_size: int = 10,
    prune_days: int = 30,
    now: datetime | None = None,
) -> RefreshReport:
    from app.services.search import build_default_adapters

    at = now or datetime.now(timezone.utc)
    adapters = adapters if adapters is not None else build_default_adapters()
    by_platform = {a.platform: a for a in adapters}
    report = RefreshReport()

    actives = index.list_streams(
        live_status="live", limit=max(1, batch_size), oldest_first=True
    )
    report.checked = len(actives)

    grouped: dict[str, list] = {}
    for record in actives:
        grouped.setdefault(record.platform, []).append(record)

    for platform, records in grouped.items():
        adapter = by_platform.get(platform)
        if adapter is None:
            continue
        try:
            verdicts = adapter.reverify([r.platform_stream_id for r in records])
        except Exception as exc:
            report.errors.append(f"{platform}: {exc}")
            logger.warning("refresh reverify failed", exc_info=True)
            continue
        for record in records:
            if record.platform_stream_id not in verdicts:
                continue  # adapter can't judge — leave untouched
            fresh = verdicts[record.platform_stream_id]
            try:
                if fresh is None:
                    ended = record.model_copy(
                        update={"live_status": "ended", "freshness": "ended"}
                    )
                    index.upsert_stream(ended, at)
                    report.ended += 1
                else:
                    index.upsert_stream(Stream(**fresh), at)
                    report.refreshed += 1
            except Exception as exc:
                report.errors.append(f"{platform}: {exc}")
                logger.warning("refresh upsert failed", exc_info=True)

    try:
        report.pruned = index.prune_ended_older_than(prune_days, at)
    except Exception as exc:
        report.errors.append(f"prune: {exc}")
        logger.warning("refresh prune failed", exc_info=True)
    return report
