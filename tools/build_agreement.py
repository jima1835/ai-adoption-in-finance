#!/usr/bin/env python3
"""Build data/agreement.json — the public human-vs-agent disagreement record.

Derived ENTIRELY from four already-public files, so anyone can reproduce it:
  data/institutions.json   — label_provenance, agent_proposed_stage, stage
  data/not_classified.json — outcome == withdrawn-on-review
  data/transitions.jsonl   — evidence-dated stage moves after first review
  data/rereads.jsonl       — re-read passes: corrections on the evidence already
                             on a row, filed by the reviewer (v1.2.2)
  data/first_review.jsonl  — what the agent proposed and what the reviewer set at
                             first review, stage and confidence, with the review time
                             and the prompt version in force (v1.2.3)

WHAT THE RATE MEASURES. `stage_agreement` is the reviewer's FIRST decision on
each row against the agent's proposal, read from `label_provenance`, which
review.py sets once at first review and never overwrites. A stage that later
changes — a correction on re-reading the same evidence, or a transition on new
evidence dated in transitions.jsonl — does not move this rate: those are a
different question, and they are listed under `since_first_review` so the
current label can be reconciled with the first decision. Comparing the proposal
with the row's CURRENT stage instead (the previous behaviour) let a correction
that happened to restore the proposal count as agreement and let an evidence
transition count as disagreement; that number is still reported, as
`current_label`, so the two are never confused.

No text from local/ ever reaches this file. Rerun after every review session:

    python3 tools/build_agreement.py           # write data/agreement.json
    python3 tools/build_agreement.py --print   # dry run, stdout only

WHAT THIS IS NOT. The reviewer saw the agent's proposed stage, and the
agent-written rationale states the stage reasoning, before deciding. So the
agreement here is ANCHORED: the decision is not independent of the proposal, so
it does not estimate how well an independent coder would reproduce these labels
and is not a reliability coefficient. No kappa is
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
TRANS = ROOT / "data" / "transitions.jsonl"
REREADS = ROOT / "data" / "rereads.jsonl"
FIRST = ROOT / "data" / "first_review.jsonl"
CONF_ORD = {"low": 0, "med": 1, "high": 2}
OUT = ROOT / "data" / "agreement.json"

STAGES = ["exploring", "piloting", "scaling", "embedded"]

README = (
    "Human-vs-agent disagreement record for the corpus. A research agent drafts "
    "each row from public sources and proposes an adoption stage; a human "
    "reviewer then checks the row against those sources and accepts, revises, or "
    "removes it. This file counts what the reviewer did at that FIRST review "
    "(label_provenance); later corrections and evidence-dated transitions are listed "
    "under since_first_review and never folded into the rate. IMPORTANT: the reviewer "
    "saw the agent's proposed stage and its written reasoning before deciding, so "
    "these figures are ANCHORED, non-independent agreement and should not be "
    "read as an inter-rater reliability estimate. No kappa is reported here and "
    "none should be inferred. Re-read passes (data/rereads.jsonl) are summarised "
    "under rereads: who drafted the change cards, the scope, the direction checked "
    "and every decision; a re-read is anchored too. The confidence block compares the "
    "confidence the agent proposed with the confidence the reviewer set at first review "
    "(anchored too), and first_review_sessions sets both fields side by side per review "
    "date with the agent prompt version in force. Derived from data/institutions.json, "
    "data/not_classified.json, data/transitions.jsonl, data/rereads.jsonl and "
    "data/first_review.jsonl; rebuild "
    "with tools/build_agreement.py."
)

LIMITATION = (
    "Anchored, not blind: the reviewer saw the agent's proposed stage and its "
    "rationale before deciding, and is also the author of the classification "
    "rules. The figures are not independent of the proposal; never read them as "
    "a reliability coefficient."
)


def _first_review_records():
    if not FIRST.exists():
        return []
    return [json.loads(line) for line in FIRST.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def sessions_block(recs):
    """Per review date: rows first reviewed, stage revisions against the agent's proposal
    (up / down), confidence raised / lowered against it, and the agent prompt version(s)
    in force. Both fields are anchored; the table shows where the reviewer moved, not
    who was right."""
    if not recs:
        return None
    out = {}
    for r in recs:
        if not r["first_review_at"]:
            continue
        d = out.setdefault(r["first_review_at"][:10], {
            "rows": 0, "stage_proposals": 0, "stage_revised_up": 0, "stage_revised_down": 0,
            "confidence_proposals": 0, "confidence_raised": 0, "confidence_lowered": 0,
            "prompt_versions": set()})
        d["rows"] += 1
        if r["prompt_version_at_first_review"]:
            d["prompt_versions"].add(r["prompt_version_at_first_review"])
        p, f = r["agent_proposed_stage"], r["first_review_stage"]
        if p:
            d["stage_proposals"] += 1
            if STAGES.index(f) > STAGES.index(p):
                d["stage_revised_up"] += 1
            elif STAGES.index(f) < STAGES.index(p):
                d["stage_revised_down"] += 1
        pc, fc = r["agent_proposed_confidence"], r["first_review_confidence"]
        if pc and fc:
            d["confidence_proposals"] += 1
            d["confidence_raised"] += CONF_ORD[fc] > CONF_ORD[pc]
            d["confidence_lowered"] += CONF_ORD[fc] < CONF_ORD[pc]
    return [dict(date=k, **{**v, "prompt_versions": sorted(v["prompt_versions"])})
            for k, v in sorted(out.items())]


def confidence_block(rows):
    """First-review confidence against the agent's proposal, from first_review.jsonl.

    Same logic as stage_agreement: the reviewer saw the proposed confidence first, so
    this is anchored, and it describes the reviewer's ruling on evidence strength, not
    the accuracy of any label. Later moves (all before v1.2.0) are reported as
    changes since first review, never folded into the first-review counts."""
    recs = [r for r in _first_review_records() if r["agent_proposed_confidence"]]
    if not recs:
        return None
    today = {r["name"]: r.get("confidence") for r in rows}
    def step(r):
        first, proposed = r["first_review_confidence"], r["agent_proposed_confidence"]
        return CONF_ORD[first] - CONF_ORD[proposed]

    up = [r for r in recs if step(r) > 0]
    down = [r for r in recs if step(r) < 0]
    pairs = Counter((r["agent_proposed_confidence"], r["first_review_confidence"]) for r in recs)
    by_date = {}
    for r in recs:
        d = by_date.setdefault(r["first_review_at"][:10], {"n": 0, "raised": 0, "lowered": 0})
        d["n"] += 1
        d["raised"] += r in up
        d["lowered"] += r in down
    since = Counter()
    for r in recs:
        now = today.get(r["institution"])
        if now and now != r["first_review_confidence"]:
            since["lowered" if CONF_ORD[now] < CONF_ORD[r["first_review_confidence"]]
                  else "raised"] += 1
    order = ["high", "med", "low"]
    return {
        "basis": "first review: the confidence the agent proposed against the confidence the "
                 "reviewer set when first approving the row; anchored (the reviewer saw the "
                 "proposal); confidence rates the public evidence for the stage, not label "
                 "accuracy",
        "n": len(recs),
        "rows_without_recoverable_proposal": len(rows) - len(recs),
        "raised_at_first_review": len(up),
        "lowered_at_first_review": len(down),
        "unchanged_at_first_review": len(recs) - len(up) - len(down),
        "matrix": [{"proposed": p, "first_review": f, "n": pairs[(p, f)]}
                   for p in order for f in order if pairs[(p, f)]],
        "by_first_review_date": [dict(date=k, **v) for k, v in sorted(by_date.items())],
        "since_first_review": {"lowered": since["lowered"], "raised": since["raised"]},
        "first_review_source": dict(
            sorted(Counter(r["first_review_confidence_source"] for r in recs).items())),
    }


def main():
    rows = json.loads(INST.read_text(encoding="utf-8"))
    nc = json.loads(NC.read_text(encoding="utf-8"))

    prov = Counter(r.get("label_provenance") or "not_yet_reviewed" for r in rows)
    moved = {}  # name -> latest evidence-dated transition after first review
    if TRANS.exists():
        for line in TRANS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                moved[rec["name"]] = rec
    passes = []
    if REREADS.exists():
        for line in REREADS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                passes.append(json.loads(line))
    passes.sort(key=lambda p: (p["date"], p["id"]))

    # Comparable = a row where the agent proposed a stage AND a human ruled on it
    # at first review. label_provenance is that ruling, captured once.
    reviewed = [r for r in rows if r.get("agent_proposed_stage") and r.get("as_of_reviewed")
                and r.get("label_provenance") in ("agent_proposed_accepted", "human_revised")]
    accepted = [r for r in reviewed if r["label_provenance"] == "agent_proposed_accepted"]
    revised_rows = [r for r in reviewed if r["label_provenance"] == "human_revised"]
    exact = len(accepted)

    # First-review outcome per row. For a row revised at first review and later
    # corrected back to the proposal, the first-review stage is the `stage_before`
    # of the approved re-read entry that restored the proposal (data/rereads.jsonl,
    # v1.2.2; the same stages were public in agreement.json from v1.0.2 to v1.1.0).
    # A row with no such entry is reported as undetermined rather than invented.
    def restoring_entry(name, proposed):
        for ps in passes:
            for e in ps["entries"]:
                if (e["institution"] == name and e["decision"] == "approved"
                        and e["stage_after"] == proposed and e["stage_before"] != proposed):
                    return ps, e
        return None, None

    pairs, undetermined, restored = [], [], {}
    for r in reviewed:
        p, cur = r["agent_proposed_stage"], r["stage"]
        if r["label_provenance"] == "agent_proposed_accepted":
            pairs.append((p, p, r["name"], r.get("as_of_reviewed")))
        elif cur != p:
            pairs.append((p, cur, r["name"], r.get("as_of_reviewed")))
        else:
            ps, e = restoring_entry(r["name"], p)
            if e:
                pairs.append((p, e["stage_before"], r["name"], r.get("as_of_reviewed")))
                restored[r["name"]] = {"reread": ps["id"], "date": ps["date"],
                                       "restored_to_proposal": p}
            else:
                undetermined.append(r["name"])
    revised = [
        {
            "institution": n,
            "proposed": p,
            "final": f,
            "direction": "up" if STAGES.index(f) > STAGES.index(p) else "down",
            "distance": abs(STAGES.index(f) - STAGES.index(p)),
            "as_of_reviewed": d,
            **({"later": restored[n]} if n in restored else {}),
        }
        for p, f, n, d in pairs
        if p != f
    ] + [
        {
            "institution": r["name"],
            "proposed": r["agent_proposed_stage"],
            "final": None,
            "direction": "corrected-back",
            "distance": None,
            "as_of_reviewed": r.get("as_of_reviewed"),
            "note": "revised at first review, later corrected back to the proposed stage on a "
                    "re-reading of the same evidence, with no re-read entry recording the "
                    "first-review stage",
        }
        for r in revised_rows if r["name"] in undetermined
    ]

    # What has changed since the first decision — reported, never folded into the rate.
    since = {
        "transitions_on_new_evidence": [
            {"institution": r["name"], "from": moved[r["name"]]["from"],
             "to": moved[r["name"]]["to"], "date_effective": moved[r["name"]]["date_effective"],
             "agent_proposed_move": moved[r["name"]].get("agent_proposed")}
            for r in reviewed if r["name"] in moved
        ],
        "corrections_after_acceptance": [
            {"institution": r["name"], "accepted_at": r["agent_proposed_stage"],
             "current": r["stage"]}
            for r in accepted if r["stage"] != r["agent_proposed_stage"] and r["name"] not in moved
        ],
        "revised_then_corrected_back": sorted(set(undetermined) | set(restored)),
    }

    # Re-read passes, summarised. A pass is anchored like the first review: the
    # reviewer ruled on change cards that carried a proposed stage.
    prov_of = {r["name"]: r for r in rows}
    reread_summary = []
    for ps in passes:
        es = ps["entries"]
        moves = [e for e in es
                 if e["decision"] == "approved" and e["stage_after"] != e["stage_before"]]
        reread_summary.append({
            "id": ps["id"], "date": ps["date"], "scope": ps["scope"],
            "n_in_scope": ps["n_in_scope"], "direction_checked": ps["direction_checked"],
            "initiated_by": ps["initiated_by"], "cards_drafted_by": ps["cards_drafted_by"],
            "cards": len(es),
            "cards_proposing_a_move": sum(
                1 for e in es if e["card_proposed_stage"] != e["stage_before"]),
            "moved": sorted(e["institution"] for e in moves),
            "rejected": sorted(e["institution"] for e in es if e["decision"] == "rejected"),
            "held_on_approval": sorted(
                e["institution"] for e in es
                if e["decision"] == "approved" and e["stage_after"] == e["stage_before"]),
            "no_card": ps["n_in_scope"] - len(es),
            "restored_to_proposal": sorted(
                e["institution"] for e in moves
                if prov_of.get(e["institution"], {}).get("label_provenance") == "human_revised"
                and prov_of[e["institution"]].get("agent_proposed_stage") == e["stage_after"]),
        })
    cur_match = sum(1 for r in reviewed if r["stage"] == r["agent_proposed_stage"])
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
    adjudicated = len(reviewed) + len(withdrawn)

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

    n_first = len(reviewed)
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
            "basis": "first review: label_provenance, set once when a human first ruled on the "
                     "agent's proposal; later corrections and transitions do not move it",
            "n": n_first,
            "unchanged": exact,
            "revised": len(revised_rows),
            "rate": round(exact / n_first, 4) if n_first else None,
            "by_distance": {str(k): dist[k] for k in sorted(dist)},
            "first_review_stage_undetermined": len(undetermined),
        },
        "proposal_accepted": {
            "n": adjudicated,
            "accepted_unchanged": exact,
            "stage_revised": len(revised_rows),
            "withdrawn_on_review": len(withdrawn),
            "rate": round(exact / adjudicated, 4) if adjudicated else None,
        },
        "current_label": {
            "basis": "agent_proposed_stage against the row's stage today; moves with corrections "
                     "and evidence-dated transitions, so it is not the anchored first decision",
            "n": n_first,
            "matches": cur_match,
            "rate": round(cur_match / n_first, 4) if n_first else None,
        },
        "matrix": [
            {"proposed": p, "final": f, "n": n}
            for (p, f), n in sorted(
                matrix.items(), key=lambda kv: (STAGES.index(kv[0][0]), STAGES.index(kv[0][1]))
            )
        ],
        "matrix_note": ("first-review outcomes; a row revised and later corrected back is placed "
                        "at its first-review stage when a re-read entry records it, and in no cell "
                        "otherwise (stage_agreement.first_review_stage_undetermined counts those)"),
        "revisions": sorted(revised, key=lambda r: r["institution"]),
        "since_first_review": since,
        "rereads": reread_summary,
        "confidence": confidence_block(rows),
        "first_review_sessions": sessions_block(_first_review_records()),
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
          "(anchored — not a reliability estimate)")
    print(f"  proposals as-is   {b['accepted_unchanged']}/{b['n']} = {b['rate']:.1%} "
          f"({b['stage_revised']} revised, {b['withdrawn_on_review']} withdrawn)")
    c = doc["current_label"]
    print(f"  current label     {c['matches']}/{c['n']} = {c['rate']:.1%} "
          "(proposal vs today's stage — moves with corrections/transitions; not the anchored rate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
