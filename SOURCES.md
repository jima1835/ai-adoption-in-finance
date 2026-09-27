# Sources and tiers

> This page prints the tier structure and the sourcing rules that
> [METHODOLOGY §2](METHODOLOGY.md) and the not-classified appendix already refer
> to. §2 remains the classification bar; nothing here loosens it. The corpus
> published to date was classified under §2, before this page existed — the
> tiers below describe that practice rather than replacing it.

METHODOLOGY §2 says classifications rest only on public evidence, and the
not-classified appendix refers to an **"accepted source list"** and a **tier**
that this repository had never defined. This file defines them.

Two rules govern what is written below:

1. **Only what the public record of this repository already attests.** Each rule
   in §2 cites the tracked file that carries it — `METHODOLOGY.md`, `README.md`,
   or a published reason in `data/not_classified.json`. No rule here was
   reconstructed from memory.
2. **Tiers are defined by criteria, not by a roster.** No list of named outlets
   is published, and none is maintained: a roster goes stale, and invites
   "is outlet X on the list?" in place of the judgment §2 actually requires.
   Where the appendix says "accepted source list", read the T1/T2 criteria below.

---

## 1. The tier structure

| Tier | What counts |
|---|---|
| **T1** | The institution's own voice — its domain, newsroom, annual report, board and committee materials, regulatory filings, and earnings notes. |
| **T2** | Staff-written outlets with editorial accountability, and credible news media outlets. |
| **T3** | Everything else: trade sites, newsletters, self-published posts (Substack and similar), and aggregators without source reference. |

Three questions about how the tiers apply were open when this file was first
drafted. They are settled:

- **A vendor or platform provider's own announcement about a named client is T1
  for that event.** Tier states proximity to the source, not sufficiency: the
  vendor is a first-hand party to a deal it announces. It does not follow that
  such an announcement can carry a classification alone — §2's rule stands that
  a vendor-published event with no independent second source does not
  (*Walleye Capital*), as does the two-event minimum.
- **The floor is two dated events, each carried by a T2-or-better source, and a
  rationale may not rest on T3 alone.** A T3 source may corroborate, and is
  admitted only on a reviewer's explicit recorded decision, never automatically.
  **Independent corroboration is sought, not required.** Where every load-bearing
  source is the institution's own voice, the row is still publishable — several
  are — on two conditions the reviewer checks document by document before
  approval: the document is a governance or operational disclosure (an annual
  report, board or committee material, a regulatory filing, a newsroom item about
  the firm's own operations), not a pitch to investors or clients, a sponsored
  piece or an advertisement (*Baillie Gifford*, §2); and the reviewer has opened
  it and confirmed the sentence that carries the call. The human pass is the
  corroboration. The limitation is stated in the rationale and confidence is
  capped at `med`. Two pages on a firm's own domain are one voice, however many
  URLs they span. A row resting on a single voice at `high` confidence would
  overstate the record, and is refused. Two independent publishers are what lift
  a row to `high`; they are not a condition of publishing one. A publisher is
  independent when it reports a fact it established itself. Several staff-written
  outlets that each carry the firm's own account, however independent of one
  another, are that one voice and hold the row at `med`.
- **Confidence is a judgment, not a formula.** `high` / `med` / `low` is the
  reviewer's reading of the evidence against the four stage criteria in
  METHODOLOGY §3, deliberately not derived from a tier count — a count would
  imply a precision the evidence does not carry.

## 2. Rules already public

Each of these is attested in a tracked file today. They are not new.

| Rule | Attested in |
|---|---|
| Evidence must be **public**: reported news, official disclosures, regulatory filings, board and committee materials, earnings calls, conference remarks, the institution's own published positions. | METHODOLOGY §2; README, "A note on sourcing" |
| **No non-public knowledge** — private conversations, rumour, vendor backchannel. If it can't be cited, it can't classify. | METHODOLOGY §2 |
| **No encyclopedias or aggregators** as evidence. | METHODOLOGY §5.1 |
| Every cited URL must be one the researcher **actually opened**; a search-result snippet is not a source. | METHODOLOGY §5.1; CONTRIBUTING §4 |
| Evidence must be dated **2023-01-01 or later**. Earlier ML history may appear as context in a rationale, never as an event. | METHODOLOGY §5.1; `data/not_classified.json` — *Wellington Management*, *Marshall Wace* ("outside this dashboard's evidence window") |
| The wording that carries the call is **quoted verbatim, in its original language**. | METHODOLOGY §5.1, §9 |
| **Two-event minimum**: one qualifying dated event is not enough to classify. | `data/not_classified.json` — *D. E. Shaw & Co.*, *Walleye Capital* ("below the two-event minimum") |
| A **sponsored or firm-authored article** is excluded as a *sole* source. | `data/not_classified.json` — *Baillie Gifford* |
| A **vendor-published** event with no independent second source does not carry a classification. | `data/not_classified.json` — *Walleye Capital* |
| Unverifiable institutional claims are labelled **company claims**, not treated as fact. | METHODOLOGY §2 |
| Absence of evidence **caps** a stage; it never infers one. | METHODOLOGY §2; README |

---

*The additional sourcing rules for the AI-leadership roles record (§3 of v1.1.0) are withdrawn with that module and will return with it.*
