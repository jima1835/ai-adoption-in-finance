# AI Adoption in Finance

**A public dashboard classifying where major institutional investors sit on AI adoption right now** — asset managers, pensions, sovereign wealth funds, hedge funds, endowments. Every classification rests strictly on public sources (news, official disclosures, board materials), and a daily automated job keeps it current.

### → [**View the live dashboard**](https://jima1835.github.io/ai-adoption-in-finance/) ←

> _Live once GitHub Pages is enabled (final step)._

---

## What it is

Most "AI in finance" coverage is vendor hype and listicles. This project answers a sharper question for each institution: **where are they actually on the adoption curve — exploring, piloting, scaling, or embedded?** Each placement is hand-curated from public evidence and carries a one-line rationale. An automated pipeline then keeps each institution's "latest signal" fresh and runs a screened news feed underneath the grid as living proof the classifications are current.

The whole thing runs on GitHub — no servers, no database, no backend.

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
GDELT DOC 2.0 API        Claude (claude-opus-4-8)        data/*.json              GitHub Pages
  global news, 24h   ──►   screens for real signal   ──►   institutions.json  ──►   static React
  (monitor.py)             (drops the hype)                 feed.json               dashboard
        ▲                                                   (committed)             (one page, no API)
        └──────────────────── GitHub Actions runs the engine on a daily schedule ──────────┘
```

The pipeline produces two datasets from one run:

1. **State** — `data/institutions.json`: one row per institution. The stage, rationale, and use-cases are **hand-curated** from public evidence; the engine only refreshes each institution's `latest_signal` / `latest_date` / `source_url` and never touches the curated fields. This is the dashboard.
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
├── pyproject.toml         # uv project + dependencies
├── CLAUDE.md              # architecture & context
├── tests/                 # pytest suite for the engine
├── data/
│   ├── institutions.json  # the STATE — hand-curated classification grid
│   ├── feed.json          # the STREAM — screened signals (newest first, ≤200)
│   └── seen_urls.json     # dedup ledger
└── web/                   # static React site (Vite) — coming next
```

## Tech stack

- **Engine** — Python + [uv](https://docs.astral.sh/uv/), [GDELT DOC 2.0](https://www.gdeltproject.org/), [Claude API](https://docs.claude.com/) (`claude-opus-4-8`)
- **Site** — Vite + React, plain CSS, static
- **Infra** — GitHub Actions (engine) + GitHub Pages (hosting). One repo, no backend.

## A note on sourcing

Every classification is based **only on public information** — reported news, official disclosures, and board materials. Stages reflect a reading of public evidence, not inside knowledge, and are updated as the public record changes.

## Status

🚧 Early — the engine works locally and is unit-tested. Front end and scheduled automation are in progress.

## License

MIT — see [LICENSE](LICENSE).

---

Built by Jiajun Ma — [github.com/jima1835](https://github.com/jima1835).
