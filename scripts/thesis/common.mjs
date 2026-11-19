// Shared helpers for the thesis experiments. Rule definitions: docs/thesis/shock-definition.md
export const COUNTRIES = ['KZ', 'RU', 'AZ', 'UZ', 'CO', 'CL', 'PE', 'BR', 'MX', 'NG', 'MN', 'ID', 'ZA']

export const monthIndex = (p) => {
  const [y, m] = p.split('-').map(Number)
  return y * 12 + m - 1
}
export const monthLabel = (i) => `${Math.floor(i / 12)}-${String(i % 12 + 1).padStart(2, '0')}`

const median = (a) => {
  const s = [...a].sort((x, y) => x - y)
  const n = s.length
  return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2
}

// series: Map<'YYYY-MM', number>. Returns Map<'YYYY-MM', z> where z is the causal robust z-score
// of the 1-month log change (median/MAD over the `lookback` months before the month, MAD floored).
export function zScores(series, floor = 0.005, lookback = 60) {
  const periods = [...series.keys()].sort()
  const d = []
  for (let i = 1; i < periods.length; i++) {
    const a = series.get(periods[i - 1])
    const b = series.get(periods[i])
    if (a > 0 && b > 0) d.push([periods[i], Math.log(b / a)])
  }
  const z = new Map()
  for (let i = lookback; i < d.length; i++) {
    const w = d.slice(i - lookback, i).map((x) => x[1])
    const m = median(w)
    const s = Math.max(1.4826 * median(w.map((x) => Math.abs(x - m))), floor)
    z.set(d[i][0], (d[i][1] - m) / s)
  }
  return z
}

// Returns Set of event months (|z| above threshold).
export function shockEvents(series, threshold = 3, floor = 0.005, lookback = 60) {
  const z = zScores(series, floor, lookback)
  const events = new Set()
  for (const [p, v] of z) if (Math.abs(v) > threshold) events.add(p)
  const firstEvaluable = z.size ? [...z.keys()].sort()[0] : null
  return { events, firstEvaluable }
}

// Shock window = event month + `after` following months. Returns Set of month indices.
export function shockMonths(events, after = 3) {
  const out = new Set()
  for (const p of events) {
    const i = monthIndex(p)
    for (let k = 0; k <= after; k++) out.add(i + k)
  }
  return out
}

// Merge shock months into episodes [[start, end], ...] (adjacent months merge).
export function episodes(months) {
  const arr = [...months].sort((a, b) => a - b)
  const eps = []
  for (const i of arr) {
    const last = eps[eps.length - 1]
    if (last && i - last[1] <= 1) last[1] = i
    else eps.push([i, i])
  }
  return eps
}

export async function getJson(url) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
      if (!r.ok) throw new Error(String(r.status))
      return await r.json()
    } catch (e) {
      if (attempt === 2) throw new Error(`${e.message} ${url}`)
    }
  }
}
