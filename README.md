# AI Adoption in Finance

**A public dashboard classifying where major institutional investors sit on AI adoption right now** — asset managers, pensions, sovereign wealth funds, hedge funds, endowments. Every classification rests strictly on public sources (news, official disclosures, board materials) and is curated by hand; a monitoring engine — run on demand today — surfaces fresh public signals to keep each institution's *latest signal* current.

### → [**View the live dashboard**](https://jima1835.github.io/ai-adoption-in-finance/) ←

---

## What it is

Most "AI in finance" coverage is vendor hype and listicles. This project answers a sharper question for each institution: **where are they actually on the adoption curve — exploring, piloting, scaling, or embedded?** Each placement is hand-curated from public evidence and carries a one-line rationale. A monitoring engine then screens public news and keeps each institution's "latest signal" fresh, so the classifications stay backed by a current, dated public record.

The whole thing runs on GitHub — no servers, no database, no backend.

## Design principle — humans hold the stage

**AI surfaces signals; humans decide what they mean.** This is the project's core principle, and it is enforced in code, not merely stated:

- The automated engine refreshes an institution's *latest signal* line, and when a daily signal looks materially stage-relevant — a firm-wide rollout, a first autonomous decision, an org restructure around AI, a pullback — it **emails a human a digest** titled _"may warrant re-classification,"_ annotated with each institution's current stage.
- It **never changes the `stage`.** No model assigns, scores, or moves a classification. A stage changes only when a **human reads the public evidence and decides** — the same human judgment that keeps the `embedded` column [deliberately empty](#the-classification).

So the pipeline is a **notifier, not a classifier**: `monitor.py` flags and emails (via [`alerts.py`](alerts.py)); a human reviews and hand-edits [`data/institutions.json`](data/institutions.json). The split is structural — automation writes only `latest_signal` / `latest_date` / `source_url`, while everything that embodies a judgment (`stage`, `rationale`, `use_cases`, `events`, `footnote`) is curated by hand and never touched by the engine. The alert email can never act on its own; it can only put a decision in front of a person.

## The classification

Four stages, applied as a strict bar:

| Stage | Bar |
|---|---|
| **exploring** | Stated intent, hiring, task forces, "evaluating" — no shipped use case. |
| **piloting** | Named pilots/POCs, limited deployment, governance build-out — not yet firm-wide. |
| **scaling** | Multiple use cases in production, firm-wide rollout, AI as a strategic pillar with deployment evidence. |
| **embedded** | AI is core infrastructure across the business. **Intentionally empty** — no institution qualifies yet. A deliberate editorial position. |

Institution types: `asset-manager` · `pension` · `sovereign-wealth` · `hedge-fund` · `endowment`.

## How it works

```
GDELT DOC 2.0 API        Claude (claude-haiku-4-5)       data/*.json              GitHub Pages
  global news, 24h   ──►   screens for real signal   ──►   institutions.json  ──►   static React
  (monitor.py)             (drops the hype)                 feed.json               dashboard
        ▲                                                   (committed)             (one page, no API)
        └──────────── run on demand today · daily GitHub Actions schedule is planned, not built ──────────┘
```

When a screened signal looks like it could move an institution's stage, the engine **notifies instead of acting** — it never edits the stage itself (see [Design principle](#design-principle--humans-hold-the-stage)):

```
monitor.py  ──flags stage-relevant──►  email digest        ──►  human reviews   ──►  hand-edits `stage`
 (collect_flagged)                      (alerts.py / Resend)     public evidence      in institutions.json
```

The pipeline produces two datasets from one run:

1. **State** — `data/institutions.json`: one row per institution. The stage, rationale, and use-cases are **hand-curated** from public evidence; the engine only refreshes each institution's `latest_signal` / `latest_date` / `source_url` (and emails a human when a signal may warrant re-classification) — it never touches the curated fields. This is the dashboard.
2. **Stream** — `data/feed.json`: the latest screened news (newest first, capped at 200), each item tagged with its institution. Backs the "Recent Signals" panel and the per-institution drill-down.

`monitor.py` queries [GDELT DOC 2.0](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) for the last 24h, dedupes against `data/seen_urls.json`, sends new candidates to Claude in one batched call, prepends the accepted items to the feed, and updates the matching institution rows. The static React site reads both JSON files from the same repo (no CORS, no API).

## Running the engine locally

The engine is a [uv](https://docs.astral.sh/uv/) project.

```bash
# 1. Install dependencies into a managed virtualenv
uv sync

# 2. Add your Anthropic API key
cp .env.example .env        # then edit .env and paste your key

# 3. Run a collection pass
uv run --env-file .env python monitor.py
```

The run prints a per-stage summary (articles fetched → new candidates → accepted → feed written → institution rows updated). Run the tests with `uv run pytest`.

Tune the GDELT search by editing the `QUERY` constant at the top of [`monitor.py`](monitor.py) — it's deliberately tight to favor signal over noise. Add institutions by hand-editing [`data/institutions.json`](data/institutions.json) (see [CLAUDE.md](CLAUDE.md) for the schema and the curated-vs-auto field split).

## Project structure

```
ai-adoption-in-finance/
├── monitor.py             # the engine: GDELT → Claude → institutions.json + feed.json
├── alerts.py              # notify-only email digest (Resend) for stage-relevant signals
├── pyproject.toml         # uv project + dependencies
├── CLAUDE.md              # architecture & context
├── METHODOLOGY.md         # how institutions are classified (the credibility spine)
├── CONTRIBUTING.md        # how to contribute
├── tests/                 # pytest suite for the engine
├── data/                  # source of truth (root) — monitor.py writes here
│   ├── institutions.json  # the STATE — hand-curated classification grid
│   ├── feed.json          # the STREAM — screened signals (newest first, ≤200)
│   ├── seen_urls.json     # dedup ledger
│   └── stage_definitions.json  # shared stage reference (defs, scope, notes)
├── index.html             # Vite entry
├── vite.config.js         # build config; copies data/ → docs/data/ on build
├── src/                   # static React site (Vite) — components + plain CSS
└── docs/                  # built site served by GitHub Pages (includes docs/data/)
```

## Tech stack

- **Engine** — Python + [uv](https://docs.astral.sh/uv/), [GDELT DOC 2.0](https://www.gdeltproject.org/), [Claude API](https://docs.claude.com/) (`claude-haiku-4-5-20251001`)
- **Site** — Vite + React, plain CSS, static (built to `docs/`)
- **Infra** — [GitHub Pages](https://jima1835.github.io/ai-adoption-in-finance/) (hosting, live) + GitHub Actions CI (runs the test suite on PRs). Scheduled automation of the engine is planned, not yet built. One repo, no backend.

## A note on sourcing

Every classification is based **only on public information** — reported news, official disclosures, and board materials. Stages reflect a reading of public evidence, not inside knowledge, and are updated as the public record changes.

## Status

🚧 Early — the dashboard is **live** on GitHub Pages, and the engine works locally (unit-tested, run on demand). **Not yet built:** scheduled daily automation of the engine, and the in-UI "Recent Signals" feed panel (the `feed.json` stream exists; it isn't rendered on the page yet).

## License

MIT — see [LICENSE](LICENSE).

---

Built by Jiajun Ma — [github.com/jima1835](https://github.com/jima1835).
