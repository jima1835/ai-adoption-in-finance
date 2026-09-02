// Generic pill-group filter — one group per criterion (type, region,
// confidence, AUM band). Client-side, defaults to the group's 'all' key.
export default function FilterPills({ label, groups, value, onChange, counts }) {
  return (
    <div className="filter-group" role="group" aria-label={`Filter by ${label}`}>
      <span className="filter-group-label">{label}</span>
      <div className="type-filter">
        {/* WCAG 4.1.2 — data-active is invisible to assistive tech; these are
            toggles within a group, so aria-pressed carries the state. */}
        {Object.entries(groups).map(([key, group]) => (
          <button
            key={key}
            type="button"
            className="filter-pill"
            data-active={value === key}
            aria-pressed={value === key}
            onClick={() => onChange(key)}
          >
            {group.label}
            <span className="filter-count" aria-hidden="true">
              {counts[key] ?? 0}
            </span>
            <span className="sr-only">, {counts[key] ?? 0} institutions</span>
          </button>
        ))}
      </div>
    </div>
  )
}
