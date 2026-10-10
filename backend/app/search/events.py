"""Advanced event detection — EXPERIMENT (Sprint 13.2, not wired into search).

Identifies a candidate event shared by multiple broadcasts, with topic,
location, time window and entities. Read-only/inspectable output.

Why this exists at all: Sprint 6.3's clustering experiment failed because it
linked on *any* token overlap, so an LA fire stream and an LA traffic stream
merged (shared "LA"). This module fixes that failure mode with three rules:

  1. **shared event family required** — streams must share at least one
     curated event family (`fire`, `weather`, `concert`, …). Shared city or
     generic words alone are *context*, not *event*.
  2. **identical family sets required** — a stream carrying a second,
     different family (e.g. "fire and storm") does not merge with one that
     carries only one of them, so a mixed-topic stream never bridges two
     unrelated events.
  3. **location disagreement vetoes**, and location OR time must agree.

The result is measured against a labeled set in
`tests/test_event_detection.py`; those recall/precision numbers decide
whether this ever ships.
"""

from collections import Counter
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.stream import Stream
from app.search.location import gazetteer_lookup
from app.search.normalize import tokens

# Curated event vocabulary, grouped into synonym families. Deliberately
# small: this is the experiment's lever, and a big hand-built ontology is
# explicitly out of bounds (Sprint 3.2 guardrail).
EVENT_FAMILIES: dict[str, frozenset[str]] = {
    "fire": frozenset({"wildfire", "fire", "blaze", "burn", "scanner"}),
    "weather": frozenset(
        {"storm", "hurricane", "tornado", "flood", "blizzard", "thunderstorm",
         "warning"}
    ),
    "seismic": frozenset({"earthquake", "tremor", "tsunami", "eruption"}),
    "civil": frozenset({"protest", "riot", "unrest"}),
    "entertainment": frozenset({"concert", "festival", "parade"}),
    "launch": frozenset({"launch", "rocket", "spacex"}),
    "info": frozenset({"news", "briefing", "update"}),
}

# Reverse lookup: term -> family.
_TERM_TO_FAMILY: dict[str, str] = {
    term: family
    for family, terms in EVENT_FAMILIES.items()
    for term in terms
}

TIME_WINDOW_HOURS = 6.0

# Words that carry no event signal. Real-data measurement (Sprint 13.2)
# showed that without this list a religious "Prophetic Wildfire Live"
# stream merges with an LA fire scanner: they share an event family and
# nothing else except filler like "live".
GENERIC_WORDS = frozenset(
    {
        "live", "streaming", "stream", "now", "today", "tonight", "hd",
        "4k", "breaking", "watch", "watching", "look", "new", "the", "and",
        "for", "with", "from", "you", "your",
    }
)


def _families(text: str) -> frozenset[str]:
    found = tokens(text) & _TERM_TO_FAMILY.keys()
    return frozenset(_TERM_TO_FAMILY[t] for t in found)


def _specific_entities(text: str) -> set[str]:
    """Non-event, non-generic words: the named entities of an event.

    Real events share a name (e.g. "isaias", "la", "tokyo"); a coincidental
    family match does not. Requiring a shared entity is what separates the
    10-broadcast hurricane cluster from a filler-word coincidence.
    """
    return tokens(text) - _TERM_TO_FAMILY.keys() - GENERIC_WORDS


def _place_of(stream: Stream) -> str | None:
    """Resolve a stream's place via the existing gazetteer, if possible."""
    if not stream.location_text:
        return None
    resolved = gazetteer_lookup(stream.location_text)
    return resolved[0] if resolved else None


def _hours_apart(a: Stream, b: Stream) -> float | None:
    if a.started_at is None or b.started_at is None:
        return None

    def as_utc(v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)

    return abs((as_utc(a.started_at) - as_utc(b.started_at)).total_seconds()) / 3600


def linked(a: Stream, b: Stream) -> str | None:
    """Name of the shared event family, or None if these are not the same event.

    The return value is the family name (for callers that want the reason);
    truthiness is what tests assert.
    """
    families_a, families_b = _families(a.title), _families(b.title)
    if not families_a or families_a != families_b:
        # No shared family, or a conflicting one (rule 2).
        return None
    if not (_specific_entities(a.title) & _specific_entities(b.title)):
        # Shared family but no shared named entity — most likely two
        # different events of the same kind, or filler coincidence.
        return None
    family = next(iter(families_a))

    place_a, place_b = _place_of(a), _place_of(b)
    if place_a and place_b and place_a != place_b:
        return None
    apart = _hours_apart(a, b)
    near_in_time = apart is None or apart <= TIME_WINDOW_HOURS
    near_in_place = (place_a and place_b) or place_a is None or place_b is None
    if not (near_in_time and near_in_place):
        return None
    return family


class EventProposal(BaseModel):
    """What an event would look like if this experiment ever shipped."""

    topic: str
    family: str
    place: str | None = None
    started_at: datetime | None = None
    entities: list[str] = Field(default_factory=list)
    related_streams: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    confidence: str = "low"  # "low" | "medium"


def detect_events(streams: list[Stream]) -> list[EventProposal]:
    """Group streams into candidate events via union-find over `linked`."""
    n = len(streams)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if linked(streams[i], streams[j]) is not None:
                parent[find(i)] = find(j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    proposals: list[EventProposal] = []
    for members in groups.values():
        group = [streams[i] for i in members]
        if len(group) < 2:
            continue  # not an event until two broadcasts agree

        counts = Counter(t for s in group for t in tokens(s.title))
        topic = next(
            (t for t, _ in counts.most_common() if t in _TERM_TO_FAMILY), None
        )
        family = _families(group[0].title) and next(iter(_families(group[0].title)))
        places = {p for p in (_place_of(s) for s in group) if p}
        starts = [s.started_at for s in group if s.started_at is not None]
        entities = {t for s in group for t in tokens(s.title)}
        platforms = sorted({s.platform for s in group})
        proposals.append(
            EventProposal(
                topic=topic or "",
                family=family or "",
                place=min(places) if places else None,
                started_at=min(starts) if starts else None,
                entities=sorted(entities),
                related_streams=[s.id for s in group],
                platforms=platforms,
                # A group spanning platforms or a named place is more likely
                # a real-world event than a coincidence.
                confidence="medium" if (len(platforms) > 1 or places) else "low",
            )
        )
    proposals.sort(key=lambda p: (-len(p.related_streams), p.topic))
    return proposals


__all__ = [
    "EVENT_FAMILIES",
    "TIME_WINDOW_HOURS",
    "EventProposal",
    "detect_events",
    "linked",
]
