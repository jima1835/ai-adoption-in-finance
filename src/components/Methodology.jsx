import { useEffect, useState } from 'react'
import {
  STAGES,
  STAGE_LABELS,
  TYPE_LABELS,
  OUTCOME_LABELS,
  stageDefinition,
  embeddedNote,
  scopeNote,
  loadNotClassified,
  loadAgreement,
} from '../data.js'
import AgreementPanel from './AgreementPanel.jsx'

// Prose page — allowed to breathe more than the dense grid. Pulls the shared
// stage-classification reference (stage_definitions.json) when available, and
// falls back to the built-in constants if it's missing.
export default function Methodology({ defs }) {
  const scope = scopeNote(defs)
  const [notClassified, setNotClassified] = useState([])
  const [agreement, setAgreement] = useState(null)

  useEffect(() => {
    let live = true
    loadNotClassified().then((d) => live && setNotClassified(d))
    loadAgreement().then((d) => live && setAgreement(d))
    return () => {
      live = false
    }
  }, [])

  return (
    <article className="prose">
      <h2 className="prose-h1">Methodology</h2>
      <p className="prose-lede">
        A public, sourced classification of AI adoption across institutional
        investors — pensions, sovereign-wealth funds, endowments, asset managers
        and hedge funds — organized by the stage each has actually reached, not
        the stage it markets.
      </p>

      <section>
        <h3 className="prose-h2">What this is</h3>
        <p>
          Most coverage of “AI in finance” collapses intent and execution into a
          single headline. This dashboard separates them. Every institution is
          placed in one of four stages based strictly on{' '}
          <strong>public evidence</strong> — news, official disclosures, board
          materials, position papers — and each placement carries a written
          rationale and a dated timeline back to its sources.
        </p>
        <p>
          It is deliberately narrow. It covers <strong>asset owners</strong> —
          pensions, sovereign-wealth funds, endowments — alongside managers, it
          publishes the institutions it assessed and could <em>not</em> place,
          and it shows its own error rate. Those three things are the point; the
          row count is not.
        </p>
      </section>

      <section>
        <h3 className="prose-h2">What we measure: operational adoption</h3>
        <p>
          The stage measures <strong>operational, internal AI adoption</strong> —
          how a firm uses AI inside its own investment process and operations.
          Two things that often get counted as “AI adoption” are deliberately{' '}
          <em>out of scope</em>: AI products a firm <strong>sells</strong> to
          clients, and AI as an <strong>investment thesis</strong> or portfolio
          holding. A firm can run a large AI business or hold every AI stock and
          still be early in how it operates internally — those are different
          questions, and this dashboard answers only the operational one.
        </p>
        {scope && <p className="prose-callout">{scope}</p>}
      </section>

      <section>
        <h3 className="prose-h2">How a row is built</h3>
        <p>
          Stated plainly, because the construction protocol is as much the
          contribution as the data: <strong>an AI research agent drafts every
          row and proposes a stage; a human verifies every row before it
          publishes.</strong> Neither half is decorative.
        </p>
        <ol className="prose-list">
          <li>
            <strong>The agent researches and drafts.</strong> It searches the
            public record, fetches every URL it intends to cite, writes the
            rationale and the dated timeline, and proposes an adoption stage. It
            works under fixed sourcing rules: public sources only, no
            encyclopedias, evidence dated 2023 or later, and no citation to a
            page that was not actually retrieved.
          </li>
          <li>
            <strong>A human verifies, row by row.</strong> The reviewer opens
            the draft against its sources in a local review tool and{' '}
            <em>accepts, revises, or removes</em> it. No row reaches this site
            without that pass, and the reviewer works from the cited evidence
            rather than re-researching the firm.
          </li>
          <li>
            <strong>The decision is recorded.</strong> Each row keeps the stage
            the agent proposed alongside the stage the human settled on, and
            whether the label was accepted, revised, or written by the human
            outright. That is what makes the disagreement record below possible
            — and auditable.
          </li>
        </ol>
        <p>
          Some fields are <strong>never</strong> written by an agent: the final{' '}
          <code>stage</code>, the review date, the provenance fields, the
          assessed-but-not-classified appendix, and the stage-transition log.
          Those are reviewer-only by construction, not by convention.
        </p>
        <p>
          Separately, a monitoring pass surfaces fresh public signals so each
          institution’s “latest signal” stays current. It is a{' '}
          <strong>notifier, not a classifier</strong>: it can put a possible
          re-classification in front of a person, and it can never move a stage
          itself.
        </p>
        <p className="prose-callout">
          The honest limitation: there is one reviewer, and he also wrote the
          classification rules. That is a real constraint on how far these
          labels should be trusted, and it is why the agreement figures below
          are published rather than asserted.
        </p>
      </section>

      <AgreementPanel data={agreement} />

      <section>
        <h3 className="prose-h2">The four stages</h3>
        <dl className="stage-defs">
          {STAGES.map((stage) => (
            <div key={stage} className="stage-def-row" data-stage={stage}>
              <dt>
                <span className="stage-swatch" data-stage={stage} />
                {STAGE_LABELS[stage]}
              </dt>
              <dd>{stageDefinition(defs, stage)}</dd>
            </div>
          ))}
        </dl>
        <p className="prose-note">
          <strong>Embedded is intentionally empty.</strong> {embeddedNote(defs)}
        </p>
      </section>

      <section>
        <h3 className="prose-h2">How this differs from the alternatives</h3>
        <p>
          A staged reading of AI adoption is not a new idea, and this project
          does not claim to have originated one. What follows is where it sits
          against the work that already exists.
        </p>
        <ul className="prose-list">
          <li>
            <strong>Commercial AI indices</strong> — chiefly the{' '}
            <a href="https://evidentinsights.com/" target="_blank" rel="noreferrer">
              Evident AI Index
            </a>
            , which ranks banks, insurers and payments firms on 60+ indicators
            and has announced an asset-management edition — score and rank large
            public <em>companies</em>. This is not a ranking and assigns no
            score: it places each institution on a stage, it covers{' '}
            <strong>asset owners</strong> that commercial benchmarks do not, and
            it publishes the assessments that failed.
          </li>
          <li>
            <strong>Staged self-assessment questionnaires</strong>, including the
            one shipped with the US financial-services AI risk framework
            published in 2026, ask a firm to place itself. This dashboard
            adapts the staged form for <em>external observation</em>: no
            institution is asked anything, and no institution can move its own
            row.
          </li>
          <li>
            <strong>Industry surveys</strong> report self-declared adoption in
            aggregate and anonymized. Every row here is named, dated and sourced,
            which makes it checkable and makes it wrong in public when it is
            wrong.
          </li>
        </ul>
      </section>

      <section>
        <h3 className="prose-h2">Sources &amp; limits</h3>
        <p>
          Classifications rest only on public sources. Where an institution’s own
          claims (e.g. realized benefits “in the billions”) cannot be
          independently verified, they are labeled as company claims. Absence of
          a public signal is not proof of inaction — it is simply the limit of
          what can be sourced.
        </p>
        <p>
          Coverage is not a sample of any defined population. Institutions enter
          the corpus through research passes, not through a sampling frame, so
          the figures on this site describe <strong>this corpus</strong> and
          should not be read as rates across an industry.
        </p>
        <p>
          Evidence in Chinese, Japanese and Korean is quoted verbatim in the
          original, because the exact wording is what carries the classification.
          An English rendering is shown alongside it; the original is always the
          record.
        </p>
      </section>

      <section className="author-bio">
        <h3 className="prose-h2">About the author</h3>
        <p>
          Built and maintained by <strong>Jiajun Ma</strong>, an investment
          professional working in institutional asset management. This is an
          independent personal project: it is not affiliated with, sponsored
          by, or endorsed by any employer, and every view and classification
          here is the author’s alone.
        </p>
        <p>
          Consistent with the public-sources-only rule above, no non-public
          information from the author’s professional work informs any
          classification, and institutions where the author has a professional
          affiliation are excluded from coverage entirely. Nothing on this
          site is investment advice.
        </p>
        <p>
          Corrections and challenges are welcome —{' '}
          <a
            href="https://github.com/jima1835/ai-adoption-in-finance/issues"
            target="_blank"
            rel="noreferrer"
          >
            open an issue
          </a>{' '}
          with the public sources you think change the call.
        </p>
      </section>
      {notClassified.length > 0 && (
        <section className="prose-bleed">
          <h3 className="prose-h2">Appendix — assessed, not classified</h3>
          <p>
            Institutions researched against this methodology whose public record
            did not support a stage. Absence from the dashboard is a finding,
            not an omission: each entry names why the record fell short.
            “No qualifying evidence” means the public record — after searching —
            contained nothing in scope that met the sourcing rules. “Withdrawn
            on review” entries were listed and then removed when human review
            found the evidence insufficient.
          </p>
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Assessed but not classified, scrollable table">
            <table className="inst-table nc-table">
              <thead>
                <tr>
                  <th>Institution</th>
                  <th>Type</th>
                  <th>Region</th>
                  <th>Outcome</th>
                  <th>Why</th>
                  <th data-align="right">As of</th>
                </tr>
              </thead>
              <tbody>
                {notClassified.map((n) => (
                  <tr key={n.name}>
                    <td className="td-name">{n.name}</td>
                    <td className="td-muted">{TYPE_LABELS[n.type] || n.type}</td>
                    <td className="td-muted">{n.region}</td>
                    <td>
                      <span className="nc-outcome" data-outcome={n.outcome}>
                        {OUTCOME_LABELS[n.outcome] || n.outcome}
                      </span>
                    </td>
                    <td className="nc-reason">{n.reason}</td>
                    <td data-align="right" className="td-num td-muted">
                      {n.as_of}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

    </article>
  )
}
