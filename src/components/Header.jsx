// Top bar: identity, the two distinct timestamps, and the page nav.
// `refreshed` is the newest dated public item across all rows — a monitor signal
// or a curated event, whichever is newer. Neither timestamp implies every
// institution was checked through that date.
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
            type="button"
            className="nav-link"
            data-active={route === 'dashboard'}
            aria-current={route === 'dashboard' ? 'page' : undefined}
            onClick={() => onNavigate('dashboard')}
          >
            Dashboard
          </button>
          <button
            type="button"
            className="nav-link"
            data-active={route === 'methodology'}
            aria-current={route === 'methodology' ? 'page' : undefined}
            onClick={() => onNavigate('methodology')}
          >
            Methodology
          </button>
          <button
            type="button"
            className="nav-link"
            data-active={route === 'releases'}
            aria-current={route === 'releases' ? 'page' : undefined}
            onClick={() => onNavigate('releases')}
          >
            Releases
          </button>
          <button
            type="button"
            className="nav-link"
            data-active={route === 'about'}
            aria-current={route === 'about' ? 'page' : undefined}
            onClick={() => onNavigate('about')}
          >
            About
          </button>
        </nav>
      </div>

      <div className="header-stamps">
        <span className="stamp">
          <span className="stamp-dot" data-kind="auto" aria-hidden="true" />
          Newest evidence <span className="stamp-val">{refreshed || '—'}</span>
          <span className="sr-only">
            {' '}
            — date of the newest dated public source across all rows
          </span>
        </span>
        <span className="stamp">
          <span className="stamp-dot" data-kind="human" aria-hidden="true" />
          Latest institution review{' '}
          <span className="stamp-val">{reviewed || '—'}</span>
          <span className="sr-only">
            {' '}
            — newest human review date across all rows
          </span>
        </span>
        <span className="stamp">
          <span className="stamp-dot" data-kind="human" aria-hidden="true" />
          Classifications curated from public sources
        </span>
      </div>
    </header>
  )
}
