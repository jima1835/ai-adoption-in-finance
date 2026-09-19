"""The roles review mode: the human gate on data/roles.jsonl.

Three things are worth a test here, and they are the three things that would
quietly corrupt the record if they broke:

  1. provenance is computed from the screener's guess vs. the reviewer's answer,
     once, at filing (the anchored-agreement input, METHODOLOGY §6);
  2. nothing outside the population — including anything on the exclusion
     denylist — can be filed at all;
  3. a withdrawal leaves a trace. Removing an event without recording why would
     make the corpus look like it was never filed.

No server, no network, no API key. `input()` is scripted.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import review  # noqa: E402

import roles  # noqa: E402

QUEUED = {
    "institution": "CalSTRS",
    "institution_raw": "CalSTRS",
    "event_type_guess": "hired",
    "person_guess": "Alex Example",
    "reason": "names a head of AI",
    "url": "https://example.org/a",
    "date": "2026-03-24",
    "queued_on": "2026-09-13",
}

# The interview, in order, as build_role_event asks it. "" takes the default.
ANSWERS = [
    "Head of Artificial Intelligence",  # title_verbatim
    "2",                                # title_normalized -> head_of_ai
    "",                                 # person -> default (the guess)
    "",                                 # event_type -> default (the guess)
    "",                                 # date -> default
    "2",                                # reporting_line -> cio
    "1",                                # scope -> firm_wide
    "",                                 # source_url -> default
    "1",                                # source_tier -> T1
    "appointed Head of Artificial Intelligence",  # quote_verbatim
    "",                                 # language -> en
    "1",                                # confidence -> high
    "One dated appointment; says nothing about what the role has shipped.",
]


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Every file the roles mode writes, redirected into tmp_path."""
    monkeypatch.setattr(roles, "ROLES_PATH", tmp_path / "roles.jsonl")
    monkeypatch.setattr(roles, "ROLES_NOT_FOUND_PATH", tmp_path / "roles_not_found.jsonl")
    monkeypatch.setattr(roles, "QUEUE_PATH", tmp_path / "roles_queue.jsonl")
    monkeypatch.setattr(review, "ROLES_LOCK", tmp_path / ".roles.lock")
    monkeypatch.setattr(review, "DECISIONS", tmp_path / "DECISIONS.jsonl")
    return tmp_path


def script(monkeypatch, answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_build_role_event_records_an_accepted_proposal(sandbox, monkeypatch):
    script(monkeypatch, ANSWERS)
    rec = review.build_role_event(QUEUED, roles.alias_index())

    assert rec["institution"] == "CalSTRS"
    assert rec["event_type"] == "hired"                     # took the guess
    assert rec["agent_proposed_event_type"] == "hired"
    assert rec["label_provenance"] == "agent_proposed_accepted"
    assert rec["person"] == "Alex Example"
    assert rec["title_normalized"] == "head_of_ai"
    assert rec["reporting_line"] == "cio" and rec["scope"] == "firm_wide"
    assert rec["date"] == "2026-03-24"                      # verbatim, unpadded
    assert len(rec["id"]) == 26
    assert rec["as_of_reviewed"]


def test_overruling_the_screener_is_recorded_as_such(sandbox, monkeypatch):
    answers = list(ANSWERS)
    answers[3] = "created"  # reviewer disagrees with "hired"
    script(monkeypatch, answers)
    rec = review.build_role_event(QUEUED, roles.alias_index())

    assert rec["event_type"] == "created"
    assert rec["agent_proposed_event_type"] == "hired"
    assert rec["label_provenance"] == "human_revised"


def test_an_event_with_no_screener_guess_is_human_originated(sandbox, monkeypatch):
    answers = list(ANSWERS)
    answers[3] = "created"  # no default to take — the guess is absent
    script(monkeypatch, answers)
    rec = review.build_role_event({**QUEUED, "event_type_guess": None},
                                  roles.alias_index())

    assert rec["label_provenance"] == "human_originated"
    assert rec["agent_proposed_event_type"] is None


def test_a_person_is_optional_and_null_is_a_complete_answer(sandbox, monkeypatch):
    answers = list(ANSWERS)
    answers[2] = " "  # reviewer clears the guessed name
    script(monkeypatch, answers)
    rec = review.build_role_event({**QUEUED, "person_guess": None}, roles.alias_index())

    assert rec["person"] is None


def test_nothing_outside_the_population_can_be_filed(sandbox, monkeypatch, capsys):
    script(monkeypatch, ANSWERS)
    assert review.build_role_event({**QUEUED, "institution": "Acme Capital"},
                                   roles.alias_index()) is None
    assert "not in the population" in capsys.readouterr().out


def test_an_excluded_institution_is_unfilable(sandbox, monkeypatch, capsys):
    """The denylist is enforced through the population, so there is no second
    check to forget: an excluded name simply is not in the index."""
    monkeypatch.setattr(roles, "load_excluded",
                        lambda: {"blocked fund": "Blocked Fund"})
    script(monkeypatch, ANSWERS)
    index = roles.alias_index(roles.load_population())
    assert review.build_role_event({**QUEUED, "institution": "Blocked Fund"},
                                   index) is None


def test_a_malformed_date_is_refused_rather_than_normalized(sandbox, monkeypatch, capsys):
    answers = list(ANSWERS)
    answers[4] = "March 2026"
    script(monkeypatch, answers)
    assert review.build_role_event(QUEUED, roles.alias_index()) is None
    assert "date must be" in capsys.readouterr().out


def test_filing_appends_one_line_and_logs_the_decision(sandbox, monkeypatch):
    script(monkeypatch, ANSWERS)
    rec = review.build_role_event(QUEUED, roles.alias_index())
    assert review.file_role_event(rec) is True

    lines = (sandbox / "roles.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["id"] == rec["id"]
    logged = json.loads((sandbox / "DECISIONS.jsonl").read_text().splitlines()[0])
    assert logged["action"] == "roles_file"
    assert logged["label_provenance"] == "agent_proposed_accepted"


def test_the_negative_record_dates_the_search_not_the_evidence(sandbox):
    assert review.file_roles_not_found("CalSTRS", "no-qualifying-evidence",
                                       "No public AI-leadership appointment.") is True
    entry = json.loads((sandbox / "roles_not_found.jsonl").read_text().splitlines()[0])
    assert set(entry) == {"institution", "searched_on", "outcome", "reason"}
    assert entry["outcome"] == "no-qualifying-evidence"


def test_removing_a_filed_event_records_the_withdrawal(sandbox, monkeypatch):
    script(monkeypatch, ANSWERS)
    rec = review.build_role_event(QUEUED, roles.alias_index())
    review.file_role_event(rec)

    assert review.remove_role_event(rec["id"], "Source retracted the appointment.")
    assert (sandbox / "roles.jsonl").read_text(encoding="utf-8") == ""
    entry = json.loads((sandbox / "roles_not_found.jsonl").read_text().splitlines()[0])
    assert entry["outcome"] == "withdrawn-on-review"
    assert entry["institution"] == "CalSTRS"


def test_removing_an_unknown_id_changes_nothing(sandbox, capsys):
    assert review.remove_role_event("01ZZZZZZZZZZZZZZZZZZZZZZZZ", "n/a") is False
    assert not (sandbox / "roles_not_found.jsonl").exists()


def test_roles_review_never_touches_institutions_json(sandbox, monkeypatch):
    """The roles module must not be able to move the dashboard. A hire is an
    input to adoption, not evidence of it (METHODOLOGY §3)."""
    before = (ROOT / "data" / "institutions.json").read_bytes()
    script(monkeypatch, ANSWERS)
    rec = review.build_role_event(QUEUED, roles.alias_index())
    review.file_role_event(rec)
    review.file_roles_not_found("CalSTRS", "no-qualifying-evidence", "none found")
    assert (ROOT / "data" / "institutions.json").read_bytes() == before
    assert "stage" not in rec
