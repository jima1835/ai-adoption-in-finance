"""Live integration test for Step 1 — hits the real GDELT DOC 2.0 API.

Deselected by default (network + GDELT rate limits). Run explicitly:

    uv run pytest -m live -v

It validates the fetch contract end-to-end against the real endpoint. Because
`fetch_articles()` skips cleanly on transient failures (429/5xx/timeout → []),
this test asserts the contract rather than a non-empty result, so a rate-limited
moment won't produce a false failure.
"""

import pytest

import monitor


@pytest.mark.live
def test_gdelt_live_fetch_contract():
    articles = monitor.fetch_articles()

    # Always a list — even on a transient GDELT failure (clean skip).
    assert isinstance(articles, list)

    # When GDELT returns data, every item carries what the pipeline reads and
    # the date is already normalized to YYYY-MM-DD (or "" if GDELT omitted it).
    for a in articles:
        assert isinstance(a.get("url", ""), str)
        seendate = a["seendate"]
        assert seendate == "" or (len(seendate) == 10 and seendate[4] == "-" and seendate[7] == "-")

    print(f"\nGDELT live: {len(articles)} article(s) for the current 24h query.")
