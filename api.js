const call = async (path, body) => {
  const res = await fetch('/api' + path, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed')
  return data
}

export const api = {
  quote: (s, r) => call(`/quote/${s}?range=${r}`),
  signal: (s) => call(`/signal/${s}`),
  watchlist: () => call('/watchlist'),
  portfolio: () => call('/portfolio'),
  trades: () => call('/trades'),
  order: (b) => call('/orders', b),
  reset: () => call('/reset', {}),
}
