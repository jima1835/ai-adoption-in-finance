# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Corpus counts and
agreement figures are those of the release they sit under, not industry rates.

## [Unreleased]

## [1.2.3] - 2026-10-29

Data-record patch. No row, stage, confidence, rationale or event changed; the corpus
stands as at v1.2.0 (111 human-reviewed institutions). The re-code freeze is still not
declared.

### Added
- **`data/first_review.jsonl`: the first review, row by row.** For all 111 rows: when
  the row was first reviewed, the agent prompt version in force, how the row
  originated, and — for stage and for confidence — what the agent proposed and what
  the reviewer set at first review. Every value names its source: the review tool's
  decision log, the intake dossier, the current value where no later change was
  logged, a logged later change that was undone, or (for two rows) the reviewer's
  contemporaneous audit note. Nine rows that originated with the reviewer have no
  logged first review.
  - **Stage.** Revised up on 4 rows and down on 1 at first review.
  - **Confidence.** Recoverable for 101 rows. Raised on 31, lowered on none, unchanged
    on 70. The raise rate ran between 0% and 36% in six review sessions and was 56%
    (9 of 16) on 2026-09-24, under the same agent prompt (v3.6, in force from
    2026-09-01 to 2026-09-26). Since first review the field has been lowered on 19 of
    these rows and raised on none, all between the v1.1.0 (2026-09-19) and v1.2.0
    (2026-09-27) releases, the window of the 2026-09-26 pre-freeze audit; 13 of them
    are among the 15 confidence moves the v1.2.0 notes report. Each of the 19 was a
    first-review raise, returned to exactly the agent's proposal; 12 of the 31 raises
    stand.
  - Like the stage figures these are anchored: the reviewer saw the proposal.
    Confidence rates the public evidence for a stage, not the accuracy of a label.
- **`data/prompt_versions.jsonl`: agent prompt versions.** Twelve versions of the
  research agent's standing prompt (v1, 2026-08-25, to v3.8, 2026-09-26), each with its
  effective time, a short label and the SHA-256 of the private prompt file as of that version (none
  for v2, which has no surviving snapshot). The text stays private; the digests let it
  be verified if it is released.
- **`CODEBOOK_HISTORY.md`: how the bar changed.** 38 substantive changes to the stage
  definitions, decision rules, source tiers and scope, in 8 commits from 2026-06-07 to
  2026-09-27, each dated against the review sessions. 14 came before the first review,
  17 while rows were being first reviewed and 7 after the last. Among them:
  - The single-use-case route to `scaling` ("A single production use case that makes
    live investment decisions with material capital counts as scaling") was added at
    22:17 on 2026-08-25, 32 minutes after the first approval (AQR Capital Management,
    `scaling`) and before the next three `scaling` approvals that evening.
  - The first written evidence floor (two independent T2-or-better sources) arrived on
    2026-09-19, three weeks into review. On 2026-09-27, after the last first review,
    it became two dated events, each from a T2-or-better source, with independent
    corroboration sought rather than required, and the one-voice rule capped a
    single-voice row at `med` — the day after the 2026-09-26 pre-freeze audit.
  - "Pick the lower", "plans are not stages", the evidence-absence cap and the three
    conditions of the `embedded` bar are unchanged since first stated.
- **Two blocks in `data/agreement.json`**, built from `first_review.jsonl`:
  `confidence` (first-review counts, the proposed × first-review matrix, counts by
  review date, moves since first review, value sources) and `first_review_sessions`
  (per review date: rows, stage and confidence proposals, revisions up and down, and
  the prompt versions in force).
- **The review tool logs what the record lacked.** From this release `tools/review.py`
  writes, on every approval, the confidence the agent proposed, the confidence the
  reviewer set, and the proposal's `agent_model` and `prompt_version` stamp (`null`
  when the proposal carries none). Earlier log entries are unchanged.
- Schemas, validator coverage and tests for both data files and the new log fields.

### Changed
- **The empty `embedded` column is described as the record shows it.** METHODOLOGY §3,
  `data/stage_definitions.json` and the dashboard's fallback note said that NBIM, CPP
  Investments, BlackRock and GIC each "independently and publicly" state they keep humans
  in control of decisions. The rows support that in the firm's own terms for NBIM only. The
  text now says what each row records — NBIM, human oversight of investment decisions is
  non-negotiable; CPP Investments, humans frame and verify every output; BlackRock, the
  AI-default workflow "isn't quite here yet"; GIC, its virtual investment-committee member
  evaluates and challenges proposals — and that an empty column is weak evidence about
  what happens inside an institution, because the markers are rarely disclosed. The stage
  bars are unchanged.
- `agreement.json`'s `matrix_note` describes the v1.2.2 placement of corrected-back rows.
- METHODOLOGY §6, the README, CONTRIBUTING and CLAUDE.md name the new files. CLAUDE.md
  now requires that any edit changing the bar add a dated row to `CODEBOOK_HISTORY.md`
  in the same commit.

## [1.2.2] - 2026-10-27

Data-record patch. No row, stage, confidence, rationale or event changed; the corpus
stands as at v1.2.0 (111 human-reviewed institutions). The re-code freeze is still not
declared.

### Added
- **`data/rereads.jsonl`, the re-read record.** One record per re-read pass — a
  re-check of reviewed rows against the evidence already on them — with its scope, the
  direction it checked, who drafted the change cards and every decision. Filed by the
  reviewer; agents never write it; its moves are corrections, never transitions. A
  schema (`schemas/rereads.schema.json`) and validator coverage come with it.
- **The first record: the skeptic re-read of 2026-09-24.** Scope: the 34 rows at
  `scaling` when the pass began, as reconstructed by the reviewer from the review tool's
  decision log (no public file holds a snapshot between 2026-09-20 and 2026-09-27).
  Direction checked: down only, under METHODOLOGY §4 ("when between two stages, pick the
  lower") — a row could be held or moved lower; no row was checked for an upward move.
  The research agent drafted 11 change cards: seven proposed `piloting`, four proposed
  holding at `scaling` with other edits. The reviewer approved nine and rejected two
  (CSOP Asset Management, EQT). Five rows moved `scaling` → `piloting`, the moves
  already disclosed under 1.2.0; 23 rows in scope had no card.

### Changed
- **`data/agreement.json` places every first-review revision.** Daiwa Asset Management,
  E Fund Management and Quilter were revised `piloting` → `scaling` at first review, as
  `agreement.json` published from 1.0.2 through 1.1.0, and restored to the proposal on
  the 2026-09-24 re-read. The record now says so under `revisions[].later` instead of
  marking the first-review stage undetermined. The 1.2.0 note that this stage was "no
  longer in the public record" was wrong: it had been in every release since 1.0.2. A
  new `rereads` block summarises each pass. The rates do not move — stage agreement
  95/100 and proposals accepted as-is 95/106 at first review, current label 96/100, all
  anchored — while the matrix's `piloting` → `scaling` cell goes from 1 to 4 and
  `first_review_stage_undetermined` from 3 to 0.
- `CITATION.cff` and `.zenodo.json` describe the corpus as human-*reviewed*, the word the
  methodology and the changelog already use; the Zenodo keyword "inter-rater agreement"
  becomes "human-AI agreement (anchored)", as in `CITATION.cff` since 23cfddb, because
  the figures are not inter-rater agreement. The v1.2.1 version DOI leaves
  `CITATION.cff`; this release's DOI is added once Zenodo mints it.
- METHODOLOGY §6, the README data table, CONTRIBUTING and CLAUDE.md name the re-read
  record. The agent harness (`.claude/settings.json`) denies agents writes to the
  reviewer-only data files.

### Fixed
- The README's link text for the NIST AI 200-2 comment DOI carried a stray "N".

## [1.2.1] - 2026-09-27

Site and documentation patch. No row, stage or methodology change; the corpus stands
as at v1.2.0 (111 human-reviewed institutions).

### Added
- `robots.txt` on the site asks crawlers that collect pages to train AI models not
  to, while leaving search indexing and per-question assistant reads open, and
  `AGENTS.md` tells automated readers of the repository to take the licensed data
  files instead of scraping pages, cite the corpus, and send people to the live site.
- A contact address for questions and inquiries, written with a deliberate
  `[at]`, on the About page, in the site footer and in the README.

### Changed
- The dashboard moved to its own domain, <https://ai-adoption-in-finance.org/>: the
  site now builds at the root path with a `CNAME`, a canonical link and `og:url`
  tag, and the README and `CITATION.cff` point at the new address.
- The independence statement is now one dated, lettered text, identical in the
  README, on the About page and in the Zenodo record, with a one-line summary in
  the footer: an independent, open-source, non-commercial research project in the
  author's individual capacity, of whose corpus and methodology the author is the
  sole author and owner; not affiliated with, sponsored by or funded by any
  employer or institution, and representing no institution's views; not a
  business or a service, and not carried out for any employer or client; to date
  no revenue and no compensation; built without any employer's resources or
  working time; open licences govern reuse by others, from which the author has
  derived nothing. The word "endorsed" is gone — an expert's letter about the
  work is an endorsement, and the statement should not read as denying one.

### Fixed
- Expanding one stage column stretched the five preview cards in every other
  column to the expanded column's height. Columns are now equal only while all
  are collapsed; opening one leaves the others exactly as they were. Every
  collapsed column divides its card area into five equal slots — an embedded
  column with one firm, or a filter that leaves two, uses the same slots — and
  every column renders the same parts (preview line, sort toggles, show-all
  button, hidden where they do not apply) so the heights match by construction.
- The review tool reported an intake dossier's path with the host's separator, so
  the Windows leg of the test suite failed on the v1.2.0 commit; the path is now
  written with forward slashes on every platform.

## [1.2.0] - 2026-09-27

Corpus at this release: 111 human-reviewed institutions, 398 dated events, 19
assessed-but-not-classified entries; stage agreement 95/100 at first review,
proposals accepted as-is 95/106. All figures describe this corpus, not an industry.

### Added
- **27 institutions, 84 → 111**, every one human-reviewed: 13 asset managers, 9
  pensions and 5 endowments (14 US, 5 Europe, 4 Canada, 2 Asia, 2 Australia);
  16 placed at piloting, 6 at exploring, 5 at scaling — Amova (formerly Nikko),
  AustralianSuper, Aware Super, BNP Paribas AM, Blackstone, CDPQ, Capital Group,
  Carlyle, Gates Foundation, GitLab Foundation, Hamilton Lane, Houston Endowment,
  IMCO, KKR, Morgan Stanley IM, Nest, Neuberger, Northern Trust AM, Nuveen,
  Ontario Teachers', PSP Investments, Partners Group, Texas TRS, Tokio Marine AM,
  USS, UTIMCO and the Wellcome Trust. Dated events 276 → 398. Three more
  assessed-but-not-classified entries (Harvard Management Company, PRINCO, the
  Hewlett Foundation), 16 → 19.
- **Release history and About pages** on the site (`#/releases`, `#/about`),
  alongside the dashboard and the methodology. The release page is a table with
  one short account of each release; this file remains the full record. The
  author note moved out of the methodology page into its own, which also lists
  the public comments and submissions, the FSB consultation response among them.
- **Per-event timeline digests.** Every dated event in a drill-down now opens with
  a title of at most twelve words and one or two bullets, the full source note one
  disclosure below (`data/event_summaries.json`, `src/timeline.js`). A digest is
  keyed on the exact event text, so an edited event falls back to its full note
  until it is re-digested, and a test holds one digest per event.
- **Requisition events rendered as postings** (`data/job_postings.json`): the
  eight job-posting citations show the role and its AI wording in their own
  section of the drill-down instead of as timeline entries. Rationale summaries
  carry an evidence label per bullet, and a homepage link says whether it was
  derived from a reviewed evidence URL.

### Changed
- **METHODOLOGY.md is about half its former length** and opens with a short
  TL;DR. Section numbers, the four stage definitions (§3) and the decision rules
  (§4) are unchanged word for word; the prose around them was compressed and the
  corpus-lifecycle passage brought up to date.
- **The agreement panel is withdrawn from the methodology page.** A
  proposed-versus-final matrix that is nearly all diagonal reads as if the
  reviewer changed two rows, when the record holds revisions, later corrections,
  an evidence-dated transition, withdrawals and confidence re-tags. The page now
  describes the protocol and links `data/agreement.json`, where every
  intervention is named; no agreement figure is rendered on the site.
- **Six stage moves against 1.1.0, all disclosed.** Five are corrections from a
  skeptic re-read of the scaling rows against §4 on 2026-09-24 — Daiwa Asset
  Management, E Fund Management, Quilter, State Street Investment Management
  (SSGA) and Vanguard, each scaling → piloting on the evidence already on the
  row, so none entered `data/transitions.jsonl`; they are logged in the decision
  record and, where an agent proposal exists, in `data/agreement.json`. One is a
  transition on new evidence: Fullgoal Fund Management, exploring → piloting,
  effective 2026-09-06, the first record in `data/transitions.jsonl`. The
  confidence field moved on 15 rows, all downward (14 high → med, Investcorp
  high → low): three under the one-voice rule below, the rest where the field
  disagreed with the row's own confidence sentence. Stage agreement 69/74 →
  95/100 and proposals accepted as-is 69/80 → 95/106, both anchored.
- **Pre-freeze consistency audit (2026-09-26).** The confidence field was re-read
  against each row's own confidence sentence (the moves are counted above); GIC
  gained its FY2025/26
  report (an enterprise AI platform, an AI research assistant and a virtual
  investment-committee member, in the fund's own voice); Citadel is re-sourced to
  Reuters' original interview and its AUM updated from it; four footnotes were
  cleared of pipeline language; key order was normalised on every row. No stage
  moved.
- **The agreement record measures the first review.** `stage_agreement` in
  `data/agreement.json` is now read from `label_provenance`, which review.py sets
  once when a human first rules on the agent's proposal, instead of comparing the
  proposal with the row's stage today. The old comparison let a later correction
  that happened to restore the proposal count as agreement and let an evidence-dated
  transition count as disagreement. The record now lists those later changes under
  `since_first_review`, reports the proposal-versus-today figure as `current_label`,
  and marks a revision whose first-review stage is no longer in the public record as
  such rather than inventing a direction. The dashboard's panel renders that case.
- **What counts as a second publisher.** SOURCES.md §1 now states the test the
  reviewer applied on 2026-09-26: a publisher is independent when it reports a fact
  it established itself; several staff-written outlets that each carry the firm's
  own account, however independent of one another, are that one voice and hold the
  row at `med`. Three rows previously lifted to `high` on a count of outlets
  (Bosera, Fullgoal, China Europe) were re-tagged `med` under it; rows whose second
  publisher reported a fact of its own (Amundi, Franklin Templeton) keep `high`.
- **Own-voice evidence is admitted on the reviewer's corroboration, not held for
  a second publisher.** SOURCES.md §1 and METHODOLOGY §5.2 now say what the corpus
  has practised since its first own-domain rows (ADIA, ATP, EQT, Ilmarinen,
  Investcorp, Lynx, Optiver) and applied again to USS: a row whose every source is
  the institution's annual report, board material or filing is publishable at
  `med` or below once a person has opened each document and confirmed it is a
  governance or operational disclosure rather than a pitch to investors, a
  sponsored piece or an advertisement. Two independent publishers lift confidence
  to `high`; they were never a condition of publishing.
- **A reviewed row is re-queued by evidence, not by the calendar.** The reviewer
  used to card every row whose last human review was 30+ days old as "re-review
  due", so a batch approved on one night came back as a batch a month later
  regardless of whether anything had happened. That is rework without new evidence
  and a recipe for review fatigue. The queue now holds never-reviewed rows only; a
  reviewed row comes back for a ruling solely through the sweep-proposals panel,
  when a news pass has staged a proposal against it. The 30-day clock survives only
  in the local dispatcher that decides which rows get that news pass.
- **The blind-review freeze is declared, not inferred.** It used to switch on the
  moment `institutions.json` reached 100 rows, which closed the corpus mid-session:
  the hundredth row had to be right before it could be approved, and a typo caught a
  minute later needed an unfreeze record to fix. `python3 tools/review.py --freeze`
  now writes `data/recode_freeze.json` and prints the four digests to pin, captured
  from one corpus at one moment. The milestone is still tracked — the reviewer shows
  a standing notice once the target is reached — but it prompts a person rather than
  closing the corpus on its own.
- **A correction no longer enters the transitions panel.** A queue entry marked
  `"correction": true` may move a stage without a `date_effective`, and appends
  nothing to `data/transitions.jsonl`. Re-reading evidence already on a row against
  the bar is not the sector moving; dating such a change with today, or with the date
  of evidence that did not trigger it, would put a transition in the panel that never
  happened. It is logged in the decision record instead.
- The corpus lifecycle is stated in METHODOLOGY §6: the expansion phase ran past
  its 100-row target to 111 rows, and the blind-review freeze is declared by the
  maintainer (above) rather than by the row count.

### Fixed
- The review tool's sweep card merged two events that shared a date and a source
  URL into one, which dropped one of IMCO's two 2025 annual-report events on
  approval; events are now de-duplicated on date, URL and text, and the lost event
  is restored.

### Removed
- **The AI-leadership roles module (v1.1.0, METHODOLOGY §11) is withdrawn from
  this release**: the roles page, the empty JSONL records, their schemas, the
  screener prompt and the `--roles` modes of the monitor and the review tool. It
  shipped unpopulated and is withdrawn unpopulated; it is preserved outside the
  public tree and will return in a later release with its rules unchanged.
  SOURCES.md §3, which served only that module, is withdrawn with it.

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
- `.gitattributes` pins `*.json` and `*.jsonl` to LF on checkout. The corpus freeze
  hashes `data/not_classified.json` byte for byte, and a Windows checkout with
  `core.autocrlf` rewrote it to CRLF, so the pin failed on the Windows CI job while
  passing on Linux. The tools already write LF on every platform (1.0.3); now the
  checkout matches. No file content changed.
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

[Unreleased]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.2.3...HEAD
[1.2.3]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/jima1835/ai-adoption-in-finance/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jima1835/ai-adoption-in-finance/releases/tag/v1.0.1
[1.0.0]: https://github.com/jima1835/ai-adoption-in-finance/commit/12f7345
[#3]: https://github.com/jima1835/ai-adoption-in-finance/pull/3
[@incisors]: https://github.com/incisors
