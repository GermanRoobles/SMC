from fastapi import FastAPI, HTTPException
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import math
import numpy as np
import pandas as pd

# Importar módulos existentes del proyecto
from fetch_data import get_ohlcv, get_ohlcv_extended
from smc_analysis import analyze
from smc_ml_signal_integration import get_ml_signal_integration
from smc_backtester import SMCBacktester, calculate_adaptive_levels
from dataclasses import asdict, is_dataclass
from smc_multi_timeframe import create_multi_timeframe_analyzer


class OHLCVRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    limit: Optional[int] = 500


class OHLCVExtendedRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    days: int = 5


class AnalyzeRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    days: int = 5


class PredictRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    days: int = 5

class SMCCountersRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    days: int = 5
    fvg_min_pct: Optional[float] = None
    ob_min_pct: Optional[float] = None
    mitigation_partial: Optional[float] = None


class BacktestSignal(BaseModel):
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    timestamp: Optional[str] = None


class BacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    days: int = 5
    initial_capital: float = 10_000
    risk_per_trade: float = 1.0
    max_trade_duration: int = 48
    signals: Optional[List[BacktestSignal]] = None
    use_ml: Optional[bool] = False
    step: Optional[int] = 10
    max_signals: Optional[int] = 50
    mode: Optional[str] = "demo"  # demo | ml | smc
    ml_min_confidence: Optional[float] = None
    ml_allow_trend_fallback: Optional[bool] = True
    # Flags SMC avanzados
    smc_require_structure_confirm: Optional[bool] = False
    smc_htf_bias: Optional[bool] = False
    smc_htf_timeframe: Optional[str] = None  # '4h' | '1d'
    smc_mitigation_only: Optional[bool] = False
    # Filtros de sesión/horarios
    sessions: Optional[List[str]] = None  # ['london','newyork','asia']
    trading_hours: Optional[Dict[str, str]] = None  # {'start': '08:00', 'end': '20:00'} UTC


app = FastAPI(title="SMC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _sanitize_scalar(value: Any):
    try:
        # Numpy escalares a tipos nativos
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            f = float(value)
            return f if math.isfinite(f) else None
        if isinstance(value, float):
            return value if math.isfinite(value) else None
    except Exception:
        pass
    return value


def _to_jsonable(obj: Any):
    try:
        if is_dataclass(obj):
            return _to_jsonable(asdict(obj))
        if isinstance(obj, pd.DataFrame):
            safe_df = obj.replace([np.inf, -np.inf], np.nan)
            safe_df = safe_df.where(pd.notna(safe_df), None)
            # Convertir tipos numpy en columnas objeto
            return [
                {k: _sanitize_scalar(v) for k, v in row.items()}
                for row in safe_df.to_dict(orient="records")
            ]
        if isinstance(obj, pd.Series):
            safe_s = obj.replace([np.inf, -np.inf], np.nan)
            safe_s = safe_s.where(pd.notna(safe_s), None)
            return {k: _sanitize_scalar(v) for k, v in safe_s.to_dict().items()}
        if isinstance(obj, dict):
            return {k: _to_jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_to_jsonable(x) for x in obj]
        # Escalares sueltos
        return _sanitize_scalar(obj)
    except Exception:
        pass
    return obj


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ohlcv")
def api_ohlcv(req: OHLCVRequest):
    df = get_ohlcv(req.symbol, req.timeframe, limit=req.limit)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Sin datos")
    return df.to_dict(orient="records")


@app.post("/api/ohlcv/extended")
def api_ohlcv_extended(req: OHLCVExtendedRequest):
    df = get_ohlcv_extended(req.symbol, req.timeframe, days=req.days)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Sin datos")
    return df.to_dict(orient="records")


@app.post("/api/smc/analyze")
def api_smc_analyze(req: AnalyzeRequest):
    df = get_ohlcv_extended(req.symbol, req.timeframe, days=req.days)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Sin datos")
    result = analyze(df, timeframe=req.timeframe)
    return _to_jsonable(result)


@app.post("/api/ml/predict")
def api_ml_predict(req: PredictRequest):
    integration = get_ml_signal_integration()
    df = get_ohlcv_extended(req.symbol, req.timeframe, days=req.days)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Sin datos")
    smc = analyze(df, timeframe=req.timeframe)
    signal = integration.generate_ml_signal(df, smc, symbol=req.symbol, timeframe=req.timeframe)
    return {
        "prediction": _to_jsonable(getattr(integration, "last_prediction", None)),
        "signal": _to_jsonable(signal.to_dict() if signal else None),
        "stats": _to_jsonable(integration.get_integration_stats()),
    }


@app.get("/api/ml/history")
def api_ml_history():
    integration = get_ml_signal_integration()
    return _to_jsonable(getattr(integration, 'prediction_history', []))

@app.get("/api/ml/active")
def api_ml_active():
    integration = get_ml_signal_integration()
    try:
        active = integration.get_active_signals()
        simplified = []
        for s in active:
            simplified.append({
                'timestamp': str(getattr(s, 'timestamp', None)),
                'symbol': getattr(s, 'symbol', None),
                'timeframe': getattr(s, 'timeframe', None),
                'type': getattr(getattr(s, 'signal_type', None), 'value', None),
                'entry': getattr(s, 'entry_price', None),
                'sl': getattr(s, 'stop_loss', None),
                'tp1': getattr(s, 'take_profit_1', None),
                'rr1': getattr(s, 'risk_reward_1', None),
                'ml_prob': getattr(s, 'ml_probability', None),
                'ml_conf': getattr(s, 'ml_confidence', None),
            })
        return _to_jsonable(simplified)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/stats")
def api_ml_stats():
    integration = get_ml_signal_integration()
    try:
        return _to_jsonable(integration.get_integration_stats())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/smc/counters")
def api_smc_counters(req: SMCCountersRequest):
    df = get_ohlcv_extended(req.symbol, req.timeframe, days=req.days)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Sin datos")
    smc = analyze(df, timeframe=req.timeframe)
    try:
        fvg_df = smc.get('fvg')
        ob_df = smc.get('orderblocks')
        liq_df = smc.get('liquidity')
        counters = {
            'fvg_count': int(len(fvg_df)) if fvg_df is not None else 0,
            'ob_count': int(len(ob_df)) if ob_df is not None else 0,
            'liquidity_count': int(len(liq_df)) if liq_df is not None else 0,
            'market_structure': smc.get('market_structure', None),
            'bos_choch_strength': smc.get('bos_choch_strength', None),
        }
        return _to_jsonable(counters)
    except Exception:
        return _to_jsonable({'fvg_count': 0, 'ob_count': 0, 'liquidity_count': 0})


@app.post("/api/backtest/run")
def api_backtest(req: BacktestRequest):
    df = get_ohlcv_extended(req.symbol, req.timeframe, days=req.days)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Sin datos")

    # Preparar señales si vienen por request (adaptarlas al formato esperado por el backtester)
    class _SignalType:
        def __init__(self, value: str):
            self.value = value

    class _SimpleSignal:
        def __init__(self, side: str, entry: float, sl: float, tp: float, ts: Optional[str]):
            self.timestamp = pd.to_datetime(ts) if ts else None
            self.entry_price = float(entry)
            self.stop_loss = float(sl)
            self.take_profit = float(tp)
            self.signal_type = _SignalType(side.upper())

    # Determinar modo solicitado
    mode = (req.mode or ("ml" if req.use_ml else "demo")).lower()
    htf_trend_used: Optional[str] = None

    signals = []
    if req.signals:
        for s in req.signals:
            try:
                signals.append(_SimpleSignal(s.side, s.entry, s.stop_loss, s.take_profit, s.timestamp))
            except Exception:
                continue
    else:
        # Si no se pasan señales, generar señales según modo
        base_step = max(10, int(req.step or 10))
        max_sigs = int(req.max_signals or 50)
        if mode == 'ml':
            integration = get_ml_signal_integration()
            # Desactivar cooldown para backtesting iterativo
            try:
                integration.signal_cooldown_minutes = 0
            except Exception:
                pass
            df_for_ml = df.copy()
            count = 0
            for i in range(base_step, len(df_for_ml), base_step):
                window = df_for_ml.iloc[:i].copy()
                smc = analyze(window, timeframe=req.timeframe)
                pred = integration.generate_ml_signal(window, smc, symbol=req.symbol, timeframe=req.timeframe)
                side_value = None
                if pred is not None:
                    # Umbral de confianza opcional
                    try:
                        conf = getattr(pred, 'ml_confidence', None)
                        if conf is None:
                            conf = getattr(pred, 'ml_probability', None)
                        if conf is not None and req.ml_min_confidence is not None and float(conf) < float(req.ml_min_confidence):
                            # Confianza baja: saltar o fallback a tendencia
                            if not (req.ml_allow_trend_fallback or False):
                                continue
                            else:
                                trend = str(smc.get('market_structure', 'neutral')).lower()
                                if 'bull' in trend:
                                    side_value = 'LONG'
                                elif 'bear' in trend:
                                    side_value = 'SHORT'
                    except Exception:
                        pass

                    # Normalizar el lado a LONG/SHORT (solo si no se decidió por fallback)
                    if side_value is None:
                        try:
                            raw_side = getattr(getattr(pred, 'signal_type', None), 'value', None) or str(getattr(pred, 'signal_type', '')).upper()
                            rs = str(raw_side).upper()
                            if 'BUY' in rs or rs == 'LONG':
                                side_value = 'LONG'
                            elif 'SELL' in rs or rs == 'SHORT':
                                side_value = 'SHORT'
                        except Exception:
                            pass
                else:
                    # Si no hay señal ML (p.ej., por restricciones internas), decidir según flag de fallback
                    if req.ml_allow_trend_fallback:
                        trend = str(smc.get('market_structure', 'neutral')).lower()
                        if 'bull' in trend:
                            side_value = 'LONG'
                        elif 'bear' in trend:
                            side_value = 'SHORT'
                    else:
                        # No permitido fallback → omitir esta iteración
                        continue

                # Si no hay lado claro por ML y el fallback no está permitido, saltar
                if side_value is None and not (req.ml_allow_trend_fallback or False):
                    continue
                if side_value:
                    entry = float(window['close'].iloc[-1])
                    sl, tp = calculate_adaptive_levels(window, entry_price=entry, signal_type=side_value)
                    signals.append(_SimpleSignal(side_value, entry, sl, tp, str(window['timestamp'].iloc[-1])))
                    count += 1
                    if count >= max_sigs:
                        break
        elif mode == 'smc':
            # Generación de señales basada en reglas SMC simples (FVG/OB + tendencia)
            count = 0
            # Calcular sesgo HTF si se solicita
            htf_trend = None
            if req.smc_htf_bias:
                try:
                    htf_tf = req.smc_htf_timeframe or '4h'
                    htf_df = get_ohlcv_extended(req.symbol, htf_tf, days=req.days)
                    if htf_df is not None and not htf_df.empty:
                        htf = analyze(htf_df, timeframe=htf_tf)
                        htf_trend = str(htf.get('market_structure', 'neutral')).lower()
                except Exception:
                    htf_trend = None
            htf_trend_used = htf_trend
            for i in range(base_step, len(df), base_step):
                try:
                    start = max(0, i - 200)
                    window = df.iloc[start:i+1].copy()
                    c = window.iloc[-1]
                    price = float(c['close'])
                    smc = analyze(window, timeframe=req.timeframe)
                    trend = str(smc.get('market_structure', 'neutral')).lower()
                    chosen_side = None
                    # ATR de tolerancia para cercanía a la zona
                    try:
                        hl = window['high'] - window['low']
                        hc = (window['high'] - window['close'].shift()).abs()
                        lc = (window['low'] - window['close'].shift()).abs()
                        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
                        atr = float(tr.rolling(window=14).mean().iloc[-1]) if len(tr) >= 14 else float(tr.mean())
                        tol = atr * 0.25 if atr and atr == atr else price * 0.001  # 0.1% fallback
                    except Exception:
                        tol = price * 0.001

                    # 1) Intentar con FVG
                    fvg_df = smc.get('fvg')
                    if hasattr(fvg_df, 'tail'):
                        try:
                            # Considerar varias FVG recientes
                            recent_fvgs = fvg_df.tail(5)
                            for _, z in recent_fvgs.iterrows():
                                top = float(z.get('Top', z.get('top', z.get('y1', np.nan))))
                                bottom = float(z.get('Bottom', z.get('bottom', z.get('y0', np.nan))))
                                if not (top == top and bottom == bottom):
                                    continue
                                y0, y1 = (min(top, bottom), max(top, bottom))
                                prev_close = float(window['close'].iloc[-2]) if len(window) >= 2 else price
                                inside_now = (y0 - tol) <= price <= (y1 + tol)
                                # Si se exige mitigación, la vela previa debía estar fuera
                                if req.smc_mitigation_only:
                                    prev_outside = (prev_close < (y0 - tol)) or (prev_close > (y1 + tol))
                                    condition = inside_now and prev_outside
                                else:
                                    condition = inside_now
                                if condition:
                                    if 'bull' in trend:
                                        chosen_side = 'LONG'
                                    elif 'bear' in trend:
                                        chosen_side = 'SHORT'
                                    else:
                                        chosen_side = 'LONG' if c['close'] >= c['open'] else 'SHORT'
                                    break
                        except Exception:
                            pass

                    # 2) Si no, intentar OB
                    if chosen_side is None:
                        ob_df = smc.get('orderblocks')
                        if hasattr(ob_df, 'tail'):
                            try:
                                recent_obs = ob_df.tail(5)
                                for _, z in recent_obs.iterrows():
                                    top = float(z.get('Top', z.get('top', z.get('y1', np.nan))))
                                    bottom = float(z.get('Bottom', z.get('bottom', z.get('y0', np.nan))))
                                    if not (top == top and bottom == bottom):
                                        continue
                                    y0, y1 = (min(top, bottom), max(top, bottom))
                                    prev_close = float(window['close'].iloc[-2]) if len(window) >= 2 else price
                                    inside_now = (y0 - tol) <= price <= (y1 + tol)
                                    if req.smc_mitigation_only:
                                        prev_outside = (prev_close < (y0 - tol)) or (prev_close > (y1 + tol))
                                        condition = inside_now and prev_outside
                                    else:
                                        condition = inside_now
                                    if condition:
                                        if 'bull' in trend:
                                            chosen_side = 'LONG'
                                        elif 'bear' in trend:
                                            chosen_side = 'SHORT'
                                        else:
                                            chosen_side = 'LONG' if (price - y0) < (y1 - price) else 'SHORT'
                                        break
                            except Exception:
                                pass

                    # 3) Validaciones de estructura/HTF antes de registrar
                    def _structure_ok(side: Optional[str]) -> bool:
                        if side is None:
                            return False
                        if req.smc_require_structure_confirm:
                            if side == 'LONG' and 'bull' not in trend:
                                return False
                            if side == 'SHORT' and 'bear' not in trend:
                                return False
                        if req.smc_htf_bias and htf_trend:
                            if side == 'LONG' and 'bull' not in htf_trend:
                                return False
                            if side == 'SHORT' and 'bear' not in htf_trend:
                                return False
                        return True

                    # 4) Fallback por tendencia si no hay proximidad a zonas
                    if chosen_side:
                        if _structure_ok(chosen_side):
                            sl, tp = calculate_adaptive_levels(window, entry_price=price, signal_type=chosen_side)
                            signals.append(_SimpleSignal(chosen_side, price, sl, tp, str(c['timestamp'])))
                            count += 1
                            if count >= max_sigs:
                                break
                    else:
                        if 'bull' in trend or 'bear' in trend:
                            fallback_side = 'LONG' if 'bull' in trend else 'SHORT'
                            if _structure_ok(fallback_side):
                                sl, tp = calculate_adaptive_levels(window, entry_price=price, signal_type=fallback_side)
                                signals.append(_SimpleSignal(fallback_side, price, sl, tp, str(c['timestamp'])))
                                count += 1
                                if count >= max_sigs:
                                    break
                except Exception:
                    continue
        else:
            count = 0
            for i in range(len(df) - base_step, base_step, -base_step):
                c = df.iloc[i]
                side = ('LONG' if (count % 2 == 0) else 'SHORT')
                entry = float(c['close'])
                sl, tp = calculate_adaptive_levels(df.iloc[:i+1], entry_price=entry, signal_type=side)
                signals.append(_SimpleSignal(side, entry, sl, tp, str(c['timestamp'])))
                count += 1
                if count >= max_sigs:
                    break

    # Filtros por sesión y horarios
    def _session_of(ts: Any) -> str:
        try:
            hour = pd.to_datetime(ts).hour
            if 8 <= hour < 16:
                return 'london'
            if 13 <= hour < 21:
                return 'newyork'
            return 'asia'
        except Exception:
            return 'asia'

    if req.sessions or req.trading_hours:
        filtered = []
        start_hm = None
        end_hm = None
        if req.trading_hours and 'start' in req.trading_hours and 'end' in req.trading_hours:
            start_hm = req.trading_hours['start']
            end_hm = req.trading_hours['end']
        for s in signals:
            ok = True
            if req.sessions:
                ok = (_session_of(s.timestamp) in set([x.lower() for x in req.sessions]))
            if ok and start_hm and end_hm:
                try:
                    t = pd.to_datetime(s.timestamp).time()
                    sh, sm = [int(x) for x in start_hm.split(':')]
                    eh, em = [int(x) for x in end_hm.split(':')]
                    start_t = pd.Timestamp(0).replace(hour=sh, minute=sm).time()
                    end_t = pd.Timestamp(0).replace(hour=eh, minute=em).time()
                    if start_t <= end_t:
                        ok = (t >= start_t and t <= end_t)
                    else:
                        ok = (t >= start_t or t <= end_t)
                except Exception:
                    pass
            if ok:
                filtered.append(s)
        signals = filtered

    backtester = SMCBacktester(initial_capital=req.initial_capital, risk_per_trade=req.risk_per_trade)
    results = backtester.run_backtest(df, signals, max_trade_duration=req.max_trade_duration)
    report = backtester.generate_report()
    # Aclarar modo en el encabezado del reporte
    try:
        report = report.replace("REPORTE DE BACKTESTING SMC", f"REPORTE DE BACKTESTING {mode.upper()}")
    except Exception:
        pass

    # Añadir bloque de parámetros/flags al reporte
    try:
        rep_step = max(10, int(req.step or 10))
        rep_max_sigs = int(req.max_signals or 50)
        lines = [
            "\n\n## ⚙️ Parámetros & Flags",
            f"- **Modo**: {mode}",
            f"- **Step**: {rep_step}",
            f"- **Max señales**: {rep_max_sigs}",
        ]
        if mode == 'ml':
            lines.append(f"- **ML min conf**: {req.ml_min_confidence if req.ml_min_confidence is not None else 'N/A'}")
            lines.append(f"- **ML fallback tendencia**: {'Sí' if (req.ml_allow_trend_fallback or False) else 'No'}")
        if mode == 'smc':
            lines.extend([
                f"- **Confirmación estructura**: {'Sí' if (req.smc_require_structure_confirm or False) else 'No'}",
                f"- **Sesgo HTF**: {'Sí' if (req.smc_htf_bias or False) else 'No'}",
                f"- **HTF timeframe**: {req.smc_htf_timeframe or 'N/A'}",
                f"- **Sesgo HTF detectado**: {htf_trend_used or 'N/A'}",
                f"- **Solo mitigación**: {'Sí' if (req.smc_mitigation_only or False) else 'No'}",
                f"- **Tolerancia zona**: ±0.25×ATR",
            ])
        report = report + "\n".join(lines)
    except Exception:
        pass

    # Serializar dataclass BacktestResults y trades
    results_dict = _to_jsonable(results)

    # Construir equity curve (mismo criterio que drawdown interno)
    equity_curve = []
    equity_points = []
    try:
        current_capital = req.initial_capital
        equity_curve.append(current_capital)
        for t in results.trades:
            risk_amount = current_capital * (req.risk_per_trade / 100.0)
            risk_points = abs(t.entry_price - t.stop_loss) if (t.entry_price is not None and t.stop_loss is not None) else 0.0
            if risk_points and t.pnl_points is not None:
                position_size = risk_amount / risk_points
                trade_pnl = t.pnl_points * position_size
                current_capital += trade_pnl
            equity_curve.append(current_capital)
            equity_points.append({
                'time': getattr(t, 'exit_time', None),
                'capital': current_capital
            })
    except Exception:
        pass

    return {
        "results": results_dict,
        "report": report,
        "equity_curve": equity_curve,
        "equity_points": _to_jsonable(equity_points),
        "mode": mode,
    }


class MTFRequest(BaseModel):
    symbol: str = "BTC/USDT"
    days: int = 30


@app.post("/api/mtf/overview")
def api_mtf_overview(req: MTFRequest):
    analyzer = create_multi_timeframe_analyzer()
    analyses = analyzer.analyze_all_timeframes(req.symbol, req.days)
    # Convertir DataFrames dentro de analyses
    jsonable = {}
    for tf, data in analyses.items():
        jsonable[tf] = {
            'data': _to_jsonable(data.get('data')),
            'analysis': _to_jsonable(data.get('analysis')),
        }
    return jsonable


@app.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    await websocket.accept()
    try:
        import asyncio
        from urllib.parse import parse_qs, urlparse

        # Extraer query params del path
        query = urlparse(str(websocket.url)).query
        params = {k: v[0] for k, v in parse_qs(query).items()}
        symbol = params.get('symbol', 'BTC/USDT')
        timeframe = params.get('timeframe', '15m')
        interval_sec = max(3, int(params.get('interval', '5')))

        while True:
            try:
                df = get_ohlcv(symbol, timeframe, limit=200)
                payload = df.tail(1).to_dict(orient='records') if df is not None and not df.empty else []
                await websocket.send_json({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'last': payload[0] if payload else None,
                })
            except Exception as e:
                await websocket.send_json({'error': str(e)})
            await asyncio.sleep(interval_sec)
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


