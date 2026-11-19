// Validity gate for the FX-based shock rule (docs/thesis/shock-definition.md).
// Question: are the largest one-step errors of a naive forecast of monthly inflation
// concentrated in shock windows more than the share of shock months would imply?
// lift = (share of top-decile errors inside shock windows) / (share of shock months).
// Null distribution: circular shifts of the shock labels within each country, which keeps
// the episode structure and the serial dependence of the labels.
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { COUNTRIES, monthIndex, monthLabel, shockEvents, shockMonths } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const snap = JSON.parse(fs.readFileSync(path.join(here, 'data', 'snapshot.json')))
const THRESHOLD = Number(process.argv[2] ?? 3)
const AFTER = Number(process.argv[3] ?? 3)
const SHIFTS = 2000
const toMap = (o) => new Map(Object.entries(o))

// Mulberry32 so the permutation test is reproducible.
function rng(seed) {
  let a = seed
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function buildCountry(c, since) {
  const cpi = snap.cpi[c]
  const fx = snap.fx[c]
  if (!cpi || !fx) return null
  const { events, firstEvaluable } = shockEvents(toMap(fx), THRESHOLD)
  if (!firstEvaluable) return null
  const shock = shockMonths(events, AFTER)
  const startIdx = Math.max(monthIndex(firstEvaluable) + 1, since ? monthIndex(since) : 0)
  const idx = Object.keys(cpi).map(monthIndex).sort((a, b) => a - b)
  const level = new Map(idx.map((i) => [i, cpi[monthLabel(i)]]))
  // Monthly inflation pi_t = 100 * ln(CPI_t / CPI_{t-1}); naive h=1 forecast of pi_t is pi_{t-1}.
  const pi = (i) => (level.has(i) && level.has(i - 1) ? 100 * Math.log(level.get(i) / level.get(i - 1)) : null)
  const rows = []
  for (const i of idx) {
    if (i < startIdx) continue
    const a = pi(i)
    const b = pi(i - 1)
    if (a === null || b === null) continue
    rows.push({ i, err: Math.abs(a - b) })
  }
  if (rows.length < 40) return null
  const sorted = rows.map((r) => r.err).sort((x, y) => x - y)
  const cut = sorted[Math.floor(0.9 * sorted.length)]
  return { c, rows: rows.map((r) => ({ ...r, big: r.err >= cut })), shock }
}

function stats(countries, targetLabel, shift) {
  let big = 0, bigIn = 0, n = 0, nIn = 0
  for (const ct of countries) {
    const s = shift?.get(ct.c) ?? 0
    const L = ct.rows.length
    ct.rows.forEach((r, k) => {
      // origin label: month T-1 flagged; target label: month T flagged (both from the same window set)
      const j = (k + s) % L
      const month = ct.rows[j].i
      const flagged = ct.shock.has(targetLabel ? month : month - 1)
      n++
      if (flagged) nIn++
      if (r.big) { big++; if (flagged) bigIn++ }
    })
  }
  const base = nIn / n
  const recall = big ? bigIn / big : 0
  return { n, big, bigIn, base, recall, lift: base ? recall / base : NaN }
}

function report(since) {
  const countries = COUNTRIES.map((c) => buildCountry(c, since)).filter(Boolean)
  console.log(`\n=== threshold ${THRESHOLD}, window +${AFTER}, sample since ${since ?? 'start of evaluable period'}; countries: ${countries.length} ===`)
  for (const targetLabel of [true, false]) {
    const obs = stats(countries, targetLabel)
    const rand = rng(12345)
    let ge = 0
    for (let t = 0; t < SHIFTS; t++) {
      const shift = new Map(countries.map((ct) => [ct.c, Math.floor(rand() * ct.rows.length)]))
      if (stats(countries, targetLabel, shift).lift >= obs.lift) ge++
    }
    const p = (ge + 1) / (SHIFTS + 1)
    console.log(`${targetLabel ? 'target-month label' : 'origin-month label'}: months=${obs.n}, shockShare=${obs.base.toFixed(3)}, topDecileErrors=${obs.big}, inShock=${obs.bigIn}, recall=${obs.recall.toFixed(3)}, lift=${obs.lift.toFixed(2)}, permutation p=${p.toFixed(4)}`)
  }
  for (const ct of countries) {
    const o = stats([ct], true)
    console.log(`  ${ct.c}: n=${o.n} shockShare=${o.base.toFixed(2)} recall=${o.recall.toFixed(2)} lift=${o.lift.toFixed(2)}`)
  }
}

report(null)
report('2015-09')
