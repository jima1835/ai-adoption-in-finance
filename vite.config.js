import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, readFileSync, mkdirSync, copyFileSync } from 'node:fs'

const rootDir = dirname(fileURLToPath(import.meta.url))
const dataDir = join(rootDir, 'data')

// Root data/ is the SINGLE source of truth (monitor.py writes there). This
// plugin propagates it automatically — no symlink, no manual copy:
//   - dev: serve the current root data/*.json at <base>data/<file>
//   - build: copy real data/*.json into the build outDir (docs/data/), so the
//     deployed site always serves fresh, real files (symlinks don't survive
//     reliably into docs/ — that was the old fragility).
function syncData() {
  // .jsonl as well as .json: the roles record is an append-only log, so it
  // ships one-record-per-line. Note the order — '.json' would also match
  // 'roles.jsonl' if tested first, so both suffixes are listed explicitly.
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

// Relative base keeps the build portable to any GitHub Pages path. data/ is the
// canonical source; syncData() propagates it into docs/ on build (see above).
export default defineConfig({
  base: '/ai-adoption-in-finance/',
  build: { outDir: 'docs' },
  plugins: [react(), syncData()],
})
