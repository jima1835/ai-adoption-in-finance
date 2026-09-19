"""The `--roles` sweep: it proposes, and it is incapable of filing.

Fixture-based; no network and no API key. The live GDELT check lives in
tests/test_gdelt_live.py behind the `live` marker, as the feed query's does.

The invariant these tests exist for: a roles sweep writes NOTHING under data/.
Everything it produces lands in local/, where a human picks it up with
`tools/review.py --roles`. If that ever stops being true, the roles module has
become a second, ungated writer of the public corpus.
"""

import json
from pathlib import Path

import pytest

import monitor

ROOT = Path(__file__).resolve().parents[1]

POPULATION = [
    {"name": "CalSTRS", "aliases": ["CalSTRS", "California State Teachers' Retirement System"],
     "source": "institutions"},
    {"name": "GIC", "aliases": ["GIC"], "source": "institutions"},
]

ARTICLE = {
    "url": "https://example.org/a",
    "title": "CalSTRS names head of artificial intelligence",
    "domain": "example.org",
    "language": "English",
    "seendate": "2026-03-24",
}

ACCEPTED = [{
    "candidate": True,
    "institution": "CalSTRS",
    "event_type_guess": "hired",
    "person_guess": "Alex Example",
    "reason": "names the appointment",
    "url": "https://example.org/a",
    "date": "2026-03-24",
}]


# --- query construction ---------------------------------------------------

def test_batches_stay_inside_the_length_budget():
    batches = monitor.roles_query_batches(monitor.load_population())
    assert batches
    overhead = len(monitor.ROLES_TERMS) + 4
    for q in batches:
        assert len(q) - overhead <= monitor.ROLES_QUERY_BUDGET + 64


def test_multiword_names_are_quoted_and_aliases_deduped():
    q = monitor.roles_query_batches(POPULATION, budget=10_000)[0]
    assert '"California State Teachers\' Retirement System"' in q
    assert q.count("CalSTRS") == 1  # the alias repeats the name; query it once
    assert "GIC" in q


def test_the_sweep_is_not_english_only():
    """The corpus covers Japan, Asia and the Middle East, and those firms
    announce leadership in their own language first. An English-only sweep would
    bias the roles record toward the rows already covered best."""
    q = monitor.roles_query_batches(POPULATION, budget=10_000)[0]
    assert "sourcelang" not in q
    assert "sourcelang:english" in monitor.QUERY  # the feed query is unchanged


def test_excluded_institutions_never_reach_a_query(monkeypatch):
    monkeypatch.setattr(monitor, "load_population",
                        lambda: [p for p in POPULATION if p["name"] != "GIC"])
    q = " ".join(monitor.roles_query_batches(monitor.load_population(), budget=10_000))
    assert "GIC" not in q


# --- queueing -------------------------------------------------------------

def test_candidates_outside_the_population_are_dropped(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "ROLES_QUEUE_PATH", tmp_path / "roles_queue.jsonl")
    index = {"calstrs": "CalSTRS"}
    queued, dropped = monitor.queue_roles_candidates(
        ACCEPTED + [{**ACCEPTED[0], "institution": "Acme Capital"}], index)

    assert (queued, dropped) == (1, 1)
    lines = (tmp_path / "roles_queue.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["institution"] == "CalSTRS"
    assert record["event_type_guess"] == "hired"
    assert "stage" not in record


def test_the_queue_is_append_only(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "ROLES_QUEUE_PATH", tmp_path / "roles_queue.jsonl")
    monitor.queue_roles_candidates(ACCEPTED, {"calstrs": "CalSTRS"})
    monitor.queue_roles_candidates(ACCEPTED, {"calstrs": "CalSTRS"})
    assert len((tmp_path / "roles_queue.jsonl").read_text().splitlines()) == 2


# --- the sweep end to end -------------------------------------------------

@pytest.fixture
def sweep(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(monitor, "ROLES_QUEUE_PATH", tmp_path / "roles_queue.jsonl")
    monkeypatch.setattr(monitor, "ROLES_SEEN_PATH", tmp_path / "roles_seen_urls.json")
    monkeypatch.setattr(monitor, "load_population", lambda: POPULATION)
    monkeypatch.setattr(monitor, "alias_index", lambda pop=None: {"calstrs": "CalSTRS"})
    monkeypatch.setattr(monitor, "fetch_articles",
                        lambda query=None, timespan="24h": [dict(ARTICLE)])
    monkeypatch.setattr(monitor.anthropic, "Anthropic", lambda *a, **k: object())
    monkeypatch.setattr(monitor, "screen", lambda *a, **k: list(ACCEPTED))
    return tmp_path


def test_sweep_queues_candidates_and_remembers_urls(sweep):
    monitor.roles_main(["--roles"])
    assert (sweep / "roles_queue.jsonl").exists()
    assert json.loads((sweep / "roles_seen_urls.json").read_text()) == [ARTICLE["url"]]


def test_sweep_writes_nothing_under_data(sweep):
    """The invariant. Everything under data/ is byte-identical afterwards."""
    data = ROOT / "data"
    before = {p.name: p.read_bytes() for p in sorted(data.iterdir()) if p.is_file()}
    monitor.roles_main(["--roles"])
    after = {p.name: p.read_bytes() for p in sorted(data.iterdir()) if p.is_file()}
    assert before == after


def test_a_seen_url_is_not_screened_twice(sweep, monkeypatch):
    monitor.save_json(sweep / "roles_seen_urls.json", [ARTICLE["url"]])
    monkeypatch.setattr(monitor, "screen",
                        lambda *a, **k: pytest.fail("screened an already-seen url"))
    monitor.roles_main(["--roles"])
    assert not (sweep / "roles_queue.jsonl").exists()


def test_limit_narrows_the_population(sweep, monkeypatch):
    seen = []
    monkeypatch.setattr(monitor, "roles_query_batches",
                        lambda pop, **k: seen.append(len(pop)) or ["q"])
    monitor.roles_main(["--roles", "--limit", "1"])
    assert seen == [1]


def test_sweep_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        monitor.roles_main(["--roles"])


def test_the_screener_prompt_is_a_reviewable_file():
    text = monitor.roles_screener_prompt()
    assert "retitled" in text and "LinkedIn" in text
    assert (ROOT / "prompts" / "roles_screen.md").exists()
