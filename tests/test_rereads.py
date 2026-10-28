"""The re-read record (data/rereads.jsonl) must agree with the corpus it describes.

A re-read pass re-checks reviewed rows against the evidence already on them. Its
moves are corrections: they never enter transitions.jsonl, so the only public
trace of who moved what, and on whose proposal, is this record. These checks keep
it honest against institutions.json and agreement.json. They read data/ and never
write it.
"""

import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data"
STAGES = ["exploring", "piloting", "scaling", "embedded"]


def _passes():
    path = DATA / "rereads.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _rows():
    rows = json.loads((DATA / "institutions.json").read_text(encoding="utf-8"))
    return {r["name"]: r for r in rows}


def _transitioned():
    path = DATA / "transitions.jsonl"
    if not path.exists():
        return set()
    return {json.loads(line)["name"] for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()}


@pytest.mark.parametrize("ps", _passes(), ids=lambda p: p["id"])
def test_scope_is_counted_and_covers_every_card(ps):
    assert len(ps["in_scope"]) == ps["n_in_scope"]
    assert len(set(ps["in_scope"])) == ps["n_in_scope"], "duplicate name in scope"
    names = [e["institution"] for e in ps["entries"]]
    assert len(set(names)) == len(names), "one card per row per pass"
    assert set(names) <= set(ps["in_scope"]), "a card outside the stated scope"


@pytest.mark.parametrize("ps", _passes(), ids=lambda p: p["id"])
def test_every_name_is_a_row(ps):
    rows = _rows()
    missing = [n for n in ps["in_scope"] if n not in rows]
    assert not missing, missing


@pytest.mark.parametrize("ps", _passes(), ids=lambda p: p["id"])
def test_entries_respect_the_direction_checked(ps):
    for e in ps["entries"]:
        before, after = STAGES.index(e["stage_before"]), STAGES.index(e["stage_after"])
        if e["decision"] == "rejected":
            assert after == before, e
        if ps["direction_checked"] == "down":
            assert after <= before, e
        if ps["direction_checked"] == "up":
            assert after >= before, e


def test_approved_moves_stand_unless_a_later_record_moved_them():
    rows, moved_on_evidence = _rows(), _transitioned()
    passes = sorted(_passes(), key=lambda p: (p["date"], p["id"]))
    final = {}
    for ps in passes:
        for e in ps["entries"]:
            if e["decision"] == "approved":
                final[e["institution"]] = e["stage_after"]
    for name, stage in final.items():
        if name not in moved_on_evidence:
            assert rows[name]["stage"] == stage, (name, rows[name]["stage"], stage)


def test_every_correction_in_the_agreement_record_has_a_reread_entry():
    agreement = json.loads((DATA / "agreement.json").read_text(encoding="utf-8"))
    since = agreement["since_first_review"]
    corrected = {c["institution"] for c in since["corrections_after_acceptance"]}
    corrected |= set(since["revised_then_corrected_back"])
    approved_moves = {e["institution"] for ps in _passes() for e in ps["entries"]
                      if e["decision"] == "approved" and e["stage_after"] != e["stage_before"]}
    assert corrected <= approved_moves, corrected - approved_moves
    assert agreement["stage_agreement"]["first_review_stage_undetermined"] == 0
