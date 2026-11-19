// Hold-out countries: commodity-dependent economies that were NOT used to shape the design.
// The candidate list and its order are fixed here, before any forecast is computed. A candidate
// is eligible if the IMF monthly all-items CPI index and the exchange rate per USD both cover
// at least 220 months within 2000-01..2026-06 with at most 3 missing CPI months; the first 10
// eligible candidates in this order form the hold-out panel (nothing is chosen by looking at
// results). Output: data/holdout.json (same shape as snapshot.json) and a printed eligibility
// table. Brent is shared with the main panel (snapshot.json / confirmatory.json).
import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { fileURLToPath } from 'url'

const here = path.dirname(fileURLToPath(import.meta.url))
const BASE = 'https://api.imf.org/external/sdmx/2.1/data'
// Fixed order: Latin America, Caucasus and Central Asia, Africa.
const CANDIDATES = [
  ['BO', 'BOL'], ['PY', 'PRY'], ['UY', 'URY'], ['GH', 'GHA'], ['ZM', 'ZMB'],
  ['GE', 'GEO'], ['AM', 'ARM'], ['KG', 'KGZ'], ['TZ', 'TZA'], ['UG', 'UGA'],
  ['KE', 'KEN'], ['PG', 'PNG'], ['AO', 'AGO'], ['IQ', 'IRQ'],
]
const NEED = 10

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
  const r = await fetch(`${BASE}/${flow}/${key}?startPeriod=1999-01`, { headers: { Accept: 'application/vnd.sdmx.data+csv;version=1.0.0' } })
  if (!r.ok) return null
  const rows = parseCsv(await r.text())
  const h = rows[0]
  const ti = h.indexOf('TIME_PERIOD'), vi = h.indexOf('OBS_VALUE')
  if (ti < 0 || vi < 0) return null
  const out = {}
  for (const x of rows.slice(1)) if (x.length > vi && x[ti] && x[vi] !== '') out[x[ti].replace('-M', '-')] = Number(x[vi])
  return Object.keys(out).length ? out : null
}

const monthsBetween = (a, b) => (Number(b.slice(0, 4)) - Number(a.slice(0, 4))) * 12 + Number(b.slice(5)) - Number(a.slice(5)) + 1

const out = { fetchedAt: new Date().toISOString(), source: 'IMF SDMX api.imf.org (CPI, ER)', rule: `first ${NEED} eligible in fixed order; >=220 months in 2000-01..2026-06, <=3 missing CPI months`, cpi: {}, fx: {}, brent: null }
let kept = 0
for (const [code, iso] of CANDIDATES) {
  const cpi = await series('IMF.STA,CPI', `${iso}.CPI._T.IX.M`)
  const usd = await series('IMF.STA,ER', `${iso}.USD_XDC.PA_RT.M`)
  if (!cpi || !usd) { console.log(code, 'NOT ELIGIBLE: missing', !cpi ? 'CPI' : 'FX'); continue }
  const win = Object.keys(cpi).filter((p) => p >= '2000-01' && p <= '2026-06').sort()
  const span = win.length ? monthsBetween(win[0], win.at(-1)) : 0
  const missing = span - win.length
  const fxn = Object.keys(usd).filter((p) => p >= '2000-01' && p <= '2026-06').length
  const ok = win.length >= 220 && missing <= 3 && fxn >= 220
  console.log(code, ok ? 'ELIGIBLE' : 'NOT ELIGIBLE', `cpi months ${win.length} (${win[0]}..${win.at(-1)}), missing ${missing}, fx months ${fxn}`)
  if (ok && kept < NEED) {
    out.cpi[code] = cpi
    out.fx[code] = Object.fromEntries(Object.entries(usd).map(([p, v]) => [p, 1 / v]))
    kept++
  }
}
console.log('kept', kept, Object.keys(out.cpi).join(','))
const text = JSON.stringify(out)
const file = path.join(here, 'data', 'holdout.json')
fs.writeFileSync(file, text)
console.log('wrote', file)
console.log('sha256', crypto.createHash('sha256').update(text).digest('hex'))
