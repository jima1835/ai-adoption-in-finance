"""Shared helpers for the AI-leadership roles module (METHODOLOGY §11).

The unit of observation is a ROLE EVENT, not an institution and not a person.
This module owns the three things every part of the roles pipeline has to agree
on — who is in the population, who is excluded from it, and the on-disk byte
format of the JSONL files — so that monitor.py (which proposes), tools/review.py
(which files) and tools/validate_data.py (which checks) cannot drift apart.

A role event NEVER moves an adoption stage: nothing here reads or writes
`stage`. Hiring is an input to adoption, not evidence of it (METHODOLOGY §3).
"""

import json
import secrets
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

ROLES_PATH = DATA_DIR / "roles.jsonl"
ROLES_NOT_FOUND_PATH = DATA_DIR / "roles_not_found.jsonl"
EXPANSION_PATH = DATA_DIR / "roles_expansion.json"
EXCLUDED_PATH = DATA_DIR / "excluded.json"
INSTITUTIONS_PATH = DATA_DIR / "institutions.json"
NOT_CLASSIFIED_PATH = DATA_DIR / "not_classified.json"
# Untracked overlay, merged with data/excluded.json. It exists so an exclusion
# whose REASON would disclose a private affiliation can still be enforced
# without publishing that reason. Absent in a fresh clone, and that is fine.
EXCLUDED_OVERLAY_PATH = ROOT / "local" / "excluded.json"

# Agents propose here; nothing under data/ is written by an agent.
QUEUE_PATH = ROOT / "local" / "roles_queue.jsonl"

# --- Vocabularies. The schemas in schemas/ are the published copy; these are
# the runtime copy the tools validate against. tests/test_schemas.py asserts the
# two agree, so a change to one fails until the other follows. ---

EVENT_TYPES = ("created", "hired", "retitled", "departed", "expanded_remit")
TITLES_NORMALIZED = (
    "chief_ai_officer",
    "head_of_ai",
    "chief_data_and_ai_officer",
    "head_of_ai_implementation",
    "ai_lead_other",
)
REPORTING_LINES = ("ceo", "cio", "cto", "coo", "cdo", "other", "unknown")
SCOPES = ("firm_wide", "division", "unknown")
TIERS = ("T1", "T2", "T3")
CONFIDENCES = ("high", "med", "low")
OUTCOMES = ("no-qualifying-evidence", "withdrawn-on-review")
PROVENANCE = (
    "agent_proposed_accepted",
    "human_revised",
    "human_originated",
    "unknown_pre_capture",
)

# Crockford base32 — no I, L, O or U, so a ULID can be read aloud and retyped.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid(now_ms=None, rand=None):
    """A ULID: 48-bit millisecond timestamp + 80 bits of randomness, base32.

    Hand-rolled rather than pulled in as a dependency — it is twelve lines, and
    this repo ships with two runtime dependencies on purpose. Lexicographic sort
    order equals creation order, which is what makes data/roles.jsonl readable
    as an append-only log.
    """
    ms = int(time.time() * 1000) if now_ms is None else now_ms
    n = (ms << 80) | (secrets.randbits(80) if rand is None else rand)
    return "".join(_CROCKFORD[(n >> shift) & 0x1F] for shift in range(125, -1, -5))


# --- I/O. Same byte contract as monitor.py:save_json — utf-8, LF only,
# ensure_ascii=False — so CJK evidence stays literal and diffs stay minimal. ---


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    """Parse a JSONL file into a list. A blank line is skipped; a malformed one
    raises, because a half-written record in an append-only public log is a
    problem to fix, not to route around."""
    if not path.exists():
        return []
    out = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path.name}:{lineno}: {e}") from e
    return out


def append_jsonl(path, record):
    """Append exactly one record. Append-only is the point: a filed role event
    is a published measurement, so it is never rewritten in place."""
    line = json.dumps(record, ensure_ascii=False)
    json.loads(line)  # round-trip guard: never write unparseable JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def rewrite_jsonl(path, records):
    """Rewrite the whole file. Used only to REMOVE a withdrawn event, which is
    a correction to the public record and is logged as one."""
    out = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    if path.exists():
        path.with_suffix(".jsonl.bak").write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )
    path.write_text(out, encoding="utf-8", newline="\n")


# --- Population and exclusions ---


def load_excluded():
    """The denylist: data/excluded.json merged with the untracked overlay.

    Returns a dict of lowercased alias -> entry name. Merging rather than
    choosing one file means the public list can stay the documented default
    while an exclusion that cannot be explained publicly is still enforced.
    """
    index = {}
    for path in (EXCLUDED_PATH, EXCLUDED_OVERLAY_PATH):
        doc = read_json(path, {})
        for entry in doc.get("excluded", []) if isinstance(doc, dict) else []:
            name = entry.get("name", "")
            for alias in [name, *entry.get("aliases", [])]:
                if alias:
                    index[alias.strip().lower()] = name
    return index


def is_excluded(name, index=None):
    """Exact, case-insensitive — the same matching discipline monitor.py uses
    for institutions. No fuzzy matching anywhere in this pipeline."""
    index = load_excluded() if index is None else index
    return (name or "").strip().lower() in index


def load_population():
    """Every institution the roles module may search, from the three files that
    define it: the dashboard, the not-classified appendix, and the hand-written
    expansion list. Excluded institutions are dropped here, once, so no caller
    has to remember to check.

    Returns a list of {name, aliases, source}. Appendix entries carry no
    aliases field, so they match on name alone — a known limit, documented in
    METHODOLOGY §11 rather than papered over with guessed aliases.
    """
    excluded = load_excluded()
    population = []
    seen = set()

    def add(name, aliases, source):
        if not name or is_excluded(name, excluded):
            return
        key = name.strip().lower()
        if key in seen:
            return
        seen.add(key)
        kept = [a for a in aliases if not is_excluded(a, excluded)]
        population.append({"name": name, "aliases": kept or [name], "source": source})

    for row in read_json(INSTITUTIONS_PATH, []):
        add(row.get("name", ""), row.get("aliases", []), "institutions")
    for row in read_json(NOT_CLASSIFIED_PATH, []):
        add(row.get("name", ""), [], "not_classified")
    for row in read_json(EXPANSION_PATH, []):
        add(row.get("name", ""), row.get("aliases", []), "roles_expansion")
    return population


def alias_index(population=None):
    """Lowercased alias -> canonical population name. Exact matches only."""
    population = load_population() if population is None else population
    return {
        alias.strip().lower(): entry["name"]
        for entry in population
        for alias in [entry["name"], *entry["aliases"]]
        if alias.strip()
    }


def resolve_institution(raw, index=None):
    """Canonical population name for a raw institution string, or None.

    None means one of two different things — outside the population, or on the
    denylist — and callers treat both the same way: the record is not written.
    """
    index = alias_index() if index is None else index
    return index.get((raw or "").strip().lower())
