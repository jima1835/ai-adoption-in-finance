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
  loadTimelineSummaries,
  loadJobPostings,
  loadHomepages,
  loadDescriptions,
  loadHighlights,
  loadPublishers,
  REGION_LABELS,
  scopeNote,
  STAGE_LABELS,
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
import About from './components/About.jsx'
import Releases from './components/Releases.jsx'
import SearchBox from './components/SearchBox.jsx'
import { institutionSearchText, matchesSearch, searchTerms } from './search.js'
import { FILTER_TAGS } from './search.js'
import { useDashboardView } from './useDashboardView.js'
import MobileFindings from './components/MobileFindings.jsx'
import MobileInstitutions from './components/MobileInstitutions.jsx'

// Minimal hash routing — no router dependency.
// #/methodology, #/releases and #/about are pages; anything else is the dashboard.
const ROUTES = ['methodology', 'releases', 'about']
const DEFAULT_FILTERS = {
  stage: 'all',
  type: 'all',
  region: [],
  confidence: 'all',
  aum: 'all',
}

function routeFromHash() {
  const hash = window.location.hash.replace(/^#\/?/, '')
  return ROUTES.includes(hash) ? hash : 'dashboard'
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
  const [view, setView] = useDashboardView()
  const [mobilePanel, setMobilePanel] = useState('findings')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(null)
  const [stageDefs, setStageDefs] = useState(null)
  const [notClassified, setNotClassified] = useState(null)
  // Role events are a separate record with a separate unit of observation
  // (METHODOLOGY §11); they never feed the stage grid.
  // The presentation-layer maps (translations, summaries, homepages,
  // descriptions, highlights, publishers) live in module-level caches in
  // data.js; this counter exists only to re-render the tree once they have
  // loaded.
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
    Promise.all([
      loadTranslations(),
      loadSummaries(),
      loadTimelineSummaries(),
      loadJobPostings(),
      loadHomepages(),
      loadDescriptions(),
      loadHighlights(),
      loadPublishers(),
    ]).then(([m]) => live && setTranslationsReady(Object.keys(m).length))
    return () => {
      live = false
    }
  }, [])

  // Refresh coverage when the live institution dataset changes. Keep the last
  // successful appendix on failure; an unavailable record is not a zero count.
  useEffect(() => {
    let live = true
    loadNotClassified({ fallback: null }).then((d) => {
      if (live && d !== null) setNotClassified(d)
    })
    return () => {
      live = false
    }
  }, [institutions])

  useEffect(() => {
    const onHash = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  function navigate(next) {
    window.location.hash = ROUTES.includes(next) ? `/${next}` : '/'
    setRoute(next)
  }

  const terms = useMemo(() => searchTerms(query), [query])
  const searchIndex = useMemo(
    () =>
      institutions.map((inst) => ({ inst, text: institutionSearchText(inst) })),
    [institutions],
  )
  const searched = useMemo(
    () =>
      searchIndex
        .filter(({ text }) => matchesSearch(text, terms))
        .map(({ inst }) => inst),
    [searchIndex, terms],
  )
  const matchingNotClassified = useMemo(
    () =>
      (notClassified || []).filter(
        (inst) =>
          matchesSearch(institutionSearchText(inst), terms) &&
          MATCHERS.type(inst, filters.type) &&
          MATCHERS.region(inst, filters.region),
      ),
    [notClassified, terms, filters.type, filters.region],
  )

  const filtered = useMemo(
    () =>
      searched.filter((i) =>
        Object.entries(filters).every(([c, key]) => MATCHERS[c](i, key)),
      ),
    [searched, filters],
  )

  // Faceted counts: each group's numbers reflect the OTHER active filters, so
  // a pill always shows how many rows selecting it would leave on screen.
  const counts = useMemo(() => {
    const facet = (criterion, groups) => {
      const base = searched.filter((i) =>
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
    const regionBase = searched.filter((i) =>
      Object.entries(filters).every(
        ([c, key]) => c === 'region' || MATCHERS[c](i, key),
      ),
    )
    return {
      type: facet('type', TYPE_GROUPS),
      region: Object.fromEntries(
        REGION_LABELS.map((r) => [
          r,
          regionBase.filter((i) => i.region === r).length,
        ]),
      ),
      confidence: facet('confidence', CONFIDENCE_GROUPS),
      aum: facet('aum', AUM_BANDS),
    }
  }, [searched, filters])

  const setFilter = (criterion) => (key) =>
    setFilters((f) => ({ ...f, [criterion]: key }))

  // The strip and the map are toggles: activating the value already selected
  // clears it, so there is always a way back to everything without hunting for
  // a reset control.
  const toggleFilter = (criterion) => (key) =>
    setFilters((f) => ({
      ...f,
      [criterion]: f[criterion] === key ? 'all' : key,
    }))

  // Regions accumulate: clicking Asia then Europe shows both. Clicking a
  // selected region removes it; the All pill clears the set.
  const toggleRegion = (label) =>
    setFilters((f) => ({
      ...f,
      region:
        label === null
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
      searched.filter((i) =>
        Object.entries(filters).every(
          ([c, key]) => c === 'stage' || MATCHERS[c](i, key),
        ),
      ),
    [searched, filters],
  )
  const mapRows = useMemo(
    () =>
      searched.filter((i) =>
        Object.entries(filters).every(
          ([c, key]) => c === 'region' || MATCHERS[c](i, key),
        ),
      ),
    [searched, filters],
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

  const activeTags = FILTER_TAGS.filter(({ criterion, key }) =>
    criterion === 'region'
      ? filters.region.includes(key)
      : filters[criterion] === key,
  )

  function showMobilePanel(panel) {
    setMobilePanel(panel)
    requestAnimationFrame(() => {
      const target = document.getElementById(
        panel === 'findings' ? 'findings-heading' : 'institution-search',
      )
      target?.focus({ preventScroll: true })
      target?.scrollIntoView({ block: 'start' })
    })
  }

  return (
    <div
      className="app"
      data-dashboard-view={route === 'dashboard' ? view : undefined}
    >
      {/* WCAG 2.4.1 Bypass Blocks — 19 filter pills sit between the header and
          the data, so a keyboard user needs a way past them. */}
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header
        route={route}
        onNavigate={navigate}
        refreshed={refreshed}
        reviewed={reviewed}
      />

      <main className="main" id="main" tabIndex={-1}>
        {route === 'methodology' ? (
          <Methodology defs={stageDefs} />
        ) : route === 'releases' ? (
          <Releases />
        ) : route === 'about' ? (
          <About />
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
            <div
              className="dashboard-view-switch"
              role="group"
              aria-label="Dashboard layout"
            >
              <span className="filter-group-label">Dashboard view</span>
              {['computer', 'mobile'].map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className="search-action"
                  aria-pressed={view === mode}
                  onClick={() => setView(mode)}
                >
                  {mode === 'computer' ? 'Computer' : 'Mobile'}
                </button>
              ))}
            </div>
            {view === 'mobile' && (
              <nav
                className="mobile-dashboard-nav"
                aria-label="Mobile dashboard sections"
              >
                <button
                  type="button"
                  className="search-action"
                  aria-pressed={mobilePanel === 'findings'}
                  onClick={() => showMobilePanel('findings')}
                >
                  Findings
                </button>
                <button
                  type="button"
                  className="search-action"
                  aria-pressed={mobilePanel === 'institutions'}
                  onClick={() => showMobilePanel('institutions')}
                >
                  Institutions
                </button>
              </nav>
            )}
            <aside className="scope-note" aria-label="Total coverage">
              <span className="scope-label">Total coverage</span>
              <div>
                {scopeNote(stageDefs) &&
                  !(view === 'mobile' && mobilePanel === 'institutions') &&
                  (view === 'mobile' ? (
                    <details className="scope-details">
                      <summary>What this dashboard measures</summary>
                      <p>{scopeNote(stageDefs)}</p>
                    </details>
                  ) : (
                    <p>{scopeNote(stageDefs)}</p>
                  ))}
                <p className="scope-coverage" aria-live="polite">
                  {notClassified !== null ? (
                    <>
                      <span>
                        <strong>
                          {institutions.length + notClassified.length}
                        </strong>{' '}
                        institutions assessed
                      </span>
                      <span>
                        <strong>{institutions.length}</strong> classified
                      </span>
                      <a href="#/methodology">
                        <strong>{notClassified.length}</strong> with
                        insufficient public evidence
                      </a>
                    </>
                  ) : (
                    <span>
                      <strong>{institutions.length}</strong> classified · full
                      coverage count unavailable
                    </span>
                  )}
                </p>
              </div>
            </aside>

            {view === 'mobile' && mobilePanel === 'findings' ? (
              <MobileFindings
                institutions={institutions}
                onBrowse={() => showMobilePanel('institutions')}
                onStage={(stage) => {
                  setQuery('')
                  setFilters({ ...DEFAULT_FILTERS, stage })
                  showMobilePanel('institutions')
                }}
              />
            ) : (
              <>
                <SearchBox
                  query={query}
                  onQuery={setQuery}
                  filters={filters}
                  onReset={() => {
                    setQuery('')
                    setFilters(DEFAULT_FILTERS)
                  }}
                />

                {view === 'computer' && (
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
                )}

                <div className="controls">
                  {view === 'mobile' && activeTags.length > 0 && (
                    <p className="active-filter-summary">
                      {activeTags
                        .map((tag) => `${tag.category}: ${tag.label}`)
                        .join(' · ')}
                    </p>
                  )}
                  <details
                    className="dashboard-filters"
                    open={view === 'computer' || filtersOpen}
                    onToggle={(event) => {
                      if (view === 'mobile')
                        setFiltersOpen(event.currentTarget.open)
                    }}
                  >
                    <summary>
                      Filters
                      {activeTags.length > 0
                        ? ` · ${activeTags.length} active`
                        : ''}
                    </summary>
                    <div className="filter-groups">
                      {view === 'mobile' && (
                        <FilterPills
                          label="Stage"
                          groups={{
                            all: { label: 'All' },
                            ...Object.fromEntries(
                              Object.entries(STAGE_LABELS).map(
                                ([key, label]) => [key, { label }],
                              ),
                            ),
                          }}
                          value={filters.stage}
                          onChange={setFilter('stage')}
                          counts={{
                            all: stripRows.length,
                            ...Object.fromEntries(
                              Object.keys(STAGE_LABELS).map((stage) => [
                                stage,
                                stripRows.filter((inst) => inst.stage === stage)
                                  .length,
                              ]),
                            ),
                          }}
                        />
                      )}
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
                      {view === 'computer' && filters.stage !== 'all' && (
                        <div
                          className="filter-group"
                          role="group"
                          aria-label="Stage filter"
                        >
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
                              <span className="sr-only">
                                , clear the stage filter
                              </span>
                            </button>
                          </div>
                        </div>
                      )}
                      <FilterPills
                        label="Evidence confidence"
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
                      <details className="confidence-help">
                        <summary>What does evidence confidence mean?</summary>
                        <p>
                          Confidence in the evidence supporting the assigned
                          stage, not the firm’s AI capability. High: strong
                          support. Med: some limitations. Low: substantial
                          uncertainty.
                        </p>
                      </details>
                      <div
                        className="filter-group date-legend"
                        aria-label="Date stamp legend"
                      >
                        <span className="filter-group-label">Dates</span>
                        <div className="legend-body">
                          <span className="legend-item legend-news">
                            <span aria-hidden="true">⚡</span> latest evidence
                            <span className="sr-only">
                              {' '}
                              — newest dated public item for an institution
                            </span>
                          </span>
                          <span className="legend-item legend-reviewed">
                            <span aria-hidden="true">✓</span> reviewed
                            <span className="sr-only">
                              {' '}
                              — date a human last reviewed the classification
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                  </details>
                  {/* WCAG 4.1.3 Status Messages — the result count changes when a
                  filter is pressed, with no other announcement. */}
                  <span
                    className="controls-hint"
                    role="status"
                    aria-live="polite"
                  >
                    {filtered.length} of {institutions.length} classified
                    institutions match
                    {view === 'computer' &&
                      ' · click any institution for its timeline'}
                    {terms.length > 0 && matchingNotClassified.length > 0 && (
                      <>
                        {' '}
                        · {matchingNotClassified.length} with insufficient
                        public evidence match below
                      </>
                    )}
                  </span>
                </div>

                {view === 'computer' ? (
                  <PhaseGrid
                    institutions={filtered}
                    onSelect={setSelected}
                    defs={stageDefs}
                  />
                ) : (
                  <MobileInstitutions
                    institutions={filtered}
                    onSelect={setSelected}
                  />
                )}

                {notClassified?.length > 0 && (
                  <section
                    className="nc-strip"
                    aria-label="Insufficient public evidence"
                  >
                    <header className="nc-strip-head">
                      <h2 className="section-title">
                        Insufficient public evidence
                      </h2>
                      <span className="nc-strip-count">
                        {matchingNotClassified.length} of {notClassified.length}
                      </span>
                      <span className="nc-strip-note">
                        assessed against the methodology — the public record
                        didn’t support a stage ·{' '}
                        <a href="#/methodology">full appendix ↗</a> · Search,
                        type and region apply here; stage, confidence and AUM
                        apply only to classified institutions.
                      </span>
                    </header>
                    <div className="nc-strip-cards">
                      {matchingNotClassified.length === 0 && (
                        <p className="col-empty">
                          No institutions in this section match this search and
                          filters.
                        </p>
                      )}
                      {matchingNotClassified.map((n) => (
                        <div key={n.name} className="nc-chip">
                          <span className="nc-chip-name">{n.name}</span>
                          <span className="nc-chip-meta">
                            {TYPE_LABELS[n.type] || n.type} · {n.region}
                          </span>
                          <span className="nc-outcome" data-outcome={n.outcome}>
                            {OUTCOME_LABELS[n.outcome] || n.outcome}
                          </span>
                          {n.reason && (
                            <span
                              className={
                                terms.length ? 'nc-search-reason' : 'sr-only'
                              }
                            >
                              {terms.length ? '' : '. '}
                              {n.reason}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {view === 'computer' && (
                  <section className="table-section">
                    <h2 className="section-title">Classified institutions</h2>
                    {filtered.length === 0 ? (
                      <p className="col-empty">
                        No classified institutions match this search and
                        filters. Clear the search or reset the filters to see
                        more.
                      </p>
                    ) : (
                      <InstitutionTable
                        institutions={filtered}
                        onSelect={setSelected}
                      />
                    )}
                  </section>
                )}
              </>
            )}
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
