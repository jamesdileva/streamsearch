"""Map experiment tests (Sprint 8.2 verification).

Confidence tiers must stay distinguishable, coverage must be measured
honestly, and clusters must merge nearby things without swallowing the
rest. Edge cases include nonsense platform coordinates.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models.stream import Stream
from app.search.geo import (
    GeoPoint,
    build_map_payload,
    cluster_markers,
    coverage,
    haversine_km,
    resolve_marker,
)

client = TestClient(app)


def _s(id: str, **over) -> Stream:
    base = {
        "id": id,
        "platform": "youtube",
        "platform_stream_id": id,
        "channel_name": "Chan",
        "title": f"Stream {id}",
        "live_status": "live",
    }
    return Stream(**{**base, **over})


def test_exact_coordinates_give_exact_confidence():
    marker = resolve_marker(_s("a", latitude=34.05, longitude=-118.24))
    assert marker is not None
    assert marker.confidence == "exact"
    assert marker.source == "platform-coordinates"
    assert (marker.lat, marker.lng) == (34.05, -118.24)


def test_location_text_resolves_via_gazetteer_as_derived():
    marker = resolve_marker(_s("a", location_text="Downtown Los Angeles, CA"))
    assert marker is not None
    assert marker.confidence == "derived"
    assert marker.source == "gazetteer:los angeles"
    # Gazetteer coordinates, not platform ones.
    assert (marker.lat, marker.lng) == (34.05, -118.24)


def test_unresolvable_text_is_unlocated():
    assert resolve_marker(_s("a", location_text="Somewhere over the rainbow")) is None
    assert resolve_marker(_s("a")) is None
    assert resolve_marker(_s("a", latitude=34.0, longitude=None)) is None


def test_nonsense_coordinates_treated_as_unlocatable():
    # Platform data is untrusted: outside valid ranges must not become markers.
    assert resolve_marker(_s("a", latitude=999.0, longitude=0.0)) is None
    assert resolve_marker(_s("a", latitude=0.0, longitude=999.0)) is None


def test_coverage_counts_each_tier():
    streams = [
        _s("a", latitude=34.05, longitude=-118.24),
        _s("b", location_text="Los Angeles, CA"),
        _s("c"),
        _s("d", location_text="Atlantis"),
        _s("e", latitude=1.0, longitude=2.0),
    ]
    report = coverage(streams)
    assert (report.total, report.exact, report.derived, report.unlocated) == (
        5, 2, 1, 2,
    )
    assert report.locatable == 3
    assert report.locatable_fraction == 0.6


def test_coverage_empty_set():
    report = coverage([])
    assert report.total == 0
    assert report.locatable_fraction == 0.0


def test_haversine_known_distance():
    la = GeoPoint(34.05, -118.24)
    nyc = GeoPoint(40.71, -74.0)
    assert 3900 < haversine_km(la, nyc) < 4000
    # Roughly antipodal to LA — near the ~20,015 km half-circumference max.
    assert haversine_km(la, GeoPoint(-34.05, 61.76)) > 19900


def test_clusters_merge_nearby_only():
    from app.search.geo import GeoMarker

    markers = [
        GeoMarker(stream_id="a", platform="y", platform_stream_id="a",
                  title="A", channel_name="C", confidence="exact",
                  source="platform-coordinates", lat=34.05, lng=-118.24),
        GeoMarker(stream_id="b", platform="y", platform_stream_id="b",
                  title="B", channel_name="C", confidence="exact",
                  source="platform-coordinates", lat=34.06, lng=-118.25),
        GeoMarker(stream_id="c", platform="y", platform_stream_id="c",
                  title="C", channel_name="C", confidence="exact",
                  source="platform-coordinates", lat=40.71, lng=-74.0),
    ]
    clusters = cluster_markers(markers)
    assert len(clusters) == 2
    biggest = clusters[0]
    assert biggest.count == 2
    assert set(biggest.stream_ids) == {"a", "b"}
    assert all(c.count >= 1 for c in clusters)


def test_singletons_cluster_alone():
    from app.search.geo import GeoMarker

    lonely = GeoMarker(stream_id="a", platform="y", platform_stream_id="a",
                       title="A", channel_name="C", confidence="derived",
                       source="gazetteer:tokyo", lat=35.68, lng=139.69)
    clusters = cluster_markers([lonely])
    assert len(clusters) == 1
    assert clusters[0].count == 1
    assert clusters[0].radius_km == 50.0


def test_build_payload_shape_and_coincident_markers():
    # Two records in the same city: one exact, one derived → same cluster.
    streams = [
        _s("a", latitude=34.05, longitude=-118.24),
        _s("b", location_text="Los Angeles, CA"),
        _s("c", location_text="Tokyo"),
    ]
    payload = build_map_payload(streams)
    assert len(payload.markers) == 3
    assert len(payload.clusters) == 2
    assert payload.coverage.exact == 1
    assert payload.coverage.derived == 2
    # Mixed-confidence cluster still merges — that's a prototype simplification
    # the worklog flags as a limitation, so pin it knowingly.
    la_cluster = next(c for c in payload.clusters if "a" in c.stream_ids)
    assert set(la_cluster.stream_ids) == {"a", "b"}


def test_geo_endpoint_rejects_empty_query():
    r = client.get("/api/geo", params={"q": "  "})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == 422


def test_geo_endpoint_measures_real_coverage():
    body = client.get("/api/geo", params={"q": "storm"}).json()
    # Fakes carry no location at all — the expected result for this dataset,
    # which is precisely the experiment's measurement.
    assert body["coverage"]["total"] == 3
    assert body["coverage"]["exact"] == 0
    assert body["coverage"]["derived"] == 0
    assert body["coverage"]["unlocated"] == 3
    assert body["markers"] == []
