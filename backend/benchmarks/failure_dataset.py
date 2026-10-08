"""Failure dataset (Sprint 7.1): is keyword search actually insufficient?

Eight hand-labeled cases. Five are adversarial keyword gaps the deterministic
pipeline is EXPECTED to fail today (each pinned with its failure class and
reason); three are controls proving the pipeline works where it should.
The runner mirrors the service (parse → topic/place → rank) and reports
per-case pass/fail plus a summary.

Run: `python -m benchmarks.failure_dataset` (from `backend/`).
Interpreting: failures here motivate a 7.2 embedding PROTOTYPE measured
against this same set — never a production decision. If a future change
fixes a pinned failure, its test fails loudly: move the case to controls.
"""

from dataclasses import dataclass, field

from app.models.stream import Stream
from app.search.location import parse_location
from app.search.scoring import rank_streams


def _rec(id: str, title: str, **over) -> dict:
    base = {
        "id": id,
        "platform": "bench",
        "platform_stream_id": id,
        "title": title,
        "live_status": "live",
        "freshness": "fresh",
    }
    return {**base, **over}


@dataclass(frozen=True)
class FailureClass:
    name: str
    reason: str


@dataclass
class Case:
    id: str
    query: str
    records: list[dict]
    expected_top: str
    failure: FailureClass | None = None


CASES: list[Case] = [
    Case(
        id="vocab-gap-fire",
        query="wildfire los angeles",
        records=[
            _rec("a", "Brush blaze erupts", description="Crews on scene"),
            _rec("b", "Wildfire concert"),
        ],
        expected_top="a",
        failure=FailureClass(
            "vocabulary-gap",
            "relevant record shares no keywords (blaze≠wildfire); "
            "keyword-only title beats it",
        ),
    ),
    Case(
        id="synonym-gap-tremor",
        query="earthquakes",
        records=[
            _rec("a", "Major tremor hits coast"),
            _rec("b", "Earthquake drill"),
        ],
        expected_top="a",
        failure=FailureClass(
            "synonym-gap",
            "tremor is outside the 13-entry map; exact phrase match wins",
        ),
    ),
    Case(
        id="description-weight",
        query="rocket launch",
        records=[
            _rec("a", "LIVE NOW", description="SpaceX rocket launch from the cape"),
            _rec("b", "Launch day parade"),
        ],
        expected_top="a",
        failure=FailureClass(
            "description-weight",
            "topic lives in the description (15) but a title token (40) outranks it",
        ),
    ),
    Case(
        id="vague-title",
        query="concert tokyo",
        records=[
            _rec("a", "LIVE"),
            _rec("b", "Concert highlights"),
        ],
        expected_top="a",
        failure=FailureClass(
            "vague-title",
            "relevant broadcast titled 'LIVE'; nothing textual to match on",
        ),
    ),
    Case(
        id="exact-control",
        query="wildfire los angeles",
        records=[
            _rec("a", "Wildfire Los Angeles live"),
            _rec("b", "Cooking show"),
        ],
        expected_top="a",
    ),
    Case(
        id="location-control",
        query="storm florida",
        records=[
            _rec("a", "Storm update", location_text="Miami, Florida"),
            _rec("b", "Storm update", location_text="Austin, Texas"),
        ],
        expected_top="a",
    ),
    Case(
        id="plural-control",
        query="wildfires",
        records=[
            _rec("a", "Wildfire response live"),
            _rec("b", "Cooking show"),
        ],
        expected_top="a",
    ),
    Case(
        id="phrase-vs-meaning",
        query="flood rescue",
        records=[
            _rec("a", "Water rescue operations downtown"),
            _rec("b", "Flood rescue seminar recording"),
        ],
        expected_top="a",
        failure=FailureClass(
            "phrase-vs-meaning",
            "exact phrase match (100) beats the actually-relevant record; "
            "phrase containment is not understanding",
        ),
    ),
]


@dataclass
class CaseResult:
    case_id: str
    expected_top: str
    actual_top: str | None
    passed: bool
    failure: FailureClass | None = None


def evaluate(case: Case) -> CaseResult:
    streams = [Stream(**r) for r in case.records]
    parsed = parse_location(case.query)
    ranked = rank_streams(streams, parsed.topic or case.query, place=parsed.place)
    top = ranked[0].id if ranked else None
    return CaseResult(
        case_id=case.id,
        expected_top=case.expected_top,
        actual_top=top,
        passed=top == case.expected_top,
        failure=case.failure,
    )


@dataclass
class Summary:
    passed: int = 0
    failed: int = 0
    results: list[CaseResult] = field(default_factory=list)


def summarize() -> Summary:
    summary = Summary()
    for case in CASES:
        result = evaluate(case)
        summary.results.append(result)
        if result.passed:
            summary.passed += 1
        else:
            summary.failed += 1
    return summary


def report() -> str:
    lines = ["query | expected -> actual | verdict"]
    for result in summarize().results:
        if result.passed:
            mark = "PASS"
        elif result.failure is not None:
            mark = f"FAIL ({result.failure.name})"
        else:
            mark = "FAIL (UNEXPECTED control failure)"
        lines.append(
            f"{result.case_id}: expected {result.expected_top}"
            f" -> got {result.actual_top} | {mark}"
        )
    summary = summarize()
    lines.append(f"passed={summary.passed} failed={summary.failed} total={len(CASES)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
