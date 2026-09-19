import { useMemo, useState } from 'react'
import {
  EVENT_TYPE_LABELS,
  TITLE_LABELS,
  REPORTING_LINE_LABELS,
  TYPE_GROUPS,
  TYPE_LABELS,
  REGION_LABELS,
  dateSortKey,
} from '../data.js'
import FilterPills from './FilterPills.jsx'

// AI leadership roles (METHODOLOGY §11).
//
// The unit of observation is a ROLE EVENT, not a person and not an institution:
// one row here says that something happened to an AI-leadership role on a date,
// with a source. A firm can appear several times, and a person can appear twice
// under `retitled` without that being a second role.
//
// This view shows no stage and links to none. A hire is an input to adoption,
// not evidence of it, and putting the two side by side would invite exactly the
// inference METHODOLOGY §3 refuses to make.

const EVENT_GROUPS = {
  all: { label: 'All', types: null },
  created: { label: 'Created', types: ['created'] },
  hired: { label: 'Hired', types: ['hired'] },
  retitled: { label: 'Retitled', types: ['retitled'] },
  departed: { label: 'Departed', types: ['departed'] },
}

const TIER_GROUPS = {
  all: { label: 'All', tiers: null },
  T1: { label: 'T1', tiers: ['T1'] },
  T2: { label: 'T2', tiers: ['T2'] },
  T3: { label: 'T3', tiers: ['T3'] },
}

export default function RolesView({
  roles = [],
  notFound = [],
  institutions = [],
}) {
  const [filters, setFilters] = useState({
    type: 'all',
    region: 'all',
    event: 'all',
    tier: 'all',
  })

  // Role events carry an institution name; type and region live on the
  // institution row. Exact, case-insensitive match on name and aliases — the
  // same key the engine uses, with no fuzzy fallback.
  const byName = useMemo(() => {
    const map = new Map()
    for (const inst of institutions) {
      for (const key of [inst.name, ...(inst.aliases || [])]) {
        if (key) map.set(String(key).trim().toLowerCase(), inst)
      }
    }
    return map
  }, [institutions])

  const rows = useMemo(
    () =>
      roles
        .map((r) => ({
          ...r,
          inst:
            byName.get(
              String(r.institution || '')
                .trim()
                .toLowerCase(),
            ) || null,
        }))
        .sort((a, b) => dateSortKey(b.date) - dateSortKey(a.date)),
    [roles, byName],
  )

  // One predicate, taken over a filter object rather than over component state,
  // so the faceted counts below can ask "what if this one pill were different?"
  // without touching state.
  const matchesWith = (r, f) => {
    const typeGroup = TYPE_GROUPS[f.type]
    if (typeGroup?.types && !typeGroup.types.includes(r.inst?.type))
      return false
    if (f.region !== 'all' && r.inst?.region !== f.region) return false
    const eventGroup = EVENT_GROUPS[f.event]
    if (eventGroup?.types && !eventGroup.types.includes(r.event_type))
      return false
    const tierGroup = TIER_GROUPS[f.tier]
    if (tierGroup?.tiers && !tierGroup.tiers.includes(r.source_tier))
      return false
    return true
  }

  const filtered = rows.filter((r) => matchesWith(r, filters))
  const setFilter = (key) => (value) =>
    setFilters((f) => ({ ...f, [key]: value }))

  // Faceted counts: each group's numbers reflect the OTHER active filters, so a
  // pill always says how many rows selecting it would leave on screen — the
  // same behaviour the dashboard's pills have.
  const countsFor = (criterion, groups) =>
    Object.fromEntries(
      Object.keys(groups).map((key) => [
        key,
        rows.filter((r) => matchesWith(r, { ...filters, [criterion]: key }))
          .length,
      ]),
    )

  const regionGroups = useMemo(
    () => ({
      all: { label: 'All' },
      ...Object.fromEntries(REGION_LABELS.map((r) => [r, { label: r }])),
    }),
    [],
  )

  return (
    <article className="roles-view">
      <h2 className="prose-h1">AI leadership roles</h2>
      <p className="prose-lede">
        Dated, publicly sourced AI-leadership role events at the institutions in
        this corpus — a role created, a person hired into it, a leader retitled,
        a departure, a remit expanded. The unit is the <strong>event</strong>,
        not the person.
      </p>
      <p className="roles-caveat">
        A hire is an input to AI adoption, not evidence of it. Nothing on this
        page moves an institution&rsquo;s adoption stage, and no stage is shown
        here. See <a href="#/methodology">Methodology §11</a> for the recording
        rules, and{' '}
        <a
          href="https://github.com/jima1835/ai-adoption-in-finance/blob/main/SOURCES.md"
          target="_blank"
          rel="noreferrer"
        >
          SOURCES.md
        </a>{' '}
        for the source tiers.
      </p>

      {roles.length === 0 ? (
        <div className="state-msg" role="status">
          <strong>No role events recorded yet.</strong>
          <span className="state-detail">
            The module is live and deliberately unpopulated: the schema, the
            review gate and the collection sweep ship before any data does, so
            the first record enters against published rules rather than rules
            written to fit it.
          </span>
          <span className="state-hint">
            Every event is filed by a human against its source, exactly as an
            institution row is.
          </span>
        </div>
      ) : (
        <>
          <div className="controls">
            <div className="filter-groups">
              <FilterPills
                label="Type"
                groups={TYPE_GROUPS}
                value={filters.type}
                onChange={setFilter('type')}
                counts={countsFor('type', TYPE_GROUPS)}
                unit="role events"
              />
              <FilterPills
                label="Region"
                groups={regionGroups}
                value={filters.region}
                onChange={setFilter('region')}
                counts={countsFor('region', regionGroups)}
                unit="role events"
              />
              <FilterPills
                label="Event"
                groups={EVENT_GROUPS}
                value={filters.event}
                onChange={setFilter('event')}
                counts={countsFor('event', EVENT_GROUPS)}
                unit="role events"
              />
              <FilterPills
                label="Tier"
                groups={TIER_GROUPS}
                value={filters.tier}
                onChange={setFilter('tier')}
                counts={countsFor('tier', TIER_GROUPS)}
                unit="role events"
              />
            </div>
            <span className="controls-hint" role="status" aria-live="polite">
              {filtered.length} of {rows.length} role event
              {rows.length === 1 ? '' : 's'} shown
            </span>
          </div>

          <div className="table-wrap" tabIndex={0}>
            <table className="inst-table roles-table">
              <thead>
                <tr>
                  <th scope="col">Institution</th>
                  <th scope="col">Title</th>
                  <th scope="col">Person</th>
                  <th scope="col">Event</th>
                  <th scope="col">Date</th>
                  <th scope="col">Reports to</th>
                  <th scope="col">Source</th>
                  <th scope="col">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id}>
                    <td>
                      {r.institution}
                      {r.inst && (
                        <span className="roles-sub">
                          {TYPE_LABELS[r.inst.type] || r.inst.type} ·{' '}
                          {r.inst.region}
                        </span>
                      )}
                    </td>
                    <td>
                      {TITLE_LABELS[r.title_normalized] || r.title_normalized}
                      <span className="roles-sub" lang={r.language}>
                        {r.title_verbatim}
                      </span>
                    </td>
                    {/* An unnamed role is a complete record, not a gap. */}
                    <td>
                      {r.person || (
                        <span className="roles-null">not named</span>
                      )}
                    </td>
                    <td>{EVENT_TYPE_LABELS[r.event_type] || r.event_type}</td>
                    <td>{r.date}</td>
                    <td>
                      {REPORTING_LINE_LABELS[r.reporting_line] ||
                        r.reporting_line}
                    </td>
                    <td>
                      <a href={r.source_url} target="_blank" rel="noreferrer">
                        {r.source_tier} <span aria-hidden="true">↗</span>
                        <span className="sr-only">
                          {' '}
                          — source for {r.institution}, opens in a new tab
                        </span>
                      </a>
                    </td>
                    <td>
                      <span
                        className="conf-dot"
                        data-conf={r.confidence}
                        aria-hidden="true"
                      />{' '}
                      {r.confidence}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {notFound.length > 0 && (
        <section
          className="nc-strip"
          aria-label="Searched, no qualifying role evidence"
        >
          <header className="nc-strip-head">
            <h3 className="section-title">Searched, nothing qualifying</h3>
            <span className="nc-strip-count">{notFound.length}</span>
            <span className="nc-strip-note">
              institutions searched whose public record carried no qualifying
              AI-leadership role event — without this, a firm that was searched
              and came up empty is indistinguishable from one never searched
            </span>
          </header>
          <div className="nc-strip-cards">
            {notFound.map((n, i) => (
              <div key={`${n.institution}-${i}`} className="nc-chip">
                <span className="nc-chip-name">{n.institution}</span>
                <span className="nc-chip-meta">searched {n.searched_on}</span>
                <span className="nc-outcome" data-outcome={n.outcome}>
                  {n.outcome === 'withdrawn-on-review'
                    ? 'Withdrawn on review'
                    : 'No qualifying evidence'}
                </span>
                {n.reason && <span className="sr-only">. {n.reason}</span>}
              </div>
            ))}
          </div>
        </section>
      )}
    </article>
  )
}
