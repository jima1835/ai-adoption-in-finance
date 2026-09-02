# Methodology

How institutions are classified on **AI Adoption in Finance**. This is the
project's credibility spine: every placement on the grid follows the rules
below, and every placement is defensible from public evidence alone.

If you want to contribute a classification or challenge one, this is the
standard you're held to. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
mechanics.

---

## 1. Scope: operational, internal AI adoption

The dashboard measures one thing: **how a firm uses AI inside its own
investment process and operations** — research, screening, due diligence, risk,
portfolio construction, trading, and back-office work that the firm runs for
itself.

It deliberately **excludes** three things that are frequently mislabeled as "AI
adoption." A firm can score high on any of them and still be early on the only
axis this dashboard tracks.

| Excluded | Why it's out of scope | Concrete example |
|---|---|---|
| **(a) AI products the firm sells to clients** | That's a product line, not internal operational adoption. | **BlackRock's Aladdin Copilot** is a GenAI layer BlackRock *sells* to Aladdin clients. It says nothing about whether BlackRock's own investors run their process on AI. Excluded. |
| **(b) AI as an investment thesis or portfolio holding** | Owning AI exposure is a *view on the market*, not use of AI in operations. | A fund that holds Nvidia and Microsoft, or runs an "AI megatrend" thematic strategy, is *investing in* AI — not *operating with* it. Excluded. |
| **(c) AI the firm helps its portfolio companies adopt** | That's value-creation at the asset level, not the firm's own operating model. | A PE firm running an "AI value-creation playbook" to push tools into its portfolio companies is changing *their* operations, not its own deal team's. Excluded. |

When a public signal is about (a), (b), or (c), it does **not** move the firm's
stage. It may still appear in the signal feed as context, but the classification
rests only on operational, internal evidence.

---

## 2. Public sources only

Every classification rests on **public evidence**: reported news, official
disclosures, regulatory filings, board and committee materials, earnings calls,
conference remarks, and the institution's own published position papers.

Two rules follow:

- **No non-public knowledge.** Private conversations, rumor, vendor backchannel,
  or "I know someone there" never inform a stage. If it can't be cited, it can't
  classify.
- **Absence of evidence caps the stage; it never infers one.** If there is no
  public evidence that a firm has reached a given stage, it is **not** placed
  there — even if it "probably" has. The lack of a public signal is noted as a
  limit of the record, not filled in by assumption. A firm may well be further
  along privately; this dashboard only reports what the public record can
  defend.

Where an institution's own claims can't be independently verified (e.g.
"benefits already in the billions"), they are labeled as **company claims** in
the rationale, not treated as established fact.

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

### `embedded` — currently UNREACHED, by design
AI is **structurally constitutive of how the firm operates**, not just a tool
within it:

- **autonomous decisions** without a human in the loop on each one,
- **org structure actually redesigned** around AI (not AI bolted onto the
  existing org), and
- **AI as the default mode**, with humans as the exception. *AI **is** the
  workflow.*

**No institution is classified `embedded`, and the column is intentionally
empty.** This is an evidence-based editorial finding, not missing data: the most
AI-advanced institutions tracked (NBIM, CPP Investments, BlackRock, GIC) each
*independently and publicly* state they keep humans in control of decisions and
have **not** redesigned their org structure around AI. The day that changes —
with public evidence — the column fills.

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

This section describes the construction protocol, in full, because it is as much
the contribution as the data is. **An AI research agent drafts every row and
proposes a stage; a human verifies every row before it publishes.**

### 5.1 The agent drafts

A research agent works one institution at a time. It searches the public record,
**fetches every URL it intends to cite** — a search-result snippet is not a
source — writes the rationale and the dated timeline, and proposes an adoption
stage against the bar in §3. Its standing constraints:

- public sources only, per §2;
- no encyclopedias or aggregators as evidence;
- evidence dated 2023 or later;
- the verbatim wording that carries the call is quoted, in its original
  language;
- when the record does not support a stage, it says so rather than reaching.

### 5.2 A human verifies, row by row

Every drafted row goes through a local review tool where a person reads it
against its cited sources and does one of three things: **accepts** the proposed
stage, **revises** it, or **removes** the row entirely. Nothing publishes without
that pass.

The reviewer works from the cited evidence rather than re-researching the firm.
That is a deliberate division of labour — the agent's job is to find and
assemble the record; the reviewer's job is to check that the record says what
the draft claims and that the stage follows from it.

### 5.3 What an agent may never write

These fields are reviewer-only, enforced in the review tool rather than left to
convention:

| Field | Why |
|---|---|
| `stage` (after first review) | A reviewed stage is a published measurement. Rewriting it destroys the before/after pair. |
| `as_of_reviewed` | The claim that a human checked this row. |
| `label_provenance`, `agent_proposed_stage` | The audit trail in §6. Self-reported provenance would be worthless. |
| the not-classified appendix (§7) | A negative record is a finding, and findings are human-gated. |
| the stage-transition log | A dated transition is the panel's spine; see §8. |

### 5.4 Freshness monitoring is separate, and is a notifier

A monitoring pass screens public news and refreshes each institution's *latest
signal* line. When a signal looks stage-relevant it **emails a human**. It never
edits a stage. The split is structural: automation writes only
`latest_signal` / `latest_date` / `source_url`.

---

## 6. The disagreement record

Because §5 logs what the reviewer did with each proposal, the rate at which the
human and the agent disagree is a **published measurement**, not an assurance.
It lives in [`data/agreement.json`](data/agreement.json), is rebuilt from
`data/institutions.json` and `data/not_classified.json` — both in this repo — and
is rendered on the dashboard's methodology page.

Two figures are reported, because one alone would flatter the pipeline:

- **Stage agreement** — of the reviewed rows that carried an agent proposal, how
  often did the proposed stage stand unchanged?
- **Proposals accepted as-is** — of every proposal the reviewer adjudicated, how
  often was it taken unchanged? This denominator includes rows that were
  **withdrawn on review**. A withdrawal is a disagreement, and excluding it
  inflates the rate.

Each row also carries its own provenance: whether the label was the agent's
proposal accepted, the agent's proposal revised, or written by the human
outright (as the earliest rows were, before the pipeline existed).

### The limitation, stated plainly

**This is anchored agreement, and it is an upper bound — not a reliability
coefficient.**

The reviewer saw the agent's proposed stage, and the agent-written rationale
states the stage reasoning, *before* deciding. Agreement measured under those
conditions is systematically higher than agreement between independent coders.
On top of that there is one reviewer, and he is also the author of the
classification rules in §3 and §4.

So: **no inter-rater reliability coefficient is computed from this file, and
none should be quoted from it.** Establishing reliability requires a blind
re-code — the same evidence stripped of the proposed stage and its reasoning,
coded cold, against an independent coder. That is a separate exercise, and its
result will be reported separately. The gap between the anchored figure here and
a blind figure is itself the quantity of interest.

---

## 7. Assessed, not classified

Institutions researched against this methodology whose public record did not
support a stage are **published**, with a reason, in
[`data/not_classified.json`](data/not_classified.json) and in the appendix on the
methodology page. Two outcomes:

- **No qualifying evidence** — the public record, after searching, contained
  nothing in scope that met the sourcing rules in §2.
- **Withdrawn on review** — the institution was listed, and human review then
  found the evidence insufficient to carry a stage.

Absence from the dashboard is a finding, not an omission. A tracker that
publishes only its hits cannot be read as a rate of anything.

---

## 8. Coverage, and what these numbers are not

**This corpus is not a sample of any defined population.** Institutions enter it
through research passes, not through a sampling frame — there is no register of
"all institutional investors" to draw from, and no weighting scheme could repair
its absence. Every figure on this site describes *this corpus*. None of them is
an industry rate, and none should be reported as one.

Coverage is also uneven by design and by circumstance: endowments are thinly
represented because their public disclosure is thin, which is itself a
disclosure finding rather than a gap to be filled by inference.

Stage **transitions** are recorded prospectively — when a reviewed row moves,
the change is logged against the date of the *triggering evidence*, never the
date of the review. A panel dated by review sessions would measure the
reviewer's calendar rather than the sector.

**The panel's baseline is the v1.0 release.** Every stage in the tagged,
DOI-archived corpus is position zero; every record in
[`data/transitions.jsonl`](data/transitions.jsonl) is a move away from it. The
file is therefore empty at v1.0 and fills forward, one approved change at a time.
It is **not** backfilled, and the series should not be reconstructed from the
event timelines in this corpus: those rows were researched to establish each
firm's *current* stage, so their early-period evidence is thin and collected
non-systematically, and any retrospective crossing date would be assigned with
knowledge of the outcome. A backfilled panel would look like data and behave like
hindsight.

---

## 9. Language

Evidence in Chinese, Japanese and Korean is quoted **verbatim in the original**,
because the exact wording is what carries the classification — the difference
between 完成部署 (deployment completed) and 将应用 (will be applied) is the
difference between two stages. An English rendering is displayed alongside it at
render time, from a separate translation map; the stored evidence is never
rewritten, and the original is always the record.

---

## 10. How this differs from the alternatives

A staged reading of AI adoption is not a new idea, and this project does not
claim to have originated one. Where it sits:

- **Commercial AI indices** — chiefly the [Evident AI
  Index](https://evidentinsights.com/), which ranks banks, insurers and payments
  firms on 60+ indicators and has announced an asset-management edition — score
  and rank large public *companies*. This is not a ranking and assigns no score.
  It places each institution on a stage, it covers **asset owners** (pensions,
  sovereign-wealth funds, endowments) that commercial benchmarks do not, and it
  publishes the assessments that failed.
- **Staged self-assessment questionnaires**, including the one shipped with the
  US financial-services AI risk management framework published in February 2026,
  ask a firm to place *itself*. This dashboard adapts the staged form for
  **external observation**: no institution is asked anything, and no institution
  can move its own row. *(The stage vocabulary of that questionnaire has not yet
  been compared line by line against §3; where they overlap, this project is the
  later work and says so.)*
- **Industry surveys** (central-bank and consultant surveys of AI use) report
  self-declared adoption in aggregate and anonymized. Every row here is named,
  dated and sourced — which makes it checkable, and makes it wrong in public
  when it is wrong.

---

*Questions about a specific classification? Open an issue with the public
sources you think change the call.*
