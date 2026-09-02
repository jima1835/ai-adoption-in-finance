import { STAGES, STAGE_LABELS } from '../data.js'

// The human-vs-agent disagreement record (data/agreement.json).
//
// Two numbers, deliberately, because they answer different questions and the
// first one alone flatters the pipeline:
//   stage agreement   — of the rows that survived review, how often did the
//                       agent's proposed stage stand?
//   proposals as-is   — of every proposal the reviewer adjudicated, how often
//                       was it taken unchanged? Withdrawn rows are
//                       disagreements too; dropping them inflates the rate.
//
// The matrix is a magnitude read on a 4×4 grid that is nearly all diagonal, so
// it is a table with a single-hue tint rather than a chart — and the diagonal
// carries a border as well as the tint, so agreement is never encoded by colour
// alone. Counts wear text tokens, not the accent.
export default function AgreementPanel({ data }) {
  if (!data || !data.stage_agreement) return null

  const { corpus, stage_agreement: sa, proposal_accepted: pa } = data
  const matrix = data.matrix || []
  const revisions = data.revisions || []
  const withdrawals = data.withdrawals || []

  // Only render stages that actually appear on either axis.
  const proposed = STAGES.filter((s) => matrix.some((m) => m.proposed === s))
  const finals = STAGES.filter((s) => matrix.some((m) => m.final === s))
  const at = (p, f) => matrix.find((m) => m.proposed === p && m.final === f)?.n || 0
  const max = matrix.reduce((a, m) => Math.max(a, m.n), 0) || 1
  const pct = (v) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`)

  return (
    <section className="agreement">
      <h3 className="prose-h2">The disagreement record</h3>
      <p>
        Every row in this corpus was drafted by a research agent that also
        proposed an adoption stage; a human reviewer then checked the row
        against its sources and accepted, revised, or removed it. That review
        is logged, so the rate at which the human and the agent disagree is
        itself a published measurement rather than an assurance.
      </p>

      <div className="agree-tiles">
        <div className="agree-tile">
          <span className="agree-num">{pct(sa.rate)}</span>
          <span className="agree-label">Proposed stage stood</span>
          <span className="agree-sub">
            {sa.unchanged} of {sa.n} reviewed rows — {sa.revised} revised
          </span>
        </div>
        <div className="agree-tile">
          <span className="agree-num">{pct(pa.rate)}</span>
          <span className="agree-label">Proposals accepted as-is</span>
          <span className="agree-sub">
            {pa.accepted_unchanged} of {pa.n} adjudicated — {pa.stage_revised}{' '}
            revised, {pa.withdrawn_on_review} withdrawn
          </span>
        </div>
        <div className="agree-tile">
          <span className="agree-num">
            {corpus.reviewed}
            <span className="agree-den">/{corpus.rows}</span>
          </span>
          <span className="agree-label">Rows human-verified</span>
          <span className="agree-sub">
            {corpus.not_yet_reviewed} still in the review queue
          </span>
        </div>
      </div>

      <p className="prose-callout agree-caveat">
        <strong>This is an upper bound, not a reliability coefficient.</strong>{' '}
        {data.limitation} A blind re-code — the same evidence stripped of the
        agent&rsquo;s stage and reasoning, coded cold — is a separate exercise,
        and only that produces a reliability coefficient. None is reported here.
      </p>

      <div className="table-wrap" tabIndex={0} role="region" aria-label="Proposed versus final stage, scrollable table">
        <table className="inst-table agree-matrix">
          <caption className="agree-caption">
            Agent-proposed stage (rows) against the human&rsquo;s final stage
            (columns). Cells on the diagonal are agreements.
          </caption>
          <thead>
            <tr>
              <th scope="col">Proposed ↓ / Final →</th>
              {finals.map((f) => (
                <th key={f} scope="col" data-align="right">
                  {STAGE_LABELS[f]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {proposed.map((p) => (
              <tr key={p}>
                <th scope="row" className="td-name">
                  <span className="stage-swatch" data-stage={p} />
                  {STAGE_LABELS[p]}
                </th>
                {finals.map((f) => {
                  const n = at(p, f)
                  return (
                    <td
                      key={f}
                      data-align="right"
                      className="agree-cell"
                      data-diagonal={p === f ? 'true' : undefined}
                      style={n ? { background: `rgba(240, 168, 48, ${(0.06 + 0.34 * (n / max)).toFixed(3)})` } : undefined}
                    >
                      {n || <span className="td-empty">·</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {revisions.length > 0 && (
        <>
          <h4 className="agree-h3">Stages the reviewer changed</h4>
          <ul className="prose-list agree-list">
            {revisions.map((r) => (
              <li key={r.institution}>
                <strong>{r.institution}</strong> — {STAGE_LABELS[r.proposed]} →{' '}
                {STAGE_LABELS[r.final]}{' '}
                <span className="agree-dir" data-direction={r.direction}>
                  {r.direction === 'up' ? 'raised' : 'lowered'}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}

      {withdrawals.length > 0 && (
        <>
          <h4 className="agree-h3">Rows the reviewer removed</h4>
          <p className="agree-note">
            Listed by the pipeline, then withdrawn when human review found the
            public record could not carry a stage. These are disagreements, and
            they are counted as such above. Each appears in the
            assessed-but-not-classified appendix below with its reason.
          </p>
          <ul className="prose-list agree-list">
            {withdrawals.map((w) => (
              <li key={w.institution}>
                <strong>{w.institution}</strong>{' '}
                <span className="td-muted">{w.as_of}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <p className="agree-note">
        Figures as of {data.as_of}. Rebuilt from{' '}
        <code>data/institutions.json</code> and{' '}
        <code>data/not_classified.json</code> — both in this repo, so the counts
        are reproducible without trusting this page. Source:{' '}
        <a
          href="https://github.com/jima1835/ai-adoption-in-finance/blob/main/data/agreement.json"
          target="_blank"
          rel="noreferrer"
        >
          data/agreement.json
        </a>
        .
      </p>
    </section>
  )
}
