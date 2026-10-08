"""Map experiment (Sprint 8.2): can we put live events on a map at all?

Prototype only — NOT wired into the UI. Answers the roadmap question with
measured coverage rather than opinion.

Confidence tiers, deliberately explicit so a map never has to guess:
- "exact":  platform-reported coordinates (YouTube `recordingDetails`);
- "derived": our own deterministic gazetteer (app/search/location.py)
  resolved the free-text `location_text`. A guess, not a platform fact —
  shown at a different confidence because it is one.
- "unlocated": neither available.

Coverage is the whole experiment: only YouTube ever reports coordinates,
and rarely for live streams; Twitch reports none. So the honest question
is not "can we draw markers" but "what fraction of a real result set has
any location at all".
"""

import math
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.models.stream import Stream
from app.search.location import PLACES

# Cluster radius in km (roughly a metro area).
CLUSTER_RADIUS_KM = 50.0
EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float


class GeoMarker(BaseModel):
    stream_id: str
    platform: str
    platform_stream_id: str
    title: str
    channel_name: str
    confidence: str  # "exact" | "derived"
    source: str  # "platform-coordinates" | "gazetteer:<place>"
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class GeoCluster(BaseModel):
    lat: float
    lng: float
    radius_km: float
    count: int
    stream_ids: list[str] = Field(default_factory=list)


class CoverageReport(BaseModel):
    total: int = 0
    exact: int = 0
    derived: int = 0
    unlocated: int = 0

    @property
    def locatable(self) -> int:
        return self.exact + self.derived

    @property
    def locatable_fraction(self) -> float:
        return self.locatable / self.total if self.total else 0.0


class MapPayload(BaseModel):
    markers: list[GeoMarker] = Field(default_factory=list)
    clusters: list[GeoCluster] = Field(default_factory=list)
    coverage: CoverageReport


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lng, b.lat, b.lng))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def _gazetteer_lookup(location_text: str) -> tuple[str, GeoPoint] | None:
    """Deterministic text → coords via our own gazetteer (no network)."""
    normalized = " ".join(
        part.lower() for part in location_text.replace(",", " ").split()
    )
    if not normalized:
        return None
    for place in PLACES.values():
        if place.name == normalized:
            return place.name, GeoPoint(place.lat, place.lng)
    # Token containment so "Downtown Los Angeles, CA" resolves to los angeles.
    for place in sorted(PLACES.values(), key=lambda p: len(p.name), reverse=True):
        if all(token in normalized.split() for token in place.name.split()):
            return place.name, GeoPoint(place.lat, place.lng)
    return None


def resolve_marker(stream: Stream) -> GeoMarker | None:
    """Best available location for a record, or None if unlocatable."""
    if stream.latitude is not None and stream.longitude is not None:
        if not (-90 <= stream.latitude <= 90 and -180 <= stream.longitude <= 180):
            return None  # platform data can be nonsense — treat as unlocatable
        return GeoMarker(
            stream_id=stream.id,
            platform=stream.platform,
            platform_stream_id=stream.platform_stream_id,
            title=stream.title,
            channel_name=stream.channel_name,
            confidence="exact",
            source="platform-coordinates",
            lat=stream.latitude,
            lng=stream.longitude,
        )
    if stream.location_text:
        resolved = _gazetteer_lookup(stream.location_text)
        if resolved:
            place, point = resolved
            return GeoMarker(
                stream_id=stream.id,
                platform=stream.platform,
                platform_stream_id=stream.platform_stream_id,
                title=stream.title,
                channel_name=stream.channel_name,
                confidence="derived",
                source=f"gazetteer:{place}",
                lat=point.lat,
                lng=point.lng,
            )
    return None


def coverage(streams: list[Stream]) -> CoverageReport:
    report = CoverageReport(total=len(streams))
    for stream in streams:
        if stream.latitude is not None and stream.longitude is not None:
            report.exact += 1
        elif stream.location_text and _gazetteer_lookup(stream.location_text):
            report.derived += 1
        else:
            report.unlocated += 1
    return report


def cluster_markers(markers: list[GeoMarker]) -> list[GeoCluster]:
    """Single-linkage clustering at CLUSTER_RADIUS_KM (event clusters)."""
    points = [GeoPoint(m.lat, m.lng) for m in markers]
    parent = list(range(len(markers)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if haversine_km(points[i], points[j]) <= CLUSTER_RADIUS_KM:
                parent[find(i)] = find(j)

    groups: dict[int, list[int]] = {}
    for i in range(len(markers)):
        groups.setdefault(find(i), []).append(i)

    clusters: list[GeoCluster] = []
    for members in groups.values():
        cluster_markers_list = [points[i] for i in members]
        # Centroids are unweighted means — fine for a prototype, flagged in
        # the worklog as a known simplification (skewed by latitude).
        lat = sum(p.lat for p in cluster_markers_list) / len(cluster_markers_list)
        lng = sum(p.lng for p in cluster_markers_list) / len(cluster_markers_list)
        span = max(
            (haversine_km(cluster_markers_list[0], p) for p in cluster_markers_list),
            default=0.0,
        )
        clusters.append(
            GeoCluster(
                lat=lat,
                lng=lng,
                radius_km=max(span, CLUSTER_RADIUS_KM),
                count=len(members),
                stream_ids=[markers[i].stream_id for i in members],
            )
        )
    clusters.sort(key=lambda c: c.count, reverse=True)
    return clusters


def build_map_payload(streams: list[Stream]) -> MapPayload:
    markers = [m for m in (resolve_marker(s) for s in streams) if m is not None]
    return MapPayload(
        markers=markers,
        clusters=cluster_markers(markers),
        coverage=coverage(streams),
    )
