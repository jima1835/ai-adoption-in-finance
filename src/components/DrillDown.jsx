import { useEffect, useRef } from 'react'
import {
  TYPE_LABELS,
  EVENT_TYPE_LABELS,
  TITLE_LABELS,
  HIGHLIGHT_LABELS,
  aumUsdApprox,
  dateSortKey,
  descriptionFor,
  highlightFor,
  jobPostingFor,
  mediumLabel,
  publisherFor,
  rolesForInstitution,
  summaryFor,
  summaryParts,
} from '../data.js'
import StageBadge from './StageBadge.jsx'
import Lang from './Lang.jsx'
import FirmLink from './FirmLink.jsx'

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])'

// A source link, labelled by who published it. "source ↗" said nothing about
// provenance; the publisher's name — and, off the press, the medium — lets a
// reader weigh an item before opening it. The visible tag is aria-hidden and the
// medium is spoken from the sr-only text instead, so a screen reader hears
// "CalSTRS, firm site, for 2024-07 — opens in a new tab" with a pause where the
// eye sees a dot, rather than the name and the tag run together. `context` names
// what the link is for ("2024-07", "the 2025-03 role event").
function SourceLink({ href, context }) {
  const pub = publisherFor(href)
  const name = pub?.name || 'source'
  const tag = mediumLabel(pub?.medium)
  return (
    <a className="tl-source" href={href} target="_blank" rel="noreferrer">
      {name}
      {tag && (
        <span className="tl-medium" aria-hidden="true">
          {' · '}
          {tag}
        </span>
      )}{' '}
      <span aria-hidden="true">↗</span>
      <span className="sr-only">
        {tag ? `, ${tag}` : ''}, for {context} — opens in a new tab
      </span>
    </a>
  )
}

// Modal panel. The head carries the name, the stage, a one-line intro (who the
// firm is) and the tags; below it, in reading order: use cases → timeline → why
// this stage.
//
// Use cases lead because they are the concrete, scannable answer to "what does
// this firm actually do with AI". The dated record follows, newest first. The
// stage argument comes last, once the reader has seen what it is arguing from —
// a short derived digest, with the complete human-reviewed rationale one
// disclosure away. The row's footnote — the scope call: what was seen but NOT
// counted toward the stage, and why — closes that section as a scope note, so
// the argument and its boundary are read together.
//
// There is no separate "latest signal" section. Across the corpus every row that
// has a latest_signal duplicates an event that is already in the timeline (all of
// them matched on source URL), so it was printing the same thing twice. Instead
// the timeline marks its most recent entry — preferring the one the latest_signal
// points at — as the latest signal.
export default function DrillDown({ inst, roles = [], onClose }) {
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
      const nodes = [
        ...(panelRef.current?.querySelectorAll(FOCUSABLE) || []),
      ].filter((el) => el.offsetParent !== null)
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

  const bullets = summaryFor(inst.name)
  const intro = descriptionFor(inst.name)

  // Newest first: the reader meets the latest signal before the history behind
  // it. Sort by padded key; DISPLAY the raw date string verbatim.
  const allEvents = [...(inst.events || [])].sort(
    (a, b) => dateSortKey(b.date) - dateSortKey(a.date),
  )
  const postings = allEvents
    .map((event) => ({ event, posting: jobPostingFor(inst.name, event) }))
    .filter(({ posting }) => posting)
  const events = allEvents.filter((event) => !jobPostingFor(inst.name, event))

  // Looked up once per event so the legend and the rows cannot disagree.
  const highlights = events.map((ev) => highlightFor(inst.name, ev))
  const hasHighlight = highlights.some(Boolean)

  // Role events are a separate record on a separate unit (METHODOLOGY §11).
  // The section is hidden when there are none: an empty "Leadership" heading
  // would read as "this firm has no AI leadership", which is a claim this
  // corpus has not made.
  const roleEvents = rolesForInstitution(roles, inst)

  // The latest signal is the most recent dated event, full stop — exactly one per
  // timeline, and a claim that is always true. Newest-first puts it at index 0.
  //
  // The row's own source_url looked like a better pointer, but it is not: on two
  // rows it names an event that is not the newest (NBIM points at 2026-03-24 when
  // a reviewed 2026-04-28 event exists; GIC points at a 2023 item while its own
  // latest_date is 2026-03-17). Badging those as "latest" would have been wrong,
  // so the timeline's own ordering decides.
  const latestEvent = allEvents[0] || null
  const isLatest = (event) =>
    event === latestEvent ||
    (event?.date === latestEvent?.date &&
      event?.source_url === latestEvent?.source_url)

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
          {intro && (
            <p className="modal-intro">
              <Lang>{intro}</Lang>
            </p>
          )}
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
                  <span className="sr-only"> approximate USD at static FX</span>
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
                  {inst.confidence} evidence confidence
                  <span className="sr-only">
                    {' '}
                    in the public evidence for this stage
                  </span>
                </span>
              </>
            )}
            <span className="card-dot">·</span>
            <span>
              Reviewed {inst.as_of_reviewed || '—'}
              <span className="sr-only">
                {' '}
                — date a human last reviewed this classification
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
          {hasHighlight && (
            <p className="modal-note">
              Boxed entries disclose a named tool in production, hard numbers,
              or live capital.
            </p>
          )}
          {events.length === 0 ? (
            <p className="td-empty">No dated public events recorded yet.</p>
          ) : (
            <ol className="timeline">
              {events.map((ev, i) => {
                const hl = highlights[i]
                return (
                  <li
                    key={i}
                    className="tl-item"
                    data-latest={isLatest(ev) ? 'true' : undefined}
                    data-highlight={hl ? hl.kind : undefined}
                  >
                    {/* The date stands in its own column, left of the rail,
                        so the eye can run straight down the record; the
                        content column stays clear for the callouts. Newest
                        first, so the ⚡ badge always hangs under the top date. */}
                    <span className="tl-when">
                      <span className="tl-date">{ev.date}</span>
                      {isLatest(ev) && (
                        <span className="tl-badge">
                          <span aria-hidden="true">⚡</span> latest
                          <span className="sr-only"> signal</span>
                        </span>
                      )}
                    </span>
                    <span className="tl-rail" aria-hidden="true">
                      <span className="tl-dot" />
                    </span>
                    <span className="tl-content">
                      {/* The kind is text, never colour alone: the box says
                          "this matters", the pill says why. */}
                      {hl && (
                        <span className="tl-tags">
                          <span className="tl-kind">
                            {HIGHLIGHT_LABELS[hl.kind] || hl.kind}
                          </span>
                          {hl.label && (
                            <span className="tl-lead">{hl.label}</span>
                          )}
                        </span>
                      )}
                      <span className="tl-event">
                        <Lang>{ev.event}</Lang>
                      </span>
                      {ev.source_url && (
                        <SourceLink href={ev.source_url} context={ev.date} />
                      )}
                    </span>
                  </li>
                )
              })}
            </ol>
          )}
        </section>

        {postings.length > 0 && (
          <section className="modal-section">
            <h3 className="modal-label">
              Job postings{' '}
              <span className="modal-label-count">{postings.length}</span>
            </h3>
            <p className="modal-note">
              Advertised roles are hiring signals. They do not prove the work
              has shipped or that a candidate was hired.
            </p>
            <ul className="job-list">
              {postings.map(({ event, posting }) => (
                <li
                  key={`${event.date}-${event.source_url}`}
                  className="job-item"
                  data-latest={isLatest(event) ? 'true' : undefined}
                >
                  <span className="job-date">
                    {event.date}
                    {isLatest(event) && (
                      <span className="tl-badge">
                        <span aria-hidden="true">⚡</span> latest
                        <span className="sr-only"> signal</span>
                      </span>
                    )}
                  </span>
                  <span className="job-body">
                    <strong className="job-title">{posting.role}</strong>
                    <span className="job-wording">
                      <Lang>{posting.ai_wording}</Lang>
                    </span>
                    <SourceLink
                      href={event.source_url}
                      context={`the ${event.date} job posting`}
                    />
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {roleEvents.length > 0 && (
          <section className="modal-section">
            <h3 className="modal-label">
              Leadership{' '}
              <span className="modal-label-count">{roleEvents.length}</span>
            </h3>
            <p className="modal-note">
              Dated AI-leadership role events, recorded separately from the
              stage. A hire is an input to adoption, not evidence of it — none
              of these moved the classification above.
            </p>
            <ul className="role-list">
              {roleEvents.map((r) => (
                <li key={r.id} className="role-item">
                  <span className="role-date">{r.date}</span>
                  <span className="role-body">
                    <span className="role-title">
                      {TITLE_LABELS[r.title_normalized] || r.title_normalized}
                      {r.person ? ` — ${r.person}` : ''}
                    </span>
                    <span className="role-meta">
                      {EVENT_TYPE_LABELS[r.event_type] || r.event_type}
                      {r.scope !== 'unknown' &&
                        ` · ${r.scope.replace('_', ' ')}`}
                      {r.reporting_line !== 'unknown' &&
                        ` · reports to ${r.reporting_line.toUpperCase()}`}
                    </span>
                    {r.source_url && (
                      <SourceLink
                        href={r.source_url}
                        context={`the ${r.date} role event`}
                      />
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="modal-section">
          <h3 className="modal-label">Why this stage</h3>
          {bullets ? (
            <>
              <ul className="why-bullets">
                {bullets.map((b, i) => {
                  const { title, context } = summaryParts(b, i)
                  return (
                    <li key={i}>
                      <strong>{title}</strong>
                      <span>{context}</span>
                    </li>
                  )
                })}
              </ul>
            </>
          ) : null}
          <details className="why-full">
            <summary>Full reviewed rationale</summary>
            <p className="modal-rationale">
              <Lang>{inst.rationale}</Lang>
            </p>
          </details>
          {inst.footnote && (
            <details className="why-full scope-full">
              <summary>Scope note</summary>
              <div className="modal-footnote">
                <p>
                  <Lang>{inst.footnote}</Lang>
                </p>
              </div>
            </details>
          )}
        </section>
      </div>
    </div>
  )
}
