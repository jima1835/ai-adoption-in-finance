# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Corpus counts and
agreement figures are those of the release they sit under, not industry rates.

## [Unreleased]

## [1.1.0] - 2026-09-19

### Added
- **The AI-leadership roles record** ([METHODOLOGY §11](METHODOLOGY.md)) — a
  second record on a different unit of observation: the dated, publicly sourced
  *role event* (`created`, `hired`, `retitled`, `departed`, `expanded_remit`).
  It ships **published and empty**: the schema, the review gate, the collection
  sweep and the rules are all in place before any data is, so the first record
  enters against rules written in advance rather than rules fitted to it. A test
  enforces the emptiness.
  - A role event **never touches an adoption `stage`**, in either direction — a
    hire is an input to adoption, not evidence of it. A test enforces that too.
  - **Nothing LinkedIn-derived** enters the pipeline at any point: not as
    evidence, not as corroboration, not as a search surface. A person is named
    only from a firm press release, a firm leadership page, a regulatory filing
    or an accepted outlet; `person: null` is a complete record.
  - **A retitle is not a new role**, and no compensation or job-posting data is
    collected.
  - `data/roles_not_found.jsonl` publishes institutions searched with no
    qualifying result, so a firm searched and found empty is distinguishable
    from one nobody looked at. `data/excluded.json` is a recusal list and
    implies nothing about the institutions on it.
  - `monitor.py --roles` only *proposes*, into an untracked local queue;
    `tools/review.py --roles` is the sole writer of the two JSONL files.
- `schemas/` — a JSON Schema for each public data file, and
  `tools/validate_data.py` to check every one of them.
- [SOURCES.md](SOURCES.md) — the source tiers (T1/T2/T3) the not-classified
  appendix refers to, defined for the first time, with the tier floor (two
  independent T2-or-better sources; never T3 alone) and the ruling that a
  vendor's own announcement is T1 for that event without thereby being
  sufficient to classify. Tiers are criteria, not a roster of named outlets.
  METHODOLOGY §2 remains the classification bar.
- A roles view on the dashboard, and `prompts/roles_screen.md`.
- `.claude/settings.json` — the agent-harness rules that keep the drafting agent
  from publishing are now tracked, so they have a history and can be inspected:
  deny rules for `git commit`, `git push`, `gh` and the rest, and a network
  sandbox whose allowlist excludes the remote. They were previously only in the
  gitignored `settings.local.json`, which is unchanged. The commit rule matches
  the literal command only; the push block also holds at the network layer.

### Changed
- Wording: anchored agreement is no longer described as an "upper bound". The
  direction of the difference between anchored and independent agreement was
  never measured, so the claim is withdrawn (raised in peer review of the
  September 2026 paper). README, METHODOLOGY §6 and §11, the `_readme` and
  `limitation` strings in `data/agreement.json` (via `tools/build_agreement.py`),
  the dashboard's agreement panel, `.zenodo.json` and code comments now say
  "anchored, non-independent agreement" that "should not be read as an
  inter-rater reliability estimate". No figure changed.
- The corpus freeze (`tests/test_frozen_corpus.py`) pins `data/agreement.json` on
  its figures instead of its bytes: every key except the prose `_readme` and
  `limitation`. The file is derived and the blind re-code reads its counts, not
  its caveat wording, so a whole-file digest went red on a rewording in which no
  figure moved. The pinned digest is the one computed at the v1.0.3 tag and is
  byte-identical after the rewording — the narrowing re-froze nothing, and a
  changed figure still fails the suite. `not_classified.json` and
  `transitions.jsonl` keep their whole-file pins.

### Fixed
- The GIC row carried an undocumented `as_of_latest_signal` key, deferred from
  1.0.3 as "left for a data release". It is removed. The strict xfail that held
  it in `tests/test_schemas.py` is retired with it, and `tools/validate_data.py`
  now reports every data file valid. No stage, confidence, review date, rationale
  or evidence changed on any row — the frozen re-code corpus hashes identically.
- The release version is carried in six files, not the four `tests/test_version.py`
  checks: `package-lock.json` (root and `packages[""]`) and `uv.lock` also hold it,
  and `npm ci` / `uv sync` leave them dirty in CI when they drift. All six are
  aligned at this release.

## [1.0.3] - 2026-09-12

Patch release: tooling, CI and presentation only. No rows added, no stage,
confidence, review date or evidence changed.

### Added
- CI runs the pytest suite on Windows as well as Linux, so the portability fix
  from [#3] by Haochen Jiang ([@incisors]) stays covered, and a `build` job runs the JavaScript
  linters and `npm run build`. Still no cron, secrets, deploy or auto-commit.
- Linting: ruff (`E`, `F`, `I`, `UP`; line length 100) for the Python engine,
  tools and tests; ESLint 9 flat config and Prettier for `src/`, exposed as
  `npm run lint` and `npm run format:check`. Only what the linters flagged was
  changed.
- `tests/test_schemas.py` checks every row of `data/institutions.json` and
  `data/not_classified.json` against the key allowlist in CONTRIBUTING and the
  documented vocabularies. One known deviation is recorded as a strict expected
  failure rather than fixed here: the GIC row carries an undocumented
  `as_of_latest_signal` key, left for a data release.
- `tests/test_version.py` asserts pyproject.toml, package.json, CITATION.cff and
  .zenodo.json carry the same version.
- Dashboard legend states how many rows the news monitor has matched
  ("monitoring covers N of M rows"), computed from non-empty `latest_date`, so
  the ⚡ date is not read as a pipeline signal on rows where it is the newest
  curated event.
- This changelog, and a **Contributors** section in the README crediting
  Haochen Jiang ([@incisors]) for the Windows portability work in [#3].

### Changed
- README: the project tree lists `tools/` (public since 1.0.2) and this
  changelog, "Running it" lists the lint commands CI enforces, and the tech-stack
  line says the suite runs on Linux and Windows.
- Version aligned to 1.0.3 in pyproject.toml, package.json (both had stayed at
  0.1.0), CITATION.cff (now with `date-released`) and .zenodo.json.

### Fixed
- The review tool writes `data/institutions.json`, `data/not_classified.json`
  and `data/transitions.jsonl` as UTF-8 with LF line endings on every platform,
  finishing the Windows work Haochen Jiang ([@incisors]) started in [#3] for
  `monitor.py`.
- A row's `footnote` — the scope call, what was seen but not counted toward the
  stage — is documented in CONTRIBUTING as shown in the drill-down but was not
  rendered. It now appears as a scope note under "Why this stage".

## [1.0.2] - 2026-09-08

Data patch. No new rows, no stage changes.

### Added
- The negative record's sixth withdrawn row: IMC Trading (hedge fund, Europe),
  pulled on review on 2026-08-31, filed so the published record matches a
  September 2026 paper's disclosure of it.
- The review tool (`tools/review.py`, `tools/review.html`) and the agreement
  builder (`tools/build_agreement.py`) published under MIT.
- Review guard: changing the stage of an already-reviewed row requires the
  evidence date and URL and writes a `data/transitions.jsonl` record
  (`tests/test_review.py`).

### Changed
- `data/agreement.json` rebuilt: 6 withdrawals; proposals accepted as-is
  69/80 (86.25%); stage agreement 69/74 (93.2%) unchanged.
- Public-field lint: internal notes and source-tier codes removed from row
  footnotes and rationales; no stage, confidence, review date or evidence
  changed.

## [1.0.1] - 2026-09-02

Citation and licensing metadata for the Zenodo record: `.zenodo.json` and
`CITATION.cff` (concept DOI 10.5281/zenodo.22247885), CC BY 4.0 for `data/`
and MIT for code, CONTRIBUTING aligned with the agent-drafts / human-verifies
protocol, and an empty `data/transitions.jsonl` to be filled prospectively.

## [1.0.0] - 2026-09-01

First release: 84 human-verified institutions across four adoption stages, the
assessed-but-not-classified appendix, and the published human-vs-agent
disagreement record (`data/agreement.json`).

[Unreleased]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jima1835/ai-adoption-in-finance/releases/tag/v1.0.1
[1.0.0]: https://github.com/jima1835/ai-adoption-in-finance/commit/12f7345
[#3]: https://github.com/jima1835/ai-adoption-in-finance/pull/3
[@incisors]: https://github.com/incisors
