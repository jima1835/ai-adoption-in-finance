"""AI in Finance — monitor.

GDELT DOC 2.0 → Claude screener → data/feed.json (event stream), and refreshes
the matching institution's latest-signal fields in data/institutions.json (the
hand-curated state dashboard). Curated fields are never touched.

Run: uv run --env-file .env python monitor.py
"""

import json
import os
import sys
from pathlib import Path

import anthropic
import requests

# --- Config ---------------------------------------------------------------

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MODEL = "claude-opus-4-8"

DATA_DIR = Path(__file__).parent / "data"
FEED_PATH = DATA_DIR / "feed.json"
SEEN_PATH = DATA_DIR / "seen_urls.json"
INSTITUTIONS_PATH = DATA_DIR / "institutions.json"

FEED_LIMIT = 200

# Tight query: named financial institutions actually deploying/investing in AI,
# not generic "AI-powered" marketing. Edit freely — GDELT ANDs the groups,
# ORs inside each group. Phrases must stay quoted.
QUERY = (
    '(bank OR "asset manager" OR "asset management" OR insurer OR insurance '
    'OR fintech OR payments OR "wealth management" OR "hedge fund") '
    '("artificial intelligence" OR "generative AI" OR "machine learning" '
    'OR "AI agent" OR "AI model" OR copilot) '
    '(deploys OR deploy OR adopts OR adopt OR rollout OR "rolls out" '
    'OR launches OR invests OR partnership OR pilot) '
    'sourcelang:english'
)

CATEGORIES = "asset-mgmt, banking, fintech, insurance, payments, other"

SCREENER_PROMPT = f"""You are a screener for an AI-in-finance intelligence analyst.

Below is a JSON array of candidate news articles (title, source, url, date).
Return ONLY the items genuinely worth an analyst's attention: a named financial
institution (bank, asset manager, insurer, fintech, payments firm) actually
adopting, deploying, investing in, or partnering on AI — not generic
"AI-powered" marketing, listicles, opinion, or vendor hype.

Return a JSON array. Each accepted item is an object with exactly these keys:
  "source"                  - the publication / domain
  "institution"             - the named financial institution involved
  "institution_normalized"  - the institution's canonical common name
                              (e.g. "Blackrock Inc" -> "BlackRock")
  "category"                - one of: {CATEGORIES}
  "headline"                - a clear, factual headline
  "url"                     - the article url, copied verbatim from the input
  "date"                    - the article date, copied verbatim from the input
  "why_it_matters"          - one sharp sentence on the significance

Return [] if nothing qualifies. Output JSON only — no markdown fences, no
preamble, no commentary."""


# --- Helpers --------------------------------------------------------------

def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path, value):
    # ensure_ascii=False keeps curated text (em-dashes, accents, £/€) human-readable.
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def normalize_date(seendate):
    """GDELT seendate ("20260603T140000Z") -> "YYYY-MM-DD"; "" if unparseable."""
    if len(seendate) >= 8 and seendate[:8].isdigit():
        return f"{seendate[:4]}-{seendate[4:6]}-{seendate[6:8]}"
    return ""


def fetch_articles():
    params = {
        "query": QUERY,
        "mode": "ArtList",
        "format": "json",
        "timespan": "24h",
        "sortby": "datedesc",
        "maxrecords": 250,
    }
    resp = requests.get(GDELT_URL, params=params, timeout=60)
    resp.raise_for_status()
    # GDELT returns an empty body when there are no matches.
    if not resp.text.strip():
        return []
    articles = resp.json().get("articles", [])
    # Normalize dates to YYYY-MM-DD before they reach Claude or feed.json.
    for a in articles:
        a["seendate"] = normalize_date(a.get("seendate", ""))
    return articles


def screen(client, candidates):
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SCREENER_PROMPT,
        messages=[{"role": "user", "content": json.dumps(candidates, indent=2)}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "").strip()
    # Defensive: strip an accidental ```json fence if one slips through.
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def update_institutions(accepted):
    """Refresh each matched institution's latest-signal fields from `accepted`.

    Touches ONLY latest_signal / latest_date / source_url, and only when the
    item's date is newer than the row's current latest_date. Hand-curated fields
    (name, aliases, type, aum, stage, rationale, use_cases, events) are never
    modified. Institutions not already in the file are skipped — rows are never
    added. Returns the number of rows updated.
    """
    if not INSTITUTIONS_PATH.exists():
        print(f"Warning: {INSTITUTIONS_PATH.name} not found; skipping state update.")
        return 0

    institutions = load_json(INSTITUTIONS_PATH, [])
    # Exact (case-insensitive) alias -> row lookup; no fuzzy matching.
    alias_to_row = {
        alias.lower(): row
        for row in institutions
        for alias in row.get("aliases", [])
    }

    updated = set()
    for item in accepted:
        norm = item.get("institution_normalized", "")
        row = alias_to_row.get(norm.lower()) if norm else None
        if row is None:
            continue
        item_date = item.get("date", "")
        # Empty latest_date is treated as oldest; only overwrite if strictly newer.
        if item_date <= row.get("latest_date", ""):
            continue
        # Auto fields only. Never touch curated fields: name, aliases, type,
        # aum, stage, rationale, use_cases, events.
        row["latest_signal"] = item.get("why_it_matters", "")
        row["latest_date"] = item_date
        row["source_url"] = item.get("url", "")
        updated.add(row["name"])

    # Only write when something actually changed — no churn on no-op runs.
    if updated:
        save_json(INSTITUTIONS_PATH, institutions)
    return len(updated)


# --- Main -----------------------------------------------------------------

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set.")

    seen = set(load_json(SEEN_PATH, []))
    feed = load_json(FEED_PATH, [])

    articles = fetch_articles()
    candidates = [
        {
            "title": a.get("title", ""),
            "source": a.get("domain", ""),
            "url": a.get("url", ""),
            "date": a.get("seendate", ""),
        }
        for a in articles
        if a.get("url") and a["url"] not in seen
    ]
    print(f"GDELT: {len(articles)} articles, {len(candidates)} new.")

    if not candidates:
        print("Nothing new to screen.")
        return

    client = anthropic.Anthropic()
    accepted = screen(client, candidates)
    print(f"Claude accepted {len(accepted)} item(s).")

    # Newest first: prepend this run's accepted items, cap at FEED_LIMIT.
    feed = (accepted + feed)[:FEED_LIMIT]
    save_json(FEED_PATH, feed)
    # Mark every candidate seen so rejected items aren't re-screened next run.
    seen.update(c["url"] for c in candidates)
    save_json(SEEN_PATH, sorted(seen))
    print(f"Wrote {len(feed)} item(s) to {FEED_PATH.name}.")

    updated = update_institutions(accepted)
    print(f"Updated {updated} institution row(s) in {INSTITUTIONS_PATH.name}.")


if __name__ == "__main__":
    main()
