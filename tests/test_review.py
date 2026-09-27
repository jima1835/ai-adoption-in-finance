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
    monkeypatch.setattr(review, "CH_QUEUE", tmp_path / "CHANGES_QUEUE.json")
    monkeypatch.setattr(review, "NEW_QUEUE", tmp_path / "NEW_INSTITUTIONS_QUEUE.json")
    monkeypatch.setattr(review, "NEW_APPROVED", tmp_path / "NEW_INSTITUTIONS_APPROVED.json")
    monkeypatch.setattr(review, "FROZEN_TEST", tmp_path / "test_frozen_corpus.py")
    monkeypatch.setattr(review, "UNFREEZE_RECORD", tmp_path / "RECODE_UNFREEZE.json")
    monkeypatch.setattr(review, "FREEZE_RECORD", tmp_path / "recode_freeze.json")
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


def test_criteria_checks_warn_the_reviewer_and_never_block_the_click(sandbox):
    """The reviewer rejects on the criteria; the tool reports, it does not refuse.

    Every check still runs, and a candidate that fails one publishes only with
    the failure named on the card and written into the decision log. Silence is
    the thing that is not allowed — not publication."""
    candidate = _new_candidate(status="evidence_gap")
    candidate["evidence"][1]["url"] = "https://publisher-b.example/unrelated"
    review.save_nc(review.NEW_QUEUE, [candidate])

    # Both failures are visible on the card before any click.
    staged = review.state()["new_queue"][0]["warnings"]
    assert any("evidence_gap" in w for w in staged)
    assert any("cannot carry it" in w and "publisher-b.example/two" in w for w in staged)

    result = review.apply_new({"action": "new_approve", "name": "New Foundation"})
    assert result.get("ok"), result
    assert len(_rows(sandbox)) == 2
    logged = [json.loads(line) for line in
              review.DECISIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    over = logged[-1]["published_over_warnings"]
    assert any("evidence_gap" in w for w in over)
    assert logged[-1]["intake_status"] == "evidence_gap"


def test_a_candidate_with_no_proposed_stage_publishes_as_human_originated(sandbox):
    """An evidence-gap dossier may propose no stage at all. The reviewer still
    supplies one; the row records null (not "") for the proposal, so it passes
    the public schema, and the label is human_originated rather than a
    manufactured "revision" of a proposal that never existed."""
    candidate = _new_candidate(status="evidence_gap")
    candidate["row"]["stage"] = ""
    candidate["row"]["confidence"] = ""
    review.save_nc(review.NEW_QUEUE, [candidate])
    result = review.apply_new({"action": "new_approve", "name": "New Foundation",
                               "fields": {"stage": "exploring", "confidence": "low"}})
    assert result.get("ok"), result
    new_row = _rows(sandbox)[1]
    assert new_row["stage"] == "exploring"
    assert new_row["agent_proposed_stage"] is None
    assert new_row["label_provenance"] == "human_originated"
    logged = [json.loads(line) for line in
              review.DECISIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert logged[-1]["agent_proposed_stage"] is None
    assert logged[-1]["label_provenance"] == "human_originated"


def test_single_voice_candidate_publishes_at_med_but_never_at_high(sandbox):
    """Own-voice sourcing caps confidence; it does not block publication.

    Seven published rows (ADIA, ATP, EQT, Ilmarinen, Investcorp, Lynx, Optiver)
    rest entirely on the institution's own domain, and MacArthur, NPS and Pictet
    say so in their own footnotes. SOURCES.md §1 records that practice: the
    limitation is disclosed and confidence caps at med. A single voice presented
    at `high` overstates the record, so the reviewer is told — and decides."""
    candidate = _new_candidate()
    # Both sources become the institution's own voice.
    for entry in candidate["evidence"]:
        entry["publisher"] = "New Foundation"
        entry["tier"] = "T1"
    candidate["row"]["confidence"] = "high"
    review.save_nc(review.NEW_QUEUE, [candidate])
    assert any("own voice" in w for w in review.state()["new_queue"][0]["warnings"])
    assert review.apply_new({"action": "new_approve", "name": "New Foundation"}).get("ok")
    assert len(_rows(sandbox)) == 2

    candidate["row"]["name"] = "Second Foundation"
    candidate["row"]["aliases"] = ["Second Foundation"]
    candidate["row"]["confidence"] = "med"
    review.save_nc(review.NEW_QUEUE, [candidate])
    assert review.apply_new({"action": "new_approve", "name": "Second Foundation"}).get("ok")
    assert len(_rows(sandbox)) == 3
    assert not any("own voice" in w
                   for w in review.judgment_warnings(candidate["row"], candidate["evidence"]))


def test_a_duplicate_row_is_still_refused(sandbox):
    """Integrity, not judgment: two rows for one institution is a broken file,
    and no reading of the criteria makes it right."""
    candidate = _new_candidate()
    candidate["row"]["name"] = "Example Fund"
    candidate["row"]["aliases"] = ["Example Fund"]
    review.save_nc(review.NEW_QUEUE, [candidate])
    result = review.apply_new({"action": "new_approve", "name": "Example Fund"})
    assert "conflicts with" in result["error"]
    assert len(_rows(sandbox)) == 1


def test_the_row_count_alone_never_freezes_the_corpus(sandbox):
    """Reaching the target is a prompt, not an event. The gate closes when a
    person declares it — so the hundredth row can be approved, and corrected,
    like every row before it."""
    review.FROZEN_TEST.touch()
    rows = _rows(sandbox)
    for i in range(99):
        extra = dict(ROW)
        extra["name"] = f"Expansion Fund {i}"
        extra["aliases"] = [extra["name"]]
        rows.append(extra)
    review.save_rows(rows)
    assert len(_rows(sandbox)) == 100
    assert review.freeze_active() is False
    assert review.freeze_due() is True
    assert review.apply_action({"action": "approve", "name": "Example Fund"}).get("ok")


def test_declaring_the_freeze_closes_public_writes(sandbox):
    rows = _rows(sandbox)
    rows.append({**ROW, "name": "Second Fund", "aliases": ["Second Fund"]})
    review.save_rows(rows)
    assert review.freeze_active() is False

    review.FREEZE_RECORD.write_text(
        json.dumps({"blind_recode_freeze": True, "declared_on": "2026-09-24",
                    "rows_at_freeze": 2}) + "\n", encoding="utf-8"
    )
    assert review.freeze_active() is True
    assert review.freeze_due() is False
    result = review.apply_action({"action": "approve", "name": "Example Fund"})
    assert "blind-review freeze is active" in result["error"]

    # The gate lifts only on the recorded completion. Deleting the test file is
    # part of that commit, never a way to reopen writes on its own.
    review.FROZEN_TEST.unlink(missing_ok=True)
    assert review.freeze_active() is True
    review.UNFREEZE_RECORD.write_text(
        json.dumps({"blind_recode_complete": True}) + "\n", encoding="utf-8"
    )
    assert review.freeze_active() is False
    assert review.apply_action({"action": "approve", "name": "Example Fund"}).get("ok")


def test_a_correction_moves_the_stage_without_touching_the_panel(sandbox):
    """A skeptic pass re-reads old evidence. Nothing moved in the sector, so the
    panel — which is dated by evidence — must record nothing."""
    review.CH_QUEUE.write_text(json.dumps([{
        "name": "Example Fund", "sweep": "2026-09 skeptic",
        "current_stage": "piloting", "proposed_stage": "exploring",
        "correction": True,
        "reason": "re-read against METHODOLOGY 3: no production use case on the record",
    }]) + "\n", encoding="utf-8")
    out = review.apply_action({
        "action": "ch_approve", "name": "Example Fund",
        "fields": {"stage": "exploring", "rationale": "Re-read: intent only."},
    })
    assert out.get("ok"), out
    assert out["transition"] is False
    assert out["correction"] is True
    assert _rows(sandbox)[0]["stage"] == "exploring"
    assert _transitions(sandbox) == []


def test_a_sweep_move_without_the_correction_flag_still_needs_its_date(sandbox):
    review.CH_QUEUE.write_text(json.dumps([{
        "name": "Example Fund", "sweep": "2026-09",
        "current_stage": "piloting", "proposed_stage": "scaling",
        "reason": "new evidence",
    }]) + "\n", encoding="utf-8")
    out = review.apply_action({
        "action": "ch_approve", "name": "Example Fund",
        "fields": {"stage": "scaling", "rationale": "Now shipping firm-wide."},
    })
    assert "date_effective" in out["error"]


def test_an_unreadable_freeze_declaration_reads_as_frozen(sandbox):
    """Fail closed: a corrupt declaration might be a real freeze."""
    review.FREEZE_RECORD.write_text("{not json", encoding="utf-8")
    assert review.freeze_declared() is True
    assert review.freeze_active() is True


def test_new_ruling_releases_a_held_candidate_and_demands_a_real_record(sandbox):
    """A candidate held on a RULE is released by a recorded judgment, not by research.

    This action was silently deleted from both review.py and review.html by a
    concurrent edit on 2026-09-24, while the already-running server kept serving it
    from its imported module — so it went on working for the reviewer and existed
    nowhere on disk. Three `tier_ruling` candidates would have become unreachable at
    the next restart. This test exists so that cannot happen quietly again."""
    candidate = _new_candidate(status="tier_ruling")
    review.save_nc(review.NEW_QUEUE, [candidate])

    # A gesture is not a record: the ruling is the public basis for the row.
    assert "error" in review.apply_new(
        {"action": "new_ruling", "name": "New Foundation", "ruling": "ok"})
    assert review.load_nc(review.NEW_QUEUE)[0]["status"] == "tier_ruling"

    ruling = "Admit all three annual reports: own audited filings, T1 under SOURCES.md."
    assert review.apply_new(
        {"action": "new_ruling", "name": "New Foundation", "ruling": ruling}).get("ok")
    held = review.load_nc(review.NEW_QUEUE)[0]
    assert held["status"] == "ready"
    assert held["reviewer_ruling"] == ruling

    # A ruling records a judgment. It never publishes, and the row bar still
    # applies at new_approve.
    assert len(_rows(sandbox)) == 1

    # It applies only to a candidate actually held on a rule.
    other = _new_candidate()
    other["row"]["name"] = "Third Foundation"
    other["row"]["aliases"] = ["Third Foundation"]
    review.save_nc(review.NEW_QUEUE, [other])
    assert "error" in review.apply_new(
        {"action": "new_ruling", "name": "Third Foundation", "ruling": ruling})


def test_sweep_decision_log_records_the_confidence_outcome(sandbox):
    """The 2026-09-26 audit found confidence raises invisible in DECISIONS.jsonl.
    A sweep approval now records proposed / from / to and whether the human
    overruled the proposed confidence, beside the stage fields it already kept."""
    review.CH_QUEUE.write_text(json.dumps([{
        "name": "Example Fund", "sweep": "2026-09-26 audit",
        "current_stage": "piloting", "proposed_stage": "piloting",
        "current_confidence": "med", "proposed_confidence": "low",
        "correction": True, "reason": "text says low",
    }]) + "\n", encoding="utf-8")
    out = review.apply_action({
        "action": "ch_approve", "name": "Example Fund",
        "fields": {"confidence": "med", "rationale": "held at med on a ruling"},
    })
    assert out.get("ok"), out
    assert (out["confidence_from"], out["confidence_to"]) == ("med", "med")
    logged = [json.loads(line) for line in
              review.DECISIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    last = logged[-1]
    assert last["agent_proposed_confidence"] == "low"
    assert (last["confidence_from"], last["confidence_to"]) == ("med", "med")
    assert last["confidence_overruled"] is True


def test_intake_dossier_backs_a_sweep_row_with_no_ledger_section(sandbox, monkeypatch):
    """A row that entered through intake has no REVIEW.md section; the sweep
    card's ledger box falls back to its dossier. Live candidate folders beat
    `_superseded` copies, and rows nobody asked about are not looked up."""
    intake = sandbox / "intake"
    (intake / "2026-09-20" / "candidates").mkdir(parents=True)
    (intake / "_superseded").mkdir()
    live = {"row": {"name": "Example Fund"}, "status": "ready",
            "evidence": [{"date": "2026-01-01", "publisher": "Example", "tier": "T1",
                          "url": "https://example.org/e", "quote": "we pilot"}]}
    stale = {"row": {"name": "Example Fund"}, "status": "evidence_gap", "evidence": []}
    (intake / "2026-09-20" / "candidates" / "example fund.json").write_text(
        json.dumps(live), encoding="utf-8")
    (intake / "_superseded" / "batch.json").write_text(json.dumps([stale]), encoding="utf-8")
    monkeypatch.setattr(review, "INTAKE_DIR", intake)
    monkeypatch.setattr(review, "ROOT", sandbox)

    found = review.intake_evidence(["Example Fund", "Nobody"])
    assert set(found) == {"Example Fund"}
    assert found["Example Fund"]["status"] == "ready"
    assert found["Example Fund"]["evidence"][0]["tier"] == "T1"
    assert found["Example Fund"]["path"].startswith("intake/2026-09-20")

    review.CH_QUEUE.write_text(json.dumps([{
        "name": "Example Fund", "current_stage": "piloting", "proposed_stage": "piloting",
        "correction": True, "reason": "r",
    }]) + "\n", encoding="utf-8")
    assert "Example Fund" in review.state()["dossier_evidence"]
    assert review.intake_evidence([]) == {}
