import { homepageFor } from '../data.js'
import Lang from './Lang.jsx'

// The institution's name, linked to its homepage when one could be derived from
// an own-domain evidence URL that already passed human review. No homepage was
// researched separately, so a firm whose evidence is all press coverage renders
// as plain text rather than carrying a guessed link.
//
// stopPropagation matters: these sit inside a row that opens the drill-down, and
// following the link should not also open the panel.
export default function FirmLink({ name, className }) {
  const href = homepageFor(name)
  if (!href) {
    return (
      <span className={className}>
        <Lang>{name}</Lang>
      </span>
    )
  }
  return (
    <a
      className={className ? `${className} firm-link` : 'firm-link'}
      href={href}
      target="_blank"
      rel="noreferrer"
      onClick={(e) => e.stopPropagation()}
    >
      <Lang>{name}</Lang>
      <span className="firm-link-mark" aria-hidden="true">↗</span>
      <span className="sr-only"> — homepage, opens in a new tab</span>
    </a>
  )
}
