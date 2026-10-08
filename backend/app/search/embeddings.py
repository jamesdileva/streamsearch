"""Embedding prototype (Sprint 7.2) — EXPERIMENTAL, not wired into search.

Semantic ranking via a local Ollama embedding model (default
nomic-embed-text, 768 dims). No torch/sentence-transformers dependency:
plain HTTP, httpx only. cosine() and hybrid blending are pure and unit
tested; the Ollama client is thin and integration-tested with server
skip-guards. Failures here raise EmbeddingsError — the production search
path never calls this module (7.3 decides if it ever should).
"""

import math
from dataclasses import dataclass, field

import httpx

from app.config import settings
from app.models.stream import Stream

MAX_TEXT_CHARS = 500


class EmbeddingsError(Exception):
    """Controlled embeddings failure (server down, unknown model, bad payload)."""


@dataclass
class HybridBreakdown:
    total: float
    keyword: float
    semantic: float


class OllamaEmbeddings:
    """Thin client for Ollama /api/embed with a text cache."""

    def __init__(
        self,
        host: str = "",
        model: str = "",
        timeout_seconds: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.embeddings_model
        self.timeout_seconds = timeout_seconds
        self._client = client
        self._cache: dict[str, list[float]] = {}

    def _post(self, texts: list[str]) -> list[list[float]]:
        try:
            if self._client is not None:
                response = self._client.post(
                    f"{self.host}/api/embed",
                    json={"model": self.model, "input": texts},
                )
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(
                        f"{self.host}/api/embed",
                        json={"model": self.model, "input": texts},
                    )
        except httpx.RequestError as exc:
            raise EmbeddingsError(f"embeddings request failed: {exc}") from exc
        if response.status_code != 200:
            raise EmbeddingsError(
                f"embeddings request failed (status {response.status_code})"
            )
        try:
            vectors = response.json()["embeddings"]
        except (ValueError, KeyError, TypeError) as exc:
            raise EmbeddingsError("embeddings returned malformed JSON") from exc
        if not isinstance(vectors, list) or not all(
            isinstance(v, list) for v in vectors
        ):
            raise EmbeddingsError("embeddings returned an unexpected payload")
        return vectors

    def embed(self, texts: list[str]) -> list[list[float]]:
        missing = [t for t in texts if t not in self._cache]
        if missing:
            for text, vector in zip(missing, self._post(missing), strict=True):
                self._cache[text] = [float(x) for x in vector]
        return [self._cache[t] for t in texts]

    def is_reachable(self) -> bool:
        try:
            if self._client is not None:
                response = self._client.get(f"{self.host}/api/tags")
            else:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except httpx.RequestError:
            return False


def record_text(stream: Stream) -> str:
    """Matchable text for a record: title, description, channel."""
    parts = [stream.title or "", stream.description or "", stream.channel_name or ""]
    return ". ".join(p for p in parts if p.strip())[:MAX_TEXT_CHARS]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def _min_max(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


@dataclass
class ScoredStream:
    stream: Stream
    keyword: float
    semantic: float
    hybrid: float
    breakdown: HybridBreakdown = field(
        default_factory=lambda: HybridBreakdown(0.0, 0.0, 0.0)
    )


def hybrid_rank(
    streams: list[Stream],
    keyword_totals: list[float],
    query: str,
    embeddings: OllamaEmbeddings,
    keyword_weight: float = 0.5,
) -> list[ScoredStream]:
    """Blend min-max-normalized keyword totals with cosine similarity.

    Normalization is per candidate set (scores are only comparable within
    one query). keyword_weight=0.5 is the documented experimental blend —
    7.3 may tune it only with benchmark evidence.
    """
    vectors = embeddings.embed([query] + [record_text(s) for s in streams])
    query_vec, record_vecs = vectors[0], vectors[1:]
    sims = [cosine(query_vec, v) for v in record_vecs]
    norm_kw = _min_max(list(keyword_totals))
    norm_sem = _min_max(sims)
    ranked: list[ScoredStream] = []
    for stream, kw, sem, nkw, nsem in zip(
        streams, keyword_totals, sims, norm_kw, norm_sem, strict=True
    ):
        total = keyword_weight * nkw + (1.0 - keyword_weight) * nsem
        ranked.append(
            ScoredStream(
                stream=stream,
                keyword=kw,
                semantic=sem,
                hybrid=total,
                breakdown=HybridBreakdown(total, nkw, nsem),
            )
        )
    ranked.sort(key=lambda r: r.hybrid, reverse=True)
    return ranked
