import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

const Candle = ({ x, y, width, height, payload: p }) => {
  const col = p.close >= p.open ? '#22C55E' : '#EF4444'
  const k = height / (p.high - p.low || 1)
  const top = y + (p.high - Math.max(p.open, p.close)) * k
  return (
    <g stroke={col} fill={col}>
      <line x1={x + width / 2} x2={x + width / 2} y1={y} y2={y + height} />
      <rect x={x + width * 0.15} y={top} width={width * 0.7} height={Math.max(1, Math.abs(p.open - p.close) * k)} />
    </g>
  )
}

const Tip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  return (
    <div className="rounded-lg border border-white/10 bg-[#162338] p-2 text-xs">
      <div className="text-[#94A3B8]">{p.t}</div>
      O {p.open} H {p.high} L {p.low} C {p.close}
      <div>Vol {Number(p.volume).toLocaleString('en-IN')}</div>
    </div>
  )
}

const tick = { fill: '#94A3B8', fontSize: 11 }

export default function Chart({ data }) {
  const d = data.map((x) => ({ ...x, hl: [x.low, x.high] }))
  return (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={d}>
          <CartesianGrid stroke="#22324b" />
          <XAxis dataKey="t" tick={tick} minTickGap={40} />
          <YAxis domain={['auto', 'auto']} orientation="right" tick={tick} />
          <Tooltip content={<Tip />} />
          <Bar dataKey="hl" shape={<Candle />} isAnimationActive={false} />
          <Line dataKey="sma20" dot={false} stroke="#F59E0B" isAnimationActive={false} />
          <Line dataKey="sma50" dot={false} stroke="#A78BFA" isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
      <ResponsiveContainer width="100%" height={70}>
        <ComposedChart data={d}>
          <XAxis dataKey="t" hide />
          <YAxis orientation="right" tick={tick} />
          <Bar dataKey="volume" fill="#3B82F6" opacity={0.5} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </>
  )
}
