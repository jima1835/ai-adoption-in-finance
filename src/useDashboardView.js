import { useEffect, useState } from 'react'

const STORAGE_KEY = 'ai-finance-dashboard-view'
const MOBILE_QUERY = '(max-width: 720px)'

function savedView() {
  try {
    const value = sessionStorage.getItem(STORAGE_KEY)
    return ['computer', 'mobile'].includes(value) ? value : null
  } catch {
    return null
  }
}

// Default to the device width; a manual choice lasts for this browser tab.
export function useDashboardView() {
  const [preference, setPreference] = useState(savedView)
  const [smallScreen, setSmallScreen] = useState(
    () => window.matchMedia(MOBILE_QUERY).matches,
  )
  useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY)
    const update = (event) => setSmallScreen(event.matches)
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  function chooseView(value) {
    setPreference(value)
    try {
      sessionStorage.setItem(STORAGE_KEY, value)
    } catch {
      // Storage can be disabled; the in-memory switch still works.
    }
  }

  return [preference || (smallScreen ? 'mobile' : 'computer'), chooseView]
}
