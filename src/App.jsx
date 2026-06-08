import { useEffect, useMemo, useState } from 'react'
import {
  TYPE_GROUPS,
  maxDate,
  loadStageDefinitions,
  scopeNote,
} from './data.js'
import { useInstitutions } from './useInstitutions.js'
import Header from './components/Header.jsx'
import Footer from './components/Footer.jsx'
import TypeFilter from './components/TypeFilter.jsx'
import PhaseGrid from './components/PhaseGrid.jsx'
import InstitutionTable from './components/InstitutionTable.jsx'
import DrillDown from './components/DrillDown.jsx'
import Methodology from './components/Methodology.jsx'

// Minimal hash routing — no router dependency. #/methodology ↔ dashboard.
function routeFromHash() {
  return window.location.hash.replace(/^#\/?/, '') === 'methodology'
    ? 'methodology'
    : 'dashboard'
}

export default function App() {
  const [route, setRoute] = useState(routeFromHash)
  const [typeFilter, setTypeFilter] = useState('all')
  const [selected, setSelected] = useState(null)
  const [stageDefs, setStageDefs] = useState(null)

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

  // Counts per filter group (always over the full set, so pills are stable).
  const counts = useMemo(() => {
    const c = {}
    for (const [key, group] of Object.entries(TYPE_GROUPS)) {
      c[key] = group.types
        ? institutions.filter((i) => group.types.includes(i.type)).length
        : institutions.length
    }
    return c
  }, [institutions])

  const filtered = useMemo(() => {
    const group = TYPE_GROUPS[typeFilter]
    if (!group?.types) return institutions
    return institutions.filter((i) => group.types.includes(i.type))
  }, [institutions, typeFilter])

  const refreshed = useMemo(
    () => maxDate(institutions.map((i) => i.latest_date)),
    [institutions],
  )

  return (
    <div className="app">
      <Header route={route} onNavigate={navigate} refreshed={refreshed} />

      <main className="main">
        {route === 'methodology' ? (
          <Methodology defs={stageDefs} />
        ) : status === 'loading' ? (
          <div className="state-msg">
            <span className="spinner" /> Loading classification data…
          </div>
        ) : status === 'error' ? (
          <div className="state-msg state-error">
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
              <aside className="scope-note">
                <span className="scope-label">Scope</span>
                <p>{scopeNote(stageDefs)}</p>
              </aside>
            )}

            <div className="controls">
              <TypeFilter
                value={typeFilter}
                onChange={setTypeFilter}
                counts={counts}
              />
              <span className="controls-hint">
                {filtered.length} of {institutions.length} shown · click any
                institution for its timeline
              </span>
            </div>

            <PhaseGrid
              institutions={filtered}
              onSelect={setSelected}
              defs={stageDefs}
            />

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
