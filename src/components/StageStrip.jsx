import { STAGES, STAGE_LABELS, aumUsd } from '../data.js'

// The executive summary: a four-panel terminal readout of the adoption ramp.
//
// Form note — the four stages are ORDERED, so this is a sequential encoding, not
// a categorical one. A pie would throw the ordering away, which is the only thing
// the framework actually asserts. Left-to-right panels keep it, and mirror the
// phase grid below.
//
// Colour cannot carry identity here: the piloting and scaling ambers sit ΔE 9.4
// apart in normal vision, below the 15 that lets colour separate two marks on its
// own. So every panel is directly labelled and every segment of the ramp carries
// its own name and count — colour is reinforcement, never the channel.
function fmtAum(usd) {
  if (!usd) return '—'
  if (usd >= 1e12) return `$${(usd / 1e12).toFixed(1)}T`
  if (usd >= 1e9) return `$${Math.round(usd / 1e9)}B`
  return `$${Math.round(usd / 1e6)}M`
}

export default function StageStrip({ institutions, active, onToggle }) {
  const total = institutions.length
  const stats = STAGES.map((stage) => {
    const rows = institutions.filter((i) => i.stage === stage)
    return {
      stage,
      n: rows.length,
      share: total ? rows.length / total : 0,
      aum: rows.reduce((sum, i) => sum + (aumUsd(i.aum) || 0), 0),
      high: rows.filter((i) => i.confidence === 'high').length,
    }
  })

  return (
    <section className="stage-strip" aria-label="Adoption stages overview">
      <div className="strip-head">
        <span className="strip-title">Adoption ramp</span>
        <span className="strip-sub">
          {total} institutions · select a stage to filter
        </span>
      </div>

      <div className="stage-panels">
        {stats.map((s, i) => {
          const on = active === s.stage
          return (
            <button
              key={s.stage}
              type="button"
              className="stage-panel"
              data-stage={s.stage}
              data-empty={s.n === 0}
              aria-pressed={on}
              onClick={() => onToggle(s.stage)}
            >
              <span className="sp-corner sp-tl" aria-hidden="true" />
              <span className="sp-corner sp-br" aria-hidden="true" />

              <span className="sp-top">
                <span className="sp-idx" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span className="sp-name">{STAGE_LABELS[s.stage]}</span>
              </span>

              <span className="sp-readout">
                <span className="sp-n">{s.n}</span>
                <span className="sp-share">
                  {total ? `${Math.round(s.share * 100)}%` : '—'}
                </span>
              </span>

              <span
                className="sp-meter"
                role="img"
                aria-label={`${Math.round(s.share * 100)} percent of the corpus`}
              >
                <span
                  className="sp-meter-fill"
                  style={{ width: `${Math.max(s.share * 100, s.n ? 2 : 0)}%` }}
                />
              </span>

              <span className="sp-foot">
                <span>
                  AUM <b>{fmtAum(s.aum)}</b>
                </span>
                <span>
                  HI-CONF <b>{s.high}</b>
                </span>
              </span>

              <span className="sr-only">
                {s.n === 0
                  ? `${STAGE_LABELS[s.stage]}: no institutions. `
                  : `${STAGE_LABELS[s.stage]}: ${s.n} institutions, ${Math.round(
                      s.share * 100,
                    )} percent of the corpus, ${fmtAum(s.aum)} combined AUM, ${
                      s.high
                    } rated high confidence. `}
                {on ? 'Filtering by this stage. Activate to clear.' : 'Activate to filter by this stage.'}
              </span>
            </button>
          )
        })}
      </div>
    </section>
  )
}
