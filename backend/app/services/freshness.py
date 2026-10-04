"""Freshness: how much a record's live flag can be trusted (Sprint 2.2).

`live_status` is what the platform last claimed; `freshness` is how much
we trust that claim, derived from `last_verified_at` and configurable
thresholds. Adapters report observations — they never set freshness;
the service layer stamps it on every search.

States:
- fresh: verified within `fresh_seconds` (default 5 min)
- aging: verification getting old (default < 30 min)
- stale: should be rechecked (old or never verified)
- ended: terminal — the broadcast is over regardless of verification age

Without a persistent index (Sprint 4.2) every search re-discovers records,
so live results are typically fresh; the stale paths matter once stored
records outlive their verification (revalidation lands in Sprint 4.3).
"""

from datetime import datetime, timezone

from app.models.stream import Freshness, Stream


def freshness_of(
    stream: Stream,
    now: datetime | None = None,
    fresh_seconds: int = 300,
    aging_seconds: int = 1800,
) -> Freshness:
    if stream.live_status == "ended":
        return "ended"
    verified = stream.last_verified_at
    if verified is None:
        return "stale"
    at = now or datetime.now(timezone.utc)
    if verified.tzinfo is None:
        verified = verified.replace(tzinfo=timezone.utc)
    age = max((at - verified).total_seconds(), 0)  # skew → just verified
    if age <= fresh_seconds:
        return "fresh"
    if age <= aging_seconds:
        return "aging"
    return "stale"
