// Top bar: identity, the two distinct timestamps, and the page nav.
// `refreshed` is the newest latest_date across all rows (automated signal).
export default function Header({ route, onNavigate, refreshed }) {
  return (
    <header className="site-header">
      <div className="header-top">
        <div className="brand">
          <span className="brand-mark">◢</span>
          <div>
            <h1 className="brand-title">AI Adoption in Finance</h1>
            <p className="brand-sub">
              Where institutional investors sit on AI adoption — by stage, from
              public sources.
            </p>
          </div>
        </div>
        <nav className="nav">
          <button
            className="nav-link"
            data-active={route === 'dashboard'}
            onClick={() => onNavigate('dashboard')}
          >
            Dashboard
          </button>
          <button
            className="nav-link"
            data-active={route === 'methodology'}
            onClick={() => onNavigate('methodology')}
          >
            Methodology
          </button>
        </nav>
      </div>

      <div className="header-stamps">
        <span className="stamp">
          <span className="stamp-dot" data-kind="auto" />
          Signals last refreshed:{' '}
          <span className="stamp-val">{refreshed || '—'}</span>
        </span>
        <span className="stamp">
          <span className="stamp-dot" data-kind="human" />
          Classifications curated from public sources
        </span>
      </div>
    </header>
  )
}
