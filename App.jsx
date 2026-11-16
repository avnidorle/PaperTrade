import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import Chart from './Chart'

const SYMS = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'ITC']
const RANGES = ['1W', '1M', '3M', '1Y']
const inr = (n) => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const tone = (n) => (n >= 0 ? 'text-[#22C55E]' : 'text-[#EF4444]')
const chip = (on) => `rounded-lg px-3 py-1 text-sm ${on ? 'bg-[#3B82F6]' : 'bg-[#162338] text-[#94A3B8]'}`
const Card = ({ title, className = '', children }) => (
  <section className={`rounded-xl border border-white/10 bg-[#111C2E] p-4 ${className}`}>
    {title && <h2 className="mb-3 font-semibold">{title}</h2>}
    {children}
  </section>
)
const Table = ({ head, rows }) => (
  <div className="overflow-x-auto">
    <table className="w-full min-w-[480px] text-sm">
      <thead className="text-left text-[#94A3B8]"><tr>{head.map((h) => <th key={h} className="p-2 font-normal">{h}</th>)}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
)

export default function App() {
  const [sym, setSym] = useState('RELIANCE')
  const [range, setRange] = useState('3M')
  const [q, setQ] = useState(null)
  const [sig, setSig] = useState(null)
  const [wl, setWl] = useState([])
  const [pf, setPf] = useState(null)
  const [tr, setTr] = useState([])
  const [form, setForm] = useState({ qty: 1, order_type: 'MARKET', limit_price: '' })
  const [msg, setMsg] = useState('')

  const load = useCallback(() => {
    api.watchlist().then(setWl); api.portfolio().then(setPf); api.trades().then(setTr)
  }, [])
  useEffect(load, [load])
  useEffect(() => { api.quote(sym, range).then(setQ); api.signal(sym).then(setSig) }, [sym, range])

  const place = async (side) => {
    try {
      const r = await api.order({ symbol: sym, side, qty: +form.qty, order_type: form.order_type,
        limit_price: form.limit_price ? +form.limit_price : null })
      setMsg(r.message); load()
    } catch (e) { setMsg(e.message) }
  }
  const reset = async () => { await api.reset(); setMsg('Account reset.'); load() }
  const last = q?.candles.at(-1)
  const inputCls = 'mt-1 w-full rounded-lg border border-white/10 bg-[#162338] p-2'

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-bold text-[#3B82F6]">PaperTrade</h1>
        <span className="rounded-full bg-[#162338] px-3 py-1 text-xs text-[#94A3B8]">
          {q?.source === 'yahoo' ? 'Yahoo Finance data (delayed)' : 'Simulated data, not live'}
        </span>
        <button onClick={reset} className={`${chip(false)} ml-auto`}>Reset account</button>
      </header>

      {pf && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[['Cash', pf.cash], ['Invested', pf.invested], ['Portfolio value', pf.value], [`Total P&L (${pf.return_pct}%)`, pf.total_pnl, 1]].map(([k, v, t]) => (
            <Card key={k}><div className="text-xs text-[#94A3B8]">{k}</div><div className={`text-lg font-semibold ${t ? tone(v) : ''}`}>{inr(v)}</div></Card>
          ))}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-2 flex flex-wrap gap-2">
            {SYMS.map((s) => <button key={s} className={chip(s === sym)} onClick={() => setSym(s)}>{s}</button>)}
            <span className="flex-1" />
            {RANGES.map((r) => <button key={r} className={chip(r === range)} onClick={() => setRange(r)}>{r}</button>)}
          </div>
          {q ? <Chart data={q.candles} /> : <div className="p-8 text-[#94A3B8]">Loading chart…</div>}
          <div className="text-xs text-[#94A3B8]">Amber: SMA 20. Purple: SMA 50. Hover for OHLC.</div>
        </Card>

        <div className="space-y-4">
          {sig && (
            <Card title={`Signal: ${sym}`}>
              <div className={`text-2xl font-bold ${sig.signal === 'BUY' ? 'text-[#22C55E]' : sig.signal === 'SELL' ? 'text-[#EF4444]' : ''}`}>{sig.signal}</div>
              <p className="my-2 text-sm">{sig.reason}</p>
              <div className="text-xs text-[#94A3B8]">Rule agreement {sig.confidence}% (not a prediction). {new Date(sig.generated_at).toLocaleString('en-IN')}</div>
            </Card>
          )}
          {last && (
            <Card title="Indicators">
              <div className="space-y-1 text-sm">
                <div>RSI {last.rsi?.toFixed(1)}: {last.rsi > 70 ? 'Overbought' : last.rsi < 30 ? 'Oversold' : 'Neutral'}</div>
                <div>MACD {last.macd} vs signal {last.signal}: {last.macd > last.signal ? 'Bullish' : 'Bearish'}</div>
                <div>SMA20 {last.sma20} · SMA50 {last.sma50} · EMA20 {last.ema20}</div>
                <div>Bollinger {last.bb_l} to {last.bb_u}</div>
              </div>
            </Card>
          )}
          <Card title={`Paper order: ${sym}`}>
            <label className="text-xs text-[#94A3B8]">Quantity
              <input type="number" min="1" className={inputCls} value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} /></label>
            <label className="mt-2 block text-xs text-[#94A3B8]">Order type
              <select className={inputCls} value={form.order_type} onChange={(e) => setForm({ ...form, order_type: e.target.value })}><option>MARKET</option><option>LIMIT</option></select></label>
            {form.order_type === 'LIMIT' && (
              <label className="mt-2 block text-xs text-[#94A3B8]">Limit price
                <input type="number" className={inputCls} value={form.limit_price} onChange={(e) => setForm({ ...form, limit_price: e.target.value })} /></label>
            )}
            <div className="mt-3 flex gap-2">
              <button onClick={() => place('BUY')} className="flex-1 rounded-lg bg-[#22C55E] p-2 font-semibold text-black">Execute Buy</button>
              <button onClick={() => place('SELL')} className="flex-1 rounded-lg bg-[#EF4444] p-2 font-semibold">Execute Sell</button>
            </div>
            {msg && <div className="mt-3 rounded-lg bg-[#162338] p-2 text-sm">{msg}</div>}
          </Card>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Watchlist">
          <Table head={['Stock', 'Price', '% change']} rows={wl.map((w) => (
            <tr key={w.symbol} onClick={() => setSym(w.symbol)} className="cursor-pointer border-t border-white/10 hover:bg-[#162338]">
              <td className="p-2">{w.symbol}</td><td className="p-2">{inr(w.price)}</td><td className={`p-2 ${tone(w.change_pct)}`}>{w.change_pct}%</td></tr>))} />
        </Card>
        <Card title="Holdings">
          <Table head={['Stock', 'Qty', 'Avg', 'Price', 'Unrealized']} rows={pf?.holdings.map((h) => (
            <tr key={h.symbol} className="border-t border-white/10"><td className="p-2">{h.symbol}</td><td className="p-2">{h.qty}</td>
              <td className="p-2">{inr(h.avg_price)}</td><td className="p-2">{inr(h.price)}</td><td className={`p-2 ${tone(h.unrealized_pnl)}`}>{inr(h.unrealized_pnl)}</td></tr>))} />
          {pf && <div className="mt-2 text-sm text-[#94A3B8]">Realized P&L: <span className={tone(pf.realized_pnl)}>{inr(pf.realized_pnl)}</span> · Daily P&L: <span className={tone(pf.daily_pnl)}>{inr(pf.daily_pnl)}</span></div>}
        </Card>
      </div>

      <Card title={`Trade history (${tr.length} trades, ${tr.filter((t) => t.pnl > 0).length} winning, ${tr.filter((t) => t.pnl < 0).length} losing)`}>
        <Table head={['Date & time', 'Stock', 'Action', 'Qty', 'Entry', 'Exit', 'P&L']} rows={tr.map((t) => (
          <tr key={t.id} className="border-t border-white/10"><td className="p-2">{new Date(t.ts).toLocaleString('en-IN')}</td><td className="p-2">{t.symbol}</td>
            <td className={`p-2 font-semibold ${t.side === 'BUY' ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>{t.side}</td><td className="p-2">{t.qty}</td>
            <td className="p-2">{inr(t.entry)}</td><td className="p-2">{t.exit ? inr(t.exit) : '-'}</td>
            <td className={`p-2 ${t.pnl == null ? '' : tone(t.pnl)}`}>{t.pnl == null ? '-' : inr(t.pnl)}</td></tr>))} />
      </Card>
    </div>
  )
}
