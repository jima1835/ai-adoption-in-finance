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
        professional working in institutional asset management, as independent
        research outside of work.
      </p>

      <section>
        <h3 className="prose-h2">Independence</h3>
        <p>
          <strong>(a) Independent research.</strong> This project (the
          “Project”) is an independent, open-source, non-commercial research
          project by its author, Jiajun Ma (the “Author”), carried out in the
          Author’s individual capacity. The Author is the sole author and owner
          of its corpus and methodology.
        </p>
        <p>
          <strong>(b) No institutional affiliation.</strong> The Project is not
          affiliated with, sponsored by, or funded by any employer or other
          institution, and it does not represent the views or positions of any
          employer or institution. Every view and classification in it is the
          Author’s alone.
        </p>
        <p>
          <strong>(c) Not a business or a service.</strong> The Project is not
          operated as a business or a service and has not been carried out for
          or on behalf of any employer or client. To date it has generated no
          revenue, has charged no fees, carried no advertising, accepted no
          sponsorship and sold no access, and the Author has received no
          compensation in connection with it.
        </p>
        <p>
          <strong>(d) Open licences.</strong> The code is licensed under the MIT
          License and the data under CC BY 4.0. Use of either by others is
          governed by those licences alone; the Project charges nothing for such
          use, and the Author has derived no revenue or compensation from it.
        </p>
        <p>
          <strong>(e) Public sources only.</strong> No non-public information
          from the Author’s professional work informs any classification, and
          institutions with which the Author has a professional affiliation are
          excluded from coverage entirely. The Project was built without the use
          of any employer’s resources or working time.
        </p>
        <p>
          <strong>(f) No advice.</strong> Nothing in the Project constitutes
          investment, legal or other professional advice.
        </p>
        <p className="prose-note">
          Statement current as of 27 September 2026. It is updated whenever any
          fact in it changes.
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
        <h3 className="prose-h2">Corrections and contact</h3>
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
        <p>
          For questions and inquiries, please contact{' '}
          <span className="contact-address">
            info[at]ai-adoption-in-finance.org
          </span>
          .
        </p>
      </section>
    </article>
  )
}
