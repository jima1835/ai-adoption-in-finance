import test from 'node:test'
import assert from 'node:assert/strict'
import {
  institutionSearchText,
  matchesSearch,
  searchTerms,
} from '../src/search.js'

const institution = {
  name: 'Québec Investment',
  aliases: ['QIC', '魁北克投资'],
  use_cases: ['Document summarization'],
  events: [{ event: 'Internal Copilot deployment' }],
  rationale: 'Excluded: cryptocurrency investing',
}
const matches = (query, inst = institution) =>
  matchesSearch(institutionSearchText(inst), searchTerms(query))

test('finds only firm names and aliases across case and Unicode forms', () => {
  for (const query of ['quebec', ' QIC ', '魁北克', 'ＱＩＣ']) {
    assert.equal(matches(query), true, query)
  }
  assert.equal(matches('quebec investment'), true)
  assert.equal(matches('investment quebec'), false)
  assert.equal(matches('quebec qic'), false)
  assert.equal(matches('copilot quebec'), false)
  assert.equal(matches('document summarization'), false)
  assert.equal(matches('copilot nonexistent'), false)
  assert.equal(matches('cryptocurrency'), false)
  assert.equal(
    matches('gic', { name: 'Investcorp Strategic Capital Group' }),
    false,
  )
  assert.equal(matches('gic', { name: 'GIC' }), true)
})

test('blank search includes sparse records; evidence and appendix reasons do not produce name matches', () => {
  assert.equal(matches(' \n\t ', { name: 'A firm' }), true)
  assert.equal(
    matches('undated', {
      name: 'A firm',
      outcome: 'withdrawn-on-review',
      reason: 'Undated production claims',
    }),
    false,
  )
  assert.equal(
    matches('Wellington', {
      name: 'Two Sigma',
      events: [{ event: 'A partnership with Wellington Management' }],
    }),
    false,
  )
  assert.equal(
    matches('Wellington', {
      name: 'Wellington Management',
      outcome: 'no-qualifying-evidence',
    }),
    true,
  )
})

test('punctuation and potential HTML/regex input are literal text', () => {
  for (const query of ['.*', '[', '(a+)+$', '<img src=x onerror=alert(1)>']) {
    assert.equal(matches(query), false)
    assert.equal(matches(query, { name: query }), true)
  }
})

test('filter words are treated only as literal institution-name text', () => {
  assert.equal(matches('Europe'), false)
  assert.equal(matches('scaling'), false)
  assert.equal(
    matches('Europe', { name: 'European Investment Management' }),
    true,
  )
})
