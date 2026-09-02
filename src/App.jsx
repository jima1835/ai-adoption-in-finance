import { useEffect, useMemo, useState } from 'react'
import {
  TYPE_GROUPS,
  TYPE_LABELS,
  CONFIDENCE_GROUPS,
  AUM_BANDS,
  OUTCOME_LABELS,
  aumUsd,
  maxDate,
  latestActivity,
  loadStageDefinitions,
  loadNotClassified,
  loadTranslations,
  loadSummaries,
  loadHomepages,
  REGION_LABELS,
  scopeNote,
} from './data.js'
import { useInstitutions } from './useInstitutions.js'
import Header from './components/Header.jsx'
import Footer from './components/Footer.jsx'
import FilterPills from './components/FilterPills.jsx'
import RegionPills from './components/RegionPills.jsx'
import PhaseGrid from './components/PhaseGrid.jsx'
import StageStrip from './components/StageStrip.jsx'
import RegionMap from './components/RegionMap.jsx'
import InstitutionTable from './components/InstitutionTable.jsx'
import DrillDown from './components/DrillDown.jsx'
import Methodology from './components/Methodology.jsx'

// Minimal hash routing — no router dependency. #/methodology ↔ dashboard.
function routeFromHash() {
  return window.location.hash.replace(/^#\/?/, '') === 'methodology'
    ? 'methodology'
    : 'dashboard'
}

// One predicate per filter criterion; 'all' (null members) always passes.
const MATCHERS = {
  // Driven by the stage strip, not by a pill group — 'all' passes everything.
  stage: (i, key) => key === 'all' || i.stage === key,
  type: (i, key) => {
    const g = TYPE_GROUPS[key]
    return !g?.types || g.types.includes(i.type)
  },
  // Multi-select: an empty selection means "all". Held as region LABELS so the
  // map and the pills speak the same language.
  region: (i, sel) => !sel || sel.length === 0 || sel.includes(i.region),
  confidence: (i, key) => {
    const g = CONFIDENCE_GROUPS[key]
    return !g?.levels || g.levels.includes(i.confidence)
  },
  aum: (i, key) => {
    if (key === 'all' || !AUM_BANDS[key]) return true
    const v = aumUsd(i.aum)
    const b = AUM_BANDS[key]
    return v >= b.min && v < b.max
  },
}

export default function App() {
  const [route, setRoute] = useState(routeFromHash)
  const [filters, setFilters] = useState({
    stage: 'all',
    type: 'all',
    region: [],
    confidence: 'all',
    aum: 'all',
  })
  const [selected, setSelected] = useState(null)
  const [stageDefs, setStageDefs] = useState(null)
  const [notClassified, setNotClassified] = useState([])
  // The translation map lives in a module-level cache in data.js; this counter
  // exists only to re-render the tree once it has loaded.
  const [, setTranslationsReady] = useState(0)

  // Live data: snappy poll in dev (edit the JSON → see it), gentle in prod.
  const {
    status,
    data: institutions,
    error,
  } = useInstitutions({ pollMs: import.meta.env.DEV ? 2000 : 60000 })

  // Stage-classification reference — static, fetched once; null → fall back to
  // the built-in constants, so the UI never breaks if the file is absent.
  useEffect(() => {
    let live = true
    loadStageDefinitions().then((d) => live && setStageDefs(d))
    loadNotClassified().then((d) => live && setNotClassified(d))
    Promise.all([loadTranslations(), loadSummaries(), loadHomepages()]).then(
      ([m]) => live && setTranslationsReady(Object.keys(m).length),
    )
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    const onHash = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  function navigate(next) {
    window.location.hash = next === 'methodology' ? '/methodology' : '/'
    setRoute(next)
  }

  const filtered = useMemo(
    () =>
      institutions.filter((i) =>
        Object.entries(filters).every(([c, key]) => MATCHERS[c](i, key)),
      ),
    [institutions, filters],
  )

  // Faceted counts: each group's numbers reflect the OTHER active filters, so
  // a pill always shows how many rows selecting it would leave on screen.
  const counts = useMemo(() => {
    const facet = (criterion, groups) => {
      const base = institutions.filter((i) =>
        Object.entries(filters).every(
          ([c, key]) => c === criterion || MATCHERS[c](i, key),
        ),
      )
      return Object.fromEntries(
        Object.keys(groups).map((k) => [
          k,
          base.filter((i) => MATCHERS[criterion](i, k)).length,
        ]),
      )
    }
    const regionBase = institutions.filter((i) =>
      Object.entries(filters).every(
        ([c, key]) => c === 'region' || MATCHERS[c](i, key),
      ),
    )
    return {
      type: facet('type', TYPE_GROUPS),
      region: Object.fromEntries(
        REGION_LABELS.map((r) => [r, regionBase.filter((i) => i.region === r).length]),
      ),
      confidence: facet('confidence', CONFIDENCE_GROUPS),
      aum: facet('aum', AUM_BANDS),
    }
  }, [institutions, filters])

  const setFilter = (criterion) => (key) =>
    setFilters((f) => ({ ...f, [criterion]: key }))

  // The strip and the map are toggles: activating the value already selected
  // clears it, so there is always a way back to everything without hunting for
  // a reset control.
  const toggleFilter = (criterion) => (key) =>
    setFilters((f) => ({ ...f, [criterion]: f[criterion] === key ? 'all' : key }))

  // Regions accumulate: clicking Asia then Europe shows both. Clicking a
  // selected region removes it; the All pill clears the set.
  const toggleRegion = (label) =>
    setFilters((f) => ({
      ...f,
      region: label === null
        ? []
        : f.region.includes(label)
          ? f.region.filter((r) => r !== label)
          : [...f.region, label],
    }))

  // The exec band follows the same faceting philosophy as the pills: each
  // control reflects every ACTIVE filter except its own, so its numbers always
  // answer "what would selecting this leave on screen".
  const stripRows = useMemo(
    () =>
      institutions.filter((i) =>
        Object.entries(filters).every(
          ([c, key]) => c === 'stage' || MATCHERS[c](i, key),
        ),
      ),
    [institutions, filters],
  )
  const mapRows = useMemo(
    () =>
      institutions.filter((i) =>
        Object.entries(filters).every(
          ([c, key]) => c === 'region' || MATCHERS[c](i, key),
        ),
      ),
    [institutions, filters],
  )

  // The newest DATED PUBLIC ITEM anywhere in the corpus — pipeline signal or
  // curated event, whichever is newer per row (latestActivity does that choice).
  // It used to read max(latest_date), which is a monitor.py-only field: 8 of 84
  // rows carry one, all of them pre-pipeline seed rows, so the stamp froze on the
  // day monitor.py last ran and understated the corpus by three months.
  const refreshed = useMemo(
    () => maxDate(institutions.map((i) => latestActivity(i)?.date || '')),
    [institutions],
  )

  const reviewed = useMemo(
    () => maxDate(institutions.map((i) => i.as_of_reviewed)),
    [institutions],
  )

  return (
    <div className="app">
      {/* WCAG 2.4.1 Bypass Blocks — 19 filter pills sit between the header and
          the data, so a keyboard user needs a way past them. */}
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header route={route} onNavigate={navigate} refreshed={refreshed} reviewed={reviewed} />

      <main className="main" id="main" tabIndex={-1}>
        {route === 'methodology' ? (
          <Methodology defs={stageDefs} />
        ) : status === 'loading' ? (
          <div className="state-msg" role="status">
            <span className="spinner" aria-hidden="true" /> Loading
            classification data…
          </div>
        ) : status === 'error' ? (
          <div className="state-msg state-error" role="alert">
            <strong>Couldn’t load the data.</strong>
            <span className="state-detail">{error}</span>
            <span className="state-hint">
              Expected <code>data/institutions.json</code> at the site root.
            </span>
          </div>
        ) : institutions.length === 0 ? (
          <div className="state-msg">
            <strong>No institutions classified yet.</strong>
            <span className="state-detail">
              The dataset is empty — check back as classifications are added.
            </span>
          </div>
        ) : (
          <>
            {scopeNote(stageDefs) && (
              <aside className="scope-note" aria-label="Scope of this dashboard">
                <span className="scope-label">Scope</span>
                <p>{scopeNote(stageDefs)}</p>
              </aside>
            )}

            <div className="exec-band">
              <StageStrip
                institutions={stripRows}
                active={filters.stage === 'all' ? null : filters.stage}
                onToggle={toggleFilter('stage')}
              />
              <RegionMap
                institutions={mapRows}
                selected={filters.region}
                onToggle={toggleRegion}
              />
            </div>

            <div className="controls">
              <div className="filter-groups">
                <FilterPills
                  label="Type"
                  groups={TYPE_GROUPS}
                  value={filters.type}
                  onChange={setFilter('type')}
                  counts={counts.type}
                />
                <RegionPills
                  value={filters.region}
                  counts={counts.region}
                  onToggle={toggleRegion}
                />
                {filters.stage !== 'all' && (
                  <div className="filter-group" role="group" aria-label="Stage filter">
                    <span className="filter-group-label">Stage</span>
                    <div className="type-filter">
                      <button
                        type="button"
                        className="filter-pill"
                        data-active="true"
                        aria-pressed="true"
                        onClick={() => setFilter('stage')('all')}
                      >
                        {filters.stage}
                        <span aria-hidden="true"> ✕</span>
                        <span className="sr-only">, clear the stage filter</span>
                      </button>
                    </div>
                  </div>
                )}
                <FilterPills
                  label="Confidence"
                  groups={CONFIDENCE_GROUPS}
                  value={filters.confidence}
                  onChange={setFilter('confidence')}
                  counts={counts.confidence}
                />
                <FilterPills
                  label="AUM"
                  groups={AUM_BANDS}
                  value={filters.aum}
                  onChange={setFilter('aum')}
                  counts={counts.aum}
                />
                <div className="filter-group date-legend" aria-label="Date stamp legend">
                  <span className="filter-group-label">Dates</span>
                  <div className="legend-body">
                    <span className="legend-item legend-news">
                      <span aria-hidden="true">⚡</span> latest activity
                      <span className="sr-only">
                        {' '}— newest dated public item for an institution
                      </span>
                    </span>
                    <span className="legend-item legend-reviewed">
                      <span aria-hidden="true">✓</span> reviewed
                      <span className="sr-only">
                        {' '}— date a human last reviewed the classification
                      </span>
                    </span>
                  </div>
                </div>
              </div>
              {/* WCAG 4.1.3 Status Messages — the result count changes when a
                  filter is pressed, with no other announcement. */}
              <span className="controls-hint" role="status" aria-live="polite">
                {filtered.length} of {institutions.length} shown · click any
                institution for its timeline
              </span>
            </div>

            <PhaseGrid
              institutions={filtered}
              onSelect={setSelected}
              defs={stageDefs}
            />

            {notClassified.length > 0 && (
              <section className="nc-strip" aria-label="Assessed, not classified">
                <header className="nc-strip-head">
                  <h2 className="section-title">Not classified</h2>
                  <span className="nc-strip-count">{notClassified.length}</span>
                  <span className="nc-strip-note">
                    assessed against the methodology — the public record didn’t
                    support a stage ·{' '}
                    <a href="#/methodology">full appendix ↗</a>
                  </span>
                </header>
                <div className="nc-strip-cards">
                  {notClassified.map((n) => (
                    <div key={n.name} className="nc-chip">
                      <span className="nc-chip-name">{n.name}</span>
                      <span className="nc-chip-meta">
                        {TYPE_LABELS[n.type] || n.type} · {n.region}
                      </span>
                      <span className="nc-outcome" data-outcome={n.outcome}>
                        {OUTCOME_LABELS[n.outcome] || n.outcome}
                      </span>
                      {n.reason && <span className="sr-only">. {n.reason}</span>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="table-section">
              <h2 className="section-title">All institutions</h2>
              {filtered.length === 0 ? (
                <p className="col-empty">No institutions match this filter.</p>
              ) : (
                <InstitutionTable
                  institutions={filtered}
                  onSelect={setSelected}
                />
              )}
            </section>
          </>
        )}
      </main>

      <Footer />

      {selected && (
        <DrillDown
          inst={institutions.find((i) => i.name === selected.name) || selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}
