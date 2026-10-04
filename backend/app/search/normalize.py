"""Query normalization without AI (Sprint 3.2).

Lowercase → strip punctuation → collapse whitespace → expand a tiny,
explicit synonym map. Applied symmetrically to queries AND stored fields,
so "Wildfires" matches a title containing "wildfire".

The map stays deliberately small: only add an entry with a recorded
equivalent-query pair. No stemming rules (they misfire: "news" is not
"new"), no ontology. Non-ASCII alphanumerics are dropped — multilingual
search is a Phase 15 experiment, not a silent behavior.
"""

import re

# token -> replacement (may be multi-word, split again after expansion).
SYNONYMS: dict[str, str] = {
    # Places (abbreviations with one overwhelming event-search meaning).
    "la": "los angeles",
    "nyc": "new york",
    # Event-noun plurals from the architecture examples.
    "wildfires": "wildfire",
    "earthquakes": "earthquake",
    "hurricanes": "hurricane",
    "floods": "flood",
    "storms": "storm",
    "tornadoes": "tornado",
    "fires": "fire",
    "eruptions": "eruption",
    "protests": "protest",
    "concerts": "concert",
    "launches": "launch",
}

MAX_SYNONYMS = 20  # roadmap guardrail: no hand-built ontology


def phrase_tokens(text: str) -> list[str]:
    """Order-preserving normalized tokens (synonyms expanded, flattened)."""
    out: list[str] = []
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        expanded = SYNONYMS.get(token, token)
        out.extend(re.findall(r"[a-z0-9]+", expanded))
    return out


def tokens(text: str) -> set[str]:
    """Normalized token set for matching (query side and field side)."""
    return set(phrase_tokens(text))


def normalized_text(text: str) -> str:
    """Canonical display/normal form: single-spaced, no punctuation."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))
