// Continuous version of the validity gate (docs/thesis/shock-definition.md, alternative).
// Stress at month t = max |z| of the FX one-month log change over months t-3..t.
// Origin stress uses information up to the forecast origin (month T-1) and is the usable one;
// target stress uses month T and is contemporaneous.
// Outcome: |pi_T - pi_{T-1}|, the one-step error of a naive forecast of monthly inflation,
// scaled by the country's median error. Stress and error are converted to within-country
// percentile ranks, so the pooled statistic is a rank correlation that does not depend on
// the level of each country's exchange-rate regime.
// Null: circular shifts of the stress series within each country (keeps its dependence).
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { COUNTRIES, monthIndex, monthLabel, zScores } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const snap = JSON.parse(fs.readFileSync(path.join(here, 'data', 'snapshot.json')))
const SHIFTS = 2000
const toMap = (o) => new Map(Object.entries(o))

function rng(seed) {
  let a = seed
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// within-array percentile ranks in (0,1], ties get the average rank
function pct(values) {
  const order = values.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0])
  const r = new Array(values.length)
  let i = 0
  while (i < order.length) {
    let j = i
    while (j + 1 < order.length && order[j + 1][0] === order[i][0]) j++
    const avg = (i + j) / 2 + 1
    for (let k = i; k <= j; k++) r[order[k][1]] = avg / values.length
    i = j + 1
  }
  return r
}

const corr = (x, y) => {
  const n = x.length
  const mx = x.reduce((a, b) => a + b, 0) / n
  const my = y.reduce((a, b) => a + b, 0) / n
  let sxy = 0, sxx = 0, syy = 0
  for (let i = 0; i < n; i++) {
    sxy += (x[i] - mx) * (y[i] - my)
    sxx += (x[i] - mx) ** 2
    syy += (y[i] - my) ** 2
  }
  return sxy / Math.sqrt(sxx * syy)
}

function buildCountry(c, since, origin) {
  const cpi = snap.cpi[c]
  const fx = snap.fx[c]
  if (!cpi || !fx) return null
  const z = zScores(toMap(fx))
  if (!z.size) return null
  const az = new Map([...z].map(([p, v]) => [monthIndex(p), Math.abs(v)]))
  const stressAt = (i) => {
    let m = -1
    for (let k = 0; k <= 3; k++) if (az.has(i - k)) m = Math.max(m, az.get(i - k))
    return m < 0 ? null : m
  }
  const idx = Object.keys(cpi).map(monthIndex).sort((a, b) => a - b)
  const level = new Map(idx.map((i) => [i, cpi[monthLabel(i)]]))
  const pi = (i) => (level.has(i) && level.has(i - 1) ? 100 * Math.log(level.get(i) / level.get(i - 1)) : null)
  const rows = []
  for (const i of idx) {
    if (since && i < monthIndex(since)) continue
    const a = pi(i), b = pi(i - 1)
    const s = stressAt(origin ? i - 1 : i)
    if (a === null || b === null || s === null) continue
    rows.push({ i, err: Math.abs(a - b), stress: s })
  }
  if (rows.length < 40) return null
  const errP = pct(rows.map((r) => r.err))
  const med = rows.map((r) => r.err).sort((x, y) => x - y)[Math.floor(rows.length / 2)] || 1e-9
  return { c, rows, errP, norm: rows.map((r) => r.err / med) }
}

function pooled(countries, shifts) {
  const sx = [], ey = []
  for (const ct of countries) {
    const L = ct.rows.length
    const s = shifts?.get(ct.c) ?? 0
    const stress = ct.rows.map((_, k) => ct.rows[(k + s) % L].stress)
    sx.push(...pct(stress))
    ey.push(...ct.errP)
  }
  return corr(sx, ey)
}

function decileTable(countries) {
  const sum = new Array(10).fill(0), cnt = new Array(10).fill(0), big = new Array(10).fill(0)
  for (const ct of countries) {
    const sp = pct(ct.rows.map((r) => r.stress))
    sp.forEach((p, k) => {
      const d = Math.min(9, Math.floor(p * 10 - 1e-9))
      sum[d] += ct.norm[k]
      cnt[d]++
      if (ct.errP[k] > 0.9) big[d]++
    })
  }
  return sum.map((s, d) => ({ decile: d + 1, n: cnt[d], meanScaledErr: s / cnt[d], shareTopErr: big[d] / cnt[d] }))
}

function run(since, origin) {
  const countries = COUNTRIES.map((c) => buildCountry(c, since, origin)).filter(Boolean)
  const obs = pooled(countries)
  const rand = rng(777)
  let ge = 0
  for (let t = 0; t < SHIFTS; t++) {
    const shifts = new Map(countries.map((ct) => [ct.c, Math.floor(rand() * ct.rows.length)]))
    if (pooled(countries, shifts) >= obs) ge++
  }
  console.log(`\n=== ${origin ? 'ORIGIN stress (usable at forecast time)' : 'TARGET stress (contemporaneous)'} | sample since ${since ?? 'start'} | countries ${countries.length}, months ${countries.reduce((a, b) => a + b.rows.length, 0)} ===`)
  console.log(`pooled rank correlation(stress, error) = ${obs.toFixed(3)}, permutation p = ${((ge + 1) / (SHIFTS + 1)).toFixed(4)}`)
  console.log('decile  n     meanErr/medianErr  shareOfTop10%Errors (base 0.10)')
  for (const r of decileTable(countries)) console.log(`${String(r.decile).padStart(4)} ${String(r.n).padStart(5)}   ${r.meanScaledErr.toFixed(2).padStart(10)}   ${r.shareTopErr.toFixed(3).padStart(10)}`)
  const per = countries.map((ct) => `${ct.c}:${corr(pct(ct.rows.map((r) => r.stress)), ct.errP).toFixed(2)}`)
  console.log('per-country rank correlation:', per.join(' '))
}

run(null, true)
run(null, false)
run('2015-09', true)
