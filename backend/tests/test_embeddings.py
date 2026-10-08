"""Embedding prototype tests (Sprint 7.2).

Pure vector/hybrid logic always runs (no network, no model). Integration
tests skip when Ollama isn't reachable, so `pytest` stays green in CI
while still proving the prototype end-to-end on a dev box.
"""

import math

import httpx
import pytest

from app.config import settings
from app.models.stream import Stream
from app.search.embeddings import (
    MODEL_PRESETS,
    HybridBreakdown,
    OllamaEmbeddings,
    cosine,
    hybrid_rank,
    preset_for,
    record_text,
)

REQUIRES_OLLAMA = pytest.mark.skipif(
    not OllamaEmbeddings().is_reachable(),
    reason="ollama not reachable (set OLLAMA_HOST or start ollama)",
)


def _stream(title: str, pid: str, description: str = "") -> Stream:
    return Stream(
        id=pid, platform="bench", platform_stream_id=pid, title=title,
        description=description, live_status="live",
    )


def _norm(vec: list[float]) -> list[float]:
    size = math.sqrt(sum(x * x for x in vec))
    return [x / size for x in vec]


def test_cosine_bounds_and_orthogonality():
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine([1.0, 0.0], [2.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [-3.0, 0.0]) == pytest.approx(-1.0)
    assert cosine([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_cosine_bounds_phi():
    # Near-collinear vectors with rounding noise still clamp to 1.0.
    v = _norm([1.0, 2.0, 3.0])
    noise = [x + 1e-12 for x in v]
    assert cosine(v, noise) <= 1.0


def test_record_text_prefers_title_then_description_then_channel():
    s = _stream("Brush blaze erupts", "a", description="Crews on scene")
    assert record_text(s) == "Brush blaze erupts. Crews on scene"


def test_record_text_truncated_to_max_chars():
    s = _stream("x" * 900, "a")
    assert len(record_text(s)) == 500


class _FakeEmbeddings(OllamaEmbeddings):
    """Stub: deterministic vectors keyed by raw text (no prefixes)."""

    def __init__(self, by_text: dict[str, list[float]]) -> None:
        self.by_text = by_text
        self.query_prefix = ""
        self.doc_prefix = ""

    def embed_query(self, query: str) -> list[float]:
        return self.by_text[query]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.by_text[t] for t in texts]


def test_hybrid_blends_normalized_keyword_and_semantic():
    # Streams have no description/channel, so record_text == title.
    by_text = {"alpha": [1.0, 0.0], "beta": [0.0, 1.0]}
    a, b = _stream("alpha", "a"), _stream("beta", "b")
    # hybrid_rank queries embeddings for the raw query string too.
    stub = _FakeEmbeddings({**by_text, "q": [1.0, 0.0]})
    ranked = hybrid_rank([a, b], [10.0, 20.0], "q", stub)
    assert all(isinstance(r.breakdown, HybridBreakdown) for r in ranked)
    # a: kw 0.0 (min), sem 1.0 -> 0.5 ; b: kw 1.0, sem 0.0 -> 0.5
    assert ranked[0].hybrid == pytest.approx(0.5)
    assert ranked[1].hybrid == pytest.approx(0.5)
    assert ranked[0].stream.id == "a"  # stable order on the tie


def test_hybrid_respects_weight():
    stub = _FakeEmbeddings({"a": [1.0], "b": [1.0], "q": [1.0]})
    ranked = hybrid_rank(
        [_stream("a", "a"), _stream("b", "b")],
        [1.0, 2.0],
        "q",
        stub,
        keyword_weight=1.0,
    )
    assert ranked[0].stream.id == "b"  # pure keyword order


def test_hybrid_normalizes_flat_scores():
    stub = _FakeEmbeddings({"a": [1.0], "b": [1.0], "q": [1.0]})
    ranked = hybrid_rank(
        [_stream("a", "a"), _stream("b", "b")],
        [5.0, 5.0],
        "q",
        stub,
        keyword_weight=1.0,
    )
    assert all(r.breakdown.keyword == 0.5 for r in ranked)


def test_stub_raises_on_unknown_text():
    with pytest.raises(KeyError):
        _FakeEmbeddings({}).embed_documents(["missing"])


def test_bad_server_payload_raises_controlled_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"nope": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    embeddings = OllamaEmbeddings(client=client)
    with pytest.raises(Exception, match="malformed"):
        embeddings.embed(["x"])


def test_server_error_raises_controlled_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(Exception, match="status 500"):
        OllamaEmbeddings(client=client).embed(["x"])


# --- ModelPreset scaffolding (the 7.2b fix) -------------------------------


def test_preset_resolution_by_prefix():
    assert preset_for("nomic-embed-text").query_prefix == "search_query: "
    assert preset_for("nomic-embed-text").doc_prefix == "search_document: "
    assert preset_for("nomic-embed-text:latest").query_prefix == "search_query: "
    assert preset_for("qwen3-embedding:0.6b").query_prefix.startswith("Instruct:")
    assert preset_for("qwen3-embedding:0.6b").doc_prefix == ""
    assert preset_for("embeddinggemma").query_prefix == "task: search result | query: "
    assert preset_for("embeddinggemma").doc_prefix == "title: none | text: "
    assert preset_for("bge-m3").query_prefix == ""
    assert preset_for("bge-m3").doc_prefix == ""
    assert preset_for("some-unknown-model").query_prefix == ""


def test_presets_carry_sources():
    for preset in MODEL_PRESETS.values():
        assert preset.source, "every preset must cite its model card"


def test_client_applies_documented_prefixes_to_the_wire():
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content)
        bodies.append(payload)
        return httpx.Response(
            200, json={"embeddings": [[1.0]] * len(payload["input"])}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    embeddings = OllamaEmbeddings(model="embeddinggemma", client=client)
    embeddings.embed_query("wildfire la")
    embeddings.embed_documents(["Brush blaze erupts"])
    assert bodies[0]["input"] == ["task: search result | query: wildfire la"]
    assert bodies[1]["input"] == ["title: none | text: Brush blaze erupts"]


def test_client_cache_is_prefix_aware():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        calls["n"] += 1
        payload = json.loads(request.content)
        return httpx.Response(
            200, json={"embeddings": [[1.0]] * len(payload["input"])}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    embeddings = OllamaEmbeddings(model="embeddinggemma", client=client)
    embeddings.embed_query("same")
    embeddings.embed_documents(["same"])
    # Same raw text, different roles -> two distinct cache entries.
    assert calls["n"] == 2
    assert embeddings.embed_query("same") is embeddings.embed_query("same")
    assert calls["n"] == 2  # cached afterwards


def test_env_overrides_beat_presets(monkeypatch):
    monkeypatch.setattr(settings, "embeddings_query_prefix", "Q: ")
    monkeypatch.setattr(settings, "embeddings_doc_prefix", "D: ")
    e = OllamaEmbeddings(model="nomic-embed-text", client=httpx.Client())
    assert e.query_prefix == "Q: "
    assert e.doc_prefix == "D: "
    monkeypatch.setattr(settings, "embeddings_query_prefix", None)
    monkeypatch.setattr(settings, "embeddings_doc_prefix", None)


@REQUIRES_OLLAMA
def test_real_model_returns_dense_vectors_and_caches():
    embeddings = OllamaEmbeddings()
    first = embeddings.embed_documents(["wildfire live"])
    second = embeddings.embed_documents(["wildfire live"])
    assert len(first) == 1 and len(first[0]) > 64
    assert first[0] is second[0]  # cached, not recomputed


@REQUIRES_OLLAMA
def test_semantic_ranks_keyword_overlap_above_true_relevance():
    """Tripwire documenting the 7.2 finding (nomic-embed-text limits)."""
    from benchmarks.failure_dataset import CASES

    embeddings = OllamaEmbeddings()
    case = next(c for c in CASES if c.id == "vocab-gap-fire")
    streams = [Stream(**r) for r in case.records]
    sims = hybrid_rank(streams, [0.0, 0.0], case.query, embeddings)
    top = sims[0].stream.id
    assert top == "b"  # literal-keyword record still outranks the relevant one
