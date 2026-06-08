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
