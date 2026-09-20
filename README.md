# AI Adoption in Finance

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22247885.svg)](https://doi.org/10.5281/zenodo.22247885)

**A public, sourced classification of where major institutional investors sit on AI adoption right now** — pensions, sovereign-wealth funds, endowments, asset managers and hedge funds. Every row is drafted by an AI research agent from public evidence, and **every row is verified by a human before it publishes**. The rate at which those two disagree is published too.

### → [**View the live dashboard**](https://jima1835.github.io/ai-adoption-in-finance/) ←

---

## What it is

Most "AI in finance" coverage is vendor hype, listicles, or self-reported surveys. This project answers a sharper question for each named institution: **where are they actually on the adoption curve — exploring, piloting, scaling, or embedded?** Each placement carries a written rationale, a dated timeline, a confidence flag, and links to the public sources behind it.

Three things make it different from a bigger tracker:

1. **It covers asset owners.** Pensions, sovereign-wealth funds and endowments, not just the managers that commercial benchmarks rank.
2. **It publishes what it could not classify.** Institutions assessed against the methodology whose public record fell short are listed by name, with the reason. A tracker that publishes only its hits cannot be read as a rate of anything.
3. **It publishes its own error rate.** See [the disagreement record](#the-disagreement-record).

The whole thing runs on GitHub — no servers, no database, no backend.

## How a row is built

**An AI research agent drafts every row and proposes a stage. A human verifies every row before it publishes.** Neither half is decorative, and the division is enforced in code rather than promised in prose.

```
  ┌── agent ──────────────────┐   ┌── human ────────────┐   ┌── public ────────┐
  research the public record  │   │ read the row        │   │ institutions.json│
  fetch every cited URL       ├──►│ against its sources ├──►│ + not_classified │
  draft rationale + timeline  │   │ accept / revise /   │   │ + agreement.json │
  PROPOSE a stage             │   │ remove              │   │ → static React   │
  └───────────────────────────┘   └──────────┬──────────┘   └──────────────────┘
                                             │
                              every decision is logged: proposed stage,
                              final stage, and which of the three it was
```

The agent's standing constraints: public sources only, no encyclopedias or aggregators as evidence, nothing dated before 2023, and **no citation to a page it did not actually fetch** — a search-result snippet is not a source. Where the record does not support a stage, it says so rather than reaching.

The reviewer works from the cited evidence rather than re-researching the firm. That is deliberate: the agent's job is to find and assemble the record; the reviewer's job is to check that the record says what the draft claims and that the stage follows from it.

**Fields an agent may never write** — enforced in the review tool, not left to convention: the final `stage` once reviewed, the review date, the provenance fields, the assessed-but-not-classified appendix, and the stage-transition log. A reviewed stage is a published measurement; rewriting it would destroy the before/after pair that makes change observable.

Separately, a monitoring pass (`monitor.py`) screens public news and refreshes each institution's *latest signal*, emailing a human when something looks stage-relevant. It is a **notifier, not a classifier** — it writes only `latest_signal` / `latest_date` / `source_url` and can never move a stage.

## The disagreement record

Because every review decision is logged, the human-vs-agent disagreement rate is a measurement rather than an assurance. It is published in [`data/agreement.json`](data/agreement.json), rebuilt from `data/institutions.json` and `data/not_classified.json` (both in this repo, so the figures are reproducible without trusting the page), and rendered on the methodology page.

Two figures, because one alone would flatter the pipeline:

| | What it answers |
|---|---|
| **Stage agreement** | Of the reviewed rows carrying an agent proposal, how often did the proposed stage stand? |
| **Proposals accepted as-is** | Of every proposal adjudicated, how often was it taken unchanged — counting rows **withdrawn on review**, which are disagreements too? |

**This is anchored, non-independent agreement, and it should not be read as an inter-rater reliability estimate.** The reviewer saw the proposed stage and the agent's written reasoning before deciding, and there is one reviewer who also wrote the classification rules. No kappa is computed from this file and none should be quoted from it; establishing reliability needs a blind re-code against stripped evidence, which is a separate exercise. See [METHODOLOGY §6](METHODOLOGY.md#6-the-disagreement-record).

## The classification

Four stages, applied as a strict bar — each higher stage requires everything the lower one does, plus more:

| Stage | Bar |
|---|---|
| **exploring** | Stated intent, hiring, task forces, "evaluating" — no shipped use case. |
| **piloting** | Named pilots/POCs, limited deployment, governance build-out — not yet firm-wide. |
| **scaling** | Multiple use cases in production, firm-wide rollout, AI as a strategic pillar with deployment evidence. |
| **embedded** | AI is core infrastructure across the business. **Intentionally empty** — no institution qualifies yet. A deliberate editorial position. |

Institution types: `asset-manager` · `pension` · `sovereign-wealth` · `hedge-fund` · `endowment`. Regions: US · Canada · Europe · Middle East · Asia · Other.

Full rules — scope exclusions, the sourcing bar, decision discipline, and how this differs from commercial indices and self-assessment questionnaires — are in [METHODOLOGY.md](METHODOLOGY.md).

## What's published

Everything the dashboard runs on is tracked in this repo:

| File | What it holds |
|---|---|
| `data/institutions.json` | **The state.** One row per institution: stage, rationale, use cases, dated events, confidence, region, AUM — plus `as_of_reviewed`, `label_provenance` and `agent_proposed_stage`, the audit trail behind the disagreement record. |
| `data/not_classified.json` | **The negative record.** Assessed, not classified — with the reason and the outcome (`no-qualifying-evidence` or `withdrawn-on-review`). |
| `data/agreement.json` | **The disagreement record.** Derived; rebuild with `tools/build_agreement.py`. |
| `data/stage_definitions.json` | The shared stage reference, so the site and the docs cannot drift apart. |
| `data/translations.json` | English renderings of the CJK evidence runs, consulted at render time. The stored evidence is never rewritten. |
| `data/summaries.json`, `data/homepages.json` | Presentation-layer derivations: bulleted digests of reviewed rationales, and firm homepages taken from own-domain evidence URLs that already passed review. |
| `data/feed.json`, `data/seen_urls.json` | The monitoring stream and its dedup ledger. |

Stage **transitions** are appended to `data/transitions.jsonl` when a reviewer approves a stage change — dated by the *triggering evidence*, never by the review date. The log starts empty and fills prospectively; a panel dated by review sessions would measure the reviewer's calendar rather than the sector.

## Roles module (v1.1.0, pre-release)

A second record, on a different unit of observation: the **AI-leadership role event** — one dated, publicly sourced thing that happened to an AI-leadership role (a role created, someone hired into it, a leader retitled, a departure, a remit expanded). It lives in `data/roles.jsonl`, one record per line, and the full rules are [METHODOLOGY §11](METHODOLOGY.md).

It ships **published and empty**. The schema, the review gate, the collection sweep and the rules are in place before any data is, so the first record enters against rules written in advance rather than rules fitted to it.

**What it records:** the institution, the title verbatim in its own language plus a normalized comparison key, the person *where a qualifying source names one*, the event type, a variable-precision date, reporting line and scope where the source states them, one source URL with its tier, the verbatim quote that carries the claim, and a rationale.

**What it refuses to record:**

- **Any effect on an adoption stage.** A hire is an input to adoption, not evidence of it. Nothing in this module reads or writes `stage`, and a test enforces that.
- **Anything LinkedIn-derived**, at any point — not as evidence, not as corroboration, not as a search surface. A person is named only from a firm press release, a firm leadership page, a regulatory filing, or an outlet meeting the T1 or T2 criteria in [SOURCES.md](SOURCES.md). `person: null` is a complete record.
- **Compensation, and job postings.** Neither is collected and no such file exists.
- **A retitle as a new role.** "Chief Data Officer becomes Chief Data & AI Officer" is one person and one job.
- **Anything about an excluded institution** (`data/excluded.json`). An exclusion is a recusal and implies nothing about that institution.

Institutions searched with no qualifying result are published in `data/roles_not_found.jsonl` — without that, a firm searched and found empty is indistinguishable from one nobody looked at.

**To submit a correction or ask for a removal:** open an issue with the public sources, or use the channels under [Public comments and submissions](#public-comments-and-submissions). Anyone named in this record can ask for a correction or removal. A withdrawn event is deleted from `data/roles.jsonl` and recorded as `withdrawn-on-review` in the negative record, so the correction itself stays visible.

## A note on sourcing

Every classification rests **only on public information** — reported news, official disclosures, regulatory filings, board materials, earnings calls, and institutions' own published positions. Stages reflect a reading of the public record, not inside knowledge.

Absence of evidence **caps** a stage; it never infers one. A firm may well be further along privately; this dashboard reports only what the public record can defend. Where an institution's own claims cannot be independently verified, they are labeled as company claims rather than treated as fact.

Evidence in Chinese, Japanese and Korean is quoted **verbatim in the original** — the difference between 完成部署 (deployment completed) and 将应用 (will be applied) is the difference between two stages. An English rendering is shown alongside; the original is always the record.

**This corpus is not a sample of any defined population.** Institutions enter through research passes, not a sampling frame. Every figure describes *this corpus* and none of them is an industry rate.

## Running it

The engine is a [uv](https://docs.astral.sh/uv/) project; the site is Vite + React.

```bash
# monitoring engine
uv sync
cp .env.example .env        # then paste your Anthropic API key
uv run --env-file .env python monitor.py
uv run pytest
uv run ruff check .
python3 tools/validate_data.py     # every data file against schemas/

# roles module (METHODOLOGY §11) — proposes into local/, files nothing
uv run --env-file .env python monitor.py --roles --limit 5
python3 tools/review.py --roles    # the human gate on data/roles.jsonl

# site
npm install
npm run dev                 # serves the live data/ directory
npm run build               # builds to docs/, copying data/*.json(l) → docs/data/
npm run lint                # eslint
npm run format:check        # prettier
```

CI runs all four checks on every pull request, and the test suite on Linux and
Windows.

`monitor.py` queries [GDELT DOC 2.0](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) for the last 24h, dedupes against `data/seen_urls.json`, screens candidates through Claude, and updates the auto-only fields. Tune the search with the `QUERY` constant at the top of the file. See [CLAUDE.md](CLAUDE.md) for the row schema and the curated-vs-auto field split.

## Project structure

```
ai-adoption-in-finance/
├── monitor.py             # freshness engine: GDELT → Claude → latest_signal
├── alerts.py              # notify-only email digest for stage-relevant signals
├── METHODOLOGY.md         # the classification rules + construction protocol
├── SOURCES.md             # source tiers, the tier floor, and how they apply
├── CLAUDE.md              # architecture & row schema
├── CONTRIBUTING.md        # how to contribute
├── CHANGELOG.md           # what changed in each release
├── tests/                 # pytest suite: engine, review tool, data schema, version
├── tools/                 # human review tool, agreement builder, data validator
├── schemas/               # JSON Schema for every public data file
├── prompts/               # screener prompts, versioned as the instruments they are
├── data/                  # source of truth — see "What's published" above
├── src/                   # static React site (Vite) — components + plain CSS
├── vite.config.js         # build config; copies data/*.json(l) → docs/data/
└── docs/                  # built site served by GitHub Pages
```

### Local working area (not in this repo)

Row construction happens in a gitignored `local/` directory that never leaves the maintainer's machine: the research queue and prompts, the per-institution evidence ledger behind each classification, and the decision log. Only its *outputs* are committed — human-verified rows and the derived files above. The review tool itself (`tools/review.py` + `tools/review.html`) and the agreement builder (`tools/build_agreement.py`) are public as of v1.0.2. If you fork this repo you need none of `local/`; everything the dashboard runs on is tracked.

## Tech stack

- **Engine** — Python + [uv](https://docs.astral.sh/uv/), [GDELT DOC 2.0](https://www.gdeltproject.org/), [Claude API](https://docs.claude.com/)
- **Research + review** — Claude Code agents for drafting; a local human review tool as the publish gate
- **Site** — Vite + React, plain CSS, static (built to `docs/`)
- **Infra** — [GitHub Pages](https://jima1835.github.io/ai-adoption-in-finance/) + GitHub Actions CI (tests on Linux and Windows, linters, site build). One repo, no backend.

## Status

🚧 Active. The dashboard is **live**; the corpus is under human review row by row, and the review queue is drained before each release. **Not yet built:** scheduled automation of the monitoring engine, and the in-UI "Recent Signals" feed panel (`data/feed.json` exists; it isn't rendered yet).

## Independence

This is an independent personal project, produced entirely in the author's personal
capacity. It is **not affiliated with, sponsored by, funded by, or endorsed by any
employer or institution**, and every view and classification here is the author's alone.

No non-public information from the author's professional work informs any classification,
and institutions where the author has a professional affiliation are **excluded from
coverage entirely**. Nothing in this repository is investment advice.

## Contributors

The corpus and its methodology are the author's; the code is not only his.

- **Haochen Jiang** ([@incisors](https://github.com/incisors)) — Windows portability
  of the monitoring engine and the review tool
  ([#3](https://github.com/jima1835/ai-adoption-in-finance/pull/3)).

See [CONTRIBUTING.md](CONTRIBUTING.md) to add to this list.

## License

**Code** — MIT, see [LICENSE](LICENSE).

**Data** — CC BY 4.0, see [data/LICENSE](data/LICENSE). Use the corpus for anything, including commercially; give credit and say what you changed. Please keep the assessed-but-not-classified appendix with it — the negative record is what makes the positive record readable as a rate rather than a highlight reel.

---

Built by Jiajun Ma — [github.com/jima1835](https://github.com/jima1835).

## Public comments and submissions
- **2026-09-19** — Comment on NIST AI 200-2 ipd, *The TEVV-Athlon Framework for Evaluating AI Systems*. Proposes a minimum reporting summary for §2.4 — which Blocks went unmeasured, what human judges were shown before judging, and the evaluator's relationship to the developer — and a declared adoption stage for §2.1, offering this corpus's four-stage classification as the scale. [PDF](comments/2026-09-19_NIST_AI_200-2_ipd_comment_Jiajun_Ma.pdf) · [doi:10.5281/zenodo.N22853598](https://doi.org/10.5281/zenodo.22853598)
- **2026-09-10** — Comment on NIST AI 300-1 ipd, *Guidance and Templates for Public-Facing AI Documentation* (AI Standards Zero Draft). Proposes Annex A subfields 1.3.2.1 *Production Method* and 8.2.1.1 *Verification Condition* and a typed-absence convention, using this corpus's provenance record as the worked example. [PDF](comments/2026-09-10_NIST_AI_300-1_ipd_comment_Jiajun_Ma.pdf) · [doi:10.5281/zenodo.22701607](https://doi.org/10.5281/zenodo.22701607)
- **2026-07-22** — Response to the FSB consultation *Sound Practices for Responsible Adoption of AI*, published on [fsb.org](https://www.fsb.org/uploads/Jiajun-M-independent-response.pdf).
