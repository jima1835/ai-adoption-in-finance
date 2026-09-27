import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, readFileSync, mkdirSync, copyFileSync } from 'node:fs'
import { execSync } from 'node:child_process'

const rootDir = dirname(fileURLToPath(import.meta.url))
const dataDir = join(rootDir, 'data')

// Root data/ is the SINGLE source of truth (monitor.py writes there). This
// plugin propagates it automatically — no symlink, no manual copy:
//   - dev: serve the current root data/*.json at <base>data/<file>
//   - build: copy real data/*.json into the build outDir (docs/data/), so the
//     deployed site always serves fresh, real files (symlinks don't survive
//     reliably into docs/ — that was the old fragility).
function syncData() {
  // .jsonl as well as .json: transitions.jsonl is an append-only log, so it
  // ships one-record-per-line. Note the order — '.json' would also match
  // 'transitions.jsonl' if tested first, so both suffixes are listed explicitly.
  const DATA_SUFFIXES = ['.json', '.jsonl']
  const jsonFiles = () =>
    readdirSync(dataDir).filter((f) => DATA_SUFFIXES.some((s) => f.endsWith(s)))
  let resolvedOutDir
  return {
    name: 'sync-data',
    configResolved(config) {
      resolvedOutDir = config.build.outDir
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const match = req.url && req.url.match(/\/data\/([\w.-]+\.jsonl?)$/)
        if (match && jsonFiles().includes(match[1])) {
          // JSON Lines is not application/json — it is a stream of them.
          res.setHeader(
            'Content-Type',
            match[1].endsWith('.jsonl') ? 'text/plain' : 'application/json',
          )
          res.end(readFileSync(join(dataDir, match[1])))
          return
        }
        next()
      })
    },
    closeBundle() {
      const outData = join(resolvedOutDir, 'data')
      mkdirSync(outData, { recursive: true })
      for (const f of jsonFiles()) {
        copyFileSync(join(dataDir, f), join(outData, f))
      }
    },
  }
}

// The site's "updated" stamp: the commit the build was made from and the day it
// was built. The build is committed together with its sources, so at build time
// HEAD is the previous commit; the build date is therefore shown beside the
// commit, and both are literal strings baked in by `define`, never fetched.
function git(args) {
  try {
    return execSync(`git ${args}`, { stdio: ['ignore', 'pipe', 'ignore'] })
      .toString()
      .trim()
  } catch {
    return ''
  }
}
const SITE_BUILD = {
  built: new Date().toISOString().slice(0, 10),
  commit: git('rev-parse --short HEAD'),
  commitDate: git('log -1 --format=%cs'),
}

// Relative base keeps the build portable to any GitHub Pages path. data/ is the
// canonical source; syncData() propagates it into docs/ on build (see above).
export default defineConfig({
  base: '/ai-adoption-in-finance/',
  build: { outDir: 'docs' },
  plugins: [react(), syncData()],
  define: { __SITE_BUILD__: JSON.stringify(SITE_BUILD) },
})
