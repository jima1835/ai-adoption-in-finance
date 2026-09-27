import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import { summaryParts } from '../src/data.js'

test('all classified institutions have a title-plus-context summary', async () => {
  const institutions = JSON.parse(
    await readFile(new URL('../data/institutions.json', import.meta.url)),
  )
  const { summaries } = JSON.parse(
    await readFile(new URL('../data/summaries.json', import.meta.url)),
  )

  assert.equal(institutions.length, 111)
  assert.equal(Object.keys(summaries).length, institutions.length)

  for (const institution of institutions) {
    const bullets = summaries[institution.name]
    assert.ok(bullets?.length, `${institution.name} is missing a summary`)
    for (const [index, bullet] of bullets.entries()) {
      const { title, context } = summaryParts(bullet, index)
      assert.ok(title, `${institution.name} bullet ${index + 1} has no title`)
      assert.ok(
        context,
        `${institution.name} bullet ${index + 1} has no supporting context`,
      )
    }
  }
})

test('every summary bullet uses the same evidence-label plus full-context structure', () => {
  const source =
    'AIA Labs, formed early 2023 and led by Co-CIO Greg Jensen, runs AI inside the investment process'
  assert.deepEqual(summaryParts(source), {
    title: 'Investment use',
    context: source,
  })
  assert.equal(
    summaryParts('Stops short of embedded because humans retain control', 3)
      .title,
    'Stage boundary',
  )
})

test('homepage audit covers every institution and tracks verification provenance', async () => {
  const institutions = JSON.parse(
    await readFile(new URL('../data/institutions.json', import.meta.url)),
  )
  const { homepages, manually_verified: manuallyVerified } = JSON.parse(
    await readFile(new URL('../data/homepages.json', import.meta.url)),
  )
  const manuallyVerifiedSet = new Set(manuallyVerified)

  assert.deepEqual(
    Object.keys(homepages).sort(),
    institutions.map(({ name }) => name).sort(),
  )
  assert.equal(manuallyVerified.length, 40)
  assert.equal(manuallyVerifiedSet.size, manuallyVerified.length)
  for (const name of manuallyVerified) {
    assert.ok(homepages[name], `${name} is not an institution homepage`)
  }
  for (const [name, homepage] of Object.entries(homepages)) {
    assert.match(homepage.url, /^https:\/\//, `${name} has a non-HTTPS homepage`)
    if (!homepage.derived_from) {
      assert.ok(
        homepage.audit_note || homepage.basis,
        `${name} needs an uncertainty note`,
      )
    }
  }
  const uncertain = Object.entries(homepages)
    .filter(
      ([name, homepage]) =>
        homepage.uncertain ||
        (!homepage.derived_from && !manuallyVerifiedSet.has(name)),
    )
    .map(([name]) => name)
  assert.deepEqual(uncertain, [])
  assert.equal(
    homepages['Fidelity Investments'].url,
    'https://institutional.fidelity.com/advisors',
  )
  assert.ok(homepages.Neuberger)
  assert.ok(!homepages['Neuberger Berman'])
})

test('every indexed job posting matches one reviewed timeline event', async () => {
  const institutions = JSON.parse(
    await readFile(new URL('../data/institutions.json', import.meta.url)),
  )
  const { postings } = JSON.parse(
    await readFile(new URL('../data/job_postings.json', import.meta.url)),
  )
  const events = new Set(
    institutions.flatMap((institution) =>
      (institution.events || []).map((event) =>
        JSON.stringify([
          institution.name,
          event.date,
          event.source_url || '',
        ]),
      ),
    ),
  )

  assert.equal(postings.length, 8)
  for (const posting of postings) {
    assert.ok(
      events.has(
        JSON.stringify([
          posting.institution,
          posting.date,
          posting.source_url,
        ]),
      ),
      `${posting.institution} ${posting.date} does not match reviewed evidence`,
    )
  }
})
