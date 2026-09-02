# AI Adoption in Finance — Architecture & Context

## What this is
A public dashboard classifying where major institutional investors sit on AI
adoption RIGHT NOW, based STRICTLY on public sources (news, official disclosures,
board materials). A daily automated job updates it. Hosted entirely on GitHub
(Actions = engine, Pages = host). One public repo: `ai-adoption-in-finance`.

## Product hierarchy (UI reflects this)
1. PRIMARY — Classification grid: institutions × 4 adoption stages, badges,
   filters by type, region, confidence, and AUM band. The homepage. The shareable artifact.
2. SECONDARY — "Recent Signals" feed: latest screened news, dated + sourced.
   Proves the dashboard is alive and backs the classifications.
3. DRILL-DOWN (v1.5) — Click an institution → its timeline of dated signals
   (feed items filtered to that institution). CalSTRS is the showcase.

## Data model — the pipeline files, plus a derived presentation layer

`data/institutions.json` — the STATE (the dashboard). Array, one row per institution:
```json
{
  "name": "CalSTRS",
  "aliases": ["CalSTRS", "California State Teachers' Retirement System"],
  "type": "pension",
  "region": "US",
  "aum": "~$390B",
  "stage": "piloting",
  "confidence": "high",
  "as_of_reviewed": "2026-08-25",
  "rationale": "hand-written, cites public evidence for the stage",
  "footnote": "optional — scope calls: what was seen but NOT counted toward the stage, and why",
  "use_cases": ["portfolio & research intelligence", "manager due diligence"],
  "events": [
    { "date": "2026-03-24", "event": "one-line description", "source_url": "..." }
  ],
  "latest_signal": "",
  "latest_date": "",
  "source_url": ""
}
```
- `type` ∈ `asset-manager | pension | sovereign-wealth | hedge-fund | endowment`
- `region` ∈ `US | Canada | Europe | Middle East | Asia | Other` — HQ region of
  the managing entity, placed immediately after `type`.
- `stage` ∈ `exploring | piloting | scaling | embedded`
- HAND-CURATED fields (never auto-touched): `name`, `aliases`, `type`, `region`,
  `aum`, `stage`, `confidence`, `as_of_reviewed`, `rationale`, `footnote`,
  `use_cases`, `events`.
- `confidence` ∈ `high | med | low` — strength of the public evidence for the stage.
- `as_of_reviewed` — date a human last confirmed the stage. Set on approval,
  never by an agent.
- `footnote` — optional. Present whenever a scope call was made (client-facing
  AI product, AI-as-thesis, portfolio-company program seen but not counted).
- AUTO fields (`monitor.py` only): `latest_signal`, `latest_date`, `source_url`.
- `events` — the institution's dated public AI-adoption arc (front end sorts it).
  Event `date` is a STRING of varying precision (`"2023"`, `"2026-03"`,
  `"2026-03-24"`) — preserved verbatim, never padded or normalized. This is
  separate from the YYYY-MM-DD `latest_date` the engine compares against.
- Events start 2023-01-01 (GenAI era). Pre-2023 ML history may appear in
  `rationale` as context; it is never an `events` entry.
- Each event has exactly one `source_url` (singular).
- Type mapping: PE / alternatives managers → `asset-manager`; foundations →
  `endowment`.

`data/feed.json` — the STREAM (recent signals + drill-down source). Array, newest
first, capped at 200. Each item carries the institution tag so the front end can
filter the per-institution drill-down:
```json
{
  "source": "...",
  "institution": "CalSTRS",
  "institution_normalized": "CalSTRS",
  "category": "asset-mgmt|banking|fintech|insurance|payments|other",
  "headline": "...",
  "url": "...",
  "date": "YYYY-MM-DD",
  "why_it_matters": "..."
}
```

`data/seen_urls.json` — dedup ledger. Array of URLs already screened. **Persisted
state**: must be committed by CI alongside the other two, or dedup resets and the
feed accumulates duplicates.

`data/not_classified.json` — the APPENDIX ("assessed, not classified"): institutions
researched against the methodology whose public record didn't support a stage.
Array of `{name, type, region, outcome, reason, as_of}`; `outcome` ∈
`no-qualifying-evidence | withdrawn-on-review` (scope and sourcing-bar failures
both read as no-qualifying-evidence — the `reason` carries the nuance).
Rendered as a strip on the dashboard below the stage grid, plus a full table on
the Methodology page (both hidden while empty). **HUMAN-GATED**: entries are
filed ONLY by a human through the local review tool; agents and `monitor.py`
never write this file. `reason` text is public — it must stand alone.

`data/agreement.json` — the DISAGREEMENT RECORD, public and derived. Built by
`local/build_agreement.py` from `institutions.json` + `not_classified.json` only, so
anyone can reproduce it from this repo. Reports two rates — `stage_agreement` (of
reviewed rows carrying an agent proposal, how often the proposed stage stood) and
`proposal_accepted` (of every proposal adjudicated, how often it was taken unchanged,
counting rows withdrawn on review) — plus a proposed-vs-final matrix, the revisions and
the withdrawals. **It is ANCHORED agreement and an upper bound, never a reliability
coefficient**: the reviewer saw the proposed stage and its reasoning before deciding, and
is also the author of the rules. No kappa is computed here and none may be quoted from
it. Rebuild after every review session. Rendered on the Methodology page.

`data/transitions.jsonl` — the PANEL SPINE. Append-only, public, tracked. One record per
approved stage move, written ONLY by `review.py`, which refuses the write without a
`date_effective` (the date of the triggering EVIDENCE, never the review date) and an
`evidence_url`. A panel dated by review sessions would measure the reviewer's calendar
instead of the sector's. Starts absent and fills prospectively.

### Presentation layer — never modifies `institutions.json`

Three derived files, consulted at render time only. `vite.config.js` copies every
`data/*.json` into `docs/data/` at build, so a new one ships automatically — but only
after `npm run build`.

`data/translations.json` — `{runs: {exact CJK run: English}}`. `<Lang>` looks each run up
by EXACT string via `segmentCjk()` in `src/data.js` (quoted 「…」/『…』 spans first, then CJK
runs in the remainder). Keys drift silently whenever a reviewed rationale is edited: the
old key orphans, the new one falls back to raw CJK, and nothing errors. **Gate it with
`python3 local/check_translations.py --check`** before every build.

`data/summaries.json` — `{summaries: {row name: [bullets]}}`. 4–5 bullets compressed from
that row's reviewed rationale, introducing no new facts, the last one carrying the
"stops short of…" clause. One entry per row; the checker above reports missing and stale.

`data/homepages.json` — `{homepages: {row name: {url}}}`. Firm homepages taken from
own-domain evidence URLs that already passed human review. A row with no own-domain
evidence gets no link rather than a guessed one, so partial coverage is expected.

### Auto vs curated vs reviewer-only

- **Auto** (`monitor.py` only): `latest_signal`, `latest_date`, top-level `source_url`.
  Empty on every agent-inserted row — the monitor has matched only the 8 pre-pipeline
  seed rows. Nothing user-facing may key off `latest_date` alone for that reason; use
  `latestActivity()` in `src/data.js`, which falls back to the newest curated event.
- **Curated** (agent drafts, human verifies): `stage`, `rationale`, `use_cases`,
  `events`, `footnote`, `confidence`, `region`, `aum`, `type`, `aliases`.
- **Reviewer-only** (`review.py` writes these; agents never do): `as_of_reviewed`,
  `label_provenance`, `agent_proposed_stage`, `data/not_classified.json`,
  `data/transitions.jsonl`.

### Data-file formatting
`monitor.py` owns the on-disk format of these files: `json.dumps(indent=2,
ensure_ascii=False)` + trailing newline. Curate `institutions.json` in that same
shape (arrays expanded one-element-per-line, raw UTF-8 — em-dashes, accents, and
currency symbols stay literal). This keeps automated rewrites to minimal,
meaningful diffs.

## Stage definitions (the classification bar)
METHODOLOGY.md is the classification bar: scope §1, sources §2, stages §3,
decision discipline §4. `data/stage_definitions.json` is the machine-readable
copy; keep it in sync with METHODOLOGY.md. Any agent classifying an
institution reads METHODOLOGY.md first.

## The engine — monitor.py (Python). Already built. Pipeline per run:
1. `fetch_articles()`: GDELT DOC 2.0 query, last 24h, normalize `seendate` to
   `YYYY-MM-DD`.
2. dedup new URLs against `seen_urls.json`.
3. `screen()`: batch new candidates to the Claude API (`claude-haiku-4-5-20251001`). Claude
   returns a JSON array of accepted items, each with `source`, `institution`,
   `institution_normalized`, `category`, `headline`, `url`, `date`,
   `why_it_matters`. Returns `[]` if nothing qualifies.
4. Prepend accepted to `feed.json`, slice to `[:200]`, save.
5. Mark all candidates seen → save `seen_urls.json`.
6. `update_institutions()`: match each item's `institution_normalized`
   (case-insensitive, exact, against each row's `aliases`) to a row; update ONLY
   `latest_signal` / `latest_date` / `source_url`, and only if the item date is
   strictly newer (empty `latest_date` treated as oldest). Never touch curated
   fields. Skip unmatched institutions (never add rows). Writes the file only when
   something actually changed.

Run locally: `uv run --env-file .env python monitor.py`
Key from env (`ANTHROPIC_API_KEY`); repo secret in CI. Never hardcoded.

> Known tradeoff: the 24h GDELT window is aligned to a daily cron. A missed or
> delayed run loses that day's articles. If that becomes a problem, widen
> `timespan` (e.g. `36h`) — the dedup ledger absorbs the overlap.

## Front end (to build) — Vite + React, plain CSS, static, one page
- Fetch `data/institutions.json` → render classification grid (primary).
- Fetch `data/feed.json` → render Recent Signals panel (secondary).
- Client-side filters: by type, by stage.
- Per-institution drill-down (v1.5): click a row → show `feed.json` items where
  `item.institution_normalized` matches one of that row's `aliases`
  (case-insensitive) — the same key the engine matches on.
- Empty states for both files (`[]` or missing).
- Header: project name, one-line description, last-updated timestamp
  (newest `latest_date` across institutions, or newest feed item).
- Footer: name + GitHub link.
- Aesthetic: clean, dense, dark, terminal/Linear-ish intelligence feed.
- Front end and `data/` live in the SAME repo (no CORS).

## Automation (to build, AFTER local works end-to-end)
- `.github/workflows/monitor.yml`: daily cron in UTC (e.g. `'0 14 * * *'`), runs
  `monitor.py`, commits updated `feed.json` + `institutions.json` + `seen_urls.json`.
  - GitHub cron is UTC and does NOT observe DST: `0 14 * * *` is 7am PDT in summer
    but 6am PST in winter. Pick the UTC hour deliberately.
- `permissions: contents: write` (required, else the commit silently fails).
- `ANTHROPIC_API_KEY` from repo secret.
- GitHub Pages serves the Vite build.

## Conventions
- Minimal code, no speculative features/abstractions, no unrequested deps.
- `main` always deployable; `feat/*` branches → PR (after scaffold is live).
- Conventional commits (`feat:`, `fix:`, `chore:`). MIT license, real name in it.
- No secrets in code or any data file. `.gitignore` covers `node_modules`, `dist`,
  `.env`, `__pycache__`, `.venv`.
- Classifications rest ONLY on public sources. README states this explicitly.
- Python engine is a `uv` project; `uv.lock` is committed.

## Build order (do not skip)
1. ✅ `monitor.py` runs clean locally + output schema is correct (unit-tested).
2. Build front end against local data files.
3. GitHub Actions automation.
4. GitHub Pages deploy + one manual `workflow_dispatch` test run.

## Repo map (orientation — avoid re-exploring)
- `monitor.py` — engine: GDELT fetch → dedup → Claude screen → feed/institutions update
- `alerts.py` — notify-only email digest (Resend) for stage-relevant signals
- `data/` — `institutions.json` (STATE) · `feed.json` (STREAM) · `seen_urls.json` (dedup) · `stage_definitions.json` · `not_classified.json` (APPENDIX, human-gated)
- `src/` — React dashboard: `App.jsx`, `main.jsx`, `data.js`, `useInstitutions.js`, `styles.css`;
  `components/`: Header, Footer, InstitutionTable, PhaseGrid, StageBadge, FilterPills, DrillDown, Methodology
- `tests/` — `test_monitor.py` (unit) · `test_gdelt_live.py` (live)
- `docs/` — built site served by GitHub Pages; `vite.config.js` copies `data/` → `docs/data/`
- `local/` + `CLAUDE.local.md` — gitignored working area (research queue, evidence
  ledger, overnight supervisor). Never committed. When present, read
  `CLAUDE.local.md` for current state before exploring `local/`.
