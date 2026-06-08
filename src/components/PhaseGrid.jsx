import {
  STAGES,
  STAGE_LABELS,
  STAGE_DEFS,
  EMBEDDED_EMPTY_NOTE,
  TYPE_LABELS,
  initials,
} from '../data.js'

function Card({ inst, onSelect }) {
  return (
    <button
      className="inst-card"
      data-stage={inst.stage}
      onClick={() => onSelect(inst)}
    >
      <span className="card-mark" aria-hidden="true">
        {initials(inst.name)}
      </span>
      <span className="card-body">
        <span className="card-name">{inst.name}</span>
        <span className="card-meta">
          <span>{TYPE_LABELS[inst.type] || inst.type}</span>
          <span className="card-dot">·</span>
          <span className="card-aum">{inst.aum}</span>
        </span>
      </span>
    </button>
  )
}

// Four columns left→right: EXPLORING | PILOTING | SCALING | EMBEDDED.
// EMBEDDED is intentionally empty — rendered as an editorial statement.
export default function PhaseGrid({ institutions, onSelect }) {
  const byStage = Object.fromEntries(STAGES.map((s) => [s, []]))
  for (const inst of institutions) {
    if (byStage[inst.stage]) byStage[inst.stage].push(inst)
  }

  return (
    <div className="phase-grid">
      {STAGES.map((stage, i) => {
        const rows = byStage[stage]
        const isEmbedded = stage === 'embedded'
        return (
          <section key={stage} className="phase-col" data-stage={stage}>
            <header className="phase-head">
              <span className="phase-index">{String(i + 1).padStart(2, '0')}</span>
              <h2 className="phase-title">{STAGE_LABELS[stage]}</h2>
              <span className="phase-count">{rows.length}</span>
            </header>
            <p className="phase-def">{STAGE_DEFS[stage]}</p>
            <div className="phase-cards">
              {isEmbedded ? (
                <div className="embedded-note">
                  <span className="embedded-rule" />
                  <p>{EMBEDDED_EMPTY_NOTE}</p>
                  <span className="embedded-tag">editorial position</span>
                </div>
              ) : rows.length === 0 ? (
                <p className="col-empty">No institutions match this filter.</p>
              ) : (
                rows.map((inst) => (
                  <Card key={inst.name} inst={inst} onSelect={onSelect} />
                ))
              )}
            </div>
          </section>
        )
      })}
    </div>
  )
}
