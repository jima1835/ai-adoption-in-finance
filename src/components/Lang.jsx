import { segmentCjk, translationFor } from '../data.js'

// Renders a possibly-multilingual string.
//
// Where data/translations.json has an entry for a Japanese / Chinese / Korean
// run, the English is shown and the original follows in parentheses, marked
// aria-hidden so it is visible for the record but never voiced — a screen
// reader hears only the English. Where there is no entry, the original is shown
// with a correct `lang` so at least it is pronounced in the right language
// rather than read as English.
//
// A string with no CJK renders as plain text with no wrapper elements.
export default function Lang({ children }) {
  const parts = segmentCjk(children)
  if (parts.length === 1 && !parts[0].lang) return parts[0].text

  // Track bracket depth across the Latin runs. Source text often already puts
  // the original inside parentheses — "(TIRD / 天弘智能研究及決策系統)" — and
  // wrapping it again produced a stray double close: "…system (天弘…))".
  // Inside an open parenthetical the original follows the English on a space.
  let depth = 0
  const insideParens = parts.map((seg) => {
    const before = depth
    if (!seg.lang) {
      for (const ch of seg.text) {
        if (ch === '(' || ch === '（') depth++
        else if ((ch === ')' || ch === '）') && depth > 0) depth--
      }
    }
    return before > 0
  })

  return (
    <>
      {parts.map((p, i) => {
        if (!p.lang) return p.text
        const en = translationFor(p.text)
        if (!en) {
          return (
            <span key={i} lang={p.lang}>
              {p.text}
            </span>
          )
        }
        // CJK needs no space against adjacent Latin, so the source often has
        // none — "NAVIS検索システム". Dropping an English word straight in
        // produced "NAVISsearch system"; add the space the English needs.
        const prev = parts[i - 1]
        const glue =
          prev && !prev.lang && /[A-Za-z0-9)\]]$/.test(prev.text) && /^[A-Za-z0-9"“(]/.test(en)
            ? ' '
            : ''
        const nested = insideParens[i]
        return (
          <span key={i}>
            {glue}
            {en}{' '}
            <span className="orig" lang={p.lang} aria-hidden="true">
              {nested ? p.text : `(${p.text})`}
            </span>
          </span>
        )
      })}
    </>
  )
}
