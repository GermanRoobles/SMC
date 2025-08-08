import { useEffect, useRef } from 'react'
// Tipos de Plotly están disponibles vía @types/plotly.js
// La build usa el bundle plotly.js-dist-min
// Para TS, tipamos mínimamente con any donde sea necesario
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import type { OHLCV } from '../api'

export type Zone = { top: number; bottom: number }

export function Chart({ data, fvg = [], ob = [], liq = [], showRangeControls = true, showSessions = true }: { data: OHLCV[]; fvg?: Zone[]; ob?: Zone[]; liq?: number[]; showRangeControls?: boolean; showSessions?: boolean }) {
  const ref = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!ref.current) return
    const x = data.map(d => d.timestamp)
    const open = data.map(d => d.open)
    const high = data.map(d => d.high)
    const low = data.map(d => d.low)
    const close = data.map(d => d.close)

    const candlestick: Partial<Plotly.PlotData> = {
      type: 'candlestick', x, open, high, low, close,
      increasing: { line: { color: '#26a69a' } },
      decreasing: { line: { color: '#ef5350' } },
    }

    // Shapes para FVG/OB y sesiones
    const shapes: any[] = []
    if (showSessions) {
      // Pintar bandas verticales aproximando sesiones UTC: Tokio 00-08, Londres 08-16, NY 13-21, Sídney 21-05
      for (let i = 0; i < x.length; i++) {
        const ts = x[i]
        const dt = new Date(ts)
        const h = dt.getUTCHours()
        // Tokio (00-08 UTC)
        if (h === 0) {
          const start = ts
          const end = x[Math.min(i + 32, x.length - 1)] || ts
          shapes.push({ type: 'rect', xref: 'x', yref: 'paper', x0: start, x1: end, y0: 0, y1: 1, fillcolor: 'rgba(255,193,7,0.06)', line: { width: 0 } })
        }
        // Londres (08-16 UTC)
        if (h === 8) {
          const start = ts
          const end = x[Math.min(i + 32, x.length - 1)] || ts  // ~8 horas a 15m
          shapes.push({ type: 'rect', xref: 'x', yref: 'paper', x0: start, x1: end, y0: 0, y1: 1, fillcolor: 'rgba(0,150,136,0.07)', line: { width: 0 } })
        }
        // Nueva York
        if (h === 13) {
          const start = ts
          const end = x[Math.min(i + 32, x.length - 1)] || ts
          shapes.push({ type: 'rect', xref: 'x', yref: 'paper', x0: start, x1: end, y0: 0, y1: 1, fillcolor: 'rgba(156,39,176,0.06)', line: { width: 0 } })
        }
        // Sídney (21-05 UTC)
        if (h === 21) {
          const start = ts
          const end = x[Math.min(i + 32, x.length - 1)] || ts
          shapes.push({ type: 'rect', xref: 'x', yref: 'paper', x0: start, x1: end, y0: 0, y1: 1, fillcolor: 'rgba(3,169,244,0.06)', line: { width: 0 } })
        }
      }
    }
    const maxZones = 10
    fvg.slice(-maxZones).forEach((z) => {
      shapes.push({ type: 'rect', xref: 'x', yref: 'y', x0: x[0], x1: x[x.length - 1], y0: z.bottom, y1: z.top, fillcolor: 'rgba(33,150,243,0.08)', line: { width: 0 } })
    })
    ob.slice(-maxZones).forEach((z) => {
      shapes.push({ type: 'rect', xref: 'x', yref: 'y', x0: x[0], x1: x[x.length - 1], y0: z.bottom, y1: z.top, fillcolor: 'rgba(76,175,80,0.10)', line: { width: 0 } })
    })
    liq.slice(-maxZones).forEach((level) => {
      shapes.push({ type: 'line', xref: 'x', yref: 'y', x0: x[0], x1: x[x.length - 1], y0: level, y1: level, line: { color: '#ffd54f', width: 1, dash: 'dot' } })
    })

    // Rango dinámico de Y basado en datos y overlays
    const dataMin = Math.min(...low)
    const dataMax = Math.max(...high)
    const fvgMin = fvg.length ? Math.min(...fvg.map(z => Math.min(z.bottom, z.top))) : Number.POSITIVE_INFINITY
    const fvgMax = fvg.length ? Math.max(...fvg.map(z => Math.max(z.bottom, z.top))) : Number.NEGATIVE_INFINITY
    const obMin = ob.length ? Math.min(...ob.map(z => Math.min(z.bottom, z.top))) : Number.POSITIVE_INFINITY
    const obMax = ob.length ? Math.max(...ob.map(z => Math.max(z.bottom, z.top))) : Number.NEGATIVE_INFINITY
    const liqMin = liq.length ? Math.min(...liq) : Number.POSITIVE_INFINITY
    const liqMax = liq.length ? Math.max(...liq) : Number.NEGATIVE_INFINITY
    let yMin = Math.min(dataMin, fvgMin, obMin, liqMin)
    let yMax = Math.max(dataMax, fvgMax, obMax, liqMax)
    if (!isFinite(yMin)) yMin = dataMin
    if (!isFinite(yMax)) yMax = dataMax
    const pad = (yMax - yMin) * 0.05

    const layout: Partial<Plotly.Layout> = {
      paper_bgcolor: '#0b0e14', plot_bgcolor: '#0b0e14',
      font: { color: '#d2d6db' },
      xaxis: {
        rangeslider: { visible: showRangeControls },
        rangeselector: showRangeControls ? {
          buttons: [
            { step: 'hour', stepmode: 'backward', count: 6, label: '6h' },
            { step: 'day', stepmode: 'backward', count: 1, label: '1d' },
            { step: 'day', stepmode: 'backward', count: 3, label: '3d' },
            { step: 'month', stepmode: 'backward', count: 1, label: '1m' },
            { step: 'all', label: 'All' },
          ]
        } : undefined,
      },
      yaxis: { fixedrange: false, autorange: false, range: [yMin - pad, yMax + pad] },
      margin: { l: 32, r: 16, t: 24, b: 24 },
      height: 520,
      shapes,
    }

    Plotly.react(ref.current, [candlestick], layout as any, { responsive: true })
    const handle = () => { if (ref.current) Plotly.Plots.resize(ref.current) }
    window.addEventListener('resize', handle)
    return () => { window.removeEventListener('resize', handle) }
  }, [data, fvg, ob, liq, showSessions])

  return <div ref={ref} style={{ width: '100%' }} />
}


