// Generic pill-group filter — one group per criterion (type, region,
// confidence, AUM band, and on the roles page event type and source tier).
// Client-side, defaults to the group's 'all' key.
//
// `unit` names what is being counted, for the screen-reader label only: the
// roles page filters role events, not institutions, and a pill that announces
// the wrong noun is worse than one that announces none.
export default function FilterPills({
  label,
  groups,
  value,
  onChange,
  counts = {},
  unit = 'institutions',
}) {
  return (
    <div
      className="filter-group"
      role="group"
      aria-label={`Filter by ${label}`}
    >
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
            <span className="sr-only">
              , {counts[key] ?? 0} {unit}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
