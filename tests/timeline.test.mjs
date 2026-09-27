import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createServer as createHttpServer } from 'node:http'
import {
  indexTimelineSummaries,
  timelineKey,
  timelineSummary,
} from '../src/timeline.js'

const rows = JSON.parse(
  await readFile(new URL('../data/institutions.json', import.meta.url)),
)
const { entries } = JSON.parse(
  await readFile(new URL('../data/event_summaries.json', import.meta.url)),
)
const index = indexTimelineSummaries(entries)

test('every current event has an exact-source title and compact supporting bullet', () => {
  const missing = []
  const currentKeys = new Set()
  for (const row of rows) {
    for (const event of row.events || []) {
      currentKeys.add(timelineKey(row.name, event))
      const result = timelineSummary(index, row.name, event)
      if (!result.summarized)
        missing.push(`${row.name} | ${event.date} | ${event.source_url}`)
      assert.ok(result.title.trim())
      assert.ok(result.bullets.length)
    }
  }
  assert.deepEqual(
    missing,
    [],
    'New or changed source notes need fresh summaries',
  )
  assert.equal(index.size, entries.length, 'Duplicate timeline summary keys')
  for (const entry of entries) {
    assert.ok(
      currentKeys.has(
        timelineKey(entry.institution, { ...entry, event: entry.source_note }),
      ),
      `Orphaned summary: ${entry.institution} ${entry.date}`,
    )
    assert.ok(entry.title.split(/\s+/).length <= 12, entry.title)
    assert.ok(
      entry.bullets.every((bullet) => bullet.split(/\s+/).length <= 35),
      entry.title,
    )
  }
})

test('a changed note never inherits an outdated summary', () => {
  const entry = entries[0]
  const event = {
    ...entry,
    event: 'The pilot was cancelled; the tool was not deployed.',
  }
  assert.deepEqual(timelineSummary(index, entry.institution, event), {
    title: 'Public source update',
    bullets: [event.event],
    summarized: false,
  })
})

test('same-date sources remain distinct and malformed summaries retain original notes', () => {
  const variants = entries.filter(
    (e) =>
      e.institution === 'Aberdeen Group (abrdn)' && e.date === '2026-07-29',
  )
  assert.equal(variants.length, 2)
  assert.notEqual(variants[0].title, variants[1].title)
  for (const entry of variants) {
    assert.equal(
      timelineSummary(index, entry.institution, {
        ...entry,
        event: entry.source_note,
      }).title,
      entry.title,
    )
  }
  assert.equal(indexTimelineSummaries([{ ...entries[0], bullets: [] }]).size, 0)
})

test('all institution dialogs render titled timeline bullets, source links and folded full notes', async () => {
  // Render the real JSX with Vite so this checks the timeline, not only a
  // formatter used by the separate rationale section.
  const { createServer } = await import('vite')
  const server = await createServer({
    server: {
      middlewareMode: true,
      watch: null,
      hmr: { server: createHttpServer() },
    },
    appType: 'custom',
  })
  const previousFetch = globalThis.fetch
  try {
    globalThis.fetch = async (url) => {
      const filename = String(url).split('/data/')[1]
      const body = await readFile(
        new URL(`../data/${filename}`, import.meta.url),
        'utf8',
      )
      return { ok: true, json: async () => JSON.parse(body) }
    }
    const data = await server.ssrLoadModule('/src/data.js')
    await Promise.all([
      data.loadTimelineSummaries(),
      data.loadHighlights(),
      data.loadJobPostings(),
    ])
    const { default: DrillDown } = await server.ssrLoadModule(
      '/src/components/DrillDown.jsx',
    )
    const { createElement } = await import('react')
    const { renderToStaticMarkup } = await import('react-dom/server')
    let total = 0
    for (const row of rows) {
      const html = renderToStaticMarkup(
        createElement(DrillDown, { inst: row, onClose() {} }),
      )
      const expected = row.events.filter(
        (e) => !data.jobPostingFor(row.name, e),
      )
      assert.equal(
        (html.match(/class="tl-title"/g) || []).length,
        expected.length,
        row.name,
      )
      assert.equal(
        (html.match(/class="tl-points"/g) || []).length,
        expected.length,
        row.name,
      )
      assert.equal(
        (html.match(/class="tl-full"/g) || []).length,
        expected.length,
        row.name,
      )
      assert.ok(
        !html.includes('data-summarized="false"'),
        `${row.name}: fallback summary rendered`,
      )
      assert.ok(
        !/<details[^>]*\bopen(?:=|\s|>)/.test(html),
        `${row.name}: source/rationale notes start open`,
      )
      for (const event of expected) {
        const escaped = event.source_url
          .replace(/&/g, '&amp;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#x27;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
        assert.ok(
          html.includes(`href="${escaped}"`),
          `${row.name}: source link missing`,
        )
      }
      total += expected.length
    }
    assert.ok(total > 0)
  } finally {
    globalThis.fetch = previousFetch
    await server.close()
  }
})
