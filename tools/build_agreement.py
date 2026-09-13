#!/usr/bin/env python3
"""Build data/agreement.json — the public human-vs-agent disagreement record.

Derived ENTIRELY from two already-public files, so anyone can reproduce it:
  data/institutions.json  — label_provenance, agent_proposed_stage, stage
  data/not_classified.json — outcome == withdrawn-on-review

No text from local/ ever reaches this file. Rerun after every review session:

    python3 tools/build_agreement.py           # write data/agreement.json
    python3 tools/build_agreement.py --print   # dry run, stdout only

WHAT THIS IS NOT. The reviewer saw the agent's proposed stage, and the
agent-written rationale states the stage reasoning, before deciding. So the
agreement here is ANCHORED: it is an upper bound on how well an independent
coder would reproduce these labels, not a reliability coefficient. No kappa is
computed here and none should be quoted from this file. A blind re-code against
stripped evidence bundles is a separate exercise.
"""
import json
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INST = ROOT / "data" / "institutions.json"
NC = ROOT / "data" / "not_classified.json"
OUT = ROOT / "data" / "agreement.json"

STAGES = ["exploring", "piloting", "scaling", "embedded"]

README = (
    "Human-vs-agent disagreement record for the corpus. A research agent drafts "
    "each row from public sources and proposes an adoption stage; a human "
    "reviewer then checks the row against those sources and accepts, revises, or "
    "removes it. This file counts what the reviewer did. IMPORTANT: the reviewer "
    "saw the agent's proposed stage and its written reasoning before deciding, so "
    "these figures are ANCHORED agreement — an upper bound on reproducibility, "
    "not an inter-rater reliability coefficient. No kappa is reported here and "
    "none should be inferred. Derived from data/institutions.json and "
    "data/not_classified.json; rebuild with tools/build_agreement.py."
)

LIMITATION = (
    "Anchored, not blind: the reviewer saw the agent's proposed stage and its "
    "rationale before deciding, and is also the author of the classification "
    "rules. Read these as an upper bound on agreement, never as a reliability "
    "coefficient."
)


def main():
    rows = json.loads(INST.read_text(encoding="utf-8"))
    nc = json.loads(NC.read_text(encoding="utf-8"))

    prov = Counter(r.get("label_provenance") or "not_yet_reviewed" for r in rows)

    # Comparable = a row where the agent proposed a stage AND a human settled one.
    pairs = [
        (r["agent_proposed_stage"], r["stage"], r["name"], r.get("as_of_reviewed"))
        for r in rows
        if r.get("agent_proposed_stage") and r.get("as_of_reviewed")
    ]
    exact = sum(1 for p, f, _, _ in pairs if p == f)
    revised = [
        {
            "institution": n,
            "proposed": p,
            "final": f,
            "direction": "up" if STAGES.index(f) > STAGES.index(p) else "down",
            "distance": abs(STAGES.index(f) - STAGES.index(p)),
            "as_of_reviewed": d,
        }
        for p, f, n, d in pairs
        if p != f
    ]
    withdrawn = [
        {"institution": e["name"], "as_of": e.get("as_of"), "reason": e.get("reason")}
        for e in nc
        if e.get("outcome") == "withdrawn-on-review"
    ]

    matrix = Counter((p, f) for p, f, _, _ in pairs)
    dist = Counter(abs(STAGES.index(f) - STAGES.index(p)) for p, f, _, _ in pairs)

    # Two denominators, because they answer different questions.
    #   stage_agreement  — of rows that survived review, how often did the stage stand?
    #   proposal_accepted — of every agent proposal adjudicated, how often was it
    #                       taken as-is? Withdrawals are disagreements too, and
    #                       dropping them flatters the pipeline.
    adjudicated = len(pairs) + len(withdrawn)

    # `as_of` describes the CORPUS STATE this file summarises, not the day the
    # script happened to run. date.today() was wrong twice over: it made the file
    # churn on every rebuild even when nothing changed, and — because this repo is
    # driven both from a Mac (UTC-7) and from a Linux VM (UTC) — the two machines
    # stamped different dates on identical data, which showed up as docs/ and data/
    # permanently "differing" after a clean build. The newest dated decision in
    # EITHER input — a row's human review date or a negative-record entry's `as_of`
    # (v1.0.2: the negative record is an input too, so filing a withdrawal moves the
    # stamp) — is deterministic, environment-independent, and is what a reader wants.
    as_of = max(
        [r.get("as_of_reviewed") or "" for r in rows] + [e.get("as_of") or "" for e in nc],
        default="",
    ) or date.today().isoformat()

    doc = {
        "_readme": README,
        "as_of": as_of,
        "corpus": {
            "rows": len(rows),
            "reviewed": sum(1 for r in rows if r.get("as_of_reviewed")),
            "not_yet_reviewed": sum(1 for r in rows if not r.get("as_of_reviewed")),
        },
        "provenance": {k: prov[k] for k in sorted(prov)},
        "stage_agreement": {
            "n": len(pairs),
            "unchanged": exact,
            "revised": len(revised),
            "rate": round(exact / len(pairs), 4) if pairs else None,
            "by_distance": {str(k): dist[k] for k in sorted(dist)},
        },
        "proposal_accepted": {
            "n": adjudicated,
            "accepted_unchanged": exact,
            "stage_revised": len(revised),
            "withdrawn_on_review": len(withdrawn),
            "rate": round(exact / adjudicated, 4) if adjudicated else None,
        },
        "matrix": [
            {"proposed": p, "final": f, "n": n}
            for (p, f), n in sorted(
                matrix.items(), key=lambda kv: (STAGES.index(kv[0][0]), STAGES.index(kv[0][1]))
            )
        ],
        "revisions": sorted(revised, key=lambda r: r["institution"]),
        "withdrawals": sorted(withdrawn, key=lambda w: w["institution"]),
        "limitation": LIMITATION,
    }

    out = json.dumps(doc, indent=1, ensure_ascii=False)
    if "--print" in sys.argv:
        print(out)
        return 0
    if OUT.exists():
        shutil.copy(OUT, OUT.with_suffix(".json.bak"))
    OUT.write_text(out, encoding="utf-8")
    json.loads(OUT.read_text(encoding="utf-8"))
    a, b = doc["stage_agreement"], doc["proposal_accepted"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  stage agreement   {a['unchanged']}/{a['n']} = {a['rate']:.1%} "
          "(anchored — upper bound)")
    print(f"  proposals as-is   {b['accepted_unchanged']}/{b['n']} = {b['rate']:.1%} "
          f"({b['stage_revised']} revised, {b['withdrawn_on_review']} withdrawn)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
