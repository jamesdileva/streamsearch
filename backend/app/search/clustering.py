"""Event-clustering EXPERIMENT (Sprint 6.3) — NOT wired into search.

Question: can broadcasts be grouped around an ongoing event from title,
location, and timing alone? Rule (deliberately transparent):

  LINK(a, b) iff title_link AND (location_link OR time_link)
              AND NOT time_veto

- title_link: stopword-filtered token Jaccard ≥ threshold. Filtering out
  generic live words ("live", "breaking", "coverage"...) lets content
  words dominate — this doubles as the "shared entities" signal, reported
  per cluster for inspection.
- location_link: both records located and same normalized text, or token
  overlap ≥ 0.5. Missing location never links (unlike time).
- time_link: both starts within the window, or either missing.
- time_veto: both starts present and farther apart than the window —
  broadcasts days apart are not one live event, whatever the titles say.

Semantic similarity was NOT needed for this experiment and is NOT used:
the verdict (worklog 6.3) keeps embeddings behind the 7.1 gate.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import timezone

from app.models.stream import Stream
from app.search.normalize import tokens

TITLE_LINK_THRESHOLD = 0.4
TIME_WINDOW_HOURS = 12.0
MAX_STOPWORDS = 30

STOPWORDS = frozenset(
    [
        "live", "stream", "streams", "streaming", "broadcast", "official",
        "breaking", "news", "update", "updates", "coverage", "watch",
        "watching", "now", "today", "tonight", "footage", "video", "cam",
        "tv", "hd", "4k", "new",
    ]
)


@dataclass
class Cluster:
    members: list[Stream] = field(default_factory=list)
    topic_guess: list[str] = field(default_factory=list)
    location: str | None = None


def content_tokens(text: str) -> set[str]:
    return tokens(text or "") - set(STOPWORDS)


def shared_entities(a: Stream, b: Stream) -> list[str]:
    return sorted(content_tokens(a.title) & content_tokens(b.title))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def title_link(a: Stream, b: Stream, threshold: float = TITLE_LINK_THRESHOLD) -> bool:
    return _jaccard(content_tokens(a.title), content_tokens(b.title)) >= threshold


def _norm_loc(text: str | None) -> str:
    return (text or "").strip().lower()


def location_link(a: Stream, b: Stream) -> bool:
    la, lb = _norm_loc(a.location_text), _norm_loc(b.location_text)
    if not la or not lb:
        return False
    if la == lb:
        return True
    ta, tb = set(la.split()), set(lb.split())
    return len(ta & tb) / max(len(ta), len(tb)) >= 0.5


def _hours_apart(a: Stream, b: Stream) -> float | None:
    if a.started_at is None or b.started_at is None:
        return None
    return abs((_as_utc(a.started_at) - _as_utc(b.started_at)).total_seconds()) / 3600


def time_link(a: Stream, b: Stream) -> bool:
    apart = _hours_apart(a, b)
    return True if apart is None else apart <= TIME_WINDOW_HOURS


def time_veto(a: Stream, b: Stream) -> bool:
    apart = _hours_apart(a, b)
    return apart is not None and apart > TIME_WINDOW_HOURS


def linked(a: Stream, b: Stream, threshold: float = TITLE_LINK_THRESHOLD) -> bool:
    return (
        title_link(a, b, threshold)
        and (location_link(a, b) or time_link(a, b))
        and not time_veto(a, b)
    )


def cluster_streams(
    streams: list[Stream], title_threshold: float = TITLE_LINK_THRESHOLD
) -> list[Cluster]:
    """Union-find over links; returns groups of ≥2 with topic/location notes."""
    parent = list(range(len(streams)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    for i in range(len(streams)):
        for j in range(i + 1, len(streams)):
            if linked(streams[i], streams[j], title_threshold):
                union(i, j)

    groups: dict[int, list[Stream]] = {}
    for i, stream in enumerate(streams):
        groups.setdefault(find(i), []).append(stream)

    clusters: list[Cluster] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        counts = Counter(t for m in members for t in content_tokens(m.title))
        topic = sorted(counts, key=lambda t: (-counts[t], t))[:3]
        locs = {_norm_loc(m.location_text) for m in members if _norm_loc(m.location_text)}
        clusters.append(
            Cluster(
                members=members,
                topic_guess=topic,
                location=next(iter(locs)) if len(locs) == 1 else None,
            )
        )
    return clusters
