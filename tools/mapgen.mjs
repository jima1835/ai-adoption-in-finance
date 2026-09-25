// Regenerates src/worldgrid.js — the dot raster the "By region" map draws.
//
//   node tools/mapgen.mjs [countries-110m.json]
//
// With no argument it fetches Natural Earth 110m countries from world-atlas.
// Nothing here runs at build or at page load: the raster is committed, so the
// site ships no mapping library and no topology file.
//
// The raster is decorative. It shades the six dashboard region buckets, not
// countries, so COUNTRY_REGION below is a presentation choice — which bucket a
// country's dots take — and never touches how an institution is classified.
import { writeFileSync, readFileSync } from 'node:fs'

const SRC = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'
const OUT = new URL('../src/worldgrid.js', import.meta.url)

// Equirectangular, cut at 84°N / 58°S: everything inhabited, no Antarctica
// (no bucket owns it) and no empty polar rows.
const COLS = 104
const ROWS = 42
const LAT_TOP = 84
const LAT_BOT = -58
const SUB = 3 // samples per cell axis; a cell takes its most-sampled region

// Everything not named here is "Other". Buckets follow the dashboard's own
// region field: the Gulf, the Levant, Anatolia, Iran and Egypt read as Middle
// East; the rest of North Africa reads as Other.
const COUNTRY_REGION = {
  'United States of America': 'US',
  Canada: 'Canada',
  ...group('Europe', [
    'Albania', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herz.', 'Bulgaria',
    'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland', 'France',
    'Germany', 'Greece', 'Greenland', 'Hungary', 'Iceland', 'Ireland', 'Italy',
    'Kosovo', 'Latvia', 'Lithuania', 'Luxembourg', 'Macedonia', 'Moldova',
    'Montenegro', 'N. Cyprus', 'Netherlands', 'Norway', 'Poland', 'Portugal',
    'Romania', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden',
    'Switzerland', 'Ukraine', 'United Kingdom',
  ]),
  ...group('Middle East', [
    'Egypt', 'Iran', 'Iraq', 'Israel', 'Jordan', 'Kuwait', 'Lebanon', 'Oman',
    'Palestine', 'Qatar', 'Saudi Arabia', 'Syria', 'Turkey',
    'United Arab Emirates', 'Yemen',
  ]),
  ...group('Asia', [
    'Afghanistan', 'Armenia', 'Azerbaijan', 'Bangladesh', 'Bhutan', 'Brunei',
    'Cambodia', 'China', 'Georgia', 'India', 'Indonesia', 'Japan', 'Kazakhstan',
    'Kyrgyzstan', 'Laos', 'Malaysia', 'Mongolia', 'Myanmar', 'Nepal',
    'North Korea', 'Pakistan', 'Philippines', 'Russia', 'South Korea',
    'Sri Lanka', 'Taiwan', 'Tajikistan', 'Thailand', 'Timor-Leste',
    'Turkmenistan', 'Uzbekistan', 'Vietnam',
  ]),
}
function group(region, names) {
  return Object.fromEntries(names.map((n) => [n, region]))
}

// Natural Earth's France carries its overseas departments. At this resolution
// only French Guiana survives, and it would paint one Europe dot into South
// America — the buckets are geographic, so the raster keeps mainland France.
const CLIP = { France: (lon, lat) => lon > -20 && lat > 30 }

const CODE = { US: 'U', Canada: 'C', Europe: 'E', Asia: 'A', 'Middle East': 'M', Other: 'O' }
// Antarctica has no bucket and is cut by LAT_BOT; the sub-antarctic dependencies
// are dropped with it rather than shaded as a region nobody is classified in.
const DROP = new Set(['Antarctica', 'Fr. S. Antarctic Lands'])

// --- TopoJSON: quantized, delta-encoded arcs; a negative index is a reversal ---
function countries(topo) {
  const [sx, sy] = topo.transform.scale
  const [tx, ty] = topo.transform.translate
  const arcs = topo.arcs.map((arc) => {
    let x = 0
    let y = 0
    return arc.map(([dx, dy]) => {
      x += dx
      y += dy
      return [x * sx + tx, y * sy + ty]
    })
  })
  // Rings that touch the antimeridian (Russia, Fiji) arrive with both -180 and
  // +180 in them, so a planar ray cast reads the seam as one segment spanning
  // the whole map and floods every cell at those latitudes. Unwrapping the ring
  // — keeping longitudes continuous, past ±180 where it has to — removes the
  // spanning segment; `hit` then also tests the point shifted by ±360 so the
  // far side of the seam still matches. This is the Asia band that ran across
  // the Arctic in the raster generated before the fix.
  const ring = (idxs) => {
    const pts = []
    for (const i of idxs) {
      const a = i < 0 ? arcs[~i].slice().reverse() : arcs[i]
      for (let k = pts.length ? 1 : 0; k < a.length; k++) pts.push(a[k])
    }
    let prev = pts[0][0]
    return pts.map(([x, y], k) => {
      if (k === 0) return [x, y]
      while (x - prev > 180) x -= 360
      while (x - prev < -180) x += 360
      prev = x
      return [x, y]
    })
  }
  return topo.objects.countries.geometries
    .filter((g) => !DROP.has(g.properties.name))
    .map((g) => {
      const clip = CLIP[g.properties.name]
      const polys = (g.type === 'Polygon' ? [g.arcs] : g.arcs)
        .map((p) => p.map(ring))
        .filter((p) => !clip || p[0].some(([x, y]) => clip(x, y)))
      let x0 = 180
      let y0 = 90
      let x1 = -180
      let y1 = -90
      for (const p of polys)
        for (const [x, y] of p[0]) {
          if (x < x0) x0 = x
          if (x > x1) x1 = x
          if (y < y0) y0 = y
          if (y > y1) y1 = y
        }
      return {
        name: g.properties.name,
        region: COUNTRY_REGION[g.properties.name] || 'Other',
        polys,
        bbox: [x0, y0, x1, y1],
      }
    })
}

function inRing(lon, lat, r) {
  let inside = false
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i]
    const [xj, yj] = r[j]
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi)
      inside = !inside
  }
  return inside
}
function hit(k, lon, lat) {
  for (const poly of k.polys)
    for (const x of [lon, lon - 360, lon + 360]) {
      if (!inRing(x, lat, poly[0])) continue
      let hole = false
      for (let h = 1; h < poly.length; h++)
        if (inRing(x, lat, poly[h])) {
          hole = true
          break
        }
      if (!hole) return true
    }
  return false
}

const topo = process.argv[2]
  ? JSON.parse(readFileSync(process.argv[2], 'utf8'))
  : await (await fetch(SRC)).json()
const world = countries(topo)

const rows = []
for (let r = 0; r < ROWS; r++) {
  let line = ''
  for (let c = 0; c < COLS; c++) {
    const votes = {}
    for (let a = 0; a < SUB; a++)
      for (let b = 0; b < SUB; b++) {
        const lon = -180 + ((c + (a + 0.5) / SUB) * 360) / COLS
        const lat = LAT_TOP - ((r + (b + 0.5) / SUB) * (LAT_TOP - LAT_BOT)) / ROWS
        for (const k of world) {
          if (lat < k.bbox[1] || lat > k.bbox[3]) continue
          if (lon + 360 < k.bbox[0] || lon - 360 > k.bbox[2]) continue
          if (!hit(k, lon, lat)) continue
          votes[k.region] = (votes[k.region] || 0) + 1
          break
        }
      }
    const win = Object.entries(votes).sort((x, y) => y[1] - x[1])[0]
    line += win ? CODE[win[0]] : '.'
  }
  rows.push(line)
}

const src = `// Generated by tools/mapgen.mjs from Natural Earth 110m via world-atlas — do not hand-edit.
// A ${COLS} x ${ROWS} dot raster of the world, each land cell tagged with the dashboard's
// own six region buckets. Precomputed at build time so the site ships no mapping
// library and no topology file: the whole world is the two strings below.
// Equirectangular, ${LAT_TOP}°N to ${Math.abs(LAT_BOT)}°S (Antarctica is cut: no region bucket owns it).
export const MAP_COLS = ${COLS}
export const MAP_ROWS = ${ROWS}
// '.' = ocean; U=US C=Canada E=Europe A=Asia M=Middle East O=Other
export const MAP_REGION_ROWS = [
${rows.map((r) => `  '${r}',`).join('\n')}
]
export const MAP_CODE_TO_REGION = {
  U: 'US',
  C: 'Canada',
  E: 'Europe',
  A: 'Asia',
  M: 'Middle East',
  O: 'Other',
}
`
writeFileSync(OUT, src)
const land = rows.join('').replace(/\./g, '').length
console.error(`wrote ${OUT.pathname} — ${land} land cells of ${COLS * ROWS}`)
for (const r of rows) console.error(r)
