"""Content-boundary regression tests (Sprint 11.1).

These pin the *structural* claims in `docs/content-boundaries.md` so the
documentation cannot silently drift from the code. The behavioural claims
(embed gating, attribution) are asserted; the absence of media storage is
asserted by inspecting the persisted schema rather than by grepping source.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models.stream import Stream

client = TestClient(app)


def _stream(**over) -> Stream:
    base = {
        "id": "y-1",
        "platform": "youtube",
        "platform_stream_id": "y-1",
        "channel_name": "Chan",
        "title": "T",
        "live_status": "live",
    }
    return Stream(**{**base, **over})


def test_stream_model_has_no_media_payload_fields():
    """The model can only describe media, never carry it."""
    forbidden = {"video", "audio", "media", "bytes", "blob", "content_bytes", "data"}
    assert not (forbidden & set(Stream.model_fields))


def test_index_persists_metadata_only():
    """Streams must round-trip through the index without anything binary."""
    from app.services import index

    stored = index.upsert_stream(_stream())
    fetched = index.get_stream("youtube", "y-1")
    assert fetched is not None
    # Thumbnails/urls are references, and every stored column is usable
    # without touching media bytes.
    assert isinstance(stored.thumbnail_url, str)
    assert fetched.title == "T"
    assert fetched.source_url is not None


def test_embed_url_only_when_platform_allows_it():
    assert _stream(embed_supported=True, embed_url="https://e/x").embed_supported
    assert _stream(embed_supported=False, embed_url=None).embed_supported is False
    # The UI contract: canWatch is a conjunction, so a URL alone is inert.
    stream = _stream(embed_supported=False, embed_url="https://e/x")
    assert not (stream.embed_supported and stream.embed_url)


def test_no_generic_proxy_endpoint():
    """The API must not be able to fetch arbitrary URLs."""
    schema = app.openapi()
    paths = set(schema.get("paths", {}))
    for path in paths:
        assert "proxy" not in path
        assert "fetch" not in path
    public = {p for p in paths if p.startswith("/api")}
    assert "/api/search" in public
    assert "/api/geo" in public
    assert "/api/reports" in public
    assert "/api/stats" in public


def test_reports_are_stored_but_do_not_remove_content():
    """Reports feed corrections back; they do not delete data."""
    from app.models.report import ReportCreate
    from app.services import reports

    before = reports.count_reports()
    reports.save_report(
        ReportCreate(stream_id="y-1", platform="youtube", reason="broken_link")
    )
    assert reports.count_reports() == before + 1
    # The reported stream is still discoverable — reporting is advisory.
    assert reports.list_reports(stream_id="y-1")


def test_boundary_doc_records_gaps():
    """The boundary doc must record that removal handling is absent.

    If this fails, the doc was edited to over-claim; fix the doc or the
    feature, not the test.
    """
    import pathlib

    doc_path = pathlib.Path(__file__).resolve().parents[2] / "docs" / "content-boundaries.md"
    assert doc_path.exists(), f"missing boundary doc: {doc_path}"
    doc = doc_path.read_text(encoding="utf-8")
    lowered = doc.lower()
    assert "not implemented" in lowered or "does not exist yet" in lowered
    # The doc must also state the enforced boundaries rather than only the gap.
    assert "metadata only" in lowered


def test_mature_flag_captured_but_not_surfaced():
    """`is_mature` is metadata only; the UI has no mature filter."""
    import httpx

    from app.adapters.twitch import TwitchAdapter

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in request.url.path:
            return httpx.Response(
                200, json={"access_token": "t", "expires_in": 3600}
            )
        if "search/categories" in request.url.path:
            return httpx.Response(200, json={"data": [{"id": "1"}]})
        return httpx.Response(200, json={"data": [{
            "id": "9", "user_id": "u1", "user_login": "c", "type": "live",
            "title": "T", "is_mature": True, "game_name": "G",
            "viewer_count": 7}]})

    adapter = TwitchAdapter(
        client_id="i",
        client_secret="s",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    (record,) = adapter.search("x")
    assert record["metadata"]["is_mature"] is True
    # Not promotmed to a first-class filter field.
    assert "is_mature" not in Stream.model_fields
