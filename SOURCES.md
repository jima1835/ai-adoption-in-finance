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
- **The floor is two independent T2-or-better sources.** A rationale may not rest
  on T3 alone. A T3 source may corroborate, and is admitted only on a reviewer's
  explicit recorded decision, never automatically.
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

## 3. Additional rules for role events

The roles module ([METHODOLOGY §11](METHODOLOGY.md)) inherits everything above
and adds one restriction, because its records can name a living person:

> **A named individual is recorded only from a firm press release, a firm
> leadership page, a regulatory filing, or an outlet on the accepted source
> list.** No LinkedIn-derived data enters this pipeline at any point — not as
> evidence, not as corroboration, not as a search surface. `person: null` is a
> valid and complete record; the event is the unit of observation, not the
> person.

No compensation data is collected, and no job-posting corpus is built.

Corrections and removal requests: see
[README, "Public comments and submissions"](README.md#public-comments-and-submissions).

---

*This file is referenced by `source_tier` in
[`schemas/role_event.schema.json`](schemas/role_event.schema.json); §1 defines
the values that field may carry.*
