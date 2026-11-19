// Second data snapshot taken directly from the IMF SDMX API (api.imf.org), written to
// data/confirmatory.json with the same shape as data/snapshot.json:
//   cpi{country}, fx{country} (domestic currency per USD, period average), brent.
// The series start in 2024-01 so that the overlap with the first snapshot (DBnomics, indexed
// 2025-08-31) can be compared month by month: any difference is a revision or a splice.
// Months after 2025-06 are the confirmatory sample of docs/thesis/experiment-protocol.md.
import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { fileURLToPath } from 'url'
import { COUNTRIES } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const ISO = { KZ: 'KAZ', RU: 'RUS', AZ: 'AZE', UZ: 'UZB', CO: 'COL', CL: 'CHL', PE: 'PER', BR: 'BRA', MX: 'MEX', NG: 'NGA', MN: 'MNG', ID: 'IDN', ZA: 'ZAF' }
const BASE = 'https://api.imf.org/external/sdmx/2.1/data'
const START = '2024-01'

function parseCsv(t) {
  const rows = []
  let row = [], f = '', q = false
  for (let i = 0; i < t.length; i++) {
    const c = t[i]
    if (q) { if (c === '"' && t[i + 1] === '"') { f += '"'; i++ } else if (c === '"') q = false; else f += c }
    else if (c === '"') q = true
    else if (c === ',') { row.push(f); f = '' }
    else if (c === '\n') { row.push(f); rows.push(row); row = []; f = '' }
    else if (c !== '\r') f += c
  }
  if (f || row.length) { row.push(f); rows.push(row) }
  return rows
}

async function series(flow, key) {
  const r = await fetch(`${BASE}/${flow}/${key}?startPeriod=${START}`, { headers: { Accept: 'application/vnd.sdmx.data+csv;version=1.0.0' } })
  if (!r.ok) throw new Error(`${r.status} ${flow}/${key}`)
  const rows = parseCsv(await r.text())
  const h = rows[0]
  const ti = h.indexOf('TIME_PERIOD'), vi = h.indexOf('OBS_VALUE')
  const out = {}
  for (const x of rows.slice(1)) {
    if (x.length > vi && x[ti] && x[vi] !== '') out[x[ti].replace('-M', '-')] = Number(x[vi])
  }
  return out
}

const snap = JSON.parse(fs.readFileSync(path.join(here, 'data', 'snapshot.json')))
const out = { fetchedAt: new Date().toISOString(), source: 'IMF SDMX api.imf.org (CPI, ER, PCPS)', cpi: {}, fx: {}, brent: null }

// The direct API uses the area code G001 (the DBnomics mirror used W00); W00 returns no rows here.
out.brent = await series('IMF.RES,PCPS', 'G001.POILBRE.USD.M')
const compare = (name, fresh, old) => {
  if (!old) return `${name}: no overlap source`
  let n = 0, maxRel = 0, worst = ''
  for (const [p, v] of Object.entries(fresh)) {
    if (old[p] === undefined) continue
    n++
    const rel = Math.abs(v / old[p] - 1)
    if (rel > maxRel) { maxRel = rel; worst = p }
  }
  return `${name}: overlap ${n} months, max |relative diff| ${(maxRel * 100).toFixed(3)}%${worst ? ' at ' + worst : ''}`
}
console.log(compare('Brent', out.brent, snap.brent))
for (const c of COUNTRIES) {
  out.cpi[c] = await series('IMF.STA,CPI', `${ISO[c]}.CPI._T.IX.M`)
  const usdPerLc = await series('IMF.STA,ER', `${ISO[c]}.USD_XDC.PA_RT.M`)
  out.fx[c] = Object.fromEntries(Object.entries(usdPerLc).map(([p, v]) => [p, 1 / v]))
  const last = Object.keys(out.cpi[c]).sort().at(-1)
  console.log(`${c}: cpi last ${last}; ${compare('cpi', out.cpi[c], snap.cpi[c])}; ${compare('fx', out.fx[c], snap.fx[c])}`)
}

const text = JSON.stringify(out)
const file = path.join(here, 'data', 'confirmatory.json')
fs.writeFileSync(file, text)
console.log('wrote', file)
console.log('sha256', crypto.createHash('sha256').update(text).digest('hex'))
