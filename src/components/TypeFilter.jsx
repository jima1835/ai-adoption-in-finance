import { TYPE_GROUPS } from '../data.js'

// [All] [Allocators] [Managers] — client-side, defaults to All.
export default function TypeFilter({ value, onChange, counts }) {
  return (
    <div className="type-filter" role="group" aria-label="Filter by type">
      {Object.entries(TYPE_GROUPS).map(([key, group]) => (
        <button
          key={key}
          className="filter-pill"
          data-active={value === key}
          onClick={() => onChange(key)}
        >
          {group.label}
          <span className="filter-count">{counts[key] ?? 0}</span>
        </button>
      ))}
    </div>
  )
}
