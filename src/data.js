// Shared constants + pure helpers for the dashboard.

// The classification bar, in adoption order. Order matters: the grid renders
// columns left→right in this sequence and the table sorts stages by index.
export const STAGES = ['exploring', 'piloting', 'scaling', 'embedded']

export const STAGE_LABELS = {
  exploring: 'Exploring',
  piloting: 'Piloting',
  scaling: 'Scaling',
  embedded: 'Embedded',
}

// One-line definitions (shown as column subtitles + in methodology).
export const STAGE_DEFS = {
  exploring:
    'Stated intent, hiring, task forces, "evaluating" — no shipped use case.',
  piloting:
    'Named pilots/POCs, limited deployment, governance build-out — not yet firm-wide production.',
  scaling:
    'Multiple use cases in production, firm-wide rollout, AI as a strategic pillar.',
  embedded: 'AI is core infrastructure across the business.',
}

// The deliberate editorial statement for the intentionally empty column.
export const EMBEDDED_EMPTY_NOTE =
  'No institution qualifies yet — even the most advanced keep humans in control of every decision.'

// Type filter groups. Allocators put capital to work via managers; managers
// run the money. All current rows are allocators; the filter already works
// when asset-manager / hedge-fund rows are added later.
export const TYPE_GROUPS = {
  all: { label: 'All', types: null },
  allocators: {
    label: 'Allocators',
    types: ['pension', 'sovereign-wealth', 'endowment'],
  },
  managers: { label: 'Managers', types: ['asset-manager', 'hedge-fund'] },
}

export const TYPE_LABELS = {
  pension: 'Pension',
  'sovereign-wealth': 'Sovereign Wealth',
  endowment: 'Endowment',
  'asset-manager': 'Asset Manager',
  'hedge-fund': 'Hedge Fund',
}

// Region filter — matches the hand-curated `region` field on each row.
export const REGION_GROUPS = {
  all: { label: 'All', regions: null },
  us: { label: 'US', regions: ['US'] },
  canada: { label: 'Canada', regions: ['Canada'] },
  europe: { label: 'Europe', regions: ['Europe'] },
  'middle-east': { label: 'Middle East', regions: ['Middle East'] },
  asia: { label: 'Asia', regions: ['Asia'] },
  other: { label: 'Other', regions: ['Other'] },
}

// Confidence filter — strength of the public evidence behind the stage call.
export const CONFIDENCE_GROUPS = {
  all: { label: 'All', levels: null },
  high: { label: 'High', levels: ['high'] },
  med: { label: 'Med', levels: ['med'] },
  low: { label: 'Low', levels: ['low'] },
}

// Rough FX to USD for SORTING/BANDING ONLY — the aum string is always
// displayed verbatim. Longest symbols first: 'RMB' must win over 'RM'
// (ringgit) and 'C$'/'A$' over '$'. In this dataset '¥' is JPY only —
// Chinese yuan rows use the 'RMB' prefix (PROMPT.md row style).
const AUM_FX = [
  ['RMB', 0.14],
  ['CNY', 0.14],
  ['DKK', 0.15],
  ['NOK', 0.099],
  ['SEK', 0.1],
  ['C$', 0.73],
  ['A$', 0.65],
  ['RM', 0.24],
  ['₩', 0.00072],
  ['£', 1.3],
  ['€', 1.1],
  ['¥', 0.0067],
  ['$', 1],
]

// Parse "~$390B" / "~£868.7B" / "~₩1,849T" / "~DKK 694bn" → approximate USD.
export function aumUsd(aum) {
  if (!aum) return 0
  const s = String(aum).replace(/,/g, '')
  const m = s.match(/([\d.]+)\s*(T|BN|B|M)?/i)
  if (!m) return 0
  const mult = { T: 1e12, BN: 1e9, B: 1e9, M: 1e6 }[(m[2] || 'B').toUpperCase()]
  const fx = (AUM_FX.find(([sym]) => s.includes(sym)) || ['$', 1])[1]
  return Number(m[1]) * mult * fx
}

// "≈$1.3T" companion label for non-USD aum strings. The verbatim disclosure
// stays the displayed ground truth; this is a rough static-FX translation for
// cross-row comparison only. Returns '' for USD rows and unparseable strings.
export function aumUsdApprox(aum) {
  if (!aum) return ''
  const t = String(aum).replace(/^~\s*/, '')
  if (t.startsWith('$')) return '' // already USD (C$/A$ don't start with $)
  const v = aumUsd(aum)
  if (!v) return ''
  if (v >= 1e12) return `≈$${(v / 1e12).toFixed(1).replace(/\.0$/, '')}T`
  if (v >= 1e9) return `≈$${Math.round(v / 1e9)}B`
  return `≈$${Math.round(v / 1e6)}M`
}

// AUM size bands (approximate USD, see aumUsd).
export const AUM_BANDS = {
  all: { label: 'All', min: 0, max: Infinity },
  sub100: { label: '<$100B', min: 0, max: 100e9 },
  b100_500: { label: '$100–500B', min: 100e9, max: 500e9 },
  b500_1t: { label: '$500B–1T', min: 500e9, max: 1e12 },
  t1plus: { label: '>$1T', min: 1e12, max: Infinity },
}

// Variable-precision date string → comparable number, for SORTING ONLY.
// "2024" → 20240000, "2025-07" → 20250700, "2026-03-24" → 20260324.
// The raw string is always displayed verbatim; this never mutates it.
export function dateSortKey(raw) {
  if (!raw) return 0
  const [y = '0', m = '0', d = '0'] = String(raw).split('-')
  return Number(y) * 10000 + Number(m) * 100 + Number(d)
}

// Newest event/latest_date wins. Empty treated as oldest.
export function maxDate(dates) {
  return dates.filter(Boolean).sort((a, b) => dateSortKey(b) - dateSortKey(a))[0] || ''
}

// ~50-word executive summary, derived at render time from the hand-written
// rationale (+ footnote). Whole sentences until the budget is spent; a single
// over-budget sentence is hard-truncated. No stored field — always in sync.
export function execSummary(inst) {
  const text = [inst.rationale, inst.footnote].filter(Boolean).join(' ')
  if (!text) return ''
  const sentences = text.match(/[^.!?]+[.!?]+["')\]]*\s*/g) || [text]
  const parts = []
  let words = 0
  for (const s of sentences) {
    const w = s.trim().split(/\s+/).length
    if (words > 0 && words + w > 50) break
    parts.push(s.trim())
    words += w
    if (words >= 50) break
  }
  const all = parts.join(' ').split(/\s+/)
  return all.length > 50 ? all.slice(0, 50).join(' ') + '…' : parts.join(' ')
}

// Newest dated public item for a row: the pipeline's latest_date, or — when
// the pipeline hasn't matched anything yet (auto fields start empty on new
// rows) — the newest curated event date. Returns { date, fromPipeline } or
// null when the row has neither.
export function latestActivity(inst) {
  const pipe = inst.latest_date || ''
  const ev = maxDate((inst.events || []).map((e) => e.date))
  if (!pipe && !ev) return null
  return dateSortKey(pipe) >= dateSortKey(ev)
    ? { date: pipe, fromPipeline: true }
    : { date: ev, fromPipeline: false }
}

// A short text initial badge — no external logos are ever fetched.
export function initials(name) {
  const cleaned = name.replace(/\(.*?\)/g, '').trim()
  const words = cleaned.split(/[\s—-]+/).filter(Boolean)
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
}

// Fetch the dashboard state. BASE_URL keeps the path correct under any
// GitHub Pages base; data/ is same-origin via the public/data symlink.
export async function loadInstitutions() {
  const res = await fetch(`${import.meta.env.BASE_URL}data/institutions.json`, {
    cache: 'no-store',
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  if (!Array.isArray(data)) throw new Error('Malformed data: expected an array')
  return data
}

// Shared stage-classification reference (data/stage_definitions.json): the four
// detailed definitions plus _scope_note and _embedded_empty_note. Returns null
// on any failure so the UI degrades to the built-in STAGE_DEFS / EMBEDDED_EMPTY_NOTE.
export async function loadStageDefinitions() {
  try {
    const res = await fetch(
      `${import.meta.env.BASE_URL}data/stage_definitions.json`,
      { cache: 'no-store' },
    )
    if (!res.ok) return null
    const data = await res.json()
    return data && typeof data === 'object' && !Array.isArray(data) ? data : null
  } catch {
    return null
  }
}

// "Assessed, not classified" appendix (data/not_classified.json): institutions
// worked against the methodology whose public record didn't support a stage.
// Returns [] on any failure — the appendix simply doesn't render.
export async function loadNotClassified() {
  try {
    const res = await fetch(
      `${import.meta.env.BASE_URL}data/not_classified.json`,
      { cache: 'no-store' },
    )
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

// Two outcomes only: evidence that never supported a stage (scope failures
// and sourcing-bar failures both collapse here — the reason text carries the
// nuance), vs. rows that were listed and then withdrawn on human review.
export const OUTCOME_LABELS = {
  'no-qualifying-evidence': 'No qualifying evidence',
  'withdrawn-on-review': 'Withdrawn on review',
}

// Resolve helpers that prefer the loaded reference and fall back to constants.
export function stageDefinition(defs, stage) {
  return defs?.[stage] || STAGE_DEFS[stage] || ''
}
export function embeddedNote(defs) {
  return defs?._embedded_empty_note || EMBEDDED_EMPTY_NOTE
}
export function scopeNote(defs) {
  return defs?._scope_note || ''
}


// ---------------------------------------------------------------------------
// Multilingual rendering.
//
// The dataset quotes Japanese, Chinese and Korean sources verbatim, because a
// verbatim original is part of this project's sourcing discipline. On the page
// that created two problems: the document is lang="en", so a screen reader
// pronounced every CJK run with an English voice (WCAG 3.1.2), and a reader who
// does not read the script got nothing at all.
//
// Both are solved at the PRESENTATION layer. institutions.json is human-reviewed
// evidence and is never rewritten. data/translations.json maps each exact CJK run
// to an English rendering; <Lang> shows the English, keeps the original beside it
// in parentheses for the record, and marks that parenthetical aria-hidden so it is
// shown but never spoken. A run with no entry in the map falls back to the original
// carrying a correct `lang`, which is still better than an English voice reading it.
//
// segmentCjk() must mirror the extractor that built the map exactly, or the keys
// will not line up: quoted spans first (they may contain Latin product names that
// must not split the run), then CJK runs in what is left.
// ---------------------------------------------------------------------------
const CJK_CHAR = /[぀-ヿ㐀-䶿一-鿿가-힯]/
const KANA = /[぀-ヿ]/
const HANGUL = /[가-힯]/
// 「…」 and 『…』, non-nesting, capped so a stray opening bracket cannot swallow
// the rest of a long rationale.
const QUOTE_SPAN = /[「『][^」』]{1,400}[」』]/g
const CJK_RUN = /[　-〻぀-ヿ㐀-䶿一-鿿가-힯]+/g
const EDGE = /^[　 ・]+|[　 ・]+$/g

export function cjkLang(run) {
  if (KANA.test(run)) return 'ja'
  if (HANGUL.test(run)) return 'ko'
  if (CJK_CHAR.test(run)) return 'zh'
  return null
}

let TRANSLATIONS = {}

// Returns the English rendering for an exact run, or undefined.
export function translationFor(run) {
  const hit = TRANSLATIONS[run]
  if (typeof hit === 'string') return hit || undefined
  return hit && hit.en ? hit.en : undefined
}

export async function loadTranslations() {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/translations.json`, {
      cache: 'no-store',
    })
    if (!res.ok) return {}
    const json = await res.json()
    TRANSLATIONS = json && json.runs ? json.runs : {}
  } catch {
    TRANSLATIONS = {} // absent or malformed → fall back to showing originals
  }
  return TRANSLATIONS
}

// Splits a string into { text, lang } segments. lang is null for Latin runs.
export function segmentCjk(text) {
  const str = String(text ?? '')
  if (!str || !CJK_CHAR.test(str)) return [{ text: str, lang: null }]

  // Pass 1 — quoted spans, recorded by index so pass 2 can skip them.
  const marks = []
  QUOTE_SPAN.lastIndex = 0
  for (const m of str.matchAll(QUOTE_SPAN)) {
    if (CJK_CHAR.test(m[0])) marks.push([m.index, m.index + m[0].length, m[0]])
  }

  // Pass 2 — CJK runs in the remainder, with the quoted spans blanked out so
  // indices still line up.
  let masked = str
  for (const [a, b] of marks) masked = masked.slice(0, a) + ' '.repeat(b - a) + masked.slice(b)
  CJK_RUN.lastIndex = 0
  for (const m of masked.matchAll(CJK_RUN)) {
    const raw = m[0]
    const lead = raw.length - raw.replace(/^[　 ・]+/, '').length
    const key = raw.replace(EDGE, '')
    if (key && CJK_CHAR.test(key)) marks.push([m.index + lead, m.index + lead + key.length, key])
  }

  marks.sort((x, y) => x[0] - y[0])
  const out = []
  let cursor = 0
  for (const [a, b, run] of marks) {
    if (a < cursor) continue // defensive: never emit overlapping segments
    if (a > cursor) out.push({ text: str.slice(cursor, a), lang: null })
    out.push({ text: run, lang: cjkLang(run) })
    cursor = b
  }
  if (cursor < str.length) out.push({ text: str.slice(cursor), lang: null })
  return out.length ? out : [{ text: str, lang: null }]
}


// ---------------------------------------------------------------------------
// Presentation-layer lookups. Neither file modifies institutions.json.
//   summaries.json — bulleted digests of each row's reviewed rationale
//   homepages.json — firm homepages derived from own-domain evidence URLs that
//                    already passed human review. A firm with no own-domain
//                    evidence gets no link rather than a guessed one.
// ---------------------------------------------------------------------------
let SUMMARIES = {}
let HOMEPAGES = {}

export function summaryFor(name) {
  const s = SUMMARIES[name]
  return Array.isArray(s) && s.length ? s : null
}
export function homepageFor(name) {
  const h = HOMEPAGES[name]
  return h && h.url ? h.url : null
}

export async function loadSummaries() {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/summaries.json`, { cache: 'no-store' })
    if (res.ok) {
      const j = await res.json()
      SUMMARIES = j && j.summaries ? j.summaries : {}
    }
  } catch {
    SUMMARIES = {}
  }
  return SUMMARIES
}

export async function loadHomepages() {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/homepages.json`, { cache: 'no-store' })
    if (res.ok) {
      const j = await res.json()
      HOMEPAGES = j && j.homepages ? j.homepages : {}
    }
  } catch {
    HOMEPAGES = {}
  }
  return HOMEPAGES
}


// The region filter is keyed by group id ('middle-east'), while the map and its
// legend work in region labels ('Middle East'). These two translate between them
// so neither side has to know the other's vocabulary.
export function regionGroupKey(label) {
  const hit = Object.entries(REGION_GROUPS).find(
    ([, g]) => g.regions && g.regions.length === 1 && g.regions[0] === label,
  )
  return hit ? hit[0] : 'all'
}
export function regionLabelFromKey(key) {
  const g = REGION_GROUPS[key]
  return g && g.regions && g.regions.length === 1 ? g.regions[0] : null
}


// The six region buckets, in a fixed order. Both the map and the region pills
// read this, so a colour always means the same region wherever it appears.
export const REGION_LABELS = ['US', 'Canada', 'Europe', 'Asia', 'Middle East', 'Other']

// Categorical palette — identity, not magnitude, so one hue per region rather
// than steps of one hue. Chosen by search against the dataviz validator on the
// dark surface with the ALL-PAIRS pairlist (a map shows all six at once, so
// adjacent-only would be the wrong test) and it passes every check: lightness
// band, chroma floor, all-pairs CVD ΔE 10.1 (target 8), normal-vision ΔE 21.0
// (hard floor 15), and 3:1 contrast against the surface. US keeps the site's
// amber so the dashboard's own identity survives.
export const REGION_COLORS = {
  US: '#ce7e2c',
  Canada: '#586800',
  Europe: '#0066a4',
  Asia: '#a03a6a',
  'Middle East': '#a07ee0',
  Other: '#00ac94',
}


// ---------------------------------------------------------------------------
// data/agreement.json — the human-vs-agent disagreement record.
//
// Built by local/build_agreement.py from institutions.json + not_classified.json
// (both public, so the figures are reproducible from this repo alone). The panel
// that renders it MUST carry the anchoring caveat: the reviewer saw the agent's
// proposed stage before deciding, so this is an upper bound on agreement, not a
// reliability coefficient. Never present a kappa from this file.
// ---------------------------------------------------------------------------
let AGREEMENT = null

export function agreementData() {
  return AGREEMENT
}

export async function loadAgreement() {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/agreement.json`, {
      cache: 'no-store',
    })
    if (res.ok) {
      const j = await res.json()
      AGREEMENT = j && j.stage_agreement ? j : null
    }
  } catch {
    AGREEMENT = null // absent or malformed → the panel simply does not render
  }
  return AGREEMENT
}
