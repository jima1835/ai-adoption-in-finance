# Methodology

How institutions are classified on **AI Adoption in Finance**. Every placement
follows the rules below and is defensible from public evidence alone; to
contribute or challenge one, this is the standard ([CONTRIBUTING.md](CONTRIBUTING.md)).

## TL;DR

Institutional investors are placed on four stages of **internal** AI adoption —
`exploring`, `piloting`, `scaling`, `embedded` — from **public evidence only**.
AI sold to clients, AI as an investment thesis and AI pushed into portfolio
companies do not count. A row needs two dated events from first-party or
staff-written sources, the decisive wording quoted verbatim. Between two stages
the lower wins; absent evidence caps a stage, never infers one. An AI agent
drafts each row and proposes a stage; a human verifies, revises or removes it,
and that decision is published as anchored agreement — not a reliability
coefficient. Unplaceable institutions are published with the reason. Nothing
here is an industry rate.

---

## 1. Scope: operational, internal AI adoption

The dashboard measures one thing: **how a firm uses AI inside its own investment
process and operations** — research, due diligence, risk, portfolio construction,
trading, back office. Three things often called "AI adoption" are **excluded**,
and a firm can score high on all of them while early on this axis:

- **(a) AI products sold to clients.** BlackRock's Aladdin Copilot is a product
  line, not internal adoption.
- **(b) AI as an investment thesis or holding.** Owning Nvidia or running an "AI
  megatrend" strategy is a view on the market.
- **(c) AI the firm pushes into its portfolio companies.** A PE value-creation
  playbook changes *their* operations, not its own deal team's.

A signal about (a), (b) or (c) never moves a stage; it may appear in the feed as
context.

---

## 2. Public sources only

Every classification rests on **public evidence**: reported news, official
disclosures, regulatory filings, board and committee materials, earnings calls,
conference remarks and the institution's own published positions. **No
non-public knowledge**: if it cannot be cited, it cannot classify. **Absence of
evidence caps the stage; it never infers one**: a firm is placed no higher than
the record defends, however far along it "probably" is, and the gap is stated as
a limit of the record.

Unverifiable institutional claims are labelled **company claims**, not fact.
Source tiers (T1 first-party, T2 staff-written, T3 everything else) and the floor
beneath which a rationale may not rest are in [SOURCES.md](SOURCES.md); tiers are
criteria, not a roster of outlets, and SOURCES.md loosens nothing here.

---

## 3. The four stages

Stages are a **strict bar**, applied in order. Each higher stage requires
*everything* the lower one does, plus more. The bar is about **production
reality and decision authority**, not announcements.

### `exploring`
Stated intent, hiring, task forces, or "evaluating" AI — but **no shipped
internal use case yet**. Board education sessions, an AI strategy memo, a new
"Head of AI" req, or a vendor proof-of-concept that hasn't shipped all live
here.

### `piloting`
**Named pilots or limited deployments** in specific teams, plus
**policy/governance build-out** (an AI use policy, a governance committee, a
scoped use-case pipeline) — but **not yet firm-wide production**. Real usage
exists, but it's contained to pockets and still provisional.

### `scaling`
**Multiple AI use cases in production across the firm, used daily, named as a
strategic priority** — with deployment evidence, not just intent. The defining
constraint: **AI augments human decisions.** People still frame the question,
set the guardrails, and make or verify the final call. *AI is in the workflow.*
A firm with firm-wide tools that nonetheless keeps a human on every investment
decision is `scaling`, not `embedded`.

A single production use case that makes live investment decisions with material capital counts as scaling.

### `embedded` — no institution currently meets this bar
AI is **structurally constitutive of how the firm operates**, not just a tool
within it:

- **autonomous decisions** without a human in the loop on each one,
- **org structure actually redesigned** around AI (not AI bolted onto the
  existing org), and
- **AI as the default mode**, with humans as the exception. *AI **is** the
  workflow.*

**The `embedded` column is empty as an observation, not as an editorial
position.** The bar above was applied to every institution in the corpus and
none met it — that is a measured result, and it is reported as one. It is also
not missing data: the most AI-advanced institutions tracked (NBIM, CPP
Investments, BlackRock, GIC) each *independently and publicly* state they keep
humans in control of decisions and have **not** redesigned their org structure
around AI, so the record actively contradicts an `embedded` placement rather
than merely failing to support one. The day that changes — with public
evidence — the column fills, and nothing about this project has to be revised
for it to.

---

## 4. Decision discipline

The rules that keep classifications honest and consistent:

- **Plans are not stages.** Future-tense language — "we will," "we plan to,"
  "by next year," "moving toward" — is evidence of *intent*, which lives one
  stage lower. A roadmap to firm-wide AI is `piloting`, not `scaling`. A stated
  ambition for autonomous agents is not `embedded`.
- **When between two stages, pick the lower.** If the public evidence genuinely
  supports either of two adjacent stages, classify at the lower one and say why
  in the rationale. The bar is "clearly cleared," not "arguably reached."
- **State confidence.** Every row carries a `high` / `med` / `low` flag, and the
  rationale should make the strength of the evidence legible. A defensible
  low-confidence call is fine; an unstated one is not.
- **Capability claims are not usage claims.** "Can process 10,000 reports a
  night" describes a design capacity, not a measured rate. Vendor-voiced claims
  about a client firm are weaker than the firm's own, and are labeled as such.
- **Re-classify only on new public evidence.** A stage moves when a person
  reviews the public record and decides — never because a model, a monitor, or a
  research agent proposed it.

---

## 5. How a row is built

**An AI research agent drafts every row and proposes a stage; a human verifies
every row before it publishes.**

### 5.1 The agent drafts

One institution at a time, it searches the public record, **fetches every URL it
cites** (a snippet is not a source), writes the rationale and the dated timeline,
and proposes a stage against §3 — under §2, with no encyclopedias or aggregators,
evidence dated 2023 or later, the decisive wording quoted verbatim in its
original language, and an explicit "the record does not support a stage" where
that is the finding.

### 5.2 A human verifies, row by row

In a local review tool a person reads each draft against its sources and
**accepts** the stage, **revises** it or **removes** the row; nothing publishes
without that pass. Where a row rests only on the institution's own voice, that
pass is the corroboration: the reviewer confirms each document is a governance or
operational disclosure — annual report, board material, filing — not a pitch or
an advertisement, and that the quoted sentence is there. Independent coverage
lifts confidence; its absence caps it at `med`, stated in the rationale
([SOURCES.md](SOURCES.md) §1).

### 5.3 What an agent may never write

Reviewer-only fields, enforced in the tool: `stage` after first review (a
published measurement), `as_of_reviewed` (the claim that a human checked the
row), `label_provenance` and `agent_proposed_stage` (the audit trail of §6), the
not-classified appendix (§7) and the stage-transition log (§8).

### 5.4 Freshness monitoring is separate, and is a notifier

A monitoring pass screens public news, refreshes each row's *latest signal* and
**emails a human** when something looks stage-relevant. It never edits a stage;
automation writes only `latest_signal`, `latest_date` and `source_url`.

---

## 6. The disagreement record

Because §5 logs what the reviewer did with each proposal, the human–agent
disagreement rate is a **published measurement**:
[`data/agreement.json`](data/agreement.json), rebuilt from the two public data
files (the site links it and renders no figure). Two figures, because one alone would
flatter the pipeline: **stage agreement** — how often the proposed stage stood at
the first human review; and **proposals accepted as-is** — how often a proposal
was taken unchanged, counting rows **withdrawn on review**, since a withdrawal is
a disagreement. Provenance (accepted, revised, or human-written) is set once, at
first review; later moves on new evidence or corrections on re-reading do not
change the rate and are listed separately, beside a proposal-versus-current-stage
figure, so the two reconcile.

### Corpus lifecycle and the blind-review freeze

The reviewed corpus passed its 100-row target in September 2026 and stands at
111 rows. The freeze for the blind re-code is **declared by the maintainer**
(`tools/review.py --freeze`), which records the digests that
`tests/test_frozen_corpus.py` then holds; no row count triggers it. Under the
freeze, research continues locally and public changes wait for the re-code.

### The limitation, stated plainly

**This is anchored, non-independent agreement, not an inter-rater reliability
estimate.** The reviewer saw the proposed stage and its written reasoning
*before* deciding, and the one reviewer also wrote §3 and §4. No reliability
coefficient is computed from this record and none should be quoted from it;
that needs a blind re-code — the same evidence stripped of stage and reasoning,
coded cold by an independent coder — reported separately. The gap between the
anchored figure and the blind one is itself the quantity of interest.

---

## 7. Assessed, not classified

Institutions researched against this methodology whose public record did not
support a stage are **published, with a reason**, in
[`data/not_classified.json`](data/not_classified.json) and on the methodology
page — **no qualifying evidence** (nothing in scope met §2) or **withdrawn on
review** (listed, then removed when human review found the evidence
insufficient). Absence from the dashboard is a finding, not an omission; a
tracker that publishes only its hits cannot be read as a rate of anything.

---

## 8. Coverage, and what these numbers are not

**This corpus is not a sample of any defined population.** Institutions enter
through research passes, not a sampling frame; every figure describes *this
corpus*, never an industry rate. Coverage is uneven — endowments are thin because
their disclosure is thin, which is itself a finding.

Stage **transitions** are recorded prospectively in
[`data/transitions.jsonl`](data/transitions.jsonl), dated by the *triggering
evidence*, never the review. The baseline is the v1.0 release — position zero for
every stage — and the file fills forward one approved change at a time. It is
not backfilled from the event timelines, which were researched to establish each
firm's *current* stage; a retrospective crossing date would be hindsight.

---

## 9. Language

Evidence in Chinese, Japanese and Korean is quoted **verbatim in the original**,
because the exact wording carries the classification — 完成部署 (deployment
completed) and 将应用 (will be applied) are two different stages. An English
rendering is shown alongside from a separate translation map; the stored
evidence is never rewritten, and the original is always the record.

---

## 10. How this differs from the alternatives

A staged reading of AI adoption is not new. **Commercial AI indices** — chiefly
the [Evident AI Index](https://evidentinsights.com/) — rank large public
*companies*; this is not a ranking, it covers **asset owners** that benchmarks do
not, and it publishes the assessments that failed. **Staged self-assessment
questionnaires**, including the one in the US financial-services AI
risk-management framework of February 2026, ask a firm to place *itself*; here no
institution is asked anything and none can move its own row. **Industry surveys**
report self-declared adoption in aggregate; every row here is named, dated and
sourced — checkable, and wrong in public when it is wrong.

---

*The AI-leadership roles record described in §11 of v1.1.0 is withdrawn from
this release and will return in a later one.*

*Questions about a specific classification? Open an issue with the public
sources you think change the call.*
