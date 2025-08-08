import { useEffect, useMemo, useState } from 'react'
// @ts-ignore
import Plotly from 'plotly.js-dist-min'

export default function MLPage() {
  const [history, setHistory] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const res = await fetch((import.meta.env.VITE_API_BASE || 'http://localhost:8000') + '/api/ml/history')
      if (!res.ok) throw new Error('HTTP ' + res.status)
      const data = await res.json()
      setHistory(data)
    } catch (e: any) {
      setError(e?.message || 'Error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const chartData = useMemo(() => {
    const t = history.map(h => h.time)
    const p = history.map(h => h.probability * 100)
    const c = history.map(h => h.confidence * 100)
    return { t, p, c }
  }, [history])

  useEffect(() => {
    const el = document.getElementById('ml-lines')
    if (!el) return
    const { t, p, c } = chartData
    Plotly.react(el, [
      { x: t, y: p, type: 'scatter', mode: 'lines', name: 'Prob %', line: { color: '#42a5f5' } },
      { x: t, y: c, type: 'scatter', mode: 'lines', name: 'Conf %', line: { color: '#ffb74d' } },
    ], { paper_bgcolor: '#0b0e14', plot_bgcolor: '#0b0e14', font: { color: '#d2d6db' }, height: 360, margin: { l: 48, r: 16, t: 24, b: 48 }, yaxis: { range: [0, 100] } })
  }, [chartData])

  return (
    <div style={{ padding: 16 }}>
      <h2>ML - Historial y Señales</h2>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={load} disabled={loading}>{loading? 'Cargando...' : 'Actualizar'}</button>
      </div>
      {error && <div style={{ color: 'crimson', marginTop: 8 }}>Error: {error}</div>}

      <div style={{ marginTop: 12 }}>
        <h3>Probabilidad y Confianza</h3>
        <div id="ml-lines" />
      </div>

      <div style={{ marginTop: 12 }}>
        <h3>Últimas Señales</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Hora','Prob %','Conf %','Recomendación'].map(h => <th key={h} style={{ position: 'sticky', top: 0, background: '#111', textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid #222' }}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {history.slice(-50).reverse().map((h, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #1a1f2b' }}>
                <td style={{ padding: '6px 8px' }}>{h.time}</td>
                <td style={{ padding: '6px 8px' }}>{(h.probability*100).toFixed(1)}%</td>
                <td style={{ padding: '6px 8px' }}>{(h.confidence*100).toFixed(1)}%</td>
                <td style={{ padding: '6px 8px' }}>{h.recommendation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


