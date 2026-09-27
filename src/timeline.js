// Match the complete note, not just its URL: one source can describe several
// events, and a later corpus correction must invalidate the older summary.
export function timelineKey(institution, event) {
  return JSON.stringify([
    institution,
    event.date,
    event.source_url || '',
    event.event,
  ])
}

export function indexTimelineSummaries(entries = []) {
  const index = new Map()
  for (const entry of entries) {
    if (
      typeof entry.title !== 'string' ||
      !entry.title.trim() ||
      !Array.isArray(entry.bullets) ||
      !entry.bullets.length ||
      !entry.bullets.every(
        (bullet) => typeof bullet === 'string' && bullet.trim(),
      )
    ) {
      continue
    }
    index.set(
      timelineKey(entry.institution, { ...entry, event: entry.source_note }),
      { title: entry.title, bullets: entry.bullets, summarized: true },
    )
  }
  return index
}

export function timelineSummary(index, institution, event) {
  return (
    index.get(timelineKey(institution, event)) || {
      title: 'Public source update',
      bullets: [event.event],
      summarized: false,
    }
  )
}
