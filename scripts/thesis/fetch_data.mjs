// Downloads the panel (monthly CPI index, FX per USD, Brent) from IMF via DBnomics into
// data/snapshot.json and prints a SHA-256 of the file so the snapshot can be recorded.
import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { fileURLToPath } from 'url'
import { COUNTRIES, getJson } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const BASE = 'https://api.db.nomics.world/v22/series'

async function series(id) {
  const d = await getJson(`${BASE}/${id}?observations=1`)
  const s = d.series.docs[0]
  if (!s) return null
  const out = {}
  s.period.forEach((p, i) => {
    if (typeof s.value[i] === 'number') out[p] = s.value[i]
  })
  return out
}

const snapshot = { fetchedAt: new Date().toISOString(), cpi: {}, fx: {}, brent: null }
snapshot.brent = await series('IMF/PCPS/M.W00.POILBRE.USD')
for (const c of COUNTRIES) {
  snapshot.cpi[c] = await series(`IMF/CPI/M.${c}.PCPI_IX`)
  snapshot.fx[c] = await series(`IMF/IFS/M.${c}.ENDA_XDC_USD_RATE`)
  console.log(c, 'cpi', Object.keys(snapshot.cpi[c] || {}).length, 'fx', Object.keys(snapshot.fx[c] || {}).length)
}

fs.mkdirSync(path.join(here, 'data'), { recursive: true })
const file = path.join(here, 'data', 'snapshot.json')
const text = JSON.stringify(snapshot)
fs.writeFileSync(file, text)
console.log('wrote', file)
console.log('sha256', crypto.createHash('sha256').update(text).digest('hex'))
