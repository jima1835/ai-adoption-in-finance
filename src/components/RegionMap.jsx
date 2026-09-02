import { useState } from 'react'
import {
  MAP_COLS,
  MAP_ROWS,
  MAP_REGION_ROWS,
  MAP_CODE_TO_REGION,
} from '../worldgrid.js'
import { REGION_LABELS, REGION_COLORS } from '../data.js'

// Dot-matrix world, one hue per region. This is a CATEGORICAL encoding — the
// colour says which region, not how many — so the counts live in the legend as
// text rather than in the shading. The palette was chosen by search against the
// dataviz validator on the all-pairs pairlist, because a map shows all six
// regions simultaneously; it clears the CVD, normal-vision, lightness, chroma
// and contrast checks.
//
// Regions accumulate: clicking Asia then Europe selects both, and the page below
// filters to the union. Clicking a selected region removes it. Both the map and
// the legend toggle the same selection — the map for pointing at a place, the
// legend for naming one (and for keyboard and screen-reader users).
//
// The dataset records a REGION, not a country, so the map deliberately shades at
// region resolution rather than implying a precision the data does not have.
export default function RegionMap({ institutions, selected, onToggle }) {
  const [hover, setHover] = useState(null)

  const counts = Object.fromEntries(REGION_LABELS.map((r) => [r, 0]))
  for (const i of institutions) if (counts[i.region] !== undefined) counts[i.region]++

  const anySelected = selected.length > 0
  // Hover previews one region; otherwise the selection is what stands out.
  const lit = (region) =>
    hover ? region === hover : !anySelected || selected.includes(region)

  // One <g> per region so the map itself is clickable, not just the legend.
  const byRegion = Object.fromEntries(REGION_LABELS.map((r) => [r, []]))
  for (let r = 0; r < MAP_ROWS; r++) {
    const row = MAP_REGION_ROWS[r]
    for (let c = 0; c < MAP_COLS; c++) {
      const code = row[c]
      if (!code || code === '.') continue
      const region = MAP_CODE_TO_REGION[code]
      if (!byRegion[region]) continue
      byRegion[region].push(
        <rect key={`${r}-${c}`} x={c * 3} y={r * 3} width={2} height={2} rx={0.4} />,
      )
    }
  }

  const summary = anySelected
    ? `${selected.join(' + ')} · ${selected.reduce((n, r) => n + counts[r], 0)}`
    : 'select a region to filter'

  return (
    <section className="region-map" aria-label="Institutions by region">
      <div className="strip-head">
        <span className="strip-title">By region</span>
        <span className="strip-sub">{summary}</span>
      </div>

      <div className="map-body">
        <svg
          className="map-svg"
          viewBox={`0 0 ${MAP_COLS * 3} ${MAP_ROWS * 3}`}
          role="img"
          aria-label={`World map of the corpus by region. ${REGION_LABELS.map(
            (r) => `${r} ${counts[r]}`,
          ).join(', ')}.`}
          focusable="false"
        >
          {REGION_LABELS.map((r) => (
            <g
              key={r}
              data-region={r}
              fill={REGION_COLORS[r]}
              opacity={lit(r) ? 1 : 0.18}
              onClick={() => onToggle(r)}
              onMouseEnter={() => setHover(r)}
              onMouseLeave={() => setHover(null)}
              /* Pointer affordance only. The legend below is the accessible
                 control — it is already a real <button> with aria-pressed,
                 keyboard focus and a spoken label — so these groups are hidden
                 from assistive tech rather than duplicated as a second, worse
                 set of controls with no keyboard path. */
              aria-hidden="true"
            >
              {byRegion[r]}
            </g>
          ))}
        </svg>

        {/* The legend is also the control. Identity is never colour-alone: every
            key names its region and its count in text. */}
        <ul className="map-legend">
          {REGION_LABELS.map((r) => (
            <li key={r}>
              <button
                type="button"
                className="map-key"
                style={{ '--region': REGION_COLORS[r] }}
                aria-pressed={selected.includes(r)}
                onMouseEnter={() => setHover(r)}
                onMouseLeave={() => setHover(null)}
                onFocus={() => setHover(r)}
                onBlur={() => setHover(null)}
                onClick={() => onToggle(r)}
              >
                <span className="mk-swatch" aria-hidden="true" />
                <span className="mk-name">{r}</span>
                <span className="mk-n">{counts[r]}</span>
                <span className="sr-only">
                  {counts[r] === 1 ? ' institution.' : ' institutions.'}
                  {selected.includes(r)
                    ? ' Selected. Activate to remove it from the filter.'
                    : ' Activate to add it to the filter.'}
                </span>
              </button>
            </li>
          ))}
          {anySelected && (
            <li>
              <button type="button" className="map-key map-clear" onClick={() => onToggle(null)}>
                <span className="mk-swatch mk-clear" aria-hidden="true">✕</span>
                <span className="mk-name">Clear</span>
                <span className="sr-only">the region selection</span>
              </button>
            </li>
          )}
        </ul>
      </div>
    </section>
  )
}
