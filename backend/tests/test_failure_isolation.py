"""Platform failure isolation (Sprint 10.1 verification).

Each failure mode is simulated while another adapter stays healthy. The
invariant: one broken platform degrades that platform's section, never the
search — partial results survive, and only a *total* outage is a 502.
"""

from fastapi.testclient import TestClient

from app.adapters.base import AdapterConfigError, AdapterError, BasePlatformAdapter
from app.main import app
from app.services.cache import SearchCache
from app.services.search import SearchService, get_search_service

client = TestClient(app)


class _Healthy(BasePlatformAdapter):
    platform = "healthy"

    def search(self, query: str) -> list[dict]:
        return [
            {
                "id": "h-1",
                "platform": self.platform,
                "platform_stream_id": "h-1",
                "channel_name": "Healthy Channel",
                "title": "Healthy stream",
                "live_status": "live",
            }
        ]


class _Failing(BasePlatformAdapter):
    platform = "failing"

    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def search(self, query: str) -> list[dict]:
        raise self.exc


class _Empty(BasePlatformAdapter):
    platform = "empty"

    def search(self, query: str) -> list[dict]:
        return []


MODES: dict[str, Exception] = {
    "timeout": AdapterError("request failed: timed out"),
    "quota-exhausted": AdapterError("api access denied or quota exhausted (403)"),
    "rate-limited": AdapterError("api rate limited (429)"),
    "auth-failure": AdapterError("auth failed (401)"),
    "malformed-response": AdapterError("platform returned malformed JSON"),
    "outage": AdapterError("request failed: connection refused"),
    "misconfigured": AdapterConfigError("CLIENT_ID/SECRET not configured"),
}


def test_route_never_echoes_internals_on_total_outage():
    """Degraded platforms surface their own controlled messages; the 502
    envelope for a total outage stays opaque (no adapter detail, no keys)."""
    service = SearchService(
        adapters=[_Failing(MODES["auth-failure"])], cache=SearchCache(ttl_seconds=0)
    )
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        response = client.get("/api/search", params={"q": "wildfire"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 502
    body = response.json()
    assert body == {
        "error": {"code": 502, "message": "live search temporarily unavailable"}
    }
    # The adapter's message (and any hypothetical credential it echoed)
    # must not reach the client on a total outage.
    assert "auth failed" not in str(body).lower()


def test_partial_outage_details_are_status_only_not_stack_traces():
    service = SearchService(
        adapters=[_Failing(MODES["malformed-response"]), _Healthy()],
        cache=SearchCache(ttl_seconds=0),
    )
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        response = client.get("/api/search", params={"q": "wildfire"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    (failing,) = [
        s for s in response.json()["platform_status"] if s["status"] == "error"
    ]
    assert failing["detail"] == "platform returned malformed JSON"
    assert "Traceback" not in failing["detail"]


def test_every_failure_mode_keeps_healthy_results():
    for name, exc in MODES.items():
        service = SearchService(
            adapters=[_Failing(exc), _Healthy()], cache=SearchCache(ttl_seconds=60)
        )
        response = service.search("wildfire")
        assert response.count == 1, f"{name} lost the healthy platform's results"
        assert [s.id for s in response.results] == ["h-1"]

        by_platform = {s.platform: s for s in response.platform_status}
        assert by_platform["healthy"].status == "ok"
        assert by_platform["failing"].status == "error", name
        # The adapter contract: errors are safe to surface (no secrets).
        assert by_platform["failing"].detail


def test_empty_result_is_not_an_error():
    service = SearchService(
        adapters=[_Empty(), _Healthy()], cache=SearchCache(ttl_seconds=60)
    )
    response = service.search("wildfire")
    statuses = {s.platform: s.status for s in response.platform_status}
    assert statuses["empty"] == "ok"
    assert statuses["healthy"] == "ok"
    assert response.count == 1


def test_all_platforms_failing_reports_all_errors():
    service = SearchService(
        adapters=[_Failing(MODES["timeout"]), _Failing(MODES["quota-exhausted"])],
        cache=SearchCache(ttl_seconds=60),
    )
    response = service.search("wildfire")
    assert response.results == []
    assert len(response.platform_status) == 2
    assert all(s.status == "error" for s in response.platform_status)


def test_degraded_responses_are_not_cached():
    # Failures must stay immediately retryable for the whole TTL.
    service = SearchService(
        adapters=[_Failing(MODES["timeout"]), _Healthy()],
        cache=SearchCache(ttl_seconds=60),
    )
    service.search("wildfire")
    assert service.cache.size == 0


def test_healthy_responses_are_still_cached():
    service = SearchService(adapters=[_Healthy()], cache=SearchCache(ttl_seconds=60))
    service.search("wildfire")
    assert service.cache.size == 1


def test_api_returns_partial_results_with_status():
    service = SearchService(
        adapters=[_Failing(MODES["outage"]), _Healthy()],
        cache=SearchCache(ttl_seconds=0),
    )
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        response = client.get("/api/search", params={"q": "wildfire"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200, "a partial outage must not be a 502"
    body = response.json()
    assert body["count"] == 1
    statuses = {s["platform"]: s["status"] for s in body["platform_status"]}
    assert statuses == {"failing": "error", "healthy": "ok"}


def test_api_total_outage_is_502():
    service = SearchService(
        adapters=[_Failing(MODES["outage"])], cache=SearchCache(ttl_seconds=0)
    )
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        response = client.get("/api/search", params={"q": "wildfire"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 502
    assert response.json() == {
        "error": {"code": 502, "message": "live search temporarily unavailable"}
    }


def test_api_genuinely_empty_is_200():
    service = SearchService(adapters=[_Empty()], cache=SearchCache(ttl_seconds=0))
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        response = client.get("/api/search", params={"q": "wildfire"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []


def test_status_detail_is_capped():
    long = AdapterError("x" * 5000)
    service = SearchService(
        adapters=[_Failing(long)], cache=SearchCache(ttl_seconds=0)
    )
    (status,) = service.search("q").platform_status
    assert len(status.detail or "") <= 200
