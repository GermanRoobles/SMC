import { useEffect, useRef, useState } from 'react'
import { runBacktest } from '../api'
// @ts-ignore
import Plotly from 'plotly.js-dist-min'

export default function BacktestPage() {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('15m')
  const [days, setDays] = useState(5)
  const [initialCapital, setInitialCapital] = useState(10000)
  const [risk, setRisk] = useState(1.0)
  const [duration, setDuration] = useState(48)
  const [mode, setMode] = useState<'demo' | 'ml' | 'smc'>('demo')
  const [step, setStep] = useState(20)
  const [maxSignals, setMaxSignals] = useState(50)
  const [mlMinConf, setMlMinConf] = useState<number | ''>('' as any)
  const [mlAllowFallback, setMlAllowFallback] = useState(true)
  const [sessions, setSessions] = useState<{london:boolean; newyork:boolean; asia:boolean}>({ london: false, newyork: false, asia: false })
  const [startHour, setStartHour] = useState('')
  const [endHour, setEndHour] = useState('')
  // Flags SMC avanzados
  const [smcRequireStruct, setSmcRequireStruct] = useState(true)
  const [smcHtfBias, setSmcHtfBias] = useState(true)
  const [smcHtfTf, setSmcHtfTf] = useState('4h')
  const [smcMitigationOnly, setSmcMitigationOnly] = useState(true)
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState('')
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [equity, setEquity] = useState<number[]>([])
  const [equityPoints, setEquityPoints] = useState<any[]>([])
  const equityRef = useRef<HTMLDivElement | null>(null)
  const pnlHistRef = useRef<HTMLDivElement | null>(null)
  const ddRef = useRef<HTMLDivElement | null>(null)

  const run = async () => {
    setLoading(true); setError(null)
    try {
      const res = await runBacktest({
        symbol, timeframe, days,
        initial_capital: initialCapital,
        risk_per_trade: risk,
        max_trade_duration: duration,
        mode, step, max_signals: maxSignals,
        use_ml: mode === 'ml',
        ml_min_confidence: (mode === 'ml' && mlMinConf !== '' ? Number(mlMinConf) : undefined),
        ml_allow_trend_fallback: mode === 'ml' ? mlAllowFallback : undefined,
        smc_require_structure_confirm: mode === 'smc' ? smcRequireStruct : undefined,
        smc_htf_bias: mode === 'smc' ? smcHtfBias : undefined,
        smc_htf_timeframe: mode === 'smc' ? smcHtfTf : undefined,
        smc_mitigation_only: mode === 'smc' ? smcMitigationOnly : undefined,
        sessions: (sessions.london || sessions.newyork || sessions.asia) ? [
          ...(sessions.london? ['london']: []),
          ...(sessions.newyork? ['newyork']: []),
          ...(sessions.asia? ['asia']: []),
        ] : undefined,
        trading_hours: (startHour && endHour) ? { start: startHour, end: endHour } : undefined,
      })
      setResults(res?.results)
      setReport(res?.report)
      setEquity(res?.equity_curve || [])
      setEquityPoints(res?.equity_points || [])
    } catch (e: any) {
      setError(e?.message || 'Error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const el = equityRef.current
    if (!el) return
    const x = (equityPoints || []).map(p => p.time || '')
    const y = (equity || [])
    try {
      Plotly.react(el, [{ x, y, type: 'scatter', mode: 'lines', line: { color: '#42a5f5' } }], { paper_bgcolor: '#0b0e14', plot_bgcolor: '#0b0e14', font: { color: '#d2d6db' }, height: 320, margin: { l: 48, r: 16, t: 24, b: 48 } })
    } catch {}
  }, [equity, equityPoints])

  // Histograma de PnL de trades y curva de drawdown (aproximada desde equity)
  useEffect(() => {
    const eh = pnlHistRef.current
    const ed = ddRef.current
    if (!eh || !ed) return
    const trades = (results?.trades || []) as any[]
    const pnl = trades.map(t => t.pnl_points || 0)
    try {
      Plotly.react(eh, [{ x: pnl, type: 'histogram', marker: { color: '#7db6ff' } }], { paper_bgcolor: '#0b0e14', plot_bgcolor: '#0b0e14', font: { color: '#d2d6db' }, height: 280, margin: { l: 48, r: 16, t: 24, b: 48 } })
    } catch {}
    try {
      const eq = equity || []
      let peak = eq[0] || 0
      const dd = eq.map(v => { peak = Math.max(peak, v); return peak - v })
      Plotly.react(ed, [{ x: dd.map((_, i) => i), y: dd, type: 'scatter', mode: 'lines', line: { color: '#ef5350' } }], { paper_bgcolor: '#0b0e14', plot_bgcolor: '#0b0e14', font: { color: '#d2d6db' }, height: 280, margin: { l: 48, r: 16, t: 24, b: 48 }, yaxis: { title: 'Drawdown' } })
    } catch {}
  }, [results, equity])

  return (
    <div style={{ padding: 16 }}>
      <h2>Backtesting</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, alignItems: 'center' }}>
        <label>Symbol <input value={symbol} onChange={e => setSymbol(e.target.value)} /></label>
        <label>Timeframe
          <select value={timeframe} onChange={e => setTimeframe(e.target.value)}>
            {['15m','1h','4h','1d'].map(tf => <option key={tf} value={tf}>{tf}</option>)}
          </select>
        </label>
        <label>Días <input type="number" min={1} max={365} value={days} onChange={e => setDays(parseInt(e.target.value||'1'))} /></label>
        <label>Capital inicial <input type="number" value={initialCapital} onChange={e => setInitialCapital(parseFloat(e.target.value||'0'))} /></label>
        <label>Riesgo % <input type="number" step={0.1} value={risk} onChange={e => setRisk(parseFloat(e.target.value||'0'))} /></label>
        <label>Duración máx (h) <input type="number" value={duration} onChange={e => setDuration(parseInt(e.target.value||'1'))} /></label>
        <label>Modo
          <select value={mode} onChange={e => setMode(e.target.value as any)}>
            <option value="demo">Demo</option>
            <option value="ml">ML</option>
            <option value="smc">SMC</option>
          </select>
        </label>
        <label>Step <input type="number" min={5} max={200} value={step} onChange={e => setStep(parseInt(e.target.value||'5'))} /></label>
        <label>Max señales <input type="number" min={1} max={200} value={maxSignals} onChange={e => setMaxSignals(parseInt(e.target.value||'10'))} /></label>
        {mode === 'ml' && (
          <>
            <label>ML min conf <input type="number" step={0.01} min={0} max={1} value={mlMinConf as any} onChange={e => setMlMinConf(e.target.value === '' ? '' : Number(e.target.value))} placeholder="0.6" /></label>
            <label><input type="checkbox" checked={mlAllowFallback} onChange={e => setMlAllowFallback(e.target.checked)} /> Permitir fallback a tendencia</label>
          </>
        )}
        <div style={{ gridColumn: '1 / -1', marginTop: 8 }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Filtros de sesión/horarios</div>
          <label><input type="checkbox" checked={sessions.london} onChange={e => setSessions(s => ({...s, london: e.target.checked}))} /> Londres</label>{' '}
          <label><input type="checkbox" checked={sessions.newyork} onChange={e => setSessions(s => ({...s, newyork: e.target.checked}))} /> Nueva York</label>{' '}
          <label><input type="checkbox" checked={sessions.asia} onChange={e => setSessions(s => ({...s, asia: e.target.checked}))} /> Asia</label>{' '}
          <span style={{ marginLeft: 8 }}>
            Horario (UTC):
            <input type="time" value={startHour} onChange={e => setStartHour(e.target.value)} style={{ marginLeft: 6 }} />
            <input type="time" value={endHour} onChange={e => setEndHour(e.target.value)} style={{ marginLeft: 6 }} />
          </span>
        </div>
        {mode === 'smc' && (
          <>
            <label><input type="checkbox" checked={smcRequireStruct} onChange={e => setSmcRequireStruct(e.target.checked)} /> Confirmación estructura</label>
            <label><input type="checkbox" checked={smcHtfBias} onChange={e => setSmcHtfBias(e.target.checked)} /> Sesgo HTF</label>
            {smcHtfBias && (
              <label>HTF TF
                <select value={smcHtfTf} onChange={e => setSmcHtfTf(e.target.value)}>
                  {['4h','1d'].map(tf => <option key={tf} value={tf}>{tf}</option>)}
                </select>
              </label>
            )}
            <label><input type="checkbox" checked={smcMitigationOnly} onChange={e => setSmcMitigationOnly(e.target.checked)} /> Solo mitigación</label>
          </>
        )}
        <div><button onClick={run} disabled={loading}>{loading? 'Ejecutando...' : 'Ejecutar backtest'}</button></div>
      </div>
      {error && <div style={{ color: 'crimson', marginTop: 8 }}>Error: {error}</div>}
      <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <h3>Curva de Capital</h3>
          <div ref={equityRef} />
        </div>
        <div>
          <h3>Reporte</h3>
          <pre style={{ maxHeight: 480, overflow: 'auto', background: '#111', color: '#ddd', padding: 8 }}>{report}</pre>
        </div>
      </div>

      <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <h3>Histograma PnL Trades</h3>
          <div ref={pnlHistRef} />
        </div>
        <div>
          <h3>Curva de Drawdown</h3>
          <div ref={ddRef} />
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Trades</h3>
        <div style={{ overflow: 'auto', maxHeight: 360 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['entry_time','exit_time','type','entry','exit','sl','tp','result','pnl','rr','dur_h'].map(h => (
                  <th key={h} style={{ position: 'sticky', top: 0, background: '#111', textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid #222' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(results?.trades || []).map((t: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid #1a1f2b' }}>
                  <td style={{ padding: '6px 8px' }}>{String(t.entry_time)}</td>
                  <td style={{ padding: '6px 8px' }}>{String(t.exit_time)}</td>
                  <td style={{ padding: '6px 8px' }}>{t.signal_type}</td>
                  <td style={{ padding: '6px 8px' }}>{t.entry_price?.toFixed?.(2) ?? t.entry_price}</td>
                  <td style={{ padding: '6px 8px' }}>{t.exit_price?.toFixed?.(2) ?? t.exit_price}</td>
                  <td style={{ padding: '6px 8px' }}>{t.stop_loss?.toFixed?.(2) ?? t.stop_loss}</td>
                  <td style={{ padding: '6px 8px' }}>{t.take_profit?.toFixed?.(2) ?? t.take_profit}</td>
                  <td style={{ padding: '6px 8px' }}>{t.result}</td>
                  <td style={{ padding: '6px 8px' }}>{t.pnl_points?.toFixed?.(2) ?? t.pnl_points}</td>
                  <td style={{ padding: '6px 8px' }}>{t.risk_reward_achieved?.toFixed?.(2) ?? t.risk_reward_achieved}</td>
                  <td style={{ padding: '6px 8px' }}>{t.duration_hours?.toFixed?.(1) ?? t.duration_hours}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}


