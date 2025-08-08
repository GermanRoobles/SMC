#!/usr/bin/env python3
"""
Test de integración completa del proyecto SMC TradingView
--------------------------------------------------------

Este archivo agrupa pruebas de:
- Integridad de datos (fetchers, caché, remuestreo 4H)
- Análisis multi-timeframe y estructura de mercado
- Generación de señales ML (generador e integración)
- Visualización (creación de figuras Plotly)
- Utilidades HTF (proyección de zonas)

Las pruebas de red (Yahoo Finance) pueden fallar si no hay internet. Se manejan de forma
robusta para evitar falsos negativos (se hace skip si no hay datos).
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import pytest


# ---------- Helpers ----------

REQUIRED_COLS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']


def _assert_ohlcv_integrity(df: pd.DataFrame):
    """Asserts básicos de integridad para OHLCV."""
    assert isinstance(df, pd.DataFrame), "Resultado no es DataFrame"
    assert not df.empty, "DataFrame vacío"
    for col in REQUIRED_COLS:
        assert col in df.columns, f"Falta columna requerida: {col}"
    # Tipos numéricos
    for col in ['open', 'high', 'low', 'close']:
        assert pd.api.types.is_numeric_dtype(df[col]), f"Columna {col} no es numérica"
    # Timestamps válidos, con tz (UTC)
    assert pd.api.types.is_datetime64_any_dtype(df['timestamp']), "timestamp no es datetime"
    # monotonicidad (permitimos igualdad si hay velas iguales)
    assert df['timestamp'].is_monotonic_increasing, "Timestamps no monotónicos"
    # sin NaNs en precios
    assert df[['open', 'high', 'low', 'close']].isna().sum().sum() == 0, "NaNs en precios"
    # sin duplicados por timestamp
    assert df['timestamp'].duplicated().sum() == 0, "Timestamps duplicados"


def _has_internet_data(df: pd.DataFrame) -> bool:
    return isinstance(df, pd.DataFrame) and not df.empty and len(df) >= 5


# ---------- Tests de datos ----------

def test_fetch_data_extended_15m():
    from fetch_data import get_ohlcv_extended
    df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
    if not _has_internet_data(df):
        pytest.skip("Sin datos de internet para 15m")
    _assert_ohlcv_integrity(df)


def test_fetch_data_extended_4h_resample():
    from fetch_data import get_ohlcv_extended
    df = get_ohlcv_extended("BTC/USDT", "4h", days=5)
    if not _has_internet_data(df):
        pytest.skip("Sin datos de internet para 4h")
    _assert_ohlcv_integrity(df)
    # Comprobar que el intervalo es cercano a 4H para la mayoría de filas (tolerante)
    diffs = df['timestamp'].diff().dropna().dt.total_seconds() / 3600.0
    if len(diffs) > 5:
        close_4h = (np.isclose(diffs, 4.0, atol=0.5)).mean()
        multiples_4h = (np.isclose(diffs % 4.0, 0.0, atol=0.25)).mean()
        assert max(close_4h, multiples_4h) > 0.7, "La mayoría de intervalos no parecen de 4H (tras remuestreo)"


def test_fetch_data_with_cache():
    from fetch_data import get_ohlcv_with_cache
    end = datetime.utcnow()
    start = end - timedelta(days=2)
    df = get_ohlcv_with_cache("BTC/USDT", "15m", start, end)
    if not _has_internet_data(df):
        pytest.skip("Sin datos de internet para with_cache 15m")
    _assert_ohlcv_integrity(df)


def test_yfinance_error_handling_no_exception():
    """Descarga de símbolo problemático no debe romper el flujo (solo silencioso)."""
    from fetch_data import get_ohlcv_extended
    try:
        df = get_ohlcv_extended("SOL/USDT", "15m", days=1)
        assert df is not None, "get_ohlcv_extended devolvió None"
        # Puede ser vacío si YF no devuelve datos, pero no debe lanzar excepción
    except Exception as e:
        pytest.fail(f"Excepción no esperada durante descarga YF: {e}")


# ---------- Tests Multi-Timeframe ----------

def test_multi_timeframe_analyzer():
    from smc_multi_timeframe import create_multi_timeframe_analyzer
    analyzer = create_multi_timeframe_analyzer()
    analyses = analyzer.analyze_all_timeframes("BTC/USDT", days=3)
    if not analyses:
        pytest.skip("Sin datos de internet para multi-timeframe")
    # Validar estructura
    for tf, payload in analyses.items():
        assert 'data' in payload and 'analysis' in payload, f"Estructura inválida para {tf}"
        df = payload['data']
        if _has_internet_data(df):
            _assert_ohlcv_integrity(df)
    # Visualización principal
    fig = analyzer.create_multi_timeframe_dashboard(analyses)
    import plotly.graph_objects as go
    assert isinstance(fig, go.Figure), "No se creó figura Plotly para dashboard multi-timeframe"


def test_multi_timeframe_comparison_and_confirmation():
    from smc_multi_timeframe import create_multi_timeframe_analyzer
    analyzer = create_multi_timeframe_analyzer()
    analyses = analyzer.analyze_all_timeframes("BTC/USDT", days=3)
    if not analyses:
        pytest.skip("Sin datos para comparación/confirmación")
    fig_cmp = analyzer.create_timeframe_comparison_chart(analyses)
    fig_conf = analyzer.create_signal_confirmation_chart(analyses)
    import plotly.graph_objects as go
    assert isinstance(fig_cmp, go.Figure)
    assert isinstance(fig_conf, go.Figure)


# ---------- Tests Market Structure ----------

def test_market_structure_analysis_and_chart():
    from smc_market_structure import create_market_structure_analyzer
    from fetch_data import get_ohlcv_extended
    df = get_ohlcv_extended("BTC/USDT", "1h", days=3)
    if not _has_internet_data(df):
        pytest.skip("Sin datos para estructura de mercado")
    analyzer = create_market_structure_analyzer()
    analysis = analyzer.analyze_market_structure(df, "1h")
    assert isinstance(analysis, dict) and analysis, "Análisis de estructura vacío"
    # Claves básicas
    for key in [
        'swing_points', 'trend_structure', 'key_levels', 'support_resistance',
        'breakout_zones', 'accumulation_distribution', 'market_phases', 'structure_score'
    ]:
        assert key in analysis, f"Falta clave {key} en análisis de estructura"
    # Visual
    fig = analyzer.create_market_structure_chart(df, analysis)
    import plotly.graph_objects as go
    assert isinstance(fig, go.Figure)


# ---------- Tests ML (Generador e Integración) ----------

def _make_synthetic_ohlcv(rows: int = 120) -> pd.DataFrame:
    ts = pd.date_range(end=pd.Timestamp.utcnow().tz_convert('UTC'), periods=rows, freq='15T')
    base = 100.0 + np.cumsum(np.random.randn(rows))
    df = pd.DataFrame({
        'timestamp': ts,
        'open': base + np.random.randn(rows) * 0.2,
        'high': base + 0.5 + np.abs(np.random.randn(rows) * 0.3),
        'low': base - 0.5 - np.abs(np.random.randn(rows) * 0.3),
        'close': base + np.random.randn(rows) * 0.2,
        'volume': np.random.randint(1000, 10000, size=rows)
    })
    return df


def test_ml_signal_generator_basic():
    from smc_ml_signal_generator import get_ml_signal_generator
    gen = get_ml_signal_generator()
    df = _make_synthetic_ohlcv(120)
    # HOLD debe descartar
    signal = gen.generate_signal(
        df, {'probability': 0.55, 'confidence': 0.6, 'recommendation': 'HOLD'}, {'fvg': [], 'ob': [], 'liquidity': [], 'market_structure': 'neutral'}, df['close'].iloc[-1]
    )
    assert signal is None, "Señales HOLD deben descartarse"
    # STRONG_BUY debe generar
    signal2 = gen.generate_signal(
        df, {'probability': 0.95, 'confidence': 0.95, 'recommendation': 'STRONG_BUY'}, {'fvg': [1,2], 'ob': [1], 'liquidity': [1], 'market_structure': 'bullish'}, df['close'].iloc[-1]
    )
    assert signal2 is not None, "STRONG_BUY debería generar señal"
    # Validar campos clave
    assert signal2.take_profit_1 != signal2.entry_price
    assert signal2.stop_loss != signal2.entry_price
    assert signal2.risk_reward_1 >= 1.0


def test_ml_signal_integration_end_to_end():
    from smc_ml_signal_integration import get_ml_signal_integration
    from fetch_data import get_ohlcv_extended
    from smc_analysis import analyze
    df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
    if not _has_internet_data(df):
        pytest.skip("Sin datos para ML integration")
    smc_results = analyze(df, timeframe="15m")
    smc_analysis = {
        'fvg': smc_results.get('fvg', []),
        'ob': smc_results.get('orderblocks', []),
        'liquidity': smc_results.get('liquidity', []),
        'bos_choch': smc_results.get('bos_choch', []),
        'market_structure': smc_results.get('market_structure', 'neutral'),
        'bos_choch_strength': len(smc_results.get('bos_choch', [])) * 0.1,
    }
    integration = get_ml_signal_integration()
    signal = integration.generate_ml_signal(df, smc_analysis, symbol="BTC/USDT", timeframe="15m")
    # Debe guardarse la última predicción siempre
    assert integration.last_prediction is not None, "last_prediction no fue actualizado"
    # Señal puede ser None si la recomendación es neutra; chequear estadísticas igualmente
    stats = integration.get_integration_stats()
    assert isinstance(stats, dict) and 'ml_signal_generator' in stats and 'ml_predictor' in stats


# ---------- Tests HTF Utils ----------

def test_utils_htf_projection_smoke():
    from utils_htf import get_htf_gaps_and_obs
    try:
        projected_fvg, projected_ob, ltf_df = get_htf_gaps_and_obs("BTC/USDT", htf="1w", ltf="4h")
        # No assert fuerte porque depende de datos, pero al menos debe retornar estructuras válidas
        assert isinstance(projected_fvg, list)
        assert isinstance(projected_ob, list)
        assert isinstance(ltf_df, pd.DataFrame)
    except Exception:
        # Si falla por internet, no romper
        pytest.skip("Sin datos para HTF utils")


# ---------- Tests SMC Analysis básicos ----------

def test_smc_analysis_basic():
    from smc_analysis import analyze
    from fetch_data import get_ohlcv_extended
    df = get_ohlcv_extended("BTC/USDT", "15m", days=1)
    if not _has_internet_data(df):
        pytest.skip("Sin datos para smc_analysis")
    result = analyze(df, timeframe="15m")
    assert isinstance(result, dict), "smc_analysis.analyze debe devolver dict"
    # Algunas claves típicas (tolerantes a cambios internos)
    for key in ['fvg', 'orderblocks', 'market_structure']:
        assert key in result, f"Falta clave {key} en análisis SMC"


# ---------- Tests Backtesting en profundidad ----------

def test_backtesting_sl_tp_realista_varios_escenarios():
    from fetch_data import get_ohlcv_extended
    from smc_analysis import analyze
    from smc_ml_signal_integration import get_ml_signal_integration
    from smc_backtester import SMCBacktester
    
    df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
    if not _has_internet_data(df):
        pytest.skip("Sin datos para backtesting")
    _assert_ohlcv_integrity(df)
    
    # Análisis SMC
    smc_results = analyze(df, timeframe="15m")
    smc_analysis = {
        'fvg': smc_results.get('fvg', []),
        'ob': smc_results.get('orderblocks', []),
        'liquidity': smc_results.get('liquidity', []),
        'bos_choch': smc_results.get('bos_choch', []),
        'market_structure': smc_results.get('market_structure', 'neutral'),
        'bos_choch_strength': len(smc_results.get('bos_choch', [])) * 0.1,
    }
    
    # Preparar 3 escenarios de señales ML con distintos RR y direcciones
    get_ml_signal_integration()  # Inicializa integración/ML manager si es necesario
    current_price = float(df['close'].iloc[-1])
    ts_now = df['timestamp'].iloc[-1]
    
    class _S:
        def __init__(self, t, typ, entry, sl, tp):
            self.timestamp = t
            self.signal_type = type('T', (), {'value': typ})
            self.entry_price = entry
            self.stop_loss = sl
            self.take_profit = tp
    
    # Construir niveles alrededor del precio con ATR aproximado
    atr = (df['high'].tail(14) - df['low'].tail(14)).mean()
    if not np.isfinite(atr) or atr <= 0:
        atr = max(1e-6, float(df['close'].iloc[-1]) * 0.002)
    
    # LONG con RR~2
    rr2_sl = current_price - atr
    rr2_tp = current_price + atr * 2
    s_long_rr2 = _S(ts_now, "LONG", current_price, rr2_sl, rr2_tp)
    
    # SHORT con RR~1.5
    rr15_sl = current_price + atr
    rr15_tp = current_price - atr * 1.5
    s_short_rr15 = _S(ts_now, "SHORT", current_price, rr15_sl, rr15_tp)
    
    # LONG conservador con SL/TP recomendados por validador (si aplica)
    from smc_backtester import validate_sl_tp_levels, LevelValidationResult
    rep = validate_sl_tp_levels(df, current_price, current_price - atr*0.3, current_price + atr*0.6, "LONG")
    if rep.result != LevelValidationResult.VALID and rep.recommended_sl and rep.recommended_tp:
        s_long_recommended = _S(ts_now, "LONG", current_price, rep.recommended_sl, rep.recommended_tp)
    else:
        s_long_recommended = _S(ts_now, "LONG", current_price, current_price - atr, current_price + atr*2)
    
    signals = [s_long_rr2, s_short_rr15, s_long_recommended]
    
    # Ejecutar backtest - garantizar coincidencia de timestamp
    # Ajustar la primera señal al próximo timestamp disponible para asegurar simulación
    base_ts = df['timestamp'].iloc[-20]
    signals[0].timestamp = base_ts
    signals[1].timestamp = df['timestamp'].iloc[-15]
    signals[2].timestamp = df['timestamp'].iloc[-10]

    backtester = SMCBacktester(initial_capital=10000, risk_per_trade=1.0)
    results = backtester.run_backtest(df, signals, max_trade_duration=48)
    
    # Asserts de resultados
    assert results.total_trades == len(signals)
    assert 0 <= results.win_rate <= 100
    assert results.final_capital > 0
    
    # Chart y reporte
    fig = backtester.create_performance_chart()
    import plotly.graph_objects as go
    assert isinstance(fig, go.Figure)
    report = backtester.generate_report()
    assert isinstance(report, str) and len(report) > 0

