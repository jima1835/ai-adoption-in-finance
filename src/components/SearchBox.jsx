import { useRef } from 'react'

export default function SearchBox({ query, onQuery, filters, onReset }) {
  const input = useRef(null)
  const hasFilters = Object.values(filters).some((value) =>
    Array.isArray(value) ? value.length > 0 : value !== 'all',
  )

  return (
    <div className="institution-search" role="search" aria-label="Institutions">
      <label htmlFor="institution-search" className="filter-group-label">
        Find an institution
      </label>
      <div className="search-input-row">
        <input
          ref={input}
          id="institution-search"
          type="search"
          value={query}
          maxLength={200}
          placeholder="Institution or manager name, e.g. BlackRock"
          aria-describedby="institution-search-help"
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => onQuery(event.target.value)}
        />
        {query && (
          <button
            type="button"
            className="search-action"
            onClick={() => {
              onQuery('')
              input.current.focus()
            }}
          >
            Clear search
          </button>
        )}
        {hasFilters && (
          <button
            type="button"
            className="search-action"
            onClick={() => {
              onReset()
              input.current.focus()
            }}
          >
            Reset all
          </button>
        )}
      </div>
      <p id="institution-search-help" className="search-help">
        Matches the institution name and reviewed aliases only. Use the controls
        below for stage, type, region, confidence and AUM.
      </p>
    </div>
  )
}
