import { TYPE_LABELS } from '../data.js'
import StageBadge from './StageBadge.jsx'
import Lang from './Lang.jsx'

export default function MobileInstitutions({ institutions, onSelect }) {
  const rows = [...institutions].sort((a, b) => a.name.localeCompare(b.name))
  return (
    <section
      className="mobile-institutions"
      aria-labelledby="mobile-institutions-title"
    >
      <h2 id="mobile-institutions-title" className="section-title">
        Classified institutions
      </h2>
      <p className="search-help">
        Alphabetical order · select a firm for its evidence
      </p>
      {rows.length === 0 ? (
        <p className="col-empty">
          No classified institutions match. Clear the name search or reset the
          filters.
        </p>
      ) : (
        <div className="mobile-institution-list">
          {rows.map((inst) => (
            <button
              type="button"
              className="mobile-institution"
              key={inst.name}
              onClick={() => onSelect(inst)}
            >
              <span>
                <strong>
                  <Lang>{inst.name}</Lang>
                </strong>
                <span className="mobile-institution-meta">
                  {TYPE_LABELS[inst.type] || inst.type} · {inst.region}
                </span>
              </span>
              <StageBadge stage={inst.stage} />
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
