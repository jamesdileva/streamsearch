"""Embedding bake-off (Sprint 7.2b): keyword vs semantic vs hybrid, per model.

Replays the 7.1 failure dataset for each candidate model, applying that
model's documented query/document prefixes. Emits a comparison table so
7.3 can decide on evidence rather than assumption.

Run: `python -m benchmarks.embedding_experiment` (default bake-off)
     `python -m benchmarks.embedding_experiment --model nomic-embed-text`
"""

import sys
import time
from dataclasses import dataclass, field

from app.models.stream import Stream
from app.search.embeddings import OllamaEmbeddings, hybrid_rank, preset_for
from app.search.location import parse_location
from app.search.scoring import rank_streams, score_stream
from benchmarks.failure_dataset import CASES

# Ordered cheapest-first; nomic (already installed) is the fair re-baseline.
BAKEOFF_MODELS = [
    "nomic-embed-text",
    "embeddinggemma",
    "qwen3-embedding:0.6b",
    "bge-m3",
]


@dataclass
class CaseRow:
    case_id: str
    expected: str
    keyword_top: str | None
    semantic_top: str | None
    hybrid_top: str | None


@dataclass
class ModelReport:
    model: str
    rows: list[CaseRow] = field(default_factory=list)
    seconds: float = 0.0
    error: str | None = None

    def counts(self) -> dict[str, int]:
        tally = {"keyword": 0, "semantic": 0, "hybrid": 0}
        for row in self.rows:
            if row.keyword_top == row.expected:
                tally["keyword"] += 1
            if row.semantic_top == row.expected:
                tally["semantic"] += 1
            if row.hybrid_top == row.expected:
                tally["hybrid"] += 1
        return tally


def run_model(model: str) -> ModelReport:
    embeddings = OllamaEmbeddings(model=model)
    report = ModelReport(model=model)
    if not embeddings.is_reachable():
        report.error = "ollama not reachable"
        return report
    started = time.monotonic()
    for case in CASES:
        streams = [Stream(**r) for r in case.records]
        parsed = parse_location(case.query)
        topic = parsed.topic or case.query
        kw_ranked = rank_streams(streams, topic, place=parsed.place)
        kw_totals = [
            score_stream(s, topic, place=parsed.place).total for s in streams
        ]
        hybrid = hybrid_rank(streams, kw_totals, case.query, embeddings)
        sem_top = (
            max(hybrid, key=lambda r: r.semantic).stream.id if hybrid else None
        )
        report.rows.append(
            CaseRow(
                case_id=case.id,
                expected=case.expected_top,
                keyword_top=kw_ranked[0].id if kw_ranked else None,
                semantic_top=sem_top,
                hybrid_top=hybrid[0].stream.id if hybrid else None,
            )
        )
    report.seconds = time.monotonic() - started
    return report


def bakeoff(models: list[str] | None = None) -> list[ModelReport]:
    return [run_model(model) for model in (models or BAKEOFF_MODELS)]


def _short(text: str, limit: int = 24) -> str:
    first = text.splitlines()[0] if text else ""
    return first[:limit] + ("…" if len(first) > limit else "")


def table(reports: list[ModelReport]) -> str:
    lines = ["model | keyword | semantic | hybrid | secs | notes"]
    for report in reports:
        if report.error:
            lines.append(f"{report.model} | - | - | - | - | {report.error}")
            continue
        tally = report.counts()
        preset = preset_for(report.model)
        note = (
            f"prefixes q={_short(preset.query_prefix)!r} "
            f"d={_short(preset.doc_prefix)!r}"
            if (preset.query_prefix or preset.doc_prefix)
            else "prefixes: none"
        )
        lines.append(
            f"{report.model} | {tally['keyword']}/8 | {tally['semantic']}/8"
            f" | {tally['hybrid']}/8 | {report.seconds:.1f} | {note}"
        )
    return "\n".join(lines)


def details(report: ModelReport) -> str:
    lines = [f"--- {report.model} ---"]
    for row in report.rows:
        cells = " / ".join(
            f"{top or '-'} {'OK' if top == row.expected else '--'}"
            for top in (row.keyword_top, row.semantic_top, row.hybrid_top)
        )
        lines.append(f"  {row.case_id}: exp {row.expected} | {cells}")
    return "\n".join(lines)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    models = args or BAKEOFF_MODELS
    reports = bakeoff(models)
    print(table(reports))
    if verbose:
        for report in reports:
            print(details(report))
