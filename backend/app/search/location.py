"""Location-aware parsing (Sprint 3.3): topic + place, no geocoding APIs.

Understood expressions (matched on synonym-expanded normalized text):
- "<topic> near <place>", "<topic> in <place>"
- "<topic> <known place>" (trailing suffix)

The gazetteer is intentionally tiny — major event places only, coordinates
included so adapters can use platform geo search (YouTube
location/locationRadius) with no external geocoding. Unknown places stay in
the topic so keyword matching still applies; the raw attempt is exposed for
the UI ("unknown location"). Size pinned ≤ 20: no ontology.
"""

import re
from dataclasses import dataclass

from app.search.normalize import phrase_tokens

MAX_PLACES = 20


@dataclass(frozen=True)
class Place:
    name: str  # normalized form
    lat: float
    lng: float


PLACES: dict[str, Place] = {
    "los angeles": Place("los angeles", 34.05, -118.24),
    "new york": Place("new york", 40.71, -74.0),
    "san francisco": Place("san francisco", 37.77, -122.41),
    "chicago": Place("chicago", 41.88, -87.63),
    "florida": Place("florida", 27.99, -81.76),
    "texas": Place("texas", 31.0, -100.0),
    "california": Place("california", 36.78, -119.42),
    "tokyo": Place("tokyo", 35.68, 139.69),
    "london": Place("london", 51.5, -0.13),
    "paris": Place("paris", 48.85, 2.35),
    "japan": Place("japan", 36.2, 138.25),
    "ukraine": Place("ukraine", 48.38, 31.17),
}


@dataclass(frozen=True)
class ParsedQuery:
    topic: str  # normalized remainder for text signals ("" if none)
    place: str | None  # normalized known place (location signal + geo)
    place_attempt: str | None  # "near X" text when X is unknown


def gazetteer_lookup(location_text: str) -> tuple[str, Place] | None:
    """Deterministic text -> gazetteer place, or None (no geocoding)."""
    normalized = " ".join(
        part.lower() for part in location_text.replace(",", " ").split()
    )
    if not normalized:
        return None
    for place in PLACES.values():
        if place.name == normalized:
            return place.name, place
    # Token containment so "Downtown Los Angeles, CA" resolves to los angeles.
    for place in sorted(PLACES.values(), key=lambda p: len(p.name), reverse=True):
        if all(token in normalized.split() for token in place.name.split()):
            return place.name, place
    return None


def _clean_topic(topic: str) -> str:
    return re.sub(r"\b(?:near|in)$", "", topic).strip()


def parse_location(query: str) -> ParsedQuery:
    expanded = " ".join(phrase_tokens(query))
    match = re.match(r"^(.+?)\s+(?:near|in)\s+(.+)$", expanded)
    if match:
        place_text = match.group(2).strip()
        if place_text in PLACES:
            return ParsedQuery(
                topic=_clean_topic(match.group(1)), place=place_text, place_attempt=None
            )
        return ParsedQuery(topic=expanded, place=None, place_attempt=place_text or None)

    toks = expanded.split()
    for n in range(min(3, len(toks)), 0, -1):
        candidate = " ".join(toks[-n:])
        if candidate in PLACES:
            return ParsedQuery(
                topic=_clean_topic(" ".join(toks[:-n])),
                place=candidate,
                place_attempt=None,
            )
    return ParsedQuery(topic=expanded, place=None, place_attempt=None)


def place_coords(place: str) -> tuple[float, float] | None:
    found = PLACES.get(place)
    return (found.lat, found.lng) if found else None
