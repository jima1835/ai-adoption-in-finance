"""The first-review record (data/first_review.jsonl) must agree with the corpus.

It holds, per published row, what the agent proposed and what the reviewer set at
first review, for stage and confidence. These checks tie it to institutions.json,
to the agreement record and to the prompt-version log. They read data/ and never
write it.
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
ORD = {"low": 0, "med": 1, "high": 2}


def _jsonl(name):
    return [json.loads(line) for line in (DATA / name).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _rows():
    rows = json.loads((DATA / "institutions.json").read_text(encoding="utf-8"))
    return {r["name"]: r for r in rows}


def _agreement():
    return json.loads((DATA / "agreement.json").read_text(encoding="utf-8"))


def test_one_record_per_published_row():
    rows, recs = _rows(), _jsonl("first_review.jsonl")
    assert sorted(r["institution"] for r in recs) == sorted(rows)


def test_stage_provenance_and_proposal_match_the_row():
    rows = _rows()
    for r in _jsonl("first_review.jsonl"):
        row = rows[r["institution"]]
        assert r["stage_provenance"] == row["label_provenance"], r
        assert r["agent_proposed_stage"] == row.get("agent_proposed_stage"), r


def test_first_review_stage_matches_the_agreement_record():
    revised = {v["institution"]: v["final"] for v in _agreement()["revisions"]}
    for r in _jsonl("first_review.jsonl"):
        if r["stage_provenance"] == "agent_proposed_accepted":
            assert r["first_review_stage"] == r["agent_proposed_stage"], r
        if r["stage_provenance"] == "human_revised" and revised.get(r["institution"]):
            assert r["first_review_stage"] == revised[r["institution"]], r


def test_values_inferred_from_today_match_today():
    rows = _rows()
    for r in _jsonl("first_review.jsonl"):
        row = rows[r["institution"]]
        if r["first_review_stage_source"].startswith("today_value"):
            assert r["first_review_stage"] == row["stage"], r
        if r["first_review_confidence_source"] == "today_value_no_logged_later_change":
            assert r["first_review_confidence"] == row["confidence"], r


def test_review_time_not_after_latest_review_and_prompt_version_exists():
    rows = _rows()
    versions = {v["version"] for v in _jsonl("prompt_versions.jsonl")}
    for r in _jsonl("first_review.jsonl"):
        if r["first_review_at"]:
            assert r["first_review_at"][:10] <= rows[r["institution"]]["as_of_reviewed"], r
            assert r["prompt_version_at_first_review"] in versions, r


def test_agreement_blocks_match_the_file():
    recs = [r for r in _jsonl("first_review.jsonl") if r["agent_proposed_confidence"]]
    agreement = _agreement()
    block = agreement["confidence"]

    def step(r):
        return ORD[r["first_review_confidence"]] - ORD[r["agent_proposed_confidence"]]
    assert block["n"] == len(recs)
    assert block["raised_at_first_review"] == sum(step(r) > 0 for r in recs)
    assert block["lowered_at_first_review"] == sum(step(r) < 0 for r in recs)
    sessions = agreement["first_review_sessions"]
    assert sum(s["confidence_raised"] for s in sessions) == block["raised_at_first_review"]
    revised = agreement["stage_agreement"]["revised"]
    assert sum(s["stage_revised_up"] + s["stage_revised_down"] for s in sessions) == revised
