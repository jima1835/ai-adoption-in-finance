import { useEffect } from 'react'
import { TYPE_LABELS, dateSortKey } from '../data.js'
import StageBadge from './StageBadge.jsx'

// Modal panel: stage + rationale, use_cases, oldest→newest timeline, latest
// signal. Renders gracefully whether an institution has 1 event or 8.
export default function DrillDown({ inst, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!inst) return null

  // Sort by padded key; DISPLAY the raw date string verbatim.
  const events = [...(inst.events || [])].sort(
    (a, b) => dateSortKey(a.date) - dateSortKey(b.date),
  )

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={`${inst.name} detail`}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label="Close">
          ✕
        </button>

        <div className="modal-head">
          <div className="modal-title-row">
            <h2 className="modal-name">{inst.name}</h2>
            <StageBadge stage={inst.stage} size="lg" />
          </div>
          <div className="modal-tags">
            <span>{TYPE_LABELS[inst.type] || inst.type}</span>
            <span className="card-dot">·</span>
            <span>AUM {inst.aum}</span>
          </div>
        </div>

        <section className="modal-section">
          <h3 className="modal-label">Why this stage</h3>
          <p className="modal-rationale">{inst.rationale}</p>
        </section>

        {inst.footnote && (
          <aside className="modal-footnote">
            <span className="footnote-label">Note</span>
            <p>{inst.footnote}</p>
          </aside>
        )}

        {inst.use_cases?.length > 0 && (
          <section className="modal-section">
            <h3 className="modal-label">Use cases</h3>
            <ul className="use-cases">
              {inst.use_cases.map((u) => (
                <li key={u}>{u}</li>
              ))}
            </ul>
          </section>
        )}

        <section className="modal-section">
          <h3 className="modal-label">
            Timeline <span className="modal-label-count">{events.length}</span>
          </h3>
          {events.length === 0 ? (
            <p className="td-empty">No dated public events recorded yet.</p>
          ) : (
            <ol className="timeline">
              {events.map((ev, i) => (
                <li key={i} className="tl-item">
                  <span className="tl-rail" aria-hidden="true">
                    <span className="tl-dot" />
                  </span>
                  <span className="tl-content">
                    <span className="tl-date">{ev.date}</span>
                    <span className="tl-event">{ev.event}</span>
                    {ev.source_url && (
                      <a
                        className="tl-source"
                        href={ev.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        source ↗
                      </a>
                    )}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </section>

        {inst.latest_signal && (
          <section className="modal-section latest-signal">
            <h3 className="modal-label">
              <span className="stamp-dot" data-kind="auto" /> Latest signal
              {inst.latest_date && (
                <span className="modal-label-count">{inst.latest_date}</span>
              )}
            </h3>
            <p className="modal-rationale">{inst.latest_signal}</p>
            {inst.source_url && (
              <a
                className="tl-source"
                href={inst.source_url}
                target="_blank"
                rel="noreferrer"
              >
                source ↗
              </a>
            )}
          </section>
        )}
      </div>
    </div>
  )
}
