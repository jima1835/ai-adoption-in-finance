// `__SITE_BUILD__` is baked in by vite.config.js: the day this bundle was built
// and the commit it was built from. Guarded so a test that imports the module
// outside Vite still renders.
const BUILD = typeof __SITE_BUILD__ !== 'undefined' ? __SITE_BUILD__ : null

export default function Footer() {
  return (
    <footer className="site-footer">
      <span>
        Built by <span className="footer-name">Jiajun Ma</span>
      </span>
      <span className="footer-sep">·</span>
      <a
        className="footer-link"
        href="https://github.com/jima1835/ai-adoption-in-finance"
        target="_blank"
        rel="noreferrer"
      >
        Source on GitHub
      </a>
      <span className="footer-sep">·</span>
      <span className="footer-muted">
        A personal, non-commercial, open-source project. Classifications rest
        only on public sources.
      </span>
      <span className="footer-sep">·</span>
      <span className="footer-muted" title="For questions and inquiries">
        Questions:{' '}
        <span className="contact-address">
          info[at]ai-adoption-in-finance.org
        </span>
      </span>
      {BUILD && BUILD.built && (
        <>
          <span className="footer-sep">·</span>
          <span className="footer-muted" title="Build date and source commit">
            Updated {BUILD.commitDate || BUILD.built}
            {BUILD.commit ? ` · ${BUILD.commit}` : ''}
          </span>
        </>
      )}
    </footer>
  )
}
