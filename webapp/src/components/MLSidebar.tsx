import { useEffect, useState } from 'react'
import { fetchMLActive, fetchMLStats } from '../api'

export default function MLSidebar() {
  const [mlActive, setMlActive] = useState<any[]>([])
  const [mlStats, setMlStats] = useState<any>(null)

  useEffect(() => {
    let mounted = true
    const tick = async () => {
      try {
        const [a, s] = await Promise.all([
          fetchMLActive().catch(() => []),
          fetchMLStats().catch(() => null),
        ])
        if (!mounted) return
        setMlActive(a || [])
        setMlStats(s || null)
      } catch {}
    }
    tick()
    const id = setInterval(tick, 5000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return (
    <div>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>ML - Señales Activas</div>
      {mlActive?.length ? mlActive.map((s, i) => (
        <div key={i} style={{ border: '1px solid #222', borderRadius: 8, padding: 8, marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>{s.type} {s.symbol}</div>
            <div style={{ opacity: 0.8 }}>{s.timeframe}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 6, fontSize: 12, marginTop: 6 }}>
            <div>Entry: {s.entry?.toFixed?.(2) ?? s.entry}</div>
            <div>SL: {s.sl?.toFixed?.(2) ?? s.sl}</div>
            <div>TP1: {s.tp1?.toFixed?.(2) ?? s.tp1}</div>
            <div>RR: {s.rr1?.toFixed?.(2) ?? s.rr1}</div>
            <div>Prob: {(s.ml_prob*100)?.toFixed?.(1) ?? s.ml_prob}%</div>
            <div>Conf: {(s.ml_conf*100)?.toFixed?.(1) ?? s.ml_conf}%</div>
          </div>
        </div>
      )) : <div style={{ opacity: 0.7 }}>Sin señales activas</div>}

      <div style={{ fontWeight: 600, margin: '12px 0 8px' }}>ML - Métricas</div>
      {mlStats ? (
        <div style={{ fontSize: 12, lineHeight: 1.4 }}>
          <div>Señales generadas: {mlStats?.ml_signal_generator?.total_signals_generated ?? 0}</div>
          <div>Señales activas: {mlStats?.ml_signal_generator?.active_signals ?? 0}</div>
          <div>Confianza prom.: {(((mlStats?.ml_signal_generator?.avg_confidence ?? 0)*100) as number).toFixed?.(1)}</div>
          <div>RR prom.: {(mlStats?.ml_signal_generator?.avg_risk_reward ?? 0).toFixed?.(2)}</div>
        </div>
      ) : <div style={{ opacity: 0.7 }}>Sin datos</div>}
    </div>
  )
}


