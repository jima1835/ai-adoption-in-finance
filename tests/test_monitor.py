"""Unit tests for the monitor engine. No network, no API key required."""

import pytest

import monitor


# --- JSON helpers ---------------------------------------------------------

def test_load_json_missing_returns_default(tmp_path):
    assert monitor.load_json(tmp_path / "nope.json", []) == []
    assert monitor.load_json(tmp_path / "nope.json", {"a": 1}) == {"a": 1}


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "x.json"
    monitor.save_json(p, [{"k": "v"}])
    assert p.read_text().endswith("\n")  # trailing newline for clean diffs
    assert monitor.load_json(p, None) == [{"k": "v"}]


# --- fetch_articles -------------------------------------------------------

class FakeResp:
    def __init__(self, text="", payload=None, ok=True):
        self.text = text
        self._payload = payload
        self._ok = ok

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


def test_fetch_articles_empty_body(monkeypatch):
    # GDELT returns an empty body when nothing matches.
    monkeypatch.setattr(monitor.requests, "get", lambda *a, **k: FakeResp(text="  "))
    assert monitor.fetch_articles() == []


def test_fetch_articles_parses_and_normalizes_date(monkeypatch):
    payload = {"articles": [{"url": "u1", "title": "t", "domain": "d", "seendate": "20260603T140000Z"}]}
    monkeypatch.setattr(monitor.requests, "get", lambda *a, **k: FakeResp(text="{}", payload=payload))
    arts = monitor.fetch_articles()
    assert [a["url"] for a in arts] == ["u1"]
    assert arts[0]["seendate"] == "2026-06-03"  # normalized before reaching Claude


def test_normalize_date():
    assert monitor.normalize_date("20260603T140000Z") == "2026-06-03"
    assert monitor.normalize_date("") == ""
    assert monitor.normalize_date("garbage") == ""


# --- screen ---------------------------------------------------------------

class _Block:
    type = "text"

    def __init__(self, text):
        self.text = text


class FakeClient:
    """Stands in for anthropic.Anthropic(); client.messages.create(...)."""

    def __init__(self, text):
        self._text = text
        self.messages = self

    def create(self, **kwargs):
        return type("Msg", (), {"content": [_Block(self._text)]})()


def test_screen_parses_plain_json():
    client = FakeClient('[{"institution": "Acme Bank"}]')
    assert monitor.screen(client, []) == [{"institution": "Acme Bank"}]


def test_screen_strips_code_fence():
    client = FakeClient('```json\n[{"institution": "Acme Bank"}]\n```')
    assert monitor.screen(client, []) == [{"institution": "Acme Bank"}]


def test_screen_handles_empty_array():
    assert monitor.screen(FakeClient("[]"), []) == []


# --- main: dedup, ordering, seen-ledger -----------------------------------

def test_main_dedup_newest_first_and_seen_update(tmp_path, monkeypatch):
    feed_path = tmp_path / "feed.json"
    seen_path = tmp_path / "seen_urls.json"
    monkeypatch.setattr(monitor, "FEED_PATH", feed_path)
    monkeypatch.setattr(monitor, "SEEN_PATH", seen_path)
    # Point at a non-existent institutions file so the real one is untouched.
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", tmp_path / "institutions.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    monitor.save_json(feed_path, [{"headline": "old", "url": "old-url"}])
    monitor.save_json(seen_path, ["seen-url"])

    articles = [
        {"url": "seen-url", "title": "dup", "domain": "d", "seendate": "s"},   # already seen
        {"url": "new-url", "title": "fresh", "domain": "d", "seendate": "s"},  # new
        {"title": "no url"},                                                   # no url
    ]
    monkeypatch.setattr(monitor, "fetch_articles", lambda: articles)

    captured = {}

    def fake_screen(client, candidates):
        captured["candidates"] = candidates
        return [{"headline": "fresh", "url": "new-url", "institution": "X",
                 "institution_normalized": "X", "date": "2026-01-01"}]

    monkeypatch.setattr(monitor, "screen", fake_screen)
    monkeypatch.setattr(monitor.anthropic, "Anthropic", lambda *a, **k: object())

    monitor.main()

    # Dedup: only the genuinely-new url reaches the screener.
    assert [c["url"] for c in captured["candidates"]] == ["new-url"]
    # Newest first: this run's accepted item is prepended to the existing feed.
    feed = monitor.load_json(feed_path, None)
    assert [item["url"] for item in feed] == ["new-url", "old-url"]
    # Seen ledger: every candidate url recorded, old entries preserved.
    seen = monitor.load_json(seen_path, None)
    assert {"seen-url", "new-url"} <= set(seen)


def test_main_no_new_candidates_skips_screen(tmp_path, monkeypatch):
    feed_path = tmp_path / "feed.json"
    seen_path = tmp_path / "seen_urls.json"
    monkeypatch.setattr(monitor, "FEED_PATH", feed_path)
    monkeypatch.setattr(monitor, "SEEN_PATH", seen_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monitor.save_json(feed_path, [])
    monitor.save_json(seen_path, ["u"])
    monkeypatch.setattr(monitor, "fetch_articles", lambda: [{"url": "u", "title": "t"}])

    def boom(*a, **k):
        raise AssertionError("screen must not run when there are no new candidates")

    monkeypatch.setattr(monitor, "screen", boom)
    monitor.main()  # returns cleanly without screening


def test_main_missing_key_exits(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        monitor.main()


def test_main_caps_feed_at_limit(tmp_path, monkeypatch):
    feed_path = tmp_path / "feed.json"
    seen_path = tmp_path / "seen_urls.json"
    monkeypatch.setattr(monitor, "FEED_PATH", feed_path)
    monkeypatch.setattr(monitor, "SEEN_PATH", seen_path)
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", tmp_path / "institutions.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    monitor.save_json(feed_path, [{"url": f"old-{i}"} for i in range(monitor.FEED_LIMIT)])
    monitor.save_json(seen_path, [])
    monkeypatch.setattr(monitor, "fetch_articles",
                        lambda: [{"url": "new", "title": "t", "domain": "d", "seendate": "20260101T000000Z"}])
    monkeypatch.setattr(monitor, "screen",
                        lambda c, cand: [{"url": "new", "why_it_matters": "w", "date": "2026-01-01",
                                          "institution_normalized": "Z"}])
    monkeypatch.setattr(monitor.anthropic, "Anthropic", lambda *a, **k: object())

    monitor.main()

    feed = monitor.load_json(feed_path, None)
    assert len(feed) == monitor.FEED_LIMIT
    assert feed[0]["url"] == "new"            # newest first
    assert feed[-1]["url"] == "old-198"       # oldest entry dropped


# --- update_institutions --------------------------------------------------

def _row(**overrides):
    row = {
        "name": "BlackRock",
        "aliases": ["BlackRock", "BLK"],
        "type": "asset-manager",
        "aum": "~$11.5T",
        "stage": "scaling",
        "rationale": "curated rationale",
        "use_cases": ["risk modeling"],
        "events": [{"date": "2023", "event": "position paper", "source_url": "e-url"}],
        "latest_signal": "old signal",
        "latest_date": "2026-01-01",
        "source_url": "old-url",
    }
    row.update(overrides)
    return row


def test_update_institutions_missing_file_warns_and_no_create(tmp_path, monkeypatch, capsys):
    path = tmp_path / "institutions.json"
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)
    n = monitor.update_institutions([{"institution_normalized": "BlackRock", "date": "2026-09-09"}])
    assert n == 0
    assert not path.exists()  # must not create the file
    assert "not found" in capsys.readouterr().out


def test_update_institutions_matches_alias_case_insensitive_preserves_curated(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row()])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)

    n = monitor.update_institutions([{
        "institution_normalized": "blk",  # matches alias "BLK", case-insensitive
        "why_it_matters": "new signal",
        "date": "2026-06-01",
        "url": "new-url",
    }])
    assert n == 1
    out = monitor.load_json(path, None)[0]
    # signal fields updated
    assert out["latest_signal"] == "new signal"
    assert out["latest_date"] == "2026-06-01"
    assert out["source_url"] == "new-url"
    # curated fields untouched
    assert out["stage"] == "scaling"
    assert out["rationale"] == "curated rationale"
    assert out["use_cases"] == ["risk modeling"]
    assert out["events"] == [{"date": "2023", "event": "position paper", "source_url": "e-url"}]


def test_update_institutions_never_touches_events(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    events = [
        {"date": "2023", "event": "paper", "source_url": "a"},
        {"date": "2026-04-28", "event": "firm-wide push", "source_url": "b"},
    ]
    monitor.save_json(path, [_row(events=events)])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)
    # An item whose date is newer than every variable-precision event date.
    monitor.update_institutions([{
        "institution_normalized": "BlackRock", "why_it_matters": "newer signal",
        "date": "2026-12-31", "url": "new-url",
    }])
    out = monitor.load_json(path, None)[0]
    assert out["latest_signal"] == "newer signal"   # auto field changed
    assert out["events"] == events                  # curated events untouched, order/precision preserved


def test_update_institutions_skips_older_or_equal_date(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row(latest_date="2026-05-01")])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)

    n = monitor.update_institutions([{
        "institution_normalized": "BlackRock", "why_it_matters": "stale",
        "date": "2026-01-01", "url": "stale-url",
    }])
    assert n == 0
    out = monitor.load_json(path, None)[0]
    assert out["latest_signal"] == "old signal"  # unchanged


def test_update_institutions_empty_latest_date_is_oldest(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row(latest_date="", latest_signal="", source_url="")])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)

    n = monitor.update_institutions([{
        "institution_normalized": "BlackRock", "why_it_matters": "first",
        "date": "2026-01-01", "url": "first-url",
    }])
    assert n == 1
    assert monitor.load_json(path, None)[0]["latest_date"] == "2026-01-01"


def test_update_institutions_skips_unknown(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row()])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)

    n = monitor.update_institutions([{
        "institution_normalized": "Vanguard", "why_it_matters": "x",
        "date": "2026-09-09", "url": "x",
    }])
    assert n == 0
    rows = monitor.load_json(path, None)
    assert len(rows) == 1  # no row added


def test_update_institutions_noop_does_not_rewrite_file(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row()])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)
    before = path.read_bytes()

    # No accepted items, and an unmatched/older item: nothing should change.
    assert monitor.update_institutions([]) == 0
    assert monitor.update_institutions([{"institution_normalized": "Vanguard",
                                         "date": "2026-09-09"}]) == 0
    assert monitor.update_institutions([{"institution_normalized": "BlackRock",
                                         "date": "2026-01-01", "why_it_matters": "old",
                                         "url": "u"}]) == 0  # older than 2026-01-01? equal -> skip
    assert path.read_bytes() == before  # byte-for-byte unchanged, no churn


def test_update_institutions_writes_only_on_change(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row()])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)
    before = path.read_bytes()
    monitor.update_institutions([{"institution_normalized": "BlackRock",
                                  "why_it_matters": "newer", "date": "2026-12-31",
                                  "url": "newer-url"}])
    assert path.read_bytes() != before  # changed run rewrites the file
    assert monitor.load_json(path, None)[0]["latest_signal"] == "newer"


def test_update_institutions_same_row_newest_wins_counts_once(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [_row(latest_date="2026-01-01")])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)
    n = monitor.update_institutions([
        {"institution_normalized": "BlackRock", "why_it_matters": "mid",
         "date": "2026-03-01", "url": "mid"},
        {"institution_normalized": "BLK", "why_it_matters": "latest",
         "date": "2026-09-01", "url": "latest"},
        {"institution_normalized": "BlackRock", "why_it_matters": "stale",
         "date": "2026-02-01", "url": "stale"},
    ])
    assert n == 1  # one row, counted once
    out = monitor.load_json(path, None)[0]
    assert out["latest_date"] == "2026-09-01"   # newest of the batch wins
    assert out["latest_signal"] == "latest"


def test_update_institutions_multiple_rows(tmp_path, monkeypatch):
    path = tmp_path / "institutions.json"
    monitor.save_json(path, [
        _row(name="BlackRock", aliases=["BlackRock", "BLK"], latest_date=""),
        _row(name="Vanguard", aliases=["Vanguard", "VG"], latest_date=""),
    ])
    monkeypatch.setattr(monitor, "INSTITUTIONS_PATH", path)
    n = monitor.update_institutions([
        {"institution_normalized": "blk", "why_it_matters": "a", "date": "2026-01-01", "url": "a"},
        {"institution_normalized": "vanguard", "why_it_matters": "b", "date": "2026-01-02", "url": "b"},
    ])
    assert n == 2


# --- save_json: UTF-8 fidelity --------------------------------------------

def test_save_json_keeps_non_ascii_raw(tmp_path):
    path = tmp_path / "x.json"
    monitor.save_json(path, [{"text": "preconditions — £390B, café"}])
    raw = path.read_text(encoding="utf-8")
    assert "—" in raw and "£" in raw and "café" in raw  # not \uXXXX-escaped
    assert "\\u" not in raw
    assert monitor.load_json(path, None) == [{"text": "preconditions — £390B, café"}]
