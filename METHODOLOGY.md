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
- **State confidence.** The rationale should make the strength of the evidence
  legible — strong and well-sourced, or thin and provisional. A defensible
  low-confidence call is fine; an unstated one is not.
- **Re-classify only on new public evidence.** The automated monitor can flag a
  signal that *may* warrant re-classification and email a human, but a stage
  moves only when a person reviews the public record and decides. The engine
  never assigns a stage. (See the "humans hold the stage" principle in the
  [README](README.md).)

---

*Questions about a specific classification? Open an issue with the public
sources you think change the call.*
