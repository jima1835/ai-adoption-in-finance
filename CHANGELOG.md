# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Corpus counts and
agreement figures are those of the release they sit under, not industry rates.

## [Unreleased]

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

[Unreleased]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jima1835/ai-adoption-in-finance/releases/tag/v1.0.1
[1.0.0]: https://github.com/jima1835/ai-adoption-in-finance/commit/12f7345
[#3]: https://github.com/jima1835/ai-adoption-in-finance/pull/3
[@incisors]: https://github.com/incisors
