// Top bar: identity, the two distinct timestamps, and the page nav.
// `refreshed` is the newest latest_date across all rows (automated signal).
export default function Header({ route, onNavigate, refreshed, reviewed }) {
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
        <span className="stamp" title="Date of the newest signal across all rows (max latest_date)">
          <span className="stamp-dot" data-kind="auto" />
          Signals through <span className="stamp-val">{refreshed || '—'}</span>
        </span>
        <span className="stamp" title="Newest human review date across all rows (max as_of_reviewed)">
          <span className="stamp-dot" data-kind="human" />
          Last reviewed <span className="stamp-val">{reviewed || '—'}</span>
        </span>
        <span className="stamp">
          <span className="stamp-dot" data-kind="human" />
          Classifications curated from public sources
        </span>
      </div>
    </header>
  )
}
