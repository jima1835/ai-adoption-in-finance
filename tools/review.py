#!/usr/bin/env python3
"""Local reviewer for data/institutions.json — approve / change-stage / add-evidence / pull.

Run:  python3 tools/review.py            → opens http://127.0.0.1:7788
      python3 tools/review.py --freeze   → declare the blind-recode freeze and
                                         print the digests to pin
(local/review.py is a symlink to this file; local/ holds the private review state.)
Writes institutions.json in monitor.py's exact format (indent=2, ensure_ascii=False,
trailing newline), .bak before every write. Localhost only. Never touches git.
"""
import hashlib
import json
import re
import shutil
import sys
import time
import webbrowser
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import fcntl  # POSIX: flock
except ImportError:  # Windows: msvcrt.locking
    fcntl = None
    import msvcrt

ROOT = Path(__file__).resolve().parent.parent

import validate_data  # noqa: E402  (same published row schema as the site)

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
# A CORRECTION is the exception, and it is marked on the queue entry itself
# (`"correction": true`). A skeptic pass re-reads evidence already on the row
# against the bar in METHODOLOGY §3-4; when it concludes the row was placed too
# high, nothing happened in the world and there is no date of triggering
# evidence to record. Writing one anyway — today's date, or the date of whatever
# evidence the row already cites — would put a transition in the panel that
# never occurred, which is precisely what dating the panel by evidence exists to
# prevent. So a correction moves the stage, is logged in DECISIONS.jsonl with
# `"correction": true`, and appends NOTHING to transitions.jsonl. The panel
# stays a record of the sector moving, not of the reviewer changing their mind.
NEW_QUEUE = ROOT / "local" / "NEW_INSTITUTIONS_QUEUE.json"
NEW_APPROVED = ROOT / "local" / "NEW_INSTITUTIONS_APPROVED.json"
# Intake dossiers (quotes, tiers, URLs) for rows that entered through the
# new-institution path and therefore have no REVIEW.md section.
INTAKE_DIR = ROOT / "local" / "intake"
# Presentation-layer lookups the dashboard uses to label a source link; the
# reviewer shows the same labels so an event reads the same in both places.
PUBLISHERS_FILE = ROOT / "data" / "publishers.json"
HOMEPAGES_FILE = ROOT / "data" / "homepages.json"
FROZEN_TEST = ROOT / "tests" / "test_frozen_corpus.py"
# The row count at which the maintainer INTENDS to freeze. It is a reminder,
# not a trigger: reaching it makes the reviewer nag (see `freeze_due`), and
# nothing more.
FREEZE_TARGET_ROWS = 100
# The freeze is DECLARED, never inferred. Row 100 landing mid-session used to
# flip the gate under the reviewer's hands, which meant the last row had to be
# perfect before it was approved and a typo in row 3 needed an unfreeze record
# to fix. Declaring it is one command — `python3 tools/review.py --freeze` —
# and that command is also where the pinned hashes are captured, so the freeze
# and the digests it enforces are taken from the same corpus at the same moment.
# Public and tracked: the freeze is a dated methodological act, so the date and
# the row count it was taken at belong in the repo, not on one laptop.
FREEZE_RECORD = ROOT / "data" / "recode_freeze.json"
# Removing the test alone does not establish that the blind re-code finished.
# The maintainer records completion here before the post-recode gate is lifted.
UNFREEZE_RECORD = ROOT / "local" / "RECODE_UNFREEZE.json"
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


def intake_evidence(names):
    """Map row name -> the intake dossier that published it (path, status,
    evidence items, uncertainty), for rows with no REVIEW.md section. The sweep
    card otherwise shows an empty ledger for exactly the rows whose confidence
    a proposal argues about. Live candidate folders win over `_superseded` and
    `_carryover` copies; the first hit per name is kept."""
    want = {n for n in names if n}
    out = {}
    if not want or not INTAKE_DIR.exists():
        return out
    paths = sorted(INTAKE_DIR.rglob("*.json"),
                   key=lambda q: (any(part.startswith("_")
                                      for part in q.relative_to(INTAKE_DIR).parts), str(q)))
    for path in paths:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in (doc if isinstance(doc, list) else [doc]):
            if not isinstance(item, dict):
                continue
            name = (item.get("row") or {}).get("name")
            if name in want and name not in out:
                out[name] = {
                    "path": str(path.relative_to(ROOT)),
                    "status": item.get("status"),
                    "evidence": item.get("evidence") or [],
                    "uncertainty": item.get("uncertainty"),
                }
        if len(out) == len(want):
            break
    return out


def load_json_or(path, default):
    """Read-only lookup file; absent or unparseable reads as its default."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


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


def freeze_declared():
    """Has the maintainer declared the blind-recode freeze?

    Absent file = expansion phase, the ordinary state. A file that exists but
    will not parse reads as declared: an unreadable declaration is not a licence
    to keep writing to a corpus that may already be frozen."""
    try:
        doc = json.loads(FREEZE_RECORD.read_text(encoding="utf-8"))
    except OSError:
        return False
    except (ValueError, AttributeError):
        return True
    return doc.get("blind_recode_freeze") is True


def freeze_due():
    """At or past the target row count with no declaration filed yet.

    Not a gate — the reviewer shows it so the milestone cannot pass unnoticed
    now that nothing trips automatically."""
    if freeze_declared():
        return False
    try:
        return len(load_rows()) >= FREEZE_TARGET_ROWS
    except (OSError, ValueError, TypeError):
        return False


def freeze_active():
    if not freeze_declared():
        return False
    # Declared. It now lifts only on a recorded completion — deleting the test
    # file is part of that commit, never a way to reopen writes on its own.
    try:
        record = json.loads(UNFREEZE_RECORD.read_text(encoding="utf-8"))
        return record.get("blind_recode_complete") is not True
    except (OSError, ValueError, AttributeError):
        return True


def state():
    rows = load_rows()
    unreviewed = sum(1 for r in rows if not r.get("as_of_reviewed"))
    sections = review_sections(rows)
    changes = load_nc(CH_QUEUE)
    return {
        "institutions": rows,
        "sections": sections,
        # Only for the rows a sweep proposal argues about and only where REVIEW.md
        # has nothing: the intake dossier is where their quotes and tiers live.
        "dossier_evidence": intake_evidence(
            [e.get("name") for e in changes if not sections.get(e.get("name"))]),
        "n_total": len(rows),
        "n_unreviewed": unreviewed,
        "nc_queue": load_nc(NC_QUEUE),
        "changes_queue": changes,
        "publishers": load_json_or(PUBLISHERS_FILE, {}),
        "homepages": load_json_or(HOMEPAGES_FILE, {}).get("homepages", {}),
        # Every candidate carries its failed checks to the card, so the reviewer
        # sees them before deciding rather than after being refused.
        "new_queue": [dict(e, warnings=judgment_warnings(
            e.get("row") or {}, e.get("evidence") or [], e.get("status")))
            for e in load_nc(NEW_QUEUE)],
        "new_approved": load_nc(NEW_APPROVED),
        "freeze_active": freeze_active(),
        "freeze_due": freeze_due(),
        "freeze_target": FREEZE_TARGET_ROWS,
        "nc_public": load_nc(NC_PUBLIC),
        "today": date.today().isoformat(),
        # No re-review cutoff is published: a reviewed row re-enters the queue
        # only through CH_QUEUE, when a news pass has staged a proposal. The
        # 30-day clock lives solely in the local dispatcher that picks which rows
        # get that news pass.
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
    """Serialize human reviewer writes against the overnight agent.

    During expansion this function is the human gate for public writes. Once
    the reviewed corpus reaches 100 rows, the blind-review freeze pauses those
    writes until the deliberate recode is complete. In either phase, this
    function is the only route that writes the public data files.
    """
    if freeze_active() and req.get("action") in {
            "approve", "pull", "ch_approve", "ch_reject", "nc_file", "new_publish",
            "new_approve", "new_to_appendix"}:
        return {"error": (
            "the blind-review freeze is active (declared in data/recode_freeze.json); "
            "finish the recode before approving more public changes"
        )}
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
        if str(req.get("action", "")).startswith("new_"):
            return apply_new(req)
        return _apply(req)


def _new_row_error(row):
    if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"].strip():
        return "candidate needs a name"
    if row.get("type") not in TYPES or row.get("region") not in REGIONS:
        return "candidate type or region is invalid"
    if row.get("stage") not in STAGES or row.get("confidence") not in CONFS:
        return "candidate stage or confidence is invalid"
    if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
        return "candidate needs a rationale"
    if (not isinstance(row.get("aliases"), list) or not row["aliases"]
            or any(not isinstance(a, str) or not a.strip() for a in row["aliases"])):
        return "candidate needs documented aliases"
    if (not isinstance(row.get("use_cases"), list)
            or any(not isinstance(u, str) or not u.strip() for u in row["use_cases"])):
        return "candidate needs a use_cases list"
    events = row.get("events")
    if not isinstance(events, list) or len(events) < 2:
        return "candidate needs two dated events"
    for event in events:
        if (not isinstance(event, dict) or not isinstance(event.get("date"), str)
                or not re.fullmatch(r"20\d{2}(?:-\d{2})?(?:-\d{2})?", event["date"])):
            return "event dates must retain YYYY, YYYY-MM or YYYY-MM-DD precision"
        when = event["date"]
        try:
            date.fromisoformat(when + {4: "-01-01", 7: "-01", 10: ""}[len(when)])
        except (ValueError, KeyError):
            return "event date is not a real calendar date"
        if when < "2023" or when > date.today().isoformat()[:len(when)]:
            return "event date must be between 2023 and today"
        if not str(event.get("event", "")).strip() or not str(event.get("source_url", "")).startswith("https://"):
            return "events need 2023+ dates, descriptions and https source URLs"
    if len({(e["date"], e["event"], e["source_url"]) for e in events}) < 2:
        return "candidate needs two distinct dated events"
    return None


def _new_duplicate(row):
    names = {str(x).casefold().strip() for x in [row["name"], *row.get("aliases", [])]}
    for existing in load_rows():
        existing_names = {str(x).casefold().strip()
                          for x in [existing["name"], *existing.get("aliases", [])]}
        if names & existing_names:
            return existing["name"]
    for existing in load_nc(NC_PUBLIC):
        if existing.get("name", "").casefold().strip() in names:
            return existing["name"] + " (public appendix; use a promotion workflow)"
    for path in (ROOT / "data" / "excluded.json", ROOT / "local" / "excluded.json"):
        if not path.exists():
            continue
        for entry in json.loads(path.read_text(encoding="utf-8")).get("excluded", []):
            if isinstance(entry, dict):
                excluded_names = [entry.get("name", ""), *entry.get("aliases", [])]
            else:
                excluded_names = [entry]
            if names & {str(x).casefold().strip() for x in excluded_names}:
                return "excluded institution"
    return None


def _own_voice(name, qualifying):
    """Publishers among `qualifying` that are NOT the institution talking about itself.
    Two pages on a firm's own domain are one voice, however many URLs they span."""
    stop = {"the", "and", "of", "group", "management", "asset", "investment", "investments",
            "fund", "funds", "capital", "company", "inc", "ltd", "plc", "llc", "holdings",
            "pension", "plan", "trust"}
    tokens = {t for t in re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\(.*?\)", "", name.casefold())).split()
              if t not in stop and len(t) > 3}
    external = set()
    for e in qualifying:
        pub = e["publisher"].casefold()
        if not any(t[:6] in pub.replace("-", "").replace(" ", "") for t in tokens):
            external.add(pub.strip())
    return external


def judgment_warnings(row, sources, status=None):
    """The criteria checks, as ADVICE rather than gates.

    These used to refuse the write. They no longer do: the reviewer reads the
    dossier, applies METHODOLOGY and SOURCES, and rejects on the criteria
    themselves — a tool that blocks the human at the moment of judgment just
    moves the decision into an error message. What the tool owes the reviewer is
    that nothing failing a check passes SILENTLY, so every check still runs and
    every failure is shown on the card before the click and recorded in
    DECISIONS.jsonl after it.

    Structural integrity is a different thing and stays hard: enum values,
    well-formed events, the public schema, and the duplicate check. Those are
    not judgments about evidence, they are whether the file stays valid."""
    out = []
    if status and status != "ready":
        out.append(f"intake left this candidate at status {status!r}, not 'ready'")
    qualifying = [e for e in sources if isinstance(e, dict)
                  and e.get("tier") in ("T1", "T2")
                  and e.get("publisher") and e.get("quote")
                  and str(e.get("url", "")).startswith("https://")]
    if not qualifying:
        out.append("no usable T1/T2 source: a source needs a publisher, a tier of "
                   "T1 or T2, and the verbatim sentence that carries it")
    # Own-voice publication is established practice, not a disqualifier: ADIA, ATP,
    # EQT, Ilmarinen, Investcorp, Lynx and Optiver all rest entirely on the
    # institution's own domain, and MacArthur, NPS and Pictet say so in their own
    # footnotes. The corpus caps such a row at med and discloses the limitation.
    if qualifying and not _own_voice(row.get("name", ""), qualifying) \
            and row.get("confidence") == "high":
        out.append("every qualifying source is this institution's own voice, and the "
                   "corpus caps a single-voice row at med (see Pictet, MacArthur, NPS)")
    backed = {q["url"] for q in qualifying}
    known = {e.get("url"): e for e in sources if isinstance(e, dict)}
    for ev in row.get("events", []):
        url = ev.get("source_url", "")
        if url in backed:
            continue
        hint = known.get(url)
        if hint is None:
            why = "not in the dossier at all"
        elif hint.get("tier") not in ("T1", "T2"):
            why = f"tier {hint.get('tier')!r} — a T3 or untiered source never carries an event"
        else:
            missing = [f for f in ("publisher", "quote") if not str(hint.get(f, "")).strip()]
            why = f"its source entry is missing {' and '.join(missing) or 'an https URL'}"
        out.append(f"event {ev.get('date', '?')} cites a source that cannot carry it "
                   f"({url}): {why}")
    return out


def apply_new(req):
    """Review and publish new rows through the human reviewer gate."""
    action = req.get("action")
    name = req.get("name", "")
    queue = load_nc(NEW_QUEUE)
    approved = load_nc(NEW_APPROVED)

    if action == "new_ruling":
        # A candidate held on a SOURCE-TIER question, or on single-voice sourcing,
        # is not a research failure — it is waiting on a rule the reviewer owns.
        # Recording that judgment releases it to `ready`; it does NOT publish and
        # does NOT relax the row bar, which still applies at new_approve.
        item = next((e for e in queue if e.get("row", {}).get("name") == name), None)
        if item is None:
            return {"error": f"no staged candidate named {name!r}"}
        if item.get("status") not in ("tier_ruling", "evidence_gap"):
            return {"error": f"{name} is {item.get('status')!r} — a ruling applies to a "
                             "candidate held on 'tier_ruling' or 'evidence_gap'"}
        ruling = (req.get("ruling") or "").strip()
        if len(ruling) < 25:
            return {"error": "state the ruling — which source or limitation you admit and "
                             "why. It is logged to DECISIONS.jsonl as the basis for the row, "
                             "so a word or two is not a record"}
        item["status"] = "ready"
        item["reviewer_ruling"] = ruling
        save_nc(NEW_QUEUE, queue)
        log_decision({"action": "new_ruling", "name": name, "ruling": ruling})
        return {"ok": True, "new_ruling": name}

    if action == "new_to_appendix":
        # An out-of-scope candidate is never a dashboard row. Move it to the
        # not-classified staging queue, where nc_file — the human-only gate on
        # data/not_classified.json — can pick it up. This stages a DRAFT; it does
        # not publish. The reviewer still files it, and still owns the wording.
        item = next((e for e in queue if e.get("row", {}).get("name") == name), None)
        if item is None:
            return {"error": f"no staged candidate named {name!r}"}
        row = item.get("row", {})
        reason = (req.get("reason") or item.get("reason") or "").strip()
        if not reason:
            return {"error": "a public reason is required — it must stand alone"}
        if row.get("type") not in TYPES or row.get("region") not in REGIONS:
            return {"error": "candidate needs a valid type and region to be filed"}
        nc = load_nc(NC_QUEUE)
        if any(e.get("name") == row["name"] for e in nc):
            return {"error": f"{row['name']} is already staged for the appendix"}
        if any(e.get("name", "").casefold() == row["name"].casefold() for e in load_nc(NC_PUBLIC)):
            return {"error": f"{row['name']} is already in the public appendix"}
        nc.append({"name": row["name"], "type": row["type"], "region": row["region"],
                   "outcome": req.get("outcome") or "no-qualifying-evidence",
                   "reason": reason})
        save_nc(NC_QUEUE, nc)
        queue.remove(item)
        save_nc(NEW_QUEUE, queue)
        log_decision({"action": "new_to_appendix", "name": name,
                      "prior_status": item.get("status")})
        return {"ok": True, "new_to_appendix": name}

    if action == "new_publish":
        item = next((e for e in approved if e.get("row", {}).get("name") == name), None)
        if item is None:
            return {"error": f"no approved candidate named {name!r}"}
        row = item["row"]
        err = _new_row_error(row)
        if err:
            return {"error": err}
        schema_errors = validate_data.validate(
            row, validate_data._load_schema("institution.schema.json")["items"])
        if schema_errors:
            return {"error": "candidate fails public schema: " + "; ".join(schema_errors)}
        duplicate = _new_duplicate(row)
        if duplicate:
            return {"error": f"candidate conflicts with {duplicate}"}
        rows = load_rows()
        rows.append(row)
        save_rows(rows)
        approved.remove(item)
        save_nc(NEW_APPROVED, approved)
        log_decision({"action": "new_publish", "name": name, "stage": row["stage"]})
        return {"ok": True, "new_published": name}

    item = next((e for e in queue if e.get("row", {}).get("name") == name), None)
    if item is None:
        return {"error": f"no staged candidate named {name!r}"}
    if action == "new_reject":
        reason = (req.get("reason") or "").strip()
        if not reason:
            return {"error": "rejection reason is required"}
        queue.remove(item)
        save_nc(NEW_QUEUE, queue)
        log_decision({"action": "new_reject", "name": name, "reason": reason})
        return {"ok": True, "new_rejected": name}
    if action != "new_approve":
        return {"error": f"unknown action {action!r}"}
    # A reviewer reading the dossier often finds the source the agent missed. An
    # event may only cite a T1/T2 entry, so adding a dated event here means
    # registering its source too — with the tier, which is the reviewer's call to
    # make and never the agent's (SOURCES.md §1). Stamped so the published
    # dossier shows which sources came from the review rather than the intake.
    added = req.get("evidence_added") or []
    if not isinstance(added, list):
        return {"error": "evidence_added must be a list"}
    stamped = []
    for e in added:
        if not isinstance(e, dict):
            return {"error": "each added source must be an object"}
        if not str(e.get("url", "")).startswith("https://"):
            return {"error": "a reviewer-added source needs an https URL"}
        note = str(e.get("note", "")).strip()
        stamped.append({
            "date": str(e.get("date", "")), "publisher": str(e.get("publisher", "")).strip(),
            "tier": e.get("tier", ""), "url": e["url"], "quote": str(e.get("quote", "")).strip(),
            "note": (note + f" [added by the reviewer on {date.today().isoformat()}]").strip(),
        })

    sources = item.get("evidence", []) + stamped
    row = dict(item["row"])
    err = _set_fields(row, req.get("fields", {}))
    if err:
        return err
    err = _new_row_error(row)
    if err:
        return {"error": err}
    # Advisory, not a gate — the reviewer disposes. Shown on the card before the
    # click; recorded below with the decision.
    warnings = judgment_warnings(row, sources, item.get("status"))
    duplicate = _new_duplicate(row)
    if duplicate:
        return {"error": f"candidate conflicts with {duplicate}"}
    if any(e.get("row", {}).get("name") == name for e in approved):
        return {"error": f"candidate {name!r} is already approved locally"}
    row["as_of_reviewed"] = date.today().isoformat()
    # An intake dossier held on an evidence gap may propose NO stage at all: the
    # agent declined to call it. The schema records that as null, never as "",
    # and a stage the reviewer supplies over no proposal is human_originated —
    # calling it "revised" would invent a proposal the agreement record then
    # counts as a disagreement.
    proposed = item["row"].get("stage") or None
    row["agent_proposed_stage"] = proposed
    if proposed is None:
        row["label_provenance"] = "human_originated"
    elif row["stage"] == proposed:
        row["label_provenance"] = "agent_proposed_accepted"
    else:
        row["label_provenance"] = "human_revised"
    schema_errors = validate_data.validate(
        row, validate_data._load_schema("institution.schema.json")["items"])
    if schema_errors:
        return {"error": "candidate fails public schema: " + "; ".join(schema_errors)}
    # This is the human gate: once the reviewer clicks Approve, the validated
    # row enters the public corpus through this endpoint. The intake agent can
    # only create NEW_QUEUE; it never reaches this branch.
    rows = load_rows()
    rows.append(row)
    save_rows(rows)
    queue.remove(item)
    save_nc(NEW_QUEUE, queue)
    log_decision({"action": "new_approve", "name": name, "stage": row["stage"],
                  "agent_proposed_stage": proposed,
                  "label_provenance": row["label_provenance"],
                  "intake_status": item.get("status"),
                  "published_over_warnings": warnings,
                  "events_proposed": len(item["row"].get("events", [])),
                  "events_approved": len(row["events"]),
                  "sources_added_by_reviewer": len(stamped),
                  "published": True,
                  "blind_recode_pending": freeze_active()})
    return {"ok": True, "new_approved": name, "new_published": name,
            "type": row["type"], "blind_recode_pending": freeze_active()}


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
        proposed_conf = entry.get("proposed_confidence")
        before_stage = row["stage"]
        before_conf = row.get("confidence")

        if action == "ch_reject":
            # The human looked and kept the row as it stands. That IS a review,
            # so the reviewed date advances; the row itself is untouched.
            row["as_of_reviewed"] = date.today().isoformat()
            save_rows(rows)
            queue.pop(qidx)
            save_nc(CH_QUEUE, queue)
            log_decision({"action": "ch_reject", "name": name,
                          "type": row.get("type"), "sweep": entry.get("sweep"),
                          "agent_proposed_stage": proposed,
                          "stage_held": before_stage,
                          "agent_proposed_confidence": proposed_conf,
                          "confidence_held": before_conf,
                          "reason": (req.get("reason") or "").strip()})
            return {"ok": True, "ch_rejected": name}

        fields = req.get("fields", {})
        err = _set_fields(row, fields)
        if err:
            return err
        after_stage = row["stage"]

        correction = entry.get("correction") is True
        if after_stage != before_stage and not correction:
            # A stage move is a dated event in the panel — same guard as `approve`.
            err = _transition_guard(req, row, name, before_stage, after_stage,
                                    sweep=entry.get("sweep"), proposed=proposed)
            if err:
                return err

        row["as_of_reviewed"] = date.today().isoformat()
        save_rows(rows)
        queue.pop(qidx)
        save_nc(CH_QUEUE, queue)
        moved = after_stage != before_stage
        after_conf = row.get("confidence")
        log_decision({"action": "ch_approve", "name": name, "type": row.get("type"),
                      "sweep": entry.get("sweep"),
                      "agent_proposed_stage": proposed,
                      "stage_from": before_stage, "stage_to": after_stage,
                      "human_overruled": proposed != after_stage,
                      # The 2026-09-26 audit found confidence raises invisible in
                      # this log; the field's outcome is now recorded beside the stage's.
                      "agent_proposed_confidence": proposed_conf,
                      "confidence_from": before_conf, "confidence_to": after_conf,
                      "confidence_overruled": (proposed_conf is not None
                                               and proposed_conf != after_conf),
                      "correction": correction,
                      "transition_logged": moved and not correction})
        return {"ok": True, "ch_approved": name,
                "transition": moved and not correction,
                "correction": correction and moved,
                "confidence_from": before_conf, "confidence_to": after_conf}

    return {"error": f"unknown action {action!r}"}


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


def freeze_cli(argv=()):
    """Declare the blind-recode freeze and print the digests it will enforce.

    One command, because the declaration and the pins have to come from the same
    corpus at the same instant. Captured by hand on different days they describe
    different data, and the test would then enforce a state that never existed.

    The digests are PRINTED, never written into the test file. Pasting them is a
    deliberate act; a tool that rewrites its own gate is how a red suite quietly
    goes green (tests/test_frozen_corpus.py)."""
    rows = load_rows()
    if freeze_declared():
        doc = json.loads(FREEZE_RECORD.read_text(encoding="utf-8"))
        print(f"already declared on {doc.get('declared_on')} "
              f"at {doc.get('rows_at_freeze')} rows — nothing to do")
        return 0
    if len(rows) < FREEZE_TARGET_ROWS and "--force" not in argv:
        print(f"{len(rows)} rows, target is {FREEZE_TARGET_ROWS}. Freezing now locks "
              f"the corpus short of the milestone.\n"
              f"If that is what you mean, re-run with --force.")
        return 1

    core = [{"name": r["name"], "stage": r["stage"], "rationale": r["rationale"],
             "events": r["events"]} for r in rows]
    agreement = json.loads((ROOT / "data" / "agreement.json").read_text(encoding="utf-8"))
    for key in ("_readme", "limitation"):
        agreement.pop(key, None)

    def _sha_json(obj):
        blob = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def _sha_file(name):
        return hashlib.sha256((ROOT / "data" / name).read_bytes()).hexdigest()

    FREEZE_RECORD.write_text(json.dumps({
        "blind_recode_freeze": True,
        "declared_on": date.today().isoformat(),
        "rows_at_freeze": len(rows),
        "note": ("The corpus is frozen for the blind re-code (METHODOLOGY §6). "
                 "Reviewer approvals of public changes are closed until the "
                 "re-code is complete and recorded."),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"declared: {len(rows)} rows frozen on {date.today().isoformat()}")
    print(f"wrote {FREEZE_RECORD.relative_to(ROOT)}")
    print("\nPaste these into tests/test_frozen_corpus.py — they are captured from "
          "this corpus,\nthis moment, and must not be re-derived later:\n")
    print(f'    "not_classified.json": "{_sha_file("not_classified.json")}",')
    print(f'    "transitions.jsonl": "{_sha_file("transitions.jsonl")}",')
    print(f'AGREEMENT_FIGURES_SHA = "{_sha_json(agreement)}"')
    print(f'INSTITUTIONS_CORE_SHA = "{_sha_json(core)}"')
    print(f"INSTITUTIONS_ROWS = {len(rows)}")
    return 0


if __name__ == "__main__":
    if "--freeze" in sys.argv[1:]:
        sys.exit(freeze_cli(sys.argv[1:]))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    _st = state()
    print(f"reviewer at {url}  (Ctrl-C to stop)")
    print(f"  {_st['n_total'] - _st['n_unreviewed']}/{_st['n_total']} reviewed "
          f"| {_st['n_unreviewed']} left")
    webbrowser.open(url)
    server.serve_forever()
