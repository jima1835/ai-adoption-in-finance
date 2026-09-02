import { useState } from 'react'
import { STAGES, TYPE_LABELS, aumUsd, aumUsdApprox, dateSortKey, latestActivity } from '../data.js'
import StageBadge from './StageBadge.jsx'
import Lang from './Lang.jsx'
import FirmLink from './FirmLink.jsx'

const COLUMNS = [
  { key: 'name', label: 'Institution', sortable: true, align: 'left' },
  { key: 'type', label: 'Type', sortable: true, align: 'left' },
  { key: 'region', label: 'Region', sortable: true, align: 'left' },
  { key: 'aum', label: 'AUM', sortable: true, align: 'right' },
  { key: 'stage', label: 'Stage', sortable: true, align: 'left' },
  { key: 'latest_signal', label: 'Latest signal', sortable: false, align: 'left' },
  { key: 'latest_date', label: 'Latest evidence', sortable: true, align: 'right' },
  { key: 'as_of_reviewed', label: 'Last reviewed', sortable: true, align: 'right' },
]

function compare(a, b, key) {
  switch (key) {
    case 'aum':
      return aumUsd(a.aum) - aumUsd(b.aum)
    case 'stage':
      return STAGES.indexOf(a.stage) - STAGES.indexOf(b.stage)
    case 'latest_date':
      // Sort on the same value the cell shows, not on the raw pipeline field —
      // 76 of 84 rows have no latest_date, so sorting by it bunched them at zero.
      return (
        dateSortKey(latestActivity(a)?.date) - dateSortKey(latestActivity(b)?.date)
      )
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
    // WCAG 2.1.1 / axe scrollable-region-focusable — this container scrolls
    // horizontally, so it must be reachable and scrollable by keyboard.
    <div
      className="table-wrap"
      tabIndex={0}
      role="region"
      aria-label="All institutions, scrollable table"
    >
      <table className="inst-table">
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                scope="col"
                data-align={col.align}
                data-sortable={col.sortable}
                aria-sort={
                  col.sortable
                    ? sort.key === col.key
                      ? sort.dir === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : 'none'
                    : undefined
                }
              >
                {col.sortable ? (
                  // WCAG 2.1.1 — a click handler on <th> is mouse-only. The
                  // label is a real button so the table can be sorted from the
                  // keyboard; aria-sort on the <th> announces the current state.
                  <button
                    type="button"
                    className="th-btn th-inner"
                    onClick={() => toggle(col.key)}
                  >
                    {col.label}
                    <span className="th-arrow" data-active={sort.key === col.key} aria-hidden="true">
                      {sort.key === col.key
                        ? sort.dir === 'asc'
                          ? '▲'
                          : '▼'
                        : '↕'}
                    </span>
                    <span className="sr-only">
                      {sort.key === col.key
                        ? `, sorted ${sort.dir === 'asc' ? 'ascending' : 'descending'}. Activate to reverse.`
                        : ', not sorted. Activate to sort by this column.'}
                    </span>
                  </button>
                ) : (
                  <span className="th-inner">{col.label}</span>
                )}
              </th>
            ))}
            <th scope="col" data-align="right">
              <span className="sr-only">Detail</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((inst) => (
            // The row stays clickable for the mouse, but it is no longer
            // announced as a button: it contains a link now, and a button may
            // not contain interactive content. The keyboard path is the
            // explicit control in the last cell.
            <tr key={inst.name} onClick={() => onSelect(inst)}>
              <td className="td-name">
                <FirmLink name={inst.name} />
              </td>
              <td className="td-muted">{TYPE_LABELS[inst.type] || inst.type}</td>
              <td className="td-muted">{inst.region || '—'}</td>
              <td data-align="right" className="td-num">
                {inst.aum}
                {aumUsdApprox(inst.aum) && (
                  <span
                    className="aum-approx"
                    title="Approximate USD at static FX — the original disclosure is the ground truth"
                  >
                    {' '}
                    {aumUsdApprox(inst.aum)}
                  </span>
                )}
              </td>
              <td>
                <StageBadge stage={inst.stage} />
              </td>
              <td className="td-signal">
                {inst.latest_signal ? <Lang>{inst.latest_signal}</Lang> : <span className="td-empty">—</span>}
              </td>
              <td
                data-align="right"
                className="td-num td-muted"
                title={
                  latestActivity(inst)?.fromPipeline
                    ? 'newest automated signal for this row'
                    : 'newest dated source in this row’s curated timeline'
                }
              >
                {latestActivity(inst)?.date || '—'}
              </td>
              <td data-align="right" className="td-num td-muted">
                {inst.as_of_reviewed || '—'}
              </td>
              <td data-align="right" className="td-open">
                <button
                  type="button"
                  className="row-open"
                  onClick={(e) => {
                    e.stopPropagation()
                    onSelect(inst)
                  }}
                >
                  <span aria-hidden="true">›</span>
                  <span className="sr-only">Open {inst.name} detail</span>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
