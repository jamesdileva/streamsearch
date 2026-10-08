"""Failure-dataset pins (Sprint 7.1).

Each documented gap must KEEP failing exactly as recorded; each control
must keep passing. If a future change flips any case, this suite fails
loudly — that is the tripwire telling 7.2 to reclassify the case.
"""

from benchmarks.failure_dataset import CASES, evaluate, summarize


def test_controls_pass():
    controls = [c for c in CASES if c.failure is None]
    assert len(controls) == 3
    for case in controls:
        result = evaluate(case)
        assert result.passed, f"control regressed: {case.id}"


def test_documented_gaps_fail_as_recorded():
    gaps = [c for c in CASES if c.failure is not None]
    assert len(gaps) == 5
    for case in gaps:
        result = evaluate(case)
        assert not result.passed, f"gap fixed, reclassify: {case.id}"
        # Retrieved but misranked (not missing) — ranking, not recall.
        assert result.actual_top is not None
        assert result.actual_top != case.expected_top


def test_failure_classes_are_known():
    known = {
        "vocabulary-gap",
        "synonym-gap",
        "description-weight",
        "vague-title",
        "phrase-vs-meaning",
    }
    for case in CASES:
        if case.failure is not None:
            assert case.failure.name in known
            assert case.failure.reason


def test_summary_counts():
    summary = summarize()
    assert (summary.passed, summary.failed) == (3, 5)
