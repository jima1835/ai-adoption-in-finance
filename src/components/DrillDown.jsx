import { useEffect, useRef } from 'react'
import { TYPE_LABELS, aumUsdApprox, dateSortKey, summaryFor } from '../data.js'
import StageBadge from './StageBadge.jsx'
import Lang from './Lang.jsx'
import FirmLink from './FirmLink.jsx'

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])'

// Modal panel, in reading order: use cases → timeline → why this stage.
//
// Use cases lead because they are the concrete, scannable answer to "what does
// this firm actually do with AI". The dated record follows. The stage argument
// comes last, once the reader has seen what it is arguing from — a short derived
// digest, with the complete human-reviewed rationale one disclosure away.
//
// There is no separate "latest signal" section. Across the corpus every row that
// has a latest_signal duplicates an event that is already in the timeline (all of
// them matched on source URL), so it was printing the same thing twice. Instead
// the timeline marks its most recent entry — preferring the one the latest_signal
// points at — as the latest signal.
export default function DrillDown({ inst, onClose }) {
  const panelRef = useRef(null)
  const closeRef = useRef(null)

  // WCAG 2.4.3 Focus Order / 4.1.2. Without this the dialog is opened by a
  // click but focus stays behind it, so a keyboard or screen-reader user can
  // never reach the timeline, the sources or the rationale — the whole point
  // of the panel. Move focus in, keep it in, and put it back where it started.
  useEffect(() => {
    const opener = document.activeElement
    closeRef.current?.focus()
    document.body.classList.add('modal-open')

    const onKey = (e) => {
      if (e.key === 'Escape') return onClose()
      if (e.key !== 'Tab') return
      const nodes = [...(panelRef.current?.querySelectorAll(FOCUSABLE) || [])].filter(
        (el) => el.offsetParent !== null,
      )
      if (!nodes.length) return
      const first = nodes[0]
      const last = nodes[nodes.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.classList.remove('modal-open')
      if (opener instanceof HTMLElement) opener.focus()
    }
  }, [onClose])

  if (!inst) return null

  // Sort by padded key; DISPLAY the raw date string verbatim.
  const bullets = summaryFor(inst.name)

  const events = [...(inst.events || [])].sort(
    (a, b) => dateSortKey(a.date) - dateSortKey(b.date),
  )

  // The latest signal is the most recent dated event, full stop — exactly one per
  // timeline, and a claim that is always true.
  //
  // The row's own source_url looked like a better pointer, but it is not: on two
  // rows it names an event that is not the newest (NBIM points at 2026-03-24 when
  // a reviewed 2026-04-28 event exists; GIC points at a 2023 item while its own
  // latest_date is 2026-03-17). Badging those as "latest" would have been wrong,
  // so the timeline's own ordering decides.
  const latestIdx = events.length - 1

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        ref={panelRef}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="modal-close"
          onClick={onClose}
          ref={closeRef}
          aria-label={`Close ${inst.name} detail`}
        >
          <span aria-hidden="true">✕</span>
        </button>

        <div className="modal-head">
          <div className="modal-title-row">
            <h2 className="modal-name" id="modal-title">
              <FirmLink name={inst.name} />
            </h2>
            <StageBadge stage={inst.stage} size="lg" />
          </div>
          <div className="modal-tags">
            <span>{TYPE_LABELS[inst.type] || inst.type}</span>
            {inst.region && (
              <>
                <span className="card-dot">·</span>
                <span>{inst.region}</span>
              </>
            )}
            <span className="card-dot">·</span>
            <span>
              AUM {inst.aum}
              {aumUsdApprox(inst.aum) && (
                <span className="aum-approx">
                  {' '}
                  {aumUsdApprox(inst.aum)}
                  <span className="sr-only">
                    {' '}approximate USD at static FX
                  </span>
                </span>
              )}
            </span>
            {inst.confidence && (
              <>
                <span className="card-dot">·</span>
                <span>
                  <span
                    className="conf-dot"
                    data-conf={inst.confidence}
                    aria-hidden="true"
                  />{' '}
                  {inst.confidence} confidence
                  <span className="sr-only">
                    {' '}in the public evidence for this stage
                  </span>
                </span>
              </>
            )}
            <span className="card-dot">·</span>
            <span>
              Reviewed {inst.as_of_reviewed || '—'}
              <span className="sr-only">
                {' '}— date a human last reviewed this classification
              </span>
            </span>
          </div>
        </div>

        {inst.use_cases?.length > 0 && (
          <section className="modal-section">
            <h3 className="modal-label">Use cases</h3>
            <ul className="use-cases">
              {inst.use_cases.map((u) => (
                <li key={u}>
                  <Lang>{u}</Lang>
                </li>
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
                <li
                  key={i}
                  className="tl-item"
                  data-latest={i === latestIdx ? 'true' : undefined}
                >
                  <span className="tl-rail" aria-hidden="true">
                    <span className="tl-dot" />
                  </span>
                  <span className="tl-content">
                    <span className="tl-date">
                      {ev.date}
                      {i === latestIdx && (
                        <span className="tl-badge">
                          <span aria-hidden="true">⚡</span> latest signal
                        </span>
                      )}
                    </span>
                    <span className="tl-event"><Lang>{ev.event}</Lang></span>
                    {ev.source_url && (
                      <a
                        className="tl-source"
                        href={ev.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        source <span aria-hidden="true">↗</span>
                        <span className="sr-only">
                          for {ev.date} — opens in a new tab
                        </span>
                      </a>
                    )}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className="modal-section">
          <h3 className="modal-label">Why this stage</h3>
          {bullets ? (
            <>
              <ul className="why-bullets">
                {bullets.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
              <details className="why-full">
                <summary>Full reviewed rationale</summary>
                <p className="modal-rationale">
                  <Lang>{inst.rationale}</Lang>
                </p>
              </details>
            </>
          ) : (
            <p className="modal-rationale">
              <Lang>{inst.rationale}</Lang>
            </p>
          )}
        </section>

      </div>
    </div>
  )
}
