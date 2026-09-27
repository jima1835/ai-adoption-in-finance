const BUILD = typeof __SITE_BUILD__ !== 'undefined' ? __SITE_BUILD__ : null

// One row per tagged release: the version, its date and a 30–50-word account
// of what mattered in it, written by hand. CHANGELOG.md in the repository is
// the full record; this page summarises it and is updated alongside it.
const RELEASES = [
  {
    version: '1.2.0',
    date: '2026-09-27',
    notes:
      'Corpus at 111 reviewed institutions. The methodology is halved and opens with a TL;DR; the agreement record now measures the first review. Every timeline event gets a short digest and job postings appear as roles. Release and About pages added; the unpopulated roles module is withdrawn.',
  },
  {
    version: '1.1.0',
    date: '2026-09-19',
    notes:
      'Adds the AI-leadership roles record, a second dataset of dated role events shipped published and empty with its rules written in advance; JSON Schemas and a validator for every public data file; and SOURCES.md, which defines the source tiers. Anchored agreement is no longer called an upper bound.',
  },
  {
    version: '1.0.3',
    date: '2026-09-12',
    notes:
      'Tooling and CI only: the test suite runs on Windows as well as Linux, ruff and ESLint enforce style, and schema and version tests are added. The review tool writes UTF-8 with LF endings on every platform, and footnotes now render in the drill-down. No row or stage changed.',
  },
  {
    version: '1.0.2',
    date: '2026-09-08',
    notes:
      'Data patch: IMC Trading is filed as the sixth withdrawn row, the review tool and the agreement builder are published under MIT, and a review guard requires an evidence date and URL before any stage change. Internal notes were removed from public fields; no stage moved.',
  },
  {
    version: '1.0.1',
    date: '2026-09-02',
    notes:
      'Citation and licensing metadata for the Zenodo record: CITATION.cff and .zenodo.json carrying the concept DOI, CC BY 4.0 for the data and MIT for the code, CONTRIBUTING aligned with the agent-drafts, human-verifies protocol, and an empty stage-transition log to be filled prospectively.',
  },
  {
    version: '1.0.0',
    date: '2026-09-01',
    notes:
      'First release: 84 human-verified institutions placed on four adoption stages from public sources only, each with a written rationale and a dated timeline; the assessed-but-not-classified appendix; and the published human-versus-agent disagreement record.',
  },
]

export default function Releases() {
  return (
    <article className="prose">
      <h2 className="prose-h1">Release history</h2>
      <p className="prose-lede">
        One line per release, newest first: what mattered in it. Counts and
        agreement figures describe the corpus as it stood, never an industry.
      </p>
      {BUILD && BUILD.built && (
        <p className="agree-note release-build">
          This site was built on <strong>{BUILD.built}</strong>
          {BUILD.commit && (
            <>
              {' '}
              from commit <code>{BUILD.commit}</code>
              {BUILD.commitDate ? ` of ${BUILD.commitDate}` : ''}
            </>
          )}
          . The build is committed with the changes it carries, so the newest
          release below is the one this build belongs to.
        </p>
      )}
      <div
        className="table-wrap"
        tabIndex={0}
        role="region"
        aria-label="Release history, scrollable table"
      >
        <table className="inst-table release-table">
          <thead>
            <tr>
              <th scope="col">Version</th>
              <th scope="col">Date</th>
              <th scope="col">What changed</th>
            </tr>
          </thead>
          <tbody>
            {RELEASES.map((r) => (
              <tr key={r.version}>
                <th scope="row" className="td-name release-version">
                  v{r.version}
                </th>
                <td className="td-num td-muted">{r.date}</td>
                <td className="release-notes">{r.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="agree-note">
        The full record of every addition, change, fix and withdrawal is{' '}
        <a
          href="https://github.com/jima1835/ai-adoption-in-finance/blob/main/CHANGELOG.md"
          target="_blank"
          rel="noreferrer"
        >
          CHANGELOG.md
        </a>
        . Tagged releases are archived with a DOI; see the README.
      </p>
    </article>
  )
}
