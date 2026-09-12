"""Unit tests for the human review tool's panel guard. No server, no network.

A stage change on an already-reviewed row is a dated event in the transition
panel: `approve` must refuse it without date_effective + evidence_url, and must
append the same data/transitions.jsonl record `ch_approve` writes when they are
present. An unchanged stage on a reviewed row is an ordinary re-approval.
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import review  # noqa: E402


ROW = {
    "name": "Example Fund",
    "aliases": ["Example Fund"],
    "type": "pension",
    "region": "Europe",
    "aum": "~$10B",
    "stage": "piloting",
    "confidence": "med",
    "as_of_reviewed": "2026-08-31",
    "rationale": "reviewed once already",
    "use_cases": [],
    "events": [{"date": "2026-01", "event": "e", "source_url": "https://example.org/e"}],
    "latest_signal": "",
    "latest_date": "",
    "source_url": "",
    "label_provenance": "agent_proposed_accepted",
    "agent_proposed_stage": "piloting",
}


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point every file review.py touches at tmp_path; REVIEW.md absent so no
    row is treated as agent-proposed (has_review_section -> False)."""
    data = tmp_path / "institutions.json"
    data.write_text(json.dumps([dict(ROW)], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(review, "DATA", data)
    monkeypatch.setattr(review, "TRANSITIONS", tmp_path / "transitions.jsonl")
    monkeypatch.setattr(review, "DECISIONS", tmp_path / "DECISIONS.jsonl")
    monkeypatch.setattr(review, "REVIEW", tmp_path / "REVIEW.md")
    monkeypatch.setattr(review, "REJECTED", tmp_path / "REJECTED.md")
    monkeypatch.setattr(review, "NC_QUEUE", tmp_path / "NOT_CLASSIFIED_QUEUE.json")
    monkeypatch.setattr(review, "NC_PUBLIC", tmp_path / "not_classified.json")
    return tmp_path


def _rows(sandbox):
    return json.loads((sandbox / "institutions.json").read_text(encoding="utf-8"))


def _transitions(sandbox):
    p = sandbox / "transitions.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_reviewed_row_stage_change_refused_without_evidence(sandbox):
    res = review._apply({"action": "approve", "name": "Example Fund",
                         "fields": {"stage": "scaling"}})
    assert "error" in res and "date_effective" in res["error"]
    assert _rows(sandbox)[0]["stage"] == "piloting"  # nothing written
    assert _rows(sandbox)[0]["as_of_reviewed"] == "2026-08-31"
    assert _transitions(sandbox) == []


def test_reviewed_row_stage_change_refused_without_url(sandbox):
    res = review._apply({"action": "approve", "name": "Example Fund",
                         "fields": {"stage": "scaling"}, "date_effective": "2026-08-01"})
    assert "error" in res and "evidence_url" in res["error"]
    assert _rows(sandbox)[0]["stage"] == "piloting"
    assert _transitions(sandbox) == []


def test_reviewed_row_stage_change_logged_with_evidence(sandbox):
    res = review._apply({"action": "approve", "name": "Example Fund",
                         "fields": {"stage": "scaling"},
                         "date_effective": "2026-08-01",
                         "evidence_url": "https://example.org/rollout"})
    assert res.get("ok") and res.get("transition") is True
    row = _rows(sandbox)[0]
    assert row["stage"] == "scaling"
    assert row["as_of_reviewed"] == date.today().isoformat()
    # provenance is write-once: untouched on a re-review
    assert row["label_provenance"] == "agent_proposed_accepted"
    assert row["agent_proposed_stage"] == "piloting"
    (rec,) = _transitions(sandbox)
    assert rec == {
        "name": "Example Fund", "type": "pension", "region": "Europe",
        "from": "piloting", "to": "scaling",
        "date_effective": "2026-08-01", "evidence_url": "https://example.org/rollout",
        "decided_on": date.today().isoformat(),
        "sweep": None, "agent_proposed": None, "human_overruled": None,
    }


def test_reviewed_row_unchanged_stage_still_approves(sandbox):
    res = review._apply({"action": "approve", "name": "Example Fund",
                         "fields": {"stage": "piloting", "confidence": "high"}})
    assert res.get("ok") and res.get("transition") is False
    row = _rows(sandbox)[0]
    assert row["stage"] == "piloting" and row["confidence"] == "high"
    assert row["as_of_reviewed"] == date.today().isoformat()
    assert _transitions(sandbox) == []


def test_first_review_stage_change_is_provenance_not_transition(sandbox):
    # A never-reviewed row: the stage edit is the human overruling the agent's
    # proposal, recorded as provenance, not as a panel transition.
    rows = _rows(sandbox)
    rows[0].pop("as_of_reviewed")
    rows[0].pop("label_provenance")
    rows[0].pop("agent_proposed_stage")
    (sandbox / "institutions.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    res = review._apply({"action": "approve", "name": "Example Fund",
                         "fields": {"stage": "scaling"}})
    assert res.get("ok") and res.get("transition") is False
    row = _rows(sandbox)[0]
    assert row["stage"] == "scaling"
    assert row["label_provenance"] == "human_originated"  # no REVIEW.md section in the sandbox
    assert _transitions(sandbox) == []


def test_try_lock_is_exclusive_across_handles(tmp_path):
    # flock on POSIX, msvcrt.locking on Windows: a second handle on the lock
    # file is refused while the first holds it, and succeeds once it is closed.
    lock = tmp_path / "institutions.lock"
    with lock.open("w") as a:
        assert review._try_lock(a) is True
        with lock.open("w") as b:
            assert review._try_lock(b) is False
    with lock.open("w") as c:
        assert review._try_lock(c) is True
