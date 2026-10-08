"""Basic duplicate detection (Sprint 6.2): collapse obvious duplicates.

Rules, in order:
1. Same (platform, platform_stream_id) twice → duplicate, always.
2. Same channel (id, else normalized name) + highly similar titles
   (token Jaccard ≥ threshold) + overlapping start times → duplicate.
   Covers restreams and cross-platform simulcasts by one creator.
3. Different channels are NEVER duplicates here — even with identical
   titles. Same-event/different-broadcast grouping is 6.3's experiment,
   not dedup's job.

Timing passes when either start is unknown (can't disprove overlap).
Collapse keeps the first record of each group: callers pass rank-ordered
lists so the best record survives. The index keeps every sighting —
dedup shapes the response only.
"""

from datetime import timezone

from app.models.stream import Stream
from app.search.normalize import tokens

TITLE_SIMILARITY_THRESHOLD = 0.8
START_OVERLAP_HOURS = 6.0


def _title_similarity(a: str, b: str) -> float:
    ta, tb = tokens(a or ""), tokens(b or "")
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _starts_overlap(a: Stream, b: Stream) -> bool:
    if a.started_at is None or b.started_at is None:
        return True
    delta = abs((_as_utc(a.started_at) - _as_utc(b.started_at)).total_seconds())
    return delta <= START_OVERLAP_HOURS * 3600


def _same_channel(a: Stream, b: Stream) -> bool:
    if a.channel_id and b.channel_id and a.channel_id == b.channel_id:
        return True
    na, nb = (a.channel_name or "").strip().lower(), (b.channel_name or "").strip().lower()
    return bool(na) and na == nb


def are_duplicates(a: Stream, b: Stream) -> bool:
    if (a.platform, a.platform_stream_id) == (b.platform, b.platform_stream_id):
        return True
    if not _same_channel(a, b):
        return False
    if _title_similarity(a.title, b.title) < TITLE_SIMILARITY_THRESHOLD:
        return False
    return _starts_overlap(a, b)


def dedupe_streams(streams: list[Stream]) -> tuple[list[Stream], int]:
    """Collapse duplicates, keeping the first of each group.

    Returns (survivors, removed_count).
    """
    survivors: list[Stream] = []
    for candidate in streams:
        if any(are_duplicates(candidate, kept) for kept in survivors):
            continue
        survivors.append(candidate)
    return survivors, len(streams) - len(survivors)
