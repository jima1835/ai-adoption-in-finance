"""Every public row carries only the keys CONTRIBUTING.md documents.

The allowlist is the row schema in CONTRIBUTING §3: the curated fields a PR may
edit, the three auto fields monitor.py owns, and the three reviewer-only fields
the review tool writes once. A key outside it is a typo or an undocumented
field, and neither belongs in a public data file. Values are checked against
the vocabularies documented in the same section (and, for the appendix, in
CLAUDE.md). These tests read data/ and never write it.
"""

import json
import sys
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


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


INSTITUTIONS = _load("institutions.json")
NOT_CLASSIFIED = _load("not_classified.json")


@pytest.mark.parametrize("row", INSTITUTIONS, ids=lambda r: r["name"])
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


# ---------------------------------------------------------------------------
# Schema validation (schemas/*.schema.json, checked by tools/validate_data.py).
#
# The tests above encode the row rules as Python sets; the schemas encode them
# as JSON Schema. Two encodings of one rule drift unless something compares
# them, so these tests run the published schemas over the real files and assert
# that the two vocabularies still agree.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_data  # noqa: E402

import roles  # noqa: E402

INSTITUTION_SCHEMA = validate_data._load_schema("institution.schema.json")


@pytest.mark.parametrize("row", INSTITUTIONS, ids=lambda r: r["name"])
def test_institution_row_validates_against_its_schema(row):
    assert validate_data.validate(row, INSTITUTION_SCHEMA["items"]) == []


@pytest.mark.parametrize("data_name,schema_name,kind", [
    (f, s, k) for f, s, k in validate_data.FILES if f != "institutions.json"
])
def test_public_data_file_validates_against_its_schema(data_name, schema_name, kind):
    assert validate_data.validate_file(data_name, schema_name, kind) == []


def test_the_validator_refuses_a_schema_it_cannot_enforce():
    """A validator that silently ignores an unimplemented keyword reads like a
    guarantee and is not one. Unknown keywords are an error, not a pass."""
    with pytest.raises(validate_data.SchemaUnsupported):
        validate_data.validate({"a": 1}, {"type": "object", "patternProperties": {}})


@pytest.mark.parametrize("field,vocabulary", [
    ("event_type", roles.EVENT_TYPES),
    ("title_normalized", roles.TITLES_NORMALIZED),
    ("reporting_line", roles.REPORTING_LINES),
    ("scope", roles.SCOPES),
    ("source_tier", roles.TIERS),
    ("confidence", roles.CONFIDENCES),
    ("label_provenance", roles.PROVENANCE),
])
def test_roles_runtime_vocabulary_matches_the_published_schema(field, vocabulary):
    schema = validate_data._load_schema("role_event.schema.json")
    assert schema["properties"][field]["enum"] == list(vocabulary)


def test_roles_outcomes_match_the_stage_appendix():
    """A negative record means the same thing in both appendices, or a reader
    has to learn two vocabularies for one idea."""
    schema = validate_data._load_schema("roles_not_found.schema.json")
    assert schema["properties"]["outcome"]["enum"] == list(roles.OUTCOMES)
    assert set(roles.OUTCOMES) == OUTCOMES


def test_no_row_in_the_population_is_on_the_denylist():
    """Exclusion is enforced by dropping names at load time, so this asserts the
    result rather than the mechanism: nothing excluded survives into the
    population the roles sweep queries."""
    excluded = roles.load_excluded()
    assert all(not roles.is_excluded(e["name"], excluded) for e in roles.load_population())
