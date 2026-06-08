import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base keeps the build portable to any GitHub Pages path
// (user/org site or project site) without hardcoding the repo name.
// data/ is served at the site root via the public/data symlink → ../data,
// so the same `data/institutions.json` the daily job rewrites is fetched
// at runtime (same origin, no CORS).
export default defineConfig({
  base: './',
  plugins: [react()],
})
