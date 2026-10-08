"""Embedding experiment (Sprint 7.2): keyword vs semantic vs hybrid.

Replays the 7.1 failure dataset through all three rankers and reports
per-case winners plus summary counts. Requires Ollama serving
EMBEDDINGS_MODEL — fails loudly otherwise (prototype context, not a
test dependency).

Run: `python -m benchmarks.embedding_experiment` (from `backend/`).
"""

import time
from dataclasses import dataclass, field

from app.models.stream import Stream
from app.search.embeddings import OllamaEmbeddings, hybrid_rank
from app.search.location import parse_location
from app.search.scoring import rank_streams, score_stream
from benchmarks.failure_dataset import CASES


@dataclass
class ExperimentRow:
    case_id: str
    expected: str
    keyword_top: str | None
    semantic_top: str | None
    hybrid_top: str | None


@dataclass
class ExperimentReport:
    rows: list[ExperimentRow] = field(default_factory=list)
    seconds: float = 0.0

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


def run(embeddings: OllamaEmbeddings | None = None) -> ExperimentReport:
    embeddings = embeddings or OllamaEmbeddings()
    if not embeddings.is_reachable():
        raise SystemExit("ollama not reachable; start it or set OLLAMA_HOST")
    report = ExperimentReport()
    started = time.monotonic()
    for case in CASES:
        streams = [Stream(**r) for r in case.records]
        parsed = parse_location(case.query)
        topic = parsed.topic or case.query
        kw_ranked = rank_streams(streams, topic, place=parsed.place)
        kw_top = kw_ranked[0].id if kw_ranked else None
        kw_totals = [score_stream(s, topic, place=parsed.place).total for s in streams]
        hybrid = hybrid_rank(streams, kw_totals, case.query, embeddings)
        sem_top = max(hybrid, key=lambda r: r.semantic).stream.id if hybrid else None
        report.rows.append(
            ExperimentRow(
                case_id=case.id,
                expected=case.expected_top,
                keyword_top=kw_top,
                semantic_top=sem_top,
                hybrid_top=hybrid[0].stream.id if hybrid else None,
            )
        )
    report.seconds = time.monotonic() - started
    return report


def text_report(report: ExperimentReport) -> str:
    lines = ["case | expected | keyword / semantic / hybrid (OK = top)"]
    for row in report.rows:
        marks = " / ".join(
            f"{top or '-'} {'OK' if top == row.expected else '--'}"
            for top in (row.keyword_top, row.semantic_top, row.hybrid_top)
        )
        lines.append(f"{row.case_id}: exp {row.expected} | {marks}")
    counts = report.counts()
    lines.append(
        f"keyword={counts['keyword']} semantic={counts['semantic']}"
        f" hybrid={counts['hybrid']} total={len(report.rows)}"
        f" ({report.seconds:.1f}s)"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    print(text_report(run()))
