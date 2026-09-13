"""The release version is written in four places; they must agree.

pyproject.toml and package.json are what the tooling reads. CITATION.cff and
.zenodo.json are what a citation and the Zenodo record carry. A release that
bumps one and not the others is drift a reader cannot see.
"""

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def _first(pattern, name):
    m = re.search(pattern, _read(name), re.MULTILINE)
    assert m, f"no version line in {name}"
    return m.group(1)


def test_versions_agree():
    versions = {
        "pyproject.toml": _first(r'^version = "([^"]+)"$', "pyproject.toml"),
        "package.json": json.loads(_read("package.json"))["version"],
        "CITATION.cff": _first(r'^version: "?([^"\s]+)"?$', "CITATION.cff"),
        ".zenodo.json": json.loads(_read(".zenodo.json"))["version"],
    }
    assert len(set(versions.values())) == 1, versions
    assert all(SEMVER.match(v) for v in versions.values()), versions


def test_citation_release_date_is_iso():
    # CFF requires YYYY-MM-DD; a bare "2026-9-12" or a free-text date breaks
    # the citation widget silently.
    released = _first(r'^date-released: "?(\S+?)"?$', "CITATION.cff")
    assert date.fromisoformat(released).isoformat() == released
