// Search is literal text, never a regular expression or HTML. Normalize full-
// width characters and accents so aliases and international names work alike.
export function normalizeSearchText(value) {
  return String(value || '')
    .normalize('NFKD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim()
}

export function searchTerms(query) {
  return normalizeSearchText(query)
}

export function institutionSearchText(inst) {
  return [inst.name, ...(inst.aliases || [])]
    .filter(Boolean)
    .map(normalizeSearchText)
    .join('\n')
}

export function matchesSearch(text, query) {
  if (!query) return true
  return String(text)
    .split('\n')
    .some((name) => {
      let from = name.indexOf(query)
      while (from >= 0) {
        if (from === 0 || /[\s(/[—-]/.test(name[from - 1])) return true
        from = name.indexOf(query, from + 1)
      }
      return false
    })
}

// Labels for filters that are already active elsewhere in the dashboard. The
// search input itself never interprets these words as commands.
export const FILTER_TAGS = [
  ...Object.entries(STAGE_LABELS).map(([key, label]) => ({
    criterion: 'stage',
    key,
    label,
  })),
  ...REGION_LABELS.map((label) => ({
    criterion: 'region',
    key: label,
    label,
  })),
  ...[
    ['type', TYPE_GROUPS],
    ['confidence', CONFIDENCE_GROUPS],
    ['aum', AUM_BANDS],
  ].flatMap(([criterion, groups]) =>
    Object.entries(groups)
      .filter(([key]) => key !== 'all')
      .map(([key, group]) => ({ criterion, key, label: group.label })),
  ),
]
import {
  STAGE_LABELS,
  TYPE_GROUPS,
  REGION_LABELS,
  CONFIDENCE_GROUPS,
  AUM_BANDS,
} from './data.js'
