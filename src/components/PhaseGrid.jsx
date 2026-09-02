import { useState } from 'react'
import {
  STAGES,
  STAGE_LABELS,
  STAGE_DEFS,
  TYPE_LABELS,
  aumUsd,
  aumUsdApprox,
  dateSortKey,
  latestActivity,
  initials,
  stageDefinition,
  embeddedNote,
} from '../data.js'
import Lang from './Lang.jsx'

function Card({ inst, onSelect }) {
  const activity = latestActivity(inst)
  const approx = aumUsdApprox(inst.aum)
  return (
    <button
      type="button"
      className="inst-card"
      data-stage={inst.stage}
      aria-label={`${inst.name} — ${inst.stage} — open detail`}
      onClick={() => onSelect(inst)}
    >
      <span className="card-mark" aria-hidden="true">
        {initials(inst.name)}
      </span>
      <span className="card-body">
        <span className="card-name"><Lang>{inst.name}</Lang></span>
        <span className="card-meta">
          <span>{TYPE_LABELS[inst.type] || inst.type}</span>
          <span className="card-dot">·</span>
          <span className="card-aum">{inst.aum}</span>
          {approx && (
            <span className="aum-approx">
              {approx}
              <span className="sr-only">
                {' '}approximate USD at static FX; the original disclosure is the
                ground truth
              </span>
            </span>
          )}
          {inst.confidence && (
            <>
              <span
                className="conf-dot"
                data-conf={inst.confidence}
                aria-hidden="true"
              />
              <span className="sr-only">
                , {inst.confidence} evidence confidence
              </span>
            </>
          )}
        </span>
      </span>
      {(activity || inst.as_of_reviewed) && (
        <span className="card-dates">
          {activity && (
            <span className="card-date card-news"
              >
              <span aria-hidden="true">⚡</span>
              <span className="sr-only">Latest activity </span>
              {activity.date}
            </span>
          )}
          {inst.as_of_reviewed && (
            <span className="card-date card-reviewed">
              <span aria-hidden="true">✓</span>
              <span className="sr-only">Last reviewed </span>
              {inst.as_of_reviewed}
            </span>
          )}
        </span>
      )}
    </button>
  )
}

// Four columns left→right: EXPLORING | PILOTING | SCALING | EMBEDDED.
// EMBEDDED is intentionally empty — rendered as an editorial statement.
// Column headers expose the full stage definition (from stage_definitions.json,
// falling back to the built-in one-liners) on hover/focus.
// Each column has its own sort toggles — AUM and ⚡ last-news date — cycling
// data order → ▼ → ▲. One sort key active per column at a time.
const SORT_NEXT = { desc: 'asc', asc: null }
const SORT_GLYPH = { desc: '▼', asc: '▲' }
const SORT_VALUE = {
  aum: (inst) => aumUsd(inst.aum),
  news: (inst) => dateSortKey(latestActivity(inst)?.date),
}

export default function PhaseGrid({ institutions, onSelect, defs }) {
  const [sorts, setSorts] = useState({}) // stage → {key:'aum'|'news', dir} | undefined

  const byStage = Object.fromEntries(STAGES.map((s) => [s, []]))
  for (const inst of institutions) {
    if (byStage[inst.stage]) byStage[inst.stage].push(inst)
  }

  const cycle = (stage, key) =>
    setSorts((s) => {
      const cur = s[stage]
      const next =
        cur?.key === key ? SORT_NEXT[cur.dir] && { key, dir: SORT_NEXT[cur.dir] }
          : { key, dir: 'desc' }
      return { ...s, [stage]: next || undefined }
    })

  return (
    <div className="phase-grid">
      {STAGES.map((stage, i) => {
        const isEmbedded = stage === 'embedded'
        const fullDef = stageDefinition(defs, stage)
        const sort = sorts[stage]
        const rows = sort
          ? [...byStage[stage]].sort((a, b) => {
              const va = SORT_VALUE[sort.key](a)
              const vb = SORT_VALUE[sort.key](b)
              return sort.dir === 'desc' ? vb - va : va - vb
            })
          : byStage[stage]
        return (
          <section key={stage} className="phase-col" data-stage={stage}>
            <header
              className="phase-head"
              tabIndex={0}
              aria-describedby={fullDef ? `stagedef-${stage}` : undefined}
            >
              <span className="phase-index" aria-hidden="true">
                {String(i + 1).padStart(2, '0')}
              </span>
              <h2 className="phase-title">{STAGE_LABELS[stage]}</h2>
              <span className="phase-count">
                {rows.length}
                <span className="sr-only"> institutions</span>
              </span>
              {fullDef && (
                <span className="phase-tooltip" role="tooltip" id={`stagedef-${stage}`}>
                  {fullDef}
                </span>
              )}
            </header>
            <p className="phase-def">{STAGE_DEFS[stage]}</p>
            {!isEmbedded && rows.length > 1 && (
              <div className="phase-sorts">
                <button
                  type="button"
                  className="phase-sort"
                  data-active={sort?.key === 'aum'}
                  aria-pressed={sort?.key === 'aum'}
                  onClick={() => cycle(stage, 'aum')}
                >
                  <span aria-hidden="true">
                    AUM {sort?.key === 'aum' ? SORT_GLYPH[sort.dir] : '↕'}
                  </span>
                  <span className="sr-only">
                    Sort {STAGE_LABELS[stage]} by approximate AUM in USD
                    {sort?.key === 'aum'
                      ? `, currently ${sort.dir === 'asc' ? 'ascending' : 'descending'}`
                      : ''}
                  </span>
                </button>
                <button
                  type="button"
                  className="phase-sort"
                  data-active={sort?.key === 'news'}
                  aria-pressed={sort?.key === 'news'}
                  onClick={() => cycle(stage, 'news')}
                >
                  <span aria-hidden="true">
                    ⚡ {sort?.key === 'news' ? SORT_GLYPH[sort.dir] : '↕'}
                  </span>
                  <span className="sr-only">
                    Sort {STAGE_LABELS[stage]} by latest activity date
                    {sort?.key === 'news'
                      ? `, currently ${sort.dir === 'asc' ? 'ascending' : 'descending'}`
                      : ''}
                  </span>
                </button>
              </div>
            )}
            <div className="phase-cards">
              {isEmbedded ? (
                <div className="embedded-note">
                  <span className="embedded-rule" />
                  <p>{embeddedNote(defs)}</p>
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
