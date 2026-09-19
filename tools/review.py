#!/usr/bin/env python3
"""Local reviewer for data/institutions.json — approve / change-stage / add-evidence / pull.

Run:  python3 tools/review.py            → opens http://127.0.0.1:7788
      python3 tools/review.py --roles    → CLI review of the AI-leadership
                                           roles queue (METHODOLOGY §11)
(local/review.py is a symlink to this file; local/ holds the private review state.)
Writes institutions.json in monitor.py's exact format (indent=2, ensure_ascii=False,
trailing newline), .bak before every write. Localhost only. Never touches git.
"""
import json
import re
import shutil
import sys
import time
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import fcntl  # POSIX: flock
except ImportError:  # Windows: msvcrt.locking
    fcntl = None
    import msvcrt

ROOT = Path(__file__).resolve().parent.parent
# Running this file directly puts tools/ on sys.path, not the repo root — where
# the shared roles helpers live beside monitor.py. Add it explicitly rather than
# duplicating the population and denylist logic in two places.
sys.path.insert(0, str(ROOT))

import roles as roles_mod  # noqa: E402  (needs the sys.path line above)

DATA = ROOT / "data" / "institutions.json"
REVIEW = ROOT / "local" / "REVIEW.md"
REJECTED = ROOT / "local" / "REJECTED.md"
DECISIONS = ROOT / "local" / "DECISIONS.jsonl"
# "Assessed, not classified" public appendix — HUMAN-GATED. This reviewer is
# the ONLY writer of NC_PUBLIC; agents may stage suggestions in NC_QUEUE (or
# leave analysis in REJECTED.md) but never touch the public file.
NC_QUEUE = ROOT / "local" / "NOT_CLASSIFIED_QUEUE.json"
NC_PUBLIC = ROOT / "data" / "not_classified.json"
# Monthly REFRESH sweep: agents PROPOSE deltas into CH_QUEUE; they never mutate a
# stage themselves. Approving a proposal here is the only way a stage moves after
# a row's first review, and a stage move appends one record to TRANSITIONS —
# the panel spine. date_effective is the date of the triggering EVIDENCE, never
# the review date, or the panel measures the reviewer's calendar instead of the
# sector's.
CH_QUEUE = ROOT / "local" / "CHANGES_QUEUE.json"
TRANSITIONS = ROOT / "data" / "transitions.jsonl"
HTML = Path(__file__).resolve().parent / "review.html"
PORT = 7788
STAGES = {"exploring", "piloting", "scaling", "embedded"}
CONFS = {"high", "med", "low"}
TYPES = {"asset-manager", "pension", "sovereign-wealth", "hedge-fund", "endowment"}
REGIONS = {"US", "Canada", "Europe", "Middle East", "Asia", "Other"}
OUTCOMES = {"no-qualifying-evidence", "withdrawn-on-review"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_rows():
    return json.loads(DATA.read_text(encoding="utf-8"))


def save_rows(rows):
    # Same serialization as monitor.py:save_json — keeps diffs minimal.
    out = json.dumps(rows, indent=2, ensure_ascii=False) + "\n"
    json.loads(out)  # round-trip guard: never write unparseable JSON
    shutil.copy(DATA, DATA.with_suffix(".json.bak"))
    # utf-8 + LF-only, as monitor.py:save_json: identical bytes on every platform.
    DATA.write_text(out, encoding="utf-8", newline="\n")


def log_decision(entry):
    """Append one human decision to local/DECISIONS.jsonl — the calibration
    log the overnight agent reads. Best-effort: never blocks a write."""
    try:
        line = json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), **entry},
                          ensure_ascii=False)
        with DECISIONS.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def append_transition(rec):
    """Append one stage transition to data/transitions.jsonl. Public, tracked,
    append-only: this file is the panel. Never rewritten in place."""
    line = json.dumps(rec, ensure_ascii=False)
    json.loads(line)  # round-trip guard
    with TRANSITIONS.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def has_review_section(row):
    """True if local/REVIEW.md carries a section for this row — i.e. the row was
    agent-proposed. Legacy/baseline rows without a section are NOT logged to
    DECISIONS.jsonl: edits there are data fixes, not corrections of agent
    judgment, and would contaminate the calibration signal."""
    if not REVIEW.exists():
        return False
    # Word-boundary match so short names like "EQT" work without a length filter
    # (a plain substring test on short keys would false-match, e.g. "GIC" in "strategic").
    keys = [k for k in [row.get("name", "")] + list(row.get("aliases", [])) if len(k) >= 3]
    pats = [re.compile(r"\b" + re.escape(k.lower()) + r"\b") for k in keys]
    for line in REVIEW.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            low = line.lower()
            if any(p.search(low) for p in pats):
                return True
    return False


def review_sections(rows):
    """Map institution name -> concatenated REVIEW.md section text (## chunks)."""
    sections = {r["name"]: "" for r in rows}
    if not REVIEW.exists():
        return sections
    text = REVIEW.read_text(encoding="utf-8")
    chunks = re.split(r"(?m)^(?=## )", text)
    for chunk in chunks:
        if not chunk.startswith("## "):
            continue
        heading = chunk.splitlines()[0].lower()
        for r in rows:
            keys = [k for k in [r["name"]] + list(r.get("aliases", [])) if len(k) >= 3]
            if any(re.search(r"\b" + re.escape(k.lower()) + r"\b", heading) for k in keys):
                sections[r["name"]] += chunk
                break
    return sections


def load_nc(path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def save_nc(path, entries):
    out = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
    json.loads(out)  # round-trip guard
    if path.exists():
        shutil.copy(path, path.with_suffix(".json.bak"))
    path.write_text(out, encoding="utf-8", newline="\n")


def state():
    rows = load_rows()
    unreviewed = sum(1 for r in rows if not r.get("as_of_reviewed"))
    return {
        "institutions": rows,
        "sections": review_sections(rows),
        "n_total": len(rows),
        "n_unreviewed": unreviewed,
        "nc_queue": load_nc(NC_QUEUE),
        "changes_queue": load_nc(CH_QUEUE),
        "nc_public": load_nc(NC_PUBLIC),
        "today": date.today().isoformat(),
        # Rows reviewed on/before this date are due for re-review (30-day cycle).
        "cutoff": (date.today() - timedelta(days=30)).isoformat(),
    }


def apply_nc(req):
    """File or discard a staged 'not classified' draft. Filing is the ONLY path
    by which data/not_classified.json gains an entry — the human gate."""
    action = req.get("action")
    name = (req.get("name") or "").strip()
    queue = load_nc(NC_QUEUE)
    idx = next((i for i, e in enumerate(queue) if e.get("name") == name), None)
    if idx is None:
        return {"error": f"no staged draft named {name!r}"}

    if action == "nc_discard":
        entry = queue.pop(idx)
        save_nc(NC_QUEUE, queue)
        log_decision({"action": "nc_discard", "name": name,
                      "outcome": entry.get("outcome"),
                      "reason": (req.get("reason") or "").strip()})
        return {"ok": True, "nc_discarded": name}

    if action == "nc_file":
        f = req.get("fields", {})
        entry = {
            "name": (f.get("name") or name).strip(),
            "type": f.get("type"),
            "region": f.get("region"),
            "outcome": f.get("outcome"),
            "reason": (f.get("reason") or "").strip(),
            "as_of": date.today().isoformat(),  # filing date = human review date
        }
        if not entry["name"] or not entry["reason"]:
            return {"error": "name and reason are required"}
        if entry["type"] not in TYPES:
            return {"error": f"bad type {entry['type']!r}"}
        if entry["region"] not in REGIONS:
            return {"error": f"bad region {entry['region']!r}"}
        if entry["outcome"] not in OUTCOMES:
            return {"error": f"bad outcome {entry['outcome']!r}"}
        public = load_nc(NC_PUBLIC)
        low = entry["name"].lower()
        if any(e.get("name", "").lower() == low for e in public):
            return {"error": f"{entry['name']} is already in the public appendix"}
        if any(r["name"].lower() == low for r in load_rows()):
            return {"error": f"{entry['name']} is on the dashboard — pull the row "
                             "first if it should move to the appendix"}
        public.append(entry)
        save_nc(NC_PUBLIC, public)
        queue.pop(idx)
        save_nc(NC_QUEUE, queue)
        log_decision({"action": "nc_file", "name": entry["name"],
                      "outcome": entry["outcome"], "type": entry["type"],
                      "region": entry["region"]})
        return {"ok": True, "nc_filed": entry["name"]}

    return {"error": f"unknown action {action!r}"}


def _try_lock(lockf):
    """Non-blocking exclusive lock on an open file handle; True if acquired.
    flock on POSIX, msvcrt.locking on Windows (fcntl does not exist there).
    Either lock is released when the handle is closed."""
    try:
        if fcntl:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            msvcrt.locking(lockf.fileno(), msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False


def apply_action(req):
    """Serialize writes against the overnight agent via a lock on data/.institutions.lock."""
    if str(req.get("action", "")).startswith("nc_"):
        return apply_nc(req)  # different file, human-only writer — no lock needed
    lock_path = ROOT / "data" / ".institutions.lock"
    with lock_path.open("w") as lockf:
        for _ in range(150):  # wait up to ~15s
            if _try_lock(lockf):
                break
            time.sleep(0.1)
        else:
            return {"error": "institutions.json is locked by another writer "
                             "(overnight agent mid-insert?) — wait a moment and retry"}
        return _apply(req)


def _set_fields(row, fields):
    """Validate and apply editable fields in place. Returns an error dict, or None.
    Shared by `approve` and `ch_approve` so a refresh proposal can never take a
    path with weaker validation than a first review."""
    if "stage" in fields:
        if fields["stage"] not in STAGES:
            return {"error": f"bad stage {fields['stage']!r}"}
        row["stage"] = fields["stage"]
    if "confidence" in fields:
        if fields["confidence"] not in CONFS:
            return {"error": f"bad confidence {fields['confidence']!r}"}
        row["confidence"] = fields["confidence"]
    for key in ("rationale", "footnote", "aum"):
        if key in fields and isinstance(fields[key], str):
            row[key] = fields[key]
    if "events" in fields:
        evs = fields["events"]
        if not (isinstance(evs, list) and all(
                isinstance(e, dict) and e.get("date") and e.get("event")
                and e.get("source_url") for e in evs)):
            return {"error": "events must each have date, event, source_url"}
        row["events"] = [
            {"date": e["date"], "event": e["event"], "source_url": e["source_url"]}
            for e in evs
        ]
    return None


def _transition_guard(req, row, name, before_stage, after_stage, sweep=None, proposed=None):
    """A stage change on an already-reviewed row is a dated event in the panel.
    It needs the date of the EVIDENCE that moved it — refuse the write rather
    than silently stamping today, which would make every transition look
    simultaneous — and the evidence URL. On success, append the record to
    data/transitions.jsonl and return None; otherwise return an error dict.
    Shared by `approve` (re-review of a reviewed row) and `ch_approve` (sweep
    proposal) so neither path can move a published stage without the panel
    record."""
    eff = (req.get("date_effective") or "").strip()
    if not ISO_DATE.match(eff):
        return {"error": "a stage change needs date_effective (YYYY-MM-DD): "
                         "the date of the evidence that moved it, not today"}
    if eff > date.today().isoformat():
        return {"error": f"date_effective {eff} is in the future"}
    url = (req.get("evidence_url") or "").strip()
    if not url.startswith("http"):
        return {"error": "a stage change needs evidence_url"}
    append_transition({
        "name": name,
        "type": row.get("type"),
        "region": row.get("region"),
        "from": before_stage,
        "to": after_stage,
        "date_effective": eff,
        "evidence_url": url,
        "decided_on": date.today().isoformat(),
        "sweep": sweep,
        "agent_proposed": proposed,
        "human_overruled": (proposed != after_stage) if proposed is not None else None,
    })
    return None


def _apply(req):
    rows = load_rows()
    name = req.get("name", "")
    idx = next((i for i, r in enumerate(rows) if r["name"] == name), None)
    if idx is None:
        return {"error": f"no row named {name!r}"}
    action = req.get("action")

    if action == "pull":
        reason = (req.get("reason") or "no reason given").replace("\n", " ").strip()
        pulled = rows.pop(idx)
        save_rows(rows)
        REJECTED.parent.mkdir(parents=True, exist_ok=True)  # fresh clones have no local/
        with REJECTED.open("a", encoding="utf-8") as f:
            f.write(f"{pulled['name']} | PULLED in human review: {reason} | —\n")
        if has_review_section(pulled):
            log_decision({"action": "pull", "name": pulled["name"],
                          "type": pulled.get("type"), "stage": pulled.get("stage"),
                          "confidence": pulled.get("confidence"), "reason": reason})
        # Demotion path: a pulled row auto-stages a withdrawn-on-review draft
        # for the public appendix. Still human-gated — it goes public only if
        # you file it in the NOT CLASSIFIED panel (edit the wording there).
        staged = False
        try:
            queue = load_nc(NC_QUEUE)
            low = pulled["name"].lower()
            if (not any(e.get("name", "").lower() == low for e in queue)
                    and not any(e.get("name", "").lower() == low
                                for e in load_nc(NC_PUBLIC))):
                queue.append({
                    "name": pulled["name"], "type": pulled.get("type"),
                    "region": pulled.get("region", ""),
                    "outcome": "withdrawn-on-review",
                    "reason": reason, "as_of": date.today().isoformat(),
                })
                save_nc(NC_QUEUE, queue)
                staged = True
        except OSError:
            pass  # staging is best-effort; the pull itself must never fail
        return {"ok": True, "pulled": name, "nc_staged": staged}

    if action == "approve":
        row = rows[idx]
        fields = req.get("fields", {})
        before = {k: row.get(k) for k in
                  ("stage", "confidence", "aum", "rationale", "footnote")}
        before_events = list(row.get("events", []))
        agent_row = has_review_section(row)  # cached: REVIEW.md is ~1.3MB
        already_reviewed = bool(row.get("as_of_reviewed"))
        err = _set_fields(row, fields)
        if err:
            return err
        # --- Panel guard: a stage change on an ALREADY-REVIEWED row is a transition. ---
        # On a first review the stage edit is the provenance path (agent proposal vs
        # human decision) and needs no transition record. On a re-review the stored
        # stage is a published measurement, so moving it needs the same evidence
        # date + URL that ch_approve demands, and writes the same panel record.
        transition = False
        if already_reviewed and row["stage"] != before["stage"]:
            err = _transition_guard(req, row, name, before["stage"], row["stage"])
            if err:
                return err
            transition = True
        # --- Label provenance (Paper 2 input) — set ONCE, on first review only. ---
        # `before["stage"]` is the agent's proposed stage only on a row that has
        # never been human-reviewed. On a 30-day re-review it is a previously
        # human-approved stage, so re-running this would silently relabel the
        # row. Absence of as_of_reviewed is the first-review test.
        #
        # These two fields make the corpus usable as Paper 2 evidence despite
        # anchoring: agreement measured here is ANCHORED (the reviewer saw the
        # proposal), so it is not independent agreement and it is not kappa.
        #
        # `label_provenance` is also checked, not just as_of_reviewed, because
        # as_of_reviewed is NOT a reliable first-review test on its own: PROMPT.md
        # instructs an ENRICH pass to BLANK it so the row re-enters the queue, and
        # anything else that reopens a row the same way would do the same. On such
        # a row `before["stage"]` is a human-approved stage, so recomputing here
        # would rewrite a recorded overrule into `agent_proposed_accepted` and
        # delete a data point from data/agreement.json. Provenance is written
        # exactly once and only here, so its presence is the durable marker.
        if not row.get("as_of_reviewed") and not row.get("label_provenance"):
            row["agent_proposed_stage"] = before["stage"] if agent_row else None
            row["label_provenance"] = (
                "human_originated" if not agent_row
                else "human_revised" if row["stage"] != before["stage"]
                else "agent_proposed_accepted"
            )
        row["as_of_reviewed"] = date.today().isoformat()
        save_rows(rows)
        if agent_row:
            changes = {k: {"old": before[k], "new": row.get(k)}
                       for k in before if row.get(k) != before[k]}
            new_events = row.get("events", [])
            log_decision({"action": "approve", "name": name, "type": row.get("type"),
                          "changes": changes,
                          "label_provenance": row.get("label_provenance"),
                          "agent_proposed_stage": row.get("agent_proposed_stage"),
                          "events_added": [e for e in new_events if e not in before_events],
                          "events_removed": [e for e in before_events if e not in new_events],
                          "transition_logged": transition})
        return {"ok": True, "approved": name, "transition": transition}

    if action in ("ch_approve", "ch_reject"):
        queue = load_nc(CH_QUEUE)
        qidx = next((i for i, e in enumerate(queue) if e.get("name") == name), None)
        if qidx is None:
            return {"error": f"no staged change for {name!r}"}
        entry = queue[qidx]
        row = rows[idx]
        proposed = entry.get("proposed_stage")
        before_stage = row["stage"]

        if action == "ch_reject":
            # The human looked and kept the row as it stands. That IS a review,
            # so the 30-day clock resets; the row itself is untouched.
            row["as_of_reviewed"] = date.today().isoformat()
            save_rows(rows)
            queue.pop(qidx)
            save_nc(CH_QUEUE, queue)
            log_decision({"action": "ch_reject", "name": name,
                          "type": row.get("type"), "sweep": entry.get("sweep"),
                          "agent_proposed_stage": proposed,
                          "stage_held": before_stage,
                          "reason": (req.get("reason") or "").strip()})
            return {"ok": True, "ch_rejected": name}

        fields = req.get("fields", {})
        err = _set_fields(row, fields)
        if err:
            return err
        after_stage = row["stage"]

        if after_stage != before_stage:
            # A stage move is a dated event in the panel — same guard as `approve`.
            err = _transition_guard(req, row, name, before_stage, after_stage,
                                    sweep=entry.get("sweep"), proposed=proposed)
            if err:
                return err

        row["as_of_reviewed"] = date.today().isoformat()
        save_rows(rows)
        queue.pop(qidx)
        save_nc(CH_QUEUE, queue)
        log_decision({"action": "ch_approve", "name": name, "type": row.get("type"),
                      "sweep": entry.get("sweep"),
                      "agent_proposed_stage": proposed,
                      "stage_from": before_stage, "stage_to": after_stage,
                      "human_overruled": proposed != after_stage,
                      "transition_logged": after_stage != before_stage})
        return {"ok": True, "ch_approved": name,
                "transition": after_stage != before_stage}

    return {"error": f"unknown action {action!r}"}


# ---------------------------------------------------------------------------
# Roles review — CLI (METHODOLOGY §11)
#
# Deliberately not a pane in review.html. That page is built around one row of
# institutions.json at a time; a role event is a different unit with a different
# shape, and bolting it on would duplicate the whole card for no gain. The
# review itself is a short, ordered set of questions, which a terminal does
# better than a form.
#
# The gate is the same as everywhere else in this repo: an agent proposes into
# local/roles_queue.jsonl, and NOTHING reaches data/roles.jsonl or
# data/roles_not_found.jsonl except through a human answering these questions.
# ---------------------------------------------------------------------------

ROLES_LOCK = ROOT / "data" / ".roles.lock"
# Variable precision, exactly like an institutions event date.
ROLE_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def _prompt(label, default=None, choices=None, required=True, allow_null=False):
    """Ask once, validate, repeat until valid. Enter takes the default.

    `allow_null` distinguishes "leave it empty" from "no answer yet": an unnamed
    person is a complete record, not a missing one.
    """
    hint = ""
    if choices:
        hint = "\n    " + "  ".join(f"[{i + 1}] {c}" for i, c in enumerate(choices))
    suffix = f" ({default})" if default not in (None, "") else ""
    while True:
        raw = input(f"  {label}{suffix}{hint}\n  > ").strip()
        if not raw and default is not None:
            return default
        if not raw:
            if allow_null:
                return None
            if not required:
                return ""
            print("    required.")
            continue
        if choices:
            if raw.isdigit() and 1 <= int(raw) <= len(choices):
                return choices[int(raw) - 1]
            if raw in choices:
                return raw
            print(f"    one of: {', '.join(choices)}")
            continue
        return raw


def _queue():
    return roles_mod.read_jsonl(roles_mod.QUEUE_PATH)


def _rewrite_queue(items):
    out = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)
    roles_mod.QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    roles_mod.QUEUE_PATH.write_text(out, encoding="utf-8", newline="\n")


def build_role_event(item, index):
    """Interview the reviewer for one queued candidate; return the record.

    Returns None if the reviewer aborts. Every field that carries a claim is
    typed by the human against the source they just read — the screener's
    guesses are offered as defaults and nothing more.
    """
    institution = roles_mod.resolve_institution(item.get("institution", ""), index)
    if not institution:
        print(f"  ! {item.get('institution')!r} is not in the population "
              f"(or is excluded) — nothing can be filed for it.")
        return None

    proposed = item.get("event_type_guess") or None
    print("\n  Fill the record from the source you just read. Enter takes the default.")
    title_verbatim = _prompt("title_verbatim (as the source prints it)")
    record = {
        "id": roles_mod.new_ulid(),
        "institution": institution,
        "title_verbatim": title_verbatim,
        "title_normalized": _prompt("title_normalized",
                                    choices=list(roles_mod.TITLES_NORMALIZED)),
        "person": _prompt("person (Enter = not named)", default=item.get("person_guess"),
                          required=False, allow_null=True) or None,
        "event_type": _prompt("event_type", default=proposed,
                              choices=list(roles_mod.EVENT_TYPES)),
        "date": _prompt("date (YYYY, YYYY-MM or YYYY-MM-DD)", default=item.get("date")),
        "reporting_line": _prompt("reporting_line", default="unknown",
                                  choices=list(roles_mod.REPORTING_LINES)),
        "scope": _prompt("scope", default="unknown", choices=list(roles_mod.SCOPES)),
        "source_url": _prompt("source_url", default=item.get("url")),
        "source_tier": _prompt("source_tier", choices=list(roles_mod.TIERS)),
        "quote_verbatim": _prompt("quote_verbatim (original language, verbatim)"),
        "language": _prompt("language (BCP-47)", default="en"),
        "confidence": _prompt("confidence", choices=list(roles_mod.CONFIDENCES)),
        "rationale": _prompt("rationale (what it shows, and what it stops short of)"),
    }
    if not ROLE_DATE.match(record["date"]):
        print("    ! date must be YYYY, YYYY-MM or YYYY-MM-DD — not filed.")
        return None

    # Provenance, written once, exactly as the institutions path does it. The
    # anchored-agreement caveat in METHODOLOGY §6 applies here unchanged: the
    # reviewer saw the screener's guess before answering.
    record["as_of_reviewed"] = date.today().isoformat()
    record["agent_proposed_event_type"] = proposed
    record["label_provenance"] = (
        "human_originated" if not proposed
        else "agent_proposed_accepted" if record["event_type"] == proposed
        else "human_revised"
    )
    return record



def file_role_event(record):
    with ROLES_LOCK.open("w") as lockf:
        if not _try_lock(lockf):
            print("  ! roles.jsonl is locked by another writer — try again.")
            return False
        roles_mod.append_jsonl(roles_mod.ROLES_PATH, record)
    log_decision({"action": "roles_file", "institution": record["institution"],
                  "id": record["id"], "event_type": record["event_type"],
                  "agent_proposed_event_type": record["agent_proposed_event_type"],
                  "label_provenance": record["label_provenance"],
                  "person_named": bool(record["person"]),
                  "source_tier": record["source_tier"]})
    return True


def file_roles_not_found(institution, outcome, reason):
    record = {
        "institution": institution,
        # This date IS the reviewer's calendar, and the field name says so: it
        # dates the LOOKING, not any evidence. Unlike a stage transition, a
        # negative result has no evidence date to take.
        "searched_on": date.today().isoformat(),
        "outcome": outcome,
        "reason": reason,
    }
    with ROLES_LOCK.open("w") as lockf:
        if not _try_lock(lockf):
            print("  ! roles_not_found.jsonl is locked by another writer — try again.")
            return False
        roles_mod.append_jsonl(roles_mod.ROLES_NOT_FOUND_PATH, record)
    log_decision({"action": "roles_not_found", "institution": institution,
                  "outcome": outcome, "reason": reason})
    return True


def remove_role_event(event_id, reason):
    """Withdraw a filed event: drop it from roles.jsonl and record WHY in the
    negative record. A removal that leaves no trace would make the corpus look
    like the event was never filed."""
    events = roles_mod.read_jsonl(roles_mod.ROLES_PATH)
    target = next((e for e in events if e.get("id") == event_id), None)
    if not target:
        print(f"  ! no filed event with id {event_id!r}")
        return False
    with ROLES_LOCK.open("w") as lockf:
        if not _try_lock(lockf):
            print("  ! roles.jsonl is locked by another writer — try again.")
            return False
        roles_mod.rewrite_jsonl(roles_mod.ROLES_PATH,
                                [e for e in events if e.get("id") != event_id])
    file_roles_not_found(target["institution"], "withdrawn-on-review", reason)
    log_decision({"action": "roles_remove", "institution": target["institution"],
                  "id": event_id, "reason": reason})
    print(f"  removed {event_id} ({target['institution']}) and recorded the withdrawal.")
    return True


def roles_cli(argv=()):
    """Walk the queue. Returns the number of records filed."""
    if "--remove" in argv:
        pos = list(argv).index("--remove")
        if pos + 1 >= len(argv):
            print("usage: review.py --roles --remove <ULID>")
            return 0
        reason = _prompt("reason for withdrawal (public text)")
        remove_role_event(argv[pos + 1], reason)
        return 0

    queue = _queue()
    if not queue:
        print(f"Roles queue is empty ({roles_mod.QUEUE_PATH}).")
        print("Populate it with:  uv run --env-file .env python monitor.py --roles --limit 5")
        return 0

    index = roles_mod.alias_index()
    filed = 0
    remaining = []
    for n, item in enumerate(queue, 1):
        print("\n" + "─" * 72)
        print(f"[{n}/{len(queue)}] {item.get('institution')} — "
              f"{item.get('event_type_guess')} (screener guess)   {item.get('date')}")
        if item.get("person_guess"):
            print(f"  person guess : {item['person_guess']}")
        print(f"  why queued   : {item.get('reason')}")
        print(f"  source       : {item.get('url')}")
        print("  Open the source and read it before answering.")
        choice = _prompt("[f]ile  [n]ot-found  [s]kip  [d]iscard  [q]uit",
                         default="s", choices=["f", "n", "s", "d", "q"])

        if choice == "q":
            remaining += queue[n - 1:]
            break
        if choice == "s":
            remaining.append(item)
            continue
        if choice == "d":
            log_decision({"action": "roles_discard",
                          "institution": item.get("institution"),
                          "url": item.get("url"),
                          "reason": _prompt("reason (private note)", required=False)})
            continue
        if choice == "n":
            institution = roles_mod.resolve_institution(item.get("institution", ""), index)
            if not institution:
                print("  ! outside the population — discarded instead.")
                continue
            file_roles_not_found(
                institution, "no-qualifying-evidence",
                _prompt("reason (PUBLIC text — it must stand alone)"))
            continue

        record = build_role_event(item, index)
        if record and file_role_event(record):
            filed += 1
            print(f"  filed {record['id']} — {record['institution']} / "
                  f"{record['event_type']} ({record['label_provenance']})")
        else:
            remaining.append(item)

    _rewrite_queue(remaining)
    print(f"\nFiled {filed}; {len(remaining)} left in the queue.")
    return filed


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        # The HTML is re-read from disk on every request, so the server is always
        # current — but without this the BROWSER caches review.html and keeps
        # rendering an old card against freshly fetched /state JSON. That failure
        # mode looks exactly like "the fix did not land", because the data is new
        # and the UI is not. /state must not be cached either: a stale queue would
        # let a reviewer act on a row that has already moved.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/state":
            self._send(200, state())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/apply":
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length))
            result = apply_action(req)
        except Exception as e:  # keep the reviewer alive; report the error
            result = {"error": str(e)}
        result["state"] = state()
        if "error" not in result:
            st = result["state"]
            print(f"  {st['n_total'] - st['n_unreviewed']}/{st['n_total']} reviewed "
                  f"| {st['n_unreviewed']} left", flush=True)
        self._send(200 if "error" not in result else 400, result)

    def log_message(self, fmt, *args):  # quiet
        pass


if __name__ == "__main__":
    if "--roles" in sys.argv[1:]:
        # CLI mode: no server, no browser. The web reviewer is untouched.
        roles_cli(sys.argv[1:])
        sys.exit(0)

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    _st = state()
    print(f"reviewer at {url}  (Ctrl-C to stop)")
    print(f"  {_st['n_total'] - _st['n_unreviewed']}/{_st['n_total']} reviewed "
          f"| {_st['n_unreviewed']} left")
    webbrowser.open(url)
    server.serve_forever()
