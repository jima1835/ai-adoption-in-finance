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
`tools/build_agreement.py` from `institutions.json` + `not_classified.json` only, so
anyone can reproduce it from this repo. Reports two rates — `stage_agreement` (of
reviewed rows carrying an agent proposal, how often the proposed stage stood **at the
first human review**, read from `label_provenance`) and `proposal_accepted` (of every
proposal adjudicated, how often it was taken unchanged, counting rows withdrawn on
review) — plus a proposed-vs-final matrix, the revisions and the withdrawals. Later
changes never move those rates: an evidence-dated transition (`transitions.jsonl`) or a
correction on re-reading is listed under `since_first_review`, and `current_label`
reports the proposal against today's stage so the two readings are never confused. **It is ANCHORED, non-independent agreement, never a reliability
coefficient**: the reviewer saw the proposed stage and its reasoning before deciding, and
is also the author of the rules. No kappa is computed here and none may be quoted from
it. Rebuild after every review session. Not rendered on the site (panel withdrawn 2026-09-27: a
near-diagonal matrix reads as two changes); the Methodology page links the file.

`data/transitions.jsonl` — the PANEL SPINE. Append-only, public, tracked. One record per
approved stage move, written ONLY by `review.py`, which refuses the write without a
`date_effective` (the date of the triggering EVIDENCE, never the review date) and an
`evidence_url`. A panel dated by review sessions would measure the reviewer's calendar
instead of the sector's. Starts absent and fills prospectively.

### Presentation layer — never modifies `institutions.json`

Derived files, consulted at render time only. `vite.config.js` copies every
`data/*.json` into `docs/data/` at build, so a new one ships automatically — but only
after `npm run build`. All of them are written AFTER human approval (the reviewer may
edit text at approval), never by the intake or refresh agents, and all degrade the same
way: absent or malformed → the lookup answers null and the feature does not render.
**Gate the whole layer with `python3 local/check_translations.py --check`** before
every build; `tests/presentation.test.mjs` and `tests/timeline.test.mjs` enforce the
same in CI.

`data/translations.json` — `{runs: {exact CJK run: English}}`. `<Lang>` looks each run up
by EXACT string via `segmentCjk()` in `src/data.js` (quoted 「…」/『…』 spans first, then CJK
runs in the remainder). Keys drift silently whenever a reviewed rationale is edited: the
old key orphans, the new one falls back to raw CJK, and nothing errors.

`data/summaries.json` — `{summaries: {row name: [bullets]}}`. 4–5 bullets compressed from
that row's reviewed rationale, introducing no new facts, the last one carrying the
"stops short of…" clause; `summaryParts()` in `src/data.js` prefixes each with a fixed
evidence label at render time. One entry per row.

`data/event_summaries.json` — `{entries: [{institution, date, source_url, source_note,
title, bullets}]}`: the per-event digest the timeline renders (`src/timeline.js`). Keyed on
the EXACT tuple of institution, date, source URL and event text (`source_note`), so a
changed event falls back to its full note until re-digested and an orphan marks an edited
or removed event. `title` ≤ 12 words, present tense, names the actor and the thing;
1–2 `bullets`, each ≤ 35 words, in English (a proper noun may keep its script; the
translation gate covers the run), preserving the event's attribution
("company claim", vendor-published), its deployment status (plan / pilot / production /
research output) and its scope calls, adding no fact the event does not carry. The full
event text stays one disclosure away in the UI. Maintain with
`python3 local/event_digests.py --check | --stubs | --merge`.

`data/descriptions.json` — `{descriptions: {row name: {text, source_url}}}`: a 15–30-word
intro under the name, drafted from the reviewed row; `source_url` is the homepage or null.

`data/homepages.json` — `{homepages: {row name: {url, derived_from, basis}}}`. Firm
homepages taken from own-domain evidence URLs that already passed human review; an
entry without `derived_from` renders as unverified.

`data/highlights.json` — `{kinds, highlights: [{institution, date, source_url, kind, label}]}`:
the few events per row worth a marker (tool / metric / capital), resolved to exactly one
event by the same exact-key rule. `data/publishers.json` — host → publisher label behind
each source link. `data/job_postings.json` — the requisition events rendered as Roles.

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
- ROLES module (METHODOLOGY §11 of v1.1.0) — withdrawn from the public tree in v1.2.0; preserved under local/roles_module/ for a later release.
- `schemas/*.schema.json` + `tools/validate_data.py` — a JSON Schema per public data file
  (`institutions.json`, `not_classified.json`, `excluded.json`) and the validator that checks
  every one of them. `data/excluded.json` is the recusal list — institutions never researched
  or proposed, merged with an untracked `local/excluded.json` overlay; it implies nothing about
  the institutions on it.
- `tests/test_frozen_corpus.py` — the blind-review gate. Dormant until the freeze is
  DECLARED: `python3 tools/review.py --freeze` writes `data/recode_freeze.json` and
  prints the digests to paste in. Nothing trips on row count alone — reaching 100 only
  makes the reviewer show `freeze_due`. Record the printed hashes once; do not re-pin
  them to go green. Delete the file only in the deliberate post-recode release.
- `src/` — React dashboard: `App.jsx`, `main.jsx`, `data.js`, `timeline.js`,
  `useInstitutions.js`, `styles.css`; `components/`: Header, Footer, InstitutionTable, PhaseGrid,
  StageBadge, FilterPills, DrillDown, Methodology, Releases, About. Hash routes:
  `#/methodology`, `#/releases` (a hand-written table, one 30–50-word row per release, kept in
  step with CHANGELOG.md at each release), `#/about`. `vite.config.js` bakes `__SITE_BUILD__` (build date,
  HEAD commit and its date) into the bundle; the footer's "Updated" stamp and the Releases page read it.
- `tests/` — `test_monitor.py` (unit) · `test_review.py` (review-tool panel guard) · `test_gdelt_live.py` (live)
- `tools/` — PUBLIC review tooling: `review.py` + `review.html` (the human audit UI) and
  `build_agreement.py` (rebuilds `data/agreement.json`). `local/review.py`, `local/review.html`
  and `local/build_agreement.py` are symlinks to these, so `python3 local/review.py` still works;
  edit the `tools/` copies. Published in v1.0.2 because the ATRACC submission and
  METHODOLOGY §5–6 describe them. Also `mapgen.mjs` — a one-shot generator that
  rewrites `src/worldgrid.js` (the By-region dot raster) from Natural Earth 110m;
  run it only to change the projection or the country→bucket table it carries.
- `docs/` — built site served by GitHub Pages; `vite.config.js` copies `data/` → `docs/data/`
- `local/` + `CLAUDE.local.md` — gitignored working area (research queue, evidence
  ledger, overnight supervisor). Never committed, except that the three tool files
  above live in `tools/` and are symlinked from here. When present, read
  `CLAUDE.local.md` for current state before exploring `local/`.
