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
- **Build the screener eval set** — a labeled set of GDELT articles (signal vs.
  noise, stage-relevant vs. not) to measure and tune the screener. High-value;
  open an issue to coordinate.

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
source of truth; `npm run build` copies it into `docs/data/` so GitHub Pages
serves current files. Never hand-edit `docs/data/` — edit root `data/`.

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
  "aum": "~$390B",                         // string, as publicly reported
  "stage": "piloting",                     // exploring | piloting | scaling | embedded  ← HUMAN judgment
  "as_of_reviewed": "2026-06-01",          // OPTIONAL — date a human last reviewed the stage (if present)
  "rationale": "Why this stage, citing public evidence. State confidence.",
  "footnote": "OPTIONAL — a caveat/clarification shown in the drill-down (e.g. why a sold AI product is excluded).",
  "use_cases": ["manager due diligence", "cash-flow forecasting"],
  "events": [                              // dated public adoption arc, oldest→newest in the UI
    {
      "date": "2024-07",                   // variable precision: "2024", "2025-07", "2026-03-24" — kept verbatim
      "event": "One-line description of the public event.",
      "source_url": "https://…"            // public source for THIS event
    }
  ],
  "latest_signal": "",                      // AUTO — engine only
  "latest_date": "",                        // AUTO — engine only (YYYY-MM-DD)
  "source_url": ""                          // AUTO — engine only (source of latest_signal)
}
```

### Hand-curated vs. auto fields

| Hand-curated (you edit) | Auto (engine writes — leave blank/untouched) |
|---|---|
| `name`, `aliases`, `type`, `aum`, `stage`, `as_of_reviewed`, `rationale`, `footnote`, `use_cases`, `events` | `latest_signal`, `latest_date`, `source_url` |

`monitor.py` writes **only** `latest_signal` / `latest_date` / `source_url`, and
only when a matched signal is strictly newer. It never touches a curated field
and never adds a row. Don't fill the auto fields by hand in a PR — leave them
empty for a new institution; the engine populates them.

**Every curated claim needs a public source.** `rationale` must be defensible
from the cited `events`; `aum` and `stage` must trace to public evidence. For
*how* to choose the stage (strict bars, decision discipline, scope exclusions),
follow [METHODOLOGY.md](METHODOLOGY.md).

---

## 4. The non-negotiable rule

**Humans set `stage`. Full stop.**

- A stage is assigned only by a person reading public evidence and exercising
  judgment.
- **Never submit an auto-generated classification** — no "I asked a model what
  stage this is." The model screens and notifies; it does not classify.
- The engine flags signals that *may* warrant re-classification and emails a
  human digest. That is the entire extent of automation's role in the stage. It
  flags and notifies; it never assigns.

A PR that moves a `stage` without a human-written, publicly-sourced rationale
will be asked to add one before review.

---

## 5. PR expectations

- **Conventional commits** — `feat:`, `fix:`, `docs:`, `chore:`, `test:` …
- **Tests pass** — `uv run pytest` is green (CI runs it on every PR).
- **One logical change per PR** — a data correction, a feature, or a doc fix —
  not a bundle. Small, reviewable, single-purpose.
- **Cite your sources** — link the public evidence in the PR description for any
  data or classification change.

Thanks for keeping this honest.
