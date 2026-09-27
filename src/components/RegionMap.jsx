import { useMemo, useState } from 'react'
import {
  MAP_COLS,
  MAP_ROWS,
  MAP_REGION_ROWS,
  MAP_CODE_TO_REGION,
} from '../worldgrid.js'
import { REGION_LABELS, REGION_COLORS } from '../data.js'

// Dot-matrix world, one hue per region, drawn as a plate tilted back 45° with
// the land extruded into a slab. This is a CATEGORICAL encoding — the colour
// says which region, not how many — so the counts live in the legend as text
// rather than in the shading, and the extrusion is a constant thickness
// everywhere: the height of the slab means nothing, it is only the angle.
// The palette was chosen by search against the dataviz validator on the
// all-pairs pairlist, because a map shows all six regions simultaneously; it
// clears the CVD, normal-vision, lightness, chroma and contrast checks.
//
// Regions accumulate: clicking Asia then Europe selects both, and the page below
// filters to the union. Clicking a selected region removes it. Both the map and
// the legend toggle the same selection — the map for pointing at a place, the
// legend for naming one (and for keyboard and screen-reader users).
//
// The dataset records a REGION, not a country, so the map deliberately shades at
// region resolution rather than implying a precision the data does not have.

// --- the projection ---------------------------------------------------------
// Grid cell (c, r) sits at (c·PITCH, r·PITCH) and every top face is drawn
// through one matrix: x stays horizontal, +y recedes down-right. TILT is
// cos 45°, so the plate reads as tilted back 45°; YAW turns it slightly off
// head-on, which is what makes each cell read as a block rather than a dot.
//
// Because the matrix leaves horizontal edges horizontal, a cell's bottom edge
// projects to a horizontal segment — so its wall is a plain axis-aligned rect,
// PITCH wide (the pitch, not the dot, so neighbouring walls close up into one
// solid side) and DEPTH deep. Walls are painted for every cell before any top
// face, so the slab is opaque from any row and no wall can land on a dot.
const PITCH = 3
const CELL = 2
const TILT = 0.707
const YAW = 0.28
const DEPTH = 6.5
const WALL = 0.34 // side faces are the region hue at a third brightness

const VIEW_W = MAP_COLS * PITCH + MAP_ROWS * PITCH * YAW
const VIEW_H = MAP_ROWS * PITCH * TILT + CELL * TILT + DEPTH

const shade = (hex, f) =>
  '#' +
  [1, 3, 5]
    .map((i) =>
      Math.round(parseInt(hex.slice(i, i + 2), 16) * f)
        .toString(16)
        .padStart(2, '0'),
    )
    .join('')

export default function RegionMap({ institutions, selected, onToggle }) {
  const [hover, setHover] = useState(null)

  const counts = Object.fromEntries(REGION_LABELS.map((r) => [r, 0]))
  for (const i of institutions)
    if (counts[i.region] !== undefined) counts[i.region]++

  const anySelected = selected.length > 0
  // Hover previews one region; otherwise the selection is what stands out.
  const lit = (region) =>
    hover ? region === hover : !anySelected || selected.includes(region)

  // The raster never changes, so the ~3,400 rects are built once and reused by
  // identity: a hover then re-renders twelve <g> opacities, not the world.
  const { tops, walls } = useMemo(() => {
    const tops = Object.fromEntries(REGION_LABELS.map((r) => [r, []]))
    const walls = Object.fromEntries(REGION_LABELS.map((r) => [r, []]))
    for (let r = 0; r < MAP_ROWS; r++) {
      const row = MAP_REGION_ROWS[r]
      for (let c = 0; c < MAP_COLS; c++) {
        const code = row[c]
        if (!code || code === '.') continue
        const region = MAP_CODE_TO_REGION[code]
        if (!tops[region]) continue
        const x = c * PITCH
        const y = r * PITCH
        tops[region].push(
          <rect
            key={`${r}-${c}`}
            x={x}
            y={y}
            width={CELL}
            height={CELL}
            rx={0.4}
          />,
        )
        walls[region].push(
          <rect
            key={`${r}-${c}`}
            x={(x + YAW * (y + CELL)).toFixed(2)}
            y={(TILT * (y + CELL)).toFixed(2)}
            width={PITCH}
            height={DEPTH}
          />,
        )
      }
    }
    return { tops, walls }
  }, [])

  const summary = anySelected
    ? `${selected.join(' + ')} · ${selected.reduce((n, r) => n + counts[r], 0)}`
    : 'select a region to filter'

  // Pointer affordance only. The legend below is the accessible control — it is
  // already a real <button> with aria-pressed, keyboard focus and a spoken
  // label — so these groups are hidden from assistive tech rather than
  // duplicated as a second, worse set of controls with no keyboard path.
  const handlers = (r) => ({
    'data-region': r,
    'data-hover': hover === r ? 'true' : undefined,
    opacity: lit(r) ? 1 : 0.16,
    onClick: () => onToggle(r),
    onMouseEnter: () => setHover(r),
    onMouseLeave: () => setHover(null),
    'aria-hidden': 'true',
  })

  return (
    <section className="region-map" aria-label="Institutions by region">
      <div className="strip-head">
        <span className="strip-title">By region</span>
        <span className="strip-sub">{summary}</span>
      </div>

      <div className="map-body">
        <svg
          className="map-svg"
          viewBox={`0 -4 ${VIEW_W.toFixed(1)} ${(VIEW_H + 4).toFixed(1)}`}
          role="img"
          aria-label={`World map of the corpus by region. ${REGION_LABELS.map(
            (r) => `${r} ${counts[r]}`,
          ).join(', ')}.`}
          focusable="false"
        >
          {/* every side face first, so the slab reads as one solid body */}
          {REGION_LABELS.map((r) => (
            <g key={r} {...handlers(r)} fill={shade(REGION_COLORS[r], WALL)}>
              {walls[r]}
            </g>
          ))}
          <g transform={`matrix(1 0 ${YAW} ${TILT} 0 0)`}>
            {REGION_LABELS.map((r) => (
              <g key={r} {...handlers(r)} fill={REGION_COLORS[r]}>
                {tops[r]}
              </g>
            ))}
          </g>
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
              <button
                type="button"
                className="map-key map-clear"
                onClick={() => onToggle(null)}
              >
                <span className="mk-swatch mk-clear" aria-hidden="true">
                  ✕
                </span>
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
