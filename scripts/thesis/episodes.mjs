// Reproduces the episode counts quoted in docs/thesis/shock-definition.md from data/snapshot.json.
// Usage: node episodes.mjs [threshold=3] [after=3]
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { COUNTRIES, monthIndex, monthLabel, shockEvents, shockMonths, episodes } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const snap = JSON.parse(fs.readFileSync(path.join(here, 'data', 'snapshot.json')))
const threshold = Number(process.argv[2] ?? 3)
const after = Number(process.argv[3] ?? 3)

let total = 0
let totalPost = 0
console.log(`threshold ${threshold}, window +${after}, driver FX per USD`)
for (const c of COUNTRIES) {
  const fx = snap.fx[c]
  const cpi = new Set(Object.keys(snap.cpi[c] ?? {}))
  const { events } = shockEvents(new Map(Object.entries(fx)), threshold)
  const months = shockMonths(events, after)
  const eps = episodes(months)
  const inCpi = (i) => cpi.has(monthLabel(i))
  const post = eps.filter(([s, e]) => monthLabel(e) >= '2015-09' && inCpi(s))
  const postMonths = [...months].filter((i) => monthLabel(i) >= '2015-09' && inCpi(i)).length
  total += eps.length
  totalPost += post.length
  console.log(`${c.padEnd(3)} episodes=${String(eps.length).padStart(3)} post2015-09=${post.length} shockMonthsPost=${postMonths}`)
  if (c === 'KZ') {
    console.log('   KZ episodes since 2015:', eps.filter(([, e]) => monthLabel(e) >= '2015-01').map(([s, e]) => `${monthLabel(s)}..${monthLabel(e)}`).join(', '))
  }
}
console.log(`TOTAL episodes=${total}, post2015-09=${totalPost}`)
