import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { analyzeSMC, fetchOHLCVExtended, mlPredict } from './api'
import type { OHLCV } from './api'
import { Chart } from './components/Chart'
import { Layout } from './components/Layout'
import MLSidebar from './components/MLSidebar'

function App() {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('15m')
  const [days, setDays] = useState(5)
  const [ohlcv, setOhlcv] = useState<OHLCV[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [smc, setSmc] = useState<any>(null)
  const [ml, setMl] = useState<any>(null)
  const [showFvg, setShowFvg] = useState(true)
  const [showOb, setShowOb] = useState(true)
  const [showLiq, setShowLiq] = useState(true)
  const [live, setLive] = useState(false)
  const [showSessions, setShowSessions] = useState(true)

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchOHLCVExtended(symbol, timeframe, days)
      setOhlcv(data)
      const smcRes = await analyzeSMC(symbol, timeframe, days)
      setSmc(smcRes)
      const mlRes = await mlPredict(symbol, timeframe, days)
      setMl(mlRes)
    } catch (e: any) {
      setError(e?.message || 'Error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Streaming de precio en vivo via WebSocket
  useEffect(() => {
    if (!live) return
    const base = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace('http', 'ws')
    const url = `${base}/ws/prices?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&interval=5`
    const ws = new WebSocket(url)
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg?.last) {
          setOhlcv(prev => {
            const copy = prev.slice()
            const i = copy.findIndex(x => x.timestamp === msg.last.timestamp)
            if (i >= 0) copy[i] = msg.last
            else copy.push(msg.last)
            return copy
          })
        }
      } catch {}
    }
    return () => { try { ws.close() } catch {} }
  }, [live, symbol, timeframe])

  const lastCandle = useMemo(() => ohlcv.at(-1), [ohlcv])

  const sidebar = (
    <div style={{ display: 'grid', gap: 12 }}>
      <MLSidebar />
      <div style={{ height: 1, background: '#222', margin: '8px 0' }} />
      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Controles</div>
        <div style={{ display: 'grid', gap: 6 }}>
          <label>Símbolo <input value={symbol} onChange={(e) => setSymbol(e.target.value)} /></label>
          <label>Timeframe
            <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
              {['15m','1h','4h','1d','1w'].map(tf => <option key={tf} value={tf}>{tf}</option>)}
            </select>
          </label>
          <label>Días <input type="number" min={1} max={365} value={days} onChange={(e) => setDays(parseInt(e.target.value||'1'))} /></label>
          <button onClick={loadAll} disabled={loading}>{loading? 'Cargando...' : 'Actualizar'}</button>
        </div>
      </div>
      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Overlays</div>
        <label><input type="checkbox" checked={showFvg} onChange={e => setShowFvg(e.target.checked)} /> FVG</label><br/>
        <label><input type="checkbox" checked={showOb} onChange={e => setShowOb(e.target.checked)} /> OB</label><br/>
        <label><input type="checkbox" checked={showLiq} onChange={e => setShowLiq(e.target.checked)} /> Liquidity</label><br/>
        <label><input type="checkbox" checked={showSessions} onChange={e => setShowSessions(e.target.checked)} /> Sesiones</label>
      </div>
      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Streaming</div>
        <label><input type="checkbox" checked={live} onChange={e => setLive(e.target.checked)} /> Actualización en vivo</label>
      </div>
      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>ML Predictor</div>
        <div style={{ fontSize: 12 }}>Estado: {ml ? 'ON' : 'Cargando...'}</div>
        <div style={{ fontSize: 12 }}>Prob: {ml?.prediction?.probability ? (ml.prediction.probability*100).toFixed(1)+'%' : '-'}</div>
        <div style={{ fontSize: 12 }}>Conf: {ml?.prediction?.confidence ? (ml.prediction.confidence*100).toFixed(1)+'%' : '-'}</div>
        <div style={{ fontSize: 12 }}>Rec: {ml?.prediction?.recommendation ?? '-'}</div>
      </div>
      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Indicadores SMC</div>
        <div style={{ fontSize: 12 }}>FVGs: {smc?.fvg?.length ?? 0}</div>
        <div style={{ fontSize: 12 }}>OBs: {smc?.orderblocks?.length ?? 0}</div>
        <div style={{ fontSize: 12 }}>Liquidity: {smc?.liquidity?.length ?? 0}</div>
        <div style={{ fontSize: 12 }}>Estructura: {smc?.market_structure ?? '-'}</div>
        <div style={{ fontSize: 12 }}>BOS/CHoCH: {smc?.bos_choch_strength ?? '-'}</div>
      </div>
      {error && <div style={{ color: 'crimson' }}>Error: {error}</div>}
    </div>
  )

  return (
    <Layout sidebar={sidebar}>
      <div style={{ display: 'grid', gap: 12 }}>
        <div style={{ fontWeight: 600 }}>Símbolo: {symbol} | TF: {timeframe} | Velas: {ohlcv.length} {lastCandle && `(última: ${lastCandle.timestamp})`}</div>
        <Chart
          data={ohlcv}
          fvg={showFvg ? (smc?.fvg?.map((z: any) => ({ top: z.Top ?? z.top, bottom: z.Bottom ?? z.bottom })) ?? []) : []}
          ob={showOb ? (smc?.orderblocks?.map((z: any) => ({ top: z.Top ?? z.top, bottom: z.Bottom ?? z.bottom })) ?? []) : []}
          liq={showLiq ? (smc?.liquidity?.map((z: any) => z.Level ?? z.level) ?? []) : []}
          showSessions={showSessions}
        />
      </div>
    </Layout>
  )
}

export default App
