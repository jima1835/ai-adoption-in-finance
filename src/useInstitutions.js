import { useCallback, useEffect, useRef, useState } from 'react'
import { loadInstitutions } from './data.js'

// Treat institutions.json as a live source. First load shows loading/error
// states; after that we refetch on tab focus/visibility and on a light
// background poll, but only re-render when the file's CONTENT actually
// changed — so an idle tab never flickers and a transient fetch error
// during a background refresh never wipes the grid that's already showing.
//
// The daily job rewrites this same file in production, so a long-lived tab
// (or a returning visitor) picks up new signals without a hard refresh.
export function useInstitutions({ pollMs = 0 } = {}) {
  const [state, setState] = useState({ status: 'loading', data: [], error: '' })
  const lastJson = useRef(null)
  const alive = useRef(true)

  const refresh = useCallback(async ({ background = false } = {}) => {
    try {
      const data = await loadInstitutions()
      const json = JSON.stringify(data)
      if (json === lastJson.current) return // unchanged → skip re-render
      lastJson.current = json
      if (alive.current) setState({ status: 'ready', data, error: '' })
    } catch (e) {
      if (!alive.current) return
      // Keep existing data on a background failure; only surface the error
      // if we have nothing to show yet.
      setState((s) =>
        background && s.status === 'ready'
          ? s
          : { status: 'error', data: [], error: e.message || 'Failed to load' },
      )
    }
  }, [])

  useEffect(() => {
    alive.current = true
    refresh()

    const onFocus = () => refresh({ background: true })
    const onVisible = () => {
      if (!document.hidden) refresh({ background: true })
    }
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVisible)
    const id = pollMs ? setInterval(() => refresh({ background: true }), pollMs) : null

    return () => {
      alive.current = false
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVisible)
      if (id) clearInterval(id)
    }
  }, [refresh, pollMs])

  return { ...state, refresh }
}
