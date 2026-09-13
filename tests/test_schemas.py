"""Every public row carries only the keys CONTRIBUTING.md documents.

The allowlist is the row schema in CONTRIBUTING §3: the curated fields a PR may
edit, the three auto fields monitor.py owns, and the three reviewer-only fields
the review tool writes once. A key outside it is a typo or an undocumented
field, and neither belongs in a public data file. Values are checked against
the vocabularies documented in the same section (and, for the appendix, in
CLAUDE.md). These tests read data/ and never write it.
"""

import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data"

CURATED = {"name", "aliases", "type", "region", "aum", "stage", "confidence",
           "rationale", "footnote", "use_cases", "events"}
AUTO = {"latest_signal", "latest_date", "source_url"}
REVIEWER_ONLY = {"as_of_reviewed", "label_provenance", "agent_proposed_stage"}
INSTITUTION_KEYS = CURATED | AUTO | REVIEWER_ONLY
# footnote is documented OPTIONAL; the reviewer-only fields exist only once a
# human has reviewed the row (every published row, in practice).
REQUIRED = (CURATED - {"footnote"}) | AUTO
EVENT_KEYS = {"date", "event", "source_url"}  # exactly one source_url, nothing else
NOT_CLASSIFIED_KEYS = {"name", "type", "region", "outcome", "reason", "as_of"}

TYPES = {"asset-manager", "pension", "sovereign-wealth", "hedge-fund", "endowment"}
REGIONS = {"US", "Canada", "Europe", "Middle East", "Asia", "Other"}
STAGES = {"exploring", "piloting", "scaling", "embedded"}
CONFIDENCES = {"high", "med", "low"}
OUTCOMES = {"no-qualifying-evidence", "withdrawn-on-review"}
PROVENANCE = {"agent_proposed_accepted", "human_revised", "human_originated",
              "unknown_pre_capture"}

# Rows known to carry a key outside the allowlist. Strict xfail: the day the
# data is corrected this test FAILS, so the entry leaves with the stray key
# instead of lingering. Data is never edited from a test.
KNOWN_STRAY_KEYS = {"GIC": {"as_of_latest_signal"}}


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


INSTITUTIONS = _load("institutions.json")
NOT_CLASSIFIED = _load("not_classified.json")


def _with_known_strays(rows):
    for row in rows:
        stray = KNOWN_STRAY_KEYS.get(row["name"])
        marks = (
            pytest.mark.xfail(strict=True,
                              reason=f"{row['name']} carries undocumented {sorted(stray)}; "
                                     "left for a data release")
            if stray else ()
        )
        yield pytest.param(row, id=row["name"], marks=marks)


@pytest.mark.parametrize("row", list(_with_known_strays(INSTITUTIONS)))
def test_institution_row_keys_match_contributing(row):
    extra, missing = set(row) - INSTITUTION_KEYS, REQUIRED - set(row)
    assert not extra and not missing, {"extra": extra, "missing": missing}


@pytest.mark.parametrize("row", INSTITUTIONS, ids=lambda r: r["name"])
def test_institution_row_values_match_contributing(row):
    assert row["type"] in TYPES
    assert row["region"] in REGIONS
    assert row["stage"] in STAGES
    assert row["confidence"] in CONFIDENCES
    for key in ("aliases", "use_cases", "events"):
        assert isinstance(row[key], list), key
    for event in row["events"]:
        assert set(event) == EVENT_KEYS, event
    if "label_provenance" in row:
        assert row["label_provenance"] in PROVENANCE
    if "agent_proposed_stage" in row:
        assert row["agent_proposed_stage"] in STAGES | {None}


@pytest.mark.parametrize("entry", NOT_CLASSIFIED, ids=lambda e: e["name"])
def test_not_classified_entry_matches_schema(entry):
    assert set(entry) == NOT_CLASSIFIED_KEYS, set(entry) ^ NOT_CLASSIFIED_KEYS
    assert entry["type"] in TYPES
    assert entry["region"] in REGIONS
    assert entry["outcome"] in OUTCOMES
    assert entry["reason"].strip()  # public text — must stand alone


def test_names_are_unique_and_the_two_files_are_disjoint():
    names = [r["name"] for r in INSTITUTIONS]
    appendix = [e["name"] for e in NOT_CLASSIFIED]
    assert len(set(names)) == len(names) and len(set(appendix)) == len(appendix)
    assert not set(names) & set(appendix)  # classified or not — never both
