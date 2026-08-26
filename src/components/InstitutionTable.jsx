import { useState } from 'react'
import { STAGES, TYPE_LABELS, dateSortKey } from '../data.js'
import StageBadge from './StageBadge.jsx'

// Parse "~$390B" / "~$2.1T" → a comparable number for AUM sorting.
function aumValue(aum) {
  if (!aum) return 0
  const m = String(aum).match(/([\d.]+)\s*([TBM])?/i)
  if (!m) return 0
  const mult = { T: 1e12, B: 1e9, M: 1e6 }[(m[2] || 'B').toUpperCase()] || 1
  return Number(m[1]) * mult
}

const COLUMNS = [
  { key: 'name', label: 'Institution', sortable: true, align: 'left' },
  { key: 'type', label: 'Type', sortable: true, align: 'left' },
  { key: 'aum', label: 'AUM', sortable: true, align: 'right' },
  { key: 'stage', label: 'Stage', sortable: true, align: 'left' },
  { key: 'latest_signal', label: 'Latest signal', sortable: false, align: 'left' },
  { key: 'latest_date', label: 'Signal date', sortable: true, align: 'right' },
  { key: 'as_of_reviewed', label: 'Last reviewed', sortable: true, align: 'right' },
]

function compare(a, b, key) {
  switch (key) {
    case 'aum':
      return aumValue(a.aum) - aumValue(b.aum)
    case 'stage':
      return STAGES.indexOf(a.stage) - STAGES.indexOf(b.stage)
    case 'latest_date':
      return dateSortKey(a.latest_date) - dateSortKey(b.latest_date)
    default:
      return String(a[key] || '').localeCompare(String(b[key] || ''))
  }
}

export default function InstitutionTable({ institutions, onSelect }) {
  const [sort, setSort] = useState({ key: 'stage', dir: 'desc' })

  const rows = [...institutions].sort((a, b) => {
    const c = compare(a, b, sort.key)
    return sort.dir === 'asc' ? c : -c
  })

  function toggle(key) {
    setSort((s) =>
      s.key === key
        ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: key === 'name' ? 'asc' : 'desc' },
    )
  }

  return (
    <div className="table-wrap">
      <table className="inst-table">
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                data-align={col.align}
                data-sortable={col.sortable}
                aria-sort={
                  sort.key === col.key
                    ? sort.dir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
                onClick={col.sortable ? () => toggle(col.key) : undefined}
              >
                <span className="th-inner">
                  {col.label}
                  {col.sortable && (
                    <span className="th-arrow" data-active={sort.key === col.key}>
                      {sort.key === col.key
                        ? sort.dir === 'asc'
                          ? '▲'
                          : '▼'
                        : '↕'}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((inst) => (
            <tr key={inst.name} onClick={() => onSelect(inst)} tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelect(inst)
                }
              }}>
              <td className="td-name">{inst.name}</td>
              <td className="td-muted">{TYPE_LABELS[inst.type] || inst.type}</td>
              <td data-align="right" className="td-num">{inst.aum}</td>
              <td>
                <StageBadge stage={inst.stage} />
              </td>
              <td className="td-signal">
                {inst.latest_signal || <span className="td-empty">—</span>}
              </td>
              <td data-align="right" className="td-num td-muted">
                {inst.latest_date || '—'}
              </td>
              <td data-align="right" className="td-num td-muted"
                title="Date a human last reviewed this row's classification against its public evidence">
                {inst.as_of_reviewed || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
