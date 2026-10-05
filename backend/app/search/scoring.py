"""Deterministic relevance scoring (Sprint 3.1, normalization in 3.2).

Isolated, configurable scoring over stored fields — the ONLY place ranking
weights live. Tokenization/normalization lives in normalize.py and applies
symmetrically to queries and fields. Viewer count is deliberately a weak
tiebreak signal, never primary. Ended broadcasts always sort below live
ones (live-first).

Signal weights (conceptual: title/location high, description/tags medium,
freshness medium, viewers low):
- title_exact: expanded query phrase appears as a contiguous token run in the title
- title_token: fraction of query tokens present in the title
- description: fraction of query tokens present in the description
- tag_category: 1.0 if any query token hits tags/category, else 0.0
- location: with a parsed place, how much of it the record covers;
  otherwise fraction of location_text tokens present in the query
- freshness: fresh 1.0 / aging 0.5 / stale or ended 0.0
- viewers: log-scaled into [0, 1], low weight
"""

from dataclasses import dataclass
from math import log10

from app.models.stream import Stream
from app.search.normalize import phrase_tokens, tokens

_FRESHNESS_SCORE = {"fresh": 1.0, "aging": 0.5, "stale": 0.0, "ended": 0.0}


@dataclass(frozen=True)
class Weights:
    title_exact: float = 100.0
    title_token: float = 40.0
    description: float = 15.0
    tag_category: float = 15.0
    location: float = 50.0
    freshness: float = 20.0
    viewers: float = 5.0


DEFAULT_WEIGHTS = Weights()


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    title_exact: float
    title_token: float
    description: float
    tag_category: float
    location: float
    freshness: float
    viewers: float


def _fraction(needles: set[str], haystack: set[str]) -> float:
    if not needles or not haystack:
        return 0.0
    return len(needles & haystack) / len(needles)


def _contains(haystack: list[str], needle: list[str]) -> bool:
    if not needle:
        return False
    return any(
        haystack[i : i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    )


def score_stream(
    stream: Stream,
    query: str,
    weights: Weights = DEFAULT_WEIGHTS,
    place: str | None = None,
) -> ScoreBreakdown:
    q_phrase = phrase_tokens(query)
    q_tokens = set(q_phrase)
    if not q_tokens:
        return ScoreBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    title_exact = 1.0 if _contains(phrase_tokens(stream.title or ""), q_phrase) else 0.0
    title_token = _fraction(q_tokens, tokens(stream.title or ""))
    description = _fraction(q_tokens, tokens(stream.description or ""))

    tag_haystack = tokens(" ".join([*(stream.tags or []), stream.category or ""]))
    tag_category = 1.0 if q_tokens & tag_haystack else 0.0

    loc_tokens = tokens(stream.location_text or "")
    if place:
        # How much of the requested place does this record cover?
        place_tokens = tokens(place)
        location = _fraction(place_tokens, loc_tokens) if place_tokens else 0.0
    elif loc_tokens:
        location = _fraction(loc_tokens, q_tokens)
    else:
        location = 0.0

    freshness = _FRESHNESS_SCORE.get(stream.freshness or "stale", 0.0)

    viewers_raw = stream.viewer_count or 0
    viewers = min(1.0, log10(1 + max(viewers_raw, 0)) / 4.0) if viewers_raw > 0 else 0.0

    parts = {
        "title_exact": weights.title_exact * title_exact,
        "title_token": weights.title_token * title_token,
        "description": weights.description * description,
        "tag_category": weights.tag_category * tag_category,
        "location": weights.location * location,
        "freshness": weights.freshness * freshness,
        "viewers": weights.viewers * viewers,
    }
    return ScoreBreakdown(total=sum(parts.values()), **parts)


def rank_streams(
    streams: list[Stream],
    query: str,
    weights: Weights = DEFAULT_WEIGHTS,
    place: str | None = None,
) -> list[Stream]:
    """Score, stamp, and order: live records by score desc, ended last.

    Python's sort is stable, so score ties keep adapter discovery order.
    """
    scored = [(s, score_stream(s, query, weights, place)) for s in streams]
    scored.sort(key=lambda t: (t[0].live_status != "ended", t[1].total), reverse=True)
    for stream, breakdown in scored:
        stream.score = round(breakdown.total, 3)
    return [s for s, _ in scored]
