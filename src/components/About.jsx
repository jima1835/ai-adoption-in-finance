// About the author — its own page, parallel to the dashboard and the
// methodology. Everything here is already public in the repository (README,
// LICENSE, the comments/ folder); the page adds no new claim about the author.
const REPO = 'https://github.com/jima1835/ai-adoption-in-finance'

const COMMENTS = [
  {
    date: '2026-09-19',
    title:
      'Comment on NIST AI 200-2 ipd, The TEVV-Athlon Framework for Evaluating AI Systems',
    text: 'Proposes a minimum reporting summary for §2.4 — which Blocks went unmeasured, what human judges were shown before judging, and the evaluator’s relationship to the developer — and a declared adoption stage for §2.1, offering this corpus’s four-stage classification as the scale.',
    pdf: `${REPO}/blob/main/comments/2026-09-19_NIST_AI_200-2_ipd_comment_Jiajun_Ma.pdf`,
    doi: 'https://doi.org/10.5281/zenodo.22853598',
  },
  {
    date: '2026-09-10',
    title:
      'Comment on NIST AI 300-1 ipd, Guidance and Templates for Public-Facing AI Documentation',
    text: 'Proposes Annex A subfields 1.3.2.1 Production Method and 8.2.1.1 Verification Condition and a typed-absence convention, using this corpus’s provenance record as the worked example.',
    pdf: `${REPO}/blob/main/comments/2026-09-10_NIST_AI_300-1_ipd_comment_Jiajun_Ma.pdf`,
    doi: 'https://doi.org/10.5281/zenodo.22701607',
  },
  {
    date: '2026-07-22',
    title:
      'Response to the FSB consultation, Sound Practices for Responsible Adoption of AI',
    text: 'Published by the Financial Stability Board with the other responses.',
    pdf: 'https://www.fsb.org/uploads/Jiajun-M-independent-response.pdf',
    label: 'fsb.org',
    doi: null,
  },
]

export default function About() {
  return (
    <article className="prose">
      <h2 className="prose-h1">About the author</h2>
      <p className="prose-lede">
        Built and maintained by <strong>Jiajun Ma</strong>, an investment
        professional working in institutional asset management.
      </p>

      <section>
        <h3 className="prose-h2">Independence</h3>
        <p>
          This is an independent personal project, produced entirely in the
          author’s personal capacity. It is not affiliated with, sponsored by,
          or endorsed by any employer or institution, and every view and
          classification here is the author’s alone.
        </p>
        <p>
          Consistent with the public-sources-only rule of the methodology, no
          non-public information from the author’s professional work informs any
          classification, and institutions where the author has a professional
          affiliation are excluded from coverage entirely. Nothing on this site
          is investment advice.
        </p>
        <p>
          The corpus and its methodology are the author’s; the code is not only
          his. Rows are drafted by an AI research agent under fixed sourcing
          rules and verified by the author before they publish, and the rate at
          which the two disagree is published with the data rather than
          asserted.
        </p>
      </section>

      <section>
        <h3 className="prose-h2">Public comments and submissions</h3>
        <p>
          Where this corpus has been offered as evidence or as a worked example
          in a public consultation.
        </p>
        <ul className="prose-list">
          {COMMENTS.map((c) => (
            <li key={c.date}>
              <strong>{c.date}</strong> — <em>{c.title}</em>. {c.text}{' '}
              <a href={c.pdf} target="_blank" rel="noreferrer">
                {c.label || 'PDF'}
              </a>
              {c.doi && (
                <>
                  {' '}
                  ·{' '}
                  <a href={c.doi} target="_blank" rel="noreferrer">
                    DOI
                  </a>
                </>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="prose-h2">Corrections</h3>
        <p>
          Corrections and challenges are welcome —{' '}
          <a href={`${REPO}/issues`} target="_blank" rel="noreferrer">
            open an issue
          </a>{' '}
          with the public sources you think change the call. The source, the
          data and every release are on{' '}
          <a href={REPO} target="_blank" rel="noreferrer">
            GitHub
          </a>
          .
        </p>
      </section>
    </article>
  )
}
