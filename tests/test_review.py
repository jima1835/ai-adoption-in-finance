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
    monkeypatch.setattr(review, "NEW_QUEUE", tmp_path / "NEW_INSTITUTIONS_QUEUE.json")
    monkeypatch.setattr(review, "NEW_APPROVED", tmp_path / "NEW_INSTITUTIONS_APPROVED.json")
    monkeypatch.setattr(review, "FROZEN_TEST", tmp_path / "test_frozen_corpus.py")
    monkeypatch.setattr(review, "UNFREEZE_RECORD", tmp_path / "RECODE_UNFREEZE.json")
    return tmp_path


def _rows(sandbox):
    return json.loads((sandbox / "institutions.json").read_text(encoding="utf-8"))


def _transitions(sandbox):
    p = sandbox / "transitions.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


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


def test_review_io_pins_utf8_and_lf_regardless_of_platform(sandbox, monkeypatch):
    # The review tool writes the same public files monitor.py does, so it gets
    # the same guarantee (tests/test_monitor.py): utf-8 and LF pinned on every
    # writer, or a Windows reviewer re-encodes institutions.json in the ANSI
    # code page and churns every line of it to CRLF.
    kwargs = []
    real_write, real_open = Path.write_text, Path.open

    def spy_write(self, data, **kw):
        kwargs.append(kw)
        return real_write(self, data, **kw)

    def spy_open(self, mode="r", *args, **kw):
        if "a" in mode:  # append_transition; write_text is captured above
            kwargs.append(kw)
        return real_open(self, mode, *args, **kw)

    monkeypatch.setattr(Path, "write_text", spy_write)
    monkeypatch.setattr(Path, "open", spy_open)

    rows = _rows(sandbox)
    rows[0]["rationale"] = "完成部署 — £390B"
    review.save_rows(rows)
    review.save_nc(sandbox / "not_classified.json", [{"name": "Example", "reason": "£ — 完成"}])
    review.append_transition({"name": "Example Fund", "from": "piloting", "to": "scaling"})

    assert len(kwargs) == 3
    assert all(kw.get("encoding") == "utf-8" and kw.get("newline") == "\n" for kw in kwargs)
    for name in ("institutions.json", "not_classified.json", "transitions.jsonl"):
        assert b"\r" not in (sandbox / name).read_bytes()  # LF-only on every platform
    assert _rows(sandbox)[0]["rationale"] == "完成部署 — £390B"


def _new_candidate(status="ready"):
    urls = ["https://publisher-a.example/one", "https://publisher-b.example/two"]
    return {
        "status": status,
        "row": {
            "name": "New Foundation", "aliases": ["New Foundation"],
            "type": "endowment", "region": "US", "aum": "",
            "stage": "piloting", "confidence": "med", "rationale": "Two internal uses.",
            "use_cases": ["grant screening", "report synthesis"],
            "events": [
                {"date": "2025-09", "event": "Screened grant requests", "source_url": urls[0]},
                {"date": "2026-06-12", "event": "Synthesized reports", "source_url": urls[1]},
            ],
            "latest_signal": "", "latest_date": "", "source_url": "",
        },
        "evidence": [
            {"publisher": "Publisher A", "tier": "T2", "url": urls[0], "quote": "screened"},
            {"publisher": "Publisher B", "tier": "T1", "url": urls[1], "quote": "synthesized"},
        ],
    }


def test_new_candidate_approval_publishes_through_reviewer_gate(sandbox):
    review.save_nc(review.NEW_QUEUE, [_new_candidate()])
    review.FROZEN_TEST.touch()
    result = review.apply_action({"action": "new_approve", "name": "New Foundation"})
    assert result.get("ok") and result.get("new_published") == "New Foundation"
    assert len(_rows(sandbox)) == 2
    assert review.load_nc(review.NEW_QUEUE) == []
    assert review.load_nc(review.NEW_APPROVED) == []
    new_row = _rows(sandbox)[1]
    assert new_row["label_provenance"] == "agent_proposed_accepted"
    assert new_row["as_of_reviewed"] == date.today().isoformat()
    # The test file remains present as a blind-recode reminder, but it does not
    # disable a human action taken through the reviewer endpoint.
    assert review.apply_action({"action": "approve", "name": "Example Fund"}).get("ok")


def test_new_candidate_requires_ready_status_and_cited_independent_events(sandbox):
    candidate = _new_candidate(status="evidence_gap")
    review.save_nc(review.NEW_QUEUE, [candidate])
    assert "gap" in review.apply_new({"action": "new_approve", "name": "New Foundation"})["error"]
    candidate["status"] = "ready"
    candidate["evidence"][1]["url"] = "https://publisher-b.example/unrelated"
    review.save_nc(review.NEW_QUEUE, [candidate])
    result = review.apply_new({"action": "new_approve", "name": "New Foundation"})
    assert "matching" in result["error"]
    assert len(_rows(sandbox)) == 1


def test_blind_review_freeze_starts_at_100_rows(sandbox):
    review.FROZEN_TEST.touch()
    rows = _rows(sandbox)
    for i in range(98):
        extra = dict(ROW)
        extra["name"] = f"Expansion Fund {i}"
        extra["aliases"] = [extra["name"]]
        rows.append(extra)
    review.save_rows(rows)
    assert len(_rows(sandbox)) == 99
    assert review.freeze_active() is False
    rows.append({**ROW, "name": "Expansion Fund 98", "aliases": ["Expansion Fund 98"]})
    review.save_rows(rows)
    assert review.freeze_active() is True
    result = review.apply_action({"action": "approve", "name": "Example Fund"})
    assert "100-row blind-review freeze" in result["error"]

    # The gate lifts only after the freeze test is removed and the explicit
    # completion marker is recorded; removing one without the other stays safe.
    review.FROZEN_TEST.unlink()
    review.UNFREEZE_RECORD.write_text(
        json.dumps({"blind_recode_complete": True}) + "\n", encoding="utf-8"
    )
    assert review.freeze_active() is False
    assert review.apply_action({"action": "approve", "name": "Example Fund"}).get("ok")
