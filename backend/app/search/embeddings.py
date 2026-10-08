"""Embedding prototype (Sprint 7.2 / bake-off 7.2b) — EXPERIMENTAL, not
wired into search.

Semantic ranking via a local Ollama embedding model (default
nomic-embed-text, 768 dims). No torch/sentence-transformers dependency:
plain HTTP, httpx only. cosine() and hybrid blending are pure and unit
tested; the Ollama client is thin and integration-tested with server
skip-guards. Failures here raise EmbeddingsError — the production search
path never calls this module (7.3 decides if it ever should).

Per-model task prefixes (ModelPreset) are applied automatically: several
popular models were trained with query/document scaffolding and quietly
degrade without it. Env overrides: EMBEDDINGS_QUERY_PREFIX /
EMBEDDINGS_DOC_PREFIX.
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


class ModelPreset:
    """Documented query/document scaffolding for an embedding model.

    Several popular models were trained with task prefixes and silently
    degrade without them (the 7.2 nomic run missed this). Sources are
    noted per model so a future reader can verify rather than trust.
    """

    def __init__(
        self,
        query_prefix: str = "",
        doc_prefix: str = "",
        source: str = "",
    ) -> None:
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix
        self.source = source


MODEL_PRESETS: dict[str, ModelPreset] = {
    # Model card: embed documents as search_document:, queries as search_query:
    "nomic-embed-text": ModelPreset(
        "search_query: ",
        "search_document: ",
        "nomic-ai model card (task instruction prefixes)",
    ),
    # Model card: query needs a one-line instruction; documents are raw.
    "qwen3-embedding": ModelPreset(
        "Instruct: Given a live stream search query, retrieve relevant live"
        " broadcast titles and descriptions\nQuery:",
        "",
        "Qwen3-Embedding README get_detailed_instruct",
    ),
    # Model card: query -> "task: search result | query: ", doc -> "title: none | text: "
    "embeddinggemma": ModelPreset(
        "task: search result | query: ",
        "title: none | text: ",
        "EmbeddingGemma model card / HF blog",
    ),
    # Model card: no prefixes required for retrieval.
    "bge-m3": ModelPreset("", "", "BAAI bge-m3 model card"),
}

DEFAULT_PRESET = ModelPreset(source="no documented prefixes for this model")


def preset_for(model: str) -> ModelPreset:
    """Longest-prefix match so tags like ":latest" / ":0.6b" resolve."""
    matches = [name for name in MODEL_PRESETS if model.startswith(name)]
    return MODEL_PRESETS[max(matches, key=len)] if matches else DEFAULT_PRESET


class OllamaEmbeddings:
    """Thin client for Ollama /api/embed with a text cache."""

    def __init__(
        self,
        host: str = "",
        model: str = "",
        timeout_seconds: float = 60.0,
        client: httpx.Client | None = None,
        query_prefix: str | None = None,
        doc_prefix: str | None = None,
    ) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.embeddings_model
        self.timeout_seconds = timeout_seconds
        self._client = client
        self._cache: dict[str, list[float]] = {}
        preset = preset_for(self.model)
        # Env override wins, then explicit arguments, then the model preset.
        env_q, env_d = settings.embeddings_query_prefix, settings.embeddings_doc_prefix
        self.query_prefix = env_q if env_q is not None else (query_prefix if query_prefix is not None else preset.query_prefix)
        self.doc_prefix = env_d if env_d is not None else (doc_prefix if doc_prefix is not None else preset.doc_prefix)

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

    def embed(self, texts: list[str], prefix: str = "") -> list[list[float]]:
        # Cache on the wire text (prefix included) so a client shared
        # across roles can never serve a document vector for a query.
        wire = [prefix + t for t in texts]
        missing = [w for w in wire if w not in self._cache]
        if missing:
            for text, vector in zip(missing, self._post(missing), strict=True):
                self._cache[text] = [float(x) for x in vector]
        return [self._cache[w] for w in wire]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query], self.query_prefix)[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts, self.doc_prefix)

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

    Query and records are embedded with their model's documented
    query/document prefixes (see ModelPreset) — asymmetric scaffolding
    matters and was missing from the first 7.2 run.

    Normalization is per candidate set (scores are only comparable within
    one query). keyword_weight=0.5 is the documented experimental blend —
    7.3 may tune it only with benchmark evidence.
    """
    query_vec = embeddings.embed_query(query)
    record_vecs = embeddings.embed_documents([record_text(s) for s in streams])
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
