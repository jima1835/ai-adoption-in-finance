import { STAGES, STAGE_LABELS, STAGE_DEFS } from '../data.js'

export default function MobileFindings({ institutions, onStage, onBrowse }) {
  return (
    <section className="mobile-findings" aria-labelledby="findings-heading">
      <h2 id="findings-heading" tabIndex={-1}>
        What the public evidence shows
      </h2>
      <p>
        Stages among all {institutions.length} classified institutions in this
        dataset. These are not industry adoption rates.
      </p>
      <div className="finding-stages">
        {STAGES.map((stage) => {
          const count = institutions.filter(
            (inst) => inst.stage === stage,
          ).length
          return (
            <button
              key={stage}
              type="button"
              className="finding-stage"
              data-stage={stage}
              onClick={() => onStage(stage)}
            >
              <span>
                <strong>{STAGE_LABELS[stage]}</strong>
                <span className="finding-definition">{STAGE_DEFS[stage]}</span>
              </span>
              <span className="finding-count">
                <strong>{count}</strong>
                <span>
                  {institutions.length
                    ? `${Math.round((count / institutions.length) * 100)}%`
                    : '—'}
                </span>
              </span>
              <span className="sr-only">
                {' '}
                · Browse {count} of {institutions.length} classified
                institutions
              </span>
            </button>
          )
        })}
      </div>
      <button type="button" className="browse-institutions" onClick={onBrowse}>
        Browse institutions →
      </button>
    </section>
  )
}
