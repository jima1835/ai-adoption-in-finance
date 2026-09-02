import { REGION_LABELS, REGION_COLORS } from '../data.js'

// Region is the one multi-select filter: clicking Asia then Europe shows both.
// The pills carry the same hue as the map so a colour means one region wherever
// the reader meets it, and each pill states its own selected state through
// aria-pressed rather than through colour.
export default function RegionPills({ value, counts, onToggle }) {
  const none = value.length === 0
  return (
    <div className="filter-group" role="group" aria-label="Filter by Region">
      <span className="filter-group-label">Region</span>
      <div className="type-filter">
        <button
          type="button"
          className="filter-pill"
          data-active={none}
          aria-pressed={none}
          onClick={() => onToggle(null)}
        >
          All
          <span className="filter-count" aria-hidden="true">
            {REGION_LABELS.reduce((n, r) => n + (counts[r] || 0), 0)}
          </span>
          <span className="sr-only">
            {none ? ', showing every region' : ', clear the region selection'}
          </span>
        </button>
        {REGION_LABELS.map((r) => {
          const on = value.includes(r)
          return (
            <button
              key={r}
              type="button"
              className="filter-pill region-pill"
              data-active={on}
              aria-pressed={on}
              style={{ '--region': REGION_COLORS[r] }}
              onClick={() => onToggle(r)}
            >
              <span className="rp-swatch" aria-hidden="true" />
              {r}
              <span className="filter-count" aria-hidden="true">
                {counts[r] || 0}
              </span>
              <span className="sr-only">
                , {counts[r] || 0} institutions
                {on ? '. Selected. Activate to remove.' : '. Activate to add to the selection.'}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
