import { useEffect, useState } from 'react'
import { fetchMTFOverview } from '../api'
// @ts-ignore
import Plotly from 'plotly.js-dist-min'

export default function MTFPage() {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [days, setDays] = useState(30)
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchMTFOverview(symbol, days)
      setData(res)
    } catch (e: any) {
      setError(e?.message || 'Error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const tfs = ['1w','1d','4h','1h','15m']
  const charts = tfs.map(tf => ({ id: `mtf-${tf}`, tf }))

  useEffect(() => {
    if (!data) return
    charts.forEach(({ id, tf }) => {
      const d = data?.[tf]?.data || []
      const el = document.getElementById(id)
      if (!el || !d.length) return
      const x = d.map((r: any) => r.timestamp)
      const open = d.map((r: any) => r.open)
      const high = d.map((r: any) => r.high)
      const low = d.map((r: any) => r.low)
      const close = d.map((r: any) => r.close)
      Plotly.react(el, [
        { type: 'candlestick', x, open, high, low, close }
      ], {
        paper_bgcolor: '#0b0e14', plot_bgcolor: '#0b0e14', font: { color: '#d2d6db' },
        height: 320,
        margin: { l: 32, r: 16, t: 24, b: 24 },
        xaxis: { rangeslider: { visible: false } },
      })
    })
  }, [data])

  return (
    <div style={{ padding: 16, maxWidth: '100%', width: '100%' }}>
      <h2>Multi‑Timeframe Overview</h2>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <input value={symbol} onChange={(e) => setSymbol(e.target.value)} />
        <input type="number" min={1} max={365} value={days} onChange={(e) => setDays(parseInt(e.target.value||'1'))} />
        <button onClick={load} disabled={loading}>{loading? 'Cargando...' : 'Actualizar'}</button>
      </div>
      {error && <div style={{ color: 'crimson', marginTop: 8 }}>Error: {error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16, marginTop: 12, width: '100%' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
          {charts.slice(0, 4).map(c => (
            <div key={c.id} style={{ width: '100%' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{c.tf.toUpperCase()}</div>
              <div id={c.id} style={{ width: '100%' }} />
            </div>
          ))}
        </div>
        <div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{charts[4].tf.toUpperCase()}</div>
          <div id={charts[4].id} style={{ width: '100%' }} />
        </div>
      </div>
    </div>
  )
}


