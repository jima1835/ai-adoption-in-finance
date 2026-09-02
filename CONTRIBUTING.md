# Contributing

Thanks for helping make **AI Adoption in Finance** more accurate and more
useful. This is a public, sourced classification of how institutional investors
adopt AI — its value is only as good as the evidence and the discipline behind
it. Contributions are welcome on exactly those terms.

Please read [METHODOLOGY.md](METHODOLOGY.md) before proposing or changing a
classification — it defines the scope, the sourcing rule, the four stages, and
the decision discipline you'll be held to.

---

## 1. How to contribute

- **Add a new institution** — **open an issue first** (proposed name, type, the
  stage you think fits, and 2–3 public sources). We align on scope and stage
  before a PR, so review stays about evidence, not mechanics.
- **Correct existing data** — wrong AUM, a stale `latest_signal`, a broken
  `source_url`, a mis-dated event, a stage you can show is wrong: **open a PR**
  with the public source that backs the fix.
- **Improve the engine or front end** — `monitor.py`, `alerts.py`, the React
  site in `src/`, build config: PRs welcome. For anything beyond a small fix,
  open an issue first so we don't both build the same thing.
- **Challenge a classification** — the highest-value contribution. Open an
  issue with the public sources you think change the call. Rows are published
  with their rationale, their confidence flag and every source, precisely so
  they can be argued with.
- **Add to the negative record** — an institution you researched against
  METHODOLOGY whose public record does not support a stage is a finding, not a
  gap. Open an issue; entries in `data/not_classified.json` are filed by a
  human through the local review tool and never by a PR.

---

## 2. Dev setup

The engine is a [uv](https://docs.astral.sh/uv/) project; the site is Vite +
React.

```bash
# --- engine (Python) ---
uv sync                          # install deps into a managed venv
cp .env.example .env             # then paste your ANTHROPIC_API_KEY
                                 # (RESEND_* vars are optional — only needed to send alert emails)

# run a collection pass
uv run --env-file .env python monitor.py

# run the tests
uv run pytest

# --- site (React) ---
npm install
npm run dev                      # local dev server, serves root data/ live
npm run build                    # builds to docs/ and copies data/ → docs/data/
```

The site reads `data/*.json` at runtime. `data/` at the repo root is the single
source of truth; `npm run build` copies every `data/*.json` into `docs/data/` so
GitHub Pages serves current files. Never hand-edit `docs/data/` — edit root
`data/` and rebuild.

Evidence in Chinese, Japanese and Korean is stored verbatim and rendered in
English at display time from `data/translations.json`, which maps each exact CJK
run to an English string. If you edit a rationale containing CJK, the old
translation key is orphaned and the text falls back to the raw original with no
error — run `python3 local/check_translations.py --check` if you have the local
tooling, or say so in the PR so the maintainer can.

---

## 3. Adding or updating an institution

Institutions live in [`data/institutions.json`](data/institutions.json) — a JSON
array, one object per institution. Match the existing formatting (2-space
indent, `ensure_ascii=False` — keep em-dashes, accents, and currency symbols
literal). Row schema:

```jsonc
{
  "name": "CalSTRS",                       // display name
  "aliases": ["CalSTRS", "California State Teachers' Retirement System"],
                                           // every name the engine should match on
  "type": "pension",                       // asset-manager | pension | sovereign-wealth | hedge-fund | endowment
  "region": "US",                          // US | Canada | Europe | Middle East | Asia | Other — HQ of the managing entity
  "aum": "~$390B",                         // string, in the DISCLOSED currency, as publicly reported
  "stage": "piloting",                     // exploring | piloting | scaling | embedded  ← HUMAN judgment
  "confidence": "med",                     // high | med | low — strength of the public evidence
  "rationale": "Why this stage, citing public evidence, ending in an explicit \"stops short of <next stage>\" clause.",
  "footnote": "OPTIONAL — a caveat/clarification shown in the drill-down (e.g. why a sold AI product is excluded).",
  "use_cases": ["manager due diligence", "cash-flow forecasting"],
  "events": [                              // dated public adoption arc, oldest→newest in the UI
    {
      "date": "2024-07",                   // variable precision: "2024", "2025-07", "2026-03-24" — kept verbatim
      "event": "One-line description of the public event.",
      "source_url": "https://…"            // public source for THIS event
    }
  ],
  "latest_signal": "",                      // AUTO — monitor.py only
  "latest_date": "",                        // AUTO — monitor.py only (YYYY-MM-DD)
  "source_url": ""                          // AUTO — monitor.py only (source of latest_signal)
  // NOT SHOWN, and never written by a contributor: as_of_reviewed,
  // label_provenance, agent_proposed_stage. See "Reviewer-only fields" below.
}
```

### Three kinds of field

| Curated — you may edit | Auto — `monitor.py` only | Reviewer-only — never in a PR |
|---|---|---|
| `name`, `aliases`, `type`, `region`, `aum`, `stage`, `confidence`, `rationale`, `footnote`, `use_cases`, `events` | `latest_signal`, `latest_date`, `source_url` | `as_of_reviewed`, `label_provenance`, `agent_proposed_stage` |

`monitor.py` writes **only** `latest_signal` / `latest_date` / `source_url`, and
only when a matched signal is strictly newer. It never touches a curated field
and never adds a row. Leave those three empty on a new institution.

The **reviewer-only** fields are the audit trail behind
[`data/agreement.json`](data/agreement.json) — they record whether the published
stage was proposed by the research agent and accepted, revised, or written by a
human outright. They are written once, by the maintainer's local review tool, on
a row's first review. A PR that sets them is a PR that marks its own homework,
so they are rejected on sight. The same applies to
[`data/not_classified.json`](data/not_classified.json) and
[`data/transitions.jsonl`](data/transitions.jsonl).

**Every curated claim needs a public source.** `rationale` must be defensible
from the cited `events`; `aum` and `stage` must trace to public evidence. For
*how* to choose the stage (strict bars, decision discipline, scope exclusions),
follow [METHODOLOGY.md](METHODOLOGY.md).

---

## 4. The non-negotiable rule

**No stage is published without a human verifying it against its sources.**

Be clear about how this project actually works, because it is unusual and it is
the point. **An AI research agent drafts every row in this corpus and proposes a
stage.** A human then opens that draft against its cited sources and accepts,
revises, or removes it, and the outcome of that decision is recorded on the row
and published in [`data/agreement.json`](data/agreement.json). The protocol is
described in full in [README](README.md#how-a-row-is-built) and
[METHODOLOGY §5](METHODOLOGY.md).

What that does **not** license is an unverified model output arriving by PR:

- **Don't submit a stage you have not checked against the sources yourself** —
  "I asked a model what stage this is" is not a contribution, because the thing
  that makes an agent-drafted row publishable is the verification step, and a
  drive-by PR has not been through one.
- Use whatever tools you like to *find* evidence. Every URL you cite must be one
  you actually opened, and the claim must appear in the page you read.
- `monitor.py` flags signals that *may* warrant re-classification and emails a
  human. It never assigns a stage.

A PR that moves a `stage` without a publicly-sourced rationale — including the
explicit "stops short of…" clause that says what caps it — will be asked to add
one before review.

---

## 5. PR expectations

- **Conventional commits** — `feat:`, `fix:`, `docs:`, `chore:`, `test:` …
- **Tests pass** — `uv run pytest` is green (CI runs it on every PR).
- **One logical change per PR** — a data correction, a feature, or a doc fix —
  not a bundle. Small, reviewable, single-purpose.
- **Cite your sources** — link the public evidence in the PR description for any
  data or classification change.

Thanks for keeping this honest.
