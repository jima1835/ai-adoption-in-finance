"""AI in Finance — monitor.

GDELT DOC 2.0 → Claude screener → data/feed.json (event stream), and refreshes
the matching institution's latest-signal fields in data/institutions.json (the
hand-curated state dashboard). Curated fields are never touched.

Run: uv run --env-file .env python monitor.py
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

import anthropic
import requests

from alerts import send_stage_alert
from roles import alias_index, append_jsonl, load_population

# --- Config ---------------------------------------------------------------

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MODEL = "claude-haiku-4-5-20251001"

DATA_DIR = Path(__file__).parent / "data"
FEED_PATH = DATA_DIR / "feed.json"
SEEN_PATH = DATA_DIR / "seen_urls.json"
INSTITUTIONS_PATH = DATA_DIR / "institutions.json"

FEED_LIMIT = 200

# Tight query: named financial institutions actually deploying/investing in AI,
# not generic "AI-powered" marketing. GDELT ANDs the groups, ORs inside each
# group; phrases must stay quoted. GDELT limits query length/complexity and
# rejects overly long queries ("Your query was too long or too short."), so keep
# the term count modest when editing.
QUERY = (
    '(bank OR "asset manager" OR insurer OR fintech OR payments) '
    '("artificial intelligence" OR "generative AI") '
    '(deploys OR adopts OR launches OR invests OR partnership) '
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
  "stage_relevant"          - true/false: does this signal plausibly suggest a
                              MATERIAL change in the institution's operational
                              AI-adoption stage — firm-wide production rollout,
                              first autonomous decisioning, an org restructure
                              around AI, or a major pullback — NOT routine
                              incremental news? Be CONSERVATIVE: a single press
                              release or a vague "AI-powered" claim is NOT
                              stage-relevant. Require language implying a real
                              shift in production scope, autonomy, or structure.
  "stage_relevant_reason"   - one sentence on why stage_relevant is true/false

Return [] if nothing qualifies. Output JSON only — no markdown fences, no
preamble, no commentary."""


# --- Helpers --------------------------------------------------------------

def load_json(path, default):
    if not path.exists():
        return default
    # Explicit utf-8: Windows defaults to the ANSI code page (cp1252, cp936, ...),
    # which cannot decode the CJK evidence in institutions.json.
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, value):
    # ensure_ascii=False keeps curated text (em-dashes, accents, £/€) human-readable.
    # utf-8 + LF-only so the on-disk format is identical on every platform: text
    # mode on Windows would otherwise write CRLF and churn every line of data/.
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def normalize_date(seendate):
    """GDELT seendate ("20260603T140000Z") -> "YYYY-MM-DD"; "" if unparseable."""
    if len(seendate) >= 8 and seendate[:8].isdigit():
        return f"{seendate[:4]}-{seendate[4:6]}-{seendate[6:8]}"
    return ""


def fetch_articles(query=QUERY, timespan="24h"):
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "timespan": timespan,
        "sortby": "datedesc",
        "maxrecords": 250,
    }
    # Transient failures (429, 5xx, timeouts, connection errors) should produce a
    # clean "nothing new" run, not a crash / red CI. No retries — a daily cron
    # won't normally hit rate limits.
    try:
        resp = requests.get(GDELT_URL, params=params, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        status = getattr(e.response, "status_code", None)
        detail = f" (HTTP {status})" if status else ""
        print(f"GDELT request failed{detail}; skipping this run.")
        return []
    body = resp.text.strip()
    # GDELT returns an empty body when there are no matches.
    if not body:
        return []
    # GDELT can return a plain-text error (e.g. "Your query was too long or too
    # short.") with HTTP 200 — don't hard-crash the daily job on a bad response.
    try:
        articles = resp.json().get("articles", [])
    except ValueError:
        print(f"Warning: GDELT returned non-JSON ({len(body)} bytes): {body[:120]!r}")
        return []
    # Normalize dates to YYYY-MM-DD before they reach Claude or feed.json.
    for a in articles:
        a["seendate"] = normalize_date(a.get("seendate", ""))
    return articles


def screen(client, candidates, system=SCREENER_PROMPT):
    # `system` is a parameter so the roles sweep can reuse this exact call —
    # same model, same fence-stripping, same JSON contract — with its own prompt.
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=system,
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
    (name, aliases, type, aum, stage, rationale, use_cases, events, footnote)
    are never modified. Institutions not already in the file are skipped — rows
    are never added. Returns the number of rows updated.

    The shared data/stage_definitions.json reference is a separate file this
    engine never reads or writes.
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
        # aum, stage, rationale, use_cases, events, footnote.
        row["latest_signal"] = item.get("why_it_matters", "")
        row["latest_date"] = item_date
        row["source_url"] = item.get("url", "")
        updated.add(row["name"])

    # Only write when something actually changed — no churn on no-op runs.
    if updated:
        save_json(INSTITUTIONS_PATH, institutions)
    return len(updated)


def collect_flagged(accepted):
    """Accepted items the screener flagged stage_relevant AND that match an
    existing institution row, each annotated with the row's CURRENT stage.

    Only matched items can be flagged — the screener's flag is advisory; the
    institution match (case-insensitive alias lookup, same key as
    update_institutions) is enforced here. Curated state is never changed; this
    is purely for notification.
    """
    if not INSTITUTIONS_PATH.exists():
        return []
    institutions = load_json(INSTITUTIONS_PATH, [])
    alias_to_row = {
        alias.lower(): row
        for row in institutions
        for alias in row.get("aliases", [])
    }
    flagged = []
    for item in accepted:
        if not item.get("stage_relevant"):
            continue
        norm = item.get("institution_normalized", "")
        row = alias_to_row.get(norm.lower()) if norm else None
        if row is None:
            continue
        flagged.append({**item, "current_stage": row.get("stage", "")})
    return flagged


# --- Roles sweep (METHODOLOGY §11) ----------------------------------------
#
# A separate pass with its own query, its own ledger and its own output. It
# PROPOSES; it never files. Three invariants, each covered by a test:
#
#   1. it writes nothing under data/ — candidates land in local/roles_queue.jsonl
#      and the dedup ledger sits beside it, so a roles sweep can never move the
#      dashboard or the feed;
#   2. it never reads or writes `stage`. A hire is an input to adoption, not
#      evidence of it (METHODOLOGY §3);
#   3. excluded institutions never reach a query — load_population() drops them
#      before the query is built, so there is no later check to forget.
#
# The ledger is local/roles_seen_urls.json rather than data/seen_urls.json on
# purpose. Sharing the feed's ledger would mark a role article "already
# screened", and the daily feed sweep would then never offer it to its own
# screener — silently shrinking the primary product's coverage to buy dedup for
# a secondary one.

ROLES_PROMPT_PATH = Path(__file__).parent / "prompts" / "roles_screen.md"
ROLES_QUEUE_PATH = Path(__file__).parent / "local" / "roles_queue.jsonl"
ROLES_SEEN_PATH = Path(__file__).parent / "local" / "roles_seen_urls.json"

# Appointment language AND AI language. Kept deliberately plain: GDELT matches
# whole words, so "appoint*" style wildcards are spelled out instead.
ROLES_TERMS = (
    '(appoint OR appoints OR appointed OR appointment OR names OR hires OR '
    '"joins as" OR promoted) '
    '("artificial intelligence" OR "AI")'
)

# GDELT rejects a long query with a plain-text 200 body ("Your query was too
# long or too short."), which fetch_articles() already survives. This budget
# caps the institution group so that does not happen in the first place; it is
# conservative on purpose. Raise it only against a live run you have watched.
ROLES_QUERY_BUDGET = 220

# One screening request per chunk of candidates. The feed sweep runs a single
# query capped at 250 articles and screens it in one call; a roles sweep runs
# one query PER BATCH of institutions, so its candidate list is unbounded and a
# single call would eventually blow the response budget.
ROLES_SCREEN_CHUNK = 120


def roles_query_batches(population, budget=ROLES_QUERY_BUDGET):
    """GDELT queries covering `population`, batched to stay inside the budget.

    No `sourcelang:english` filter, unlike the feed query. The corpus covers
    Japan, Asia and the Middle East, and those institutions announce leadership
    in their own language first; an English-only sweep would bias the roles
    record toward the firms the dashboard already covers best.
    """
    terms, seen = [], set()
    for entry in population:
        for key in [entry["name"], *entry["aliases"]]:
            key = key.strip()
            if not key or key.lower() in seen:
                continue
            seen.add(key.lower())
            terms.append(f'"{key}"' if " " in key else key)

    batches, current, size = [], [], 0
    for term in terms:
        if current and size + len(term) + 4 > budget:
            batches.append(current)
            current, size = [], 0
        current.append(term)
        size += len(term) + 4
    if current:
        batches.append(current)
    return [f"({' OR '.join(b)}) {ROLES_TERMS}" for b in batches]


def roles_screener_prompt():
    """The screener prompt lives in prompts/roles_screen.md so it can be read,
    reviewed and diffed on its own — it is an instrument, not a string."""
    return ROLES_PROMPT_PATH.read_text(encoding="utf-8")


def queue_roles_candidates(accepted, index):
    """Append screener output to the local review queue, one record per line.

    Items naming an institution outside the population are dropped here. That
    covers two different cases — never in scope, and on the exclusion denylist —
    and both get the same treatment: nothing is written.
    Returns (queued, dropped).
    """
    queued = dropped = 0
    for item in accepted:
        name = index.get(str(item.get("institution", "")).strip().lower())
        if not name:
            dropped += 1
            continue
        append_jsonl(ROLES_QUEUE_PATH, {
            "institution": name,
            "institution_raw": item.get("institution", ""),
            "event_type_guess": item.get("event_type_guess", ""),
            "person_guess": item.get("person_guess"),
            "reason": item.get("reason", ""),
            "url": item.get("url", ""),
            "date": item.get("date", ""),
            "queued_on": date.today().isoformat(),
        })
        queued += 1
    return queued, dropped


def roles_main(argv=()):
    """`python monitor.py --roles [--limit N]` — propose role events for review.

    --limit is the pre-flight control: run the sweep over the first N
    institutions and read the queue before pointing it at the whole population.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set.")

    limit = None
    if "--limit" in argv:
        pos = list(argv).index("--limit")
        limit = int(argv[pos + 1]) if pos + 1 < len(argv) else None

    population = load_population()
    if limit:
        population = population[:limit]
    if not population:
        print("Population is empty — nothing to sweep.")
        return

    batches = roles_query_batches(population)
    index = alias_index(population)
    seen = set(load_json(ROLES_SEEN_PATH, []))
    print(f"Roles sweep: {len(population)} institution(s), {len(batches)} GDELT batch(es).")

    candidates = []
    for n, query in enumerate(batches, 1):
        articles = fetch_articles(query=query)
        # GDELT ArtList returns no excerpt field today, so `snippet` is usually
        # empty; the key is kept because the screener contract includes it and
        # another source can fill it. `language` is passed through because this
        # sweep is deliberately not English-only.
        fresh = [
            {
                "title": a.get("title", ""),
                "snippet": a.get("excerpt", ""),
                "source": a.get("domain", ""),
                "language": a.get("language", ""),
                "url": a.get("url", ""),
                "date": a.get("seendate", ""),
            }
            for a in articles
            if a.get("url") and a["url"] not in seen
        ]
        seen.update(c["url"] for c in fresh)
        candidates += fresh
        print(f"  batch {n}/{len(batches)}: {len(articles)} article(s), {len(fresh)} new.")

    if not candidates:
        print("Nothing new to screen.")
        return

    client = anthropic.Anthropic()
    prompt = roles_screener_prompt()
    accepted = []
    for start in range(0, len(candidates), ROLES_SCREEN_CHUNK):
        chunk = candidates[start:start + ROLES_SCREEN_CHUNK]
        accepted += screen(client, chunk, system=prompt)
    print(f"Claude accepted {len(accepted)} of {len(candidates)} item(s).")

    queued, dropped = queue_roles_candidates(accepted, index)
    save_json(ROLES_SEEN_PATH, sorted(seen))
    print(f"Queued {queued} candidate(s) to {ROLES_QUEUE_PATH.name}"
          f"{f'; dropped {dropped} outside the population' if dropped else ''}.")
    print("Nothing under data/ was written. Review with: python3 tools/review.py --roles")


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

    # Notify-only: flag matched signals that may warrant re-classification. The
    # stage is NEVER changed by this script; the email just prompts a review.
    flagged = collect_flagged(accepted)
    print(f"{len(flagged)} signal(s) flagged stage-relevant.")
    send_stage_alert(flagged)


if __name__ == "__main__":
    # Two sweeps, one entry point. The roles sweep is opt-in and never
    # runs as a side effect of the daily feed run.
    if "--roles" in sys.argv[1:]:
        roles_main(sys.argv[1:])
    else:
        main()
