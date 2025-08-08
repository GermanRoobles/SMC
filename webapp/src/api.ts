export type OHLCV = { timestamp: string; open: number; high: number; low: number; close: number; volume: number };

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export async function fetchOHLCV(symbol: string, timeframe: string, limit?: number): Promise<OHLCV[]> {
  const res = await fetch(`${API_BASE}/api/ohlcv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, timeframe, limit }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchOHLCVExtended(symbol: string, timeframe: string, days: number): Promise<OHLCV[]> {
  const res = await fetch(`${API_BASE}/api/ohlcv/extended`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, timeframe, days }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function analyzeSMC(symbol: string, timeframe: string, days: number) {
  const res = await fetch(`${API_BASE}/api/smc/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, timeframe, days }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function mlPredict(symbol: string, timeframe: string, days: number) {
  const res = await fetch(`${API_BASE}/api/ml/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, timeframe, days }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function runBacktest(payload: {
  symbol: string;
  timeframe: string;
  days: number;
  initial_capital?: number;
  risk_per_trade?: number;
  max_trade_duration?: number;
  signals?: Array<{ side: string; entry: number; stop_loss: number; take_profit: number; timestamp?: string }>;
  mode?: 'demo' | 'ml' | 'smc';
  step?: number;
  max_signals?: number;
  use_ml?: boolean;
  ml_min_confidence?: number;
  ml_allow_trend_fallback?: boolean;
  // SMC flags
  smc_require_structure_confirm?: boolean;
  smc_htf_bias?: boolean;
  smc_htf_timeframe?: string;
  smc_mitigation_only?: boolean;
  // Filtros de sesión/horarios
  sessions?: string[];
  trading_hours?: { start: string; end: string };
}) {
  const res = await fetch(`${API_BASE}/api/backtest/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchMTFOverview(symbol: string, days: number) {
  const res = await fetch(`${API_BASE}/api/mtf/overview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, days }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fetchMLActive() {
  const res = await fetch(`${API_BASE}/api/ml/active`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fetchMLStats() {
  const res = await fetch(`${API_BASE}/api/ml/stats`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fetchSMCCounters(symbol: string, timeframe: string, days: number) {
  const res = await fetch(`${API_BASE}/api/smc/counters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, timeframe, days })
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

