#!/usr/bin/env python3
"""
Test del Backtester SMC
======================

Script p            # Crear señal SHORT
            signal = TradeSignal(
                timestamp=timestamp,
                symbol="EURUSD",
                timeframe="15m",
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=entry_price + 2.0,  # SL 2 puntos
                take_profit=entry_price - 4.0,  # TP 4 puntos (RR 1:2)
                risk_reward=2.0,
                confidence=0.7,
                setup_components={"test": True},
                confirmation_type=ConfirmationType.REJECTION_WICK
            ) el funcionamiento del sistema de backtesting SMC.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from smc_backtester import SMCBacktester, run_backtest_analysis
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType

def create_test_data():
    """Crear datos de prueba para backtesting"""
    # Crear 500 velas de 15 minutos
    dates = pd.date_range(start='2025-01-01', periods=500, freq='15min')

    # Crear datos OHLC simulados con tendencia
    np.random.seed(42)
    base_price = 100.0

    data = []
    current_price = base_price

    for i in range(500):
        # Simular movimiento de precio con tendencia
        change = np.random.normal(0, 0.5)
        if i > 250:  # Tendencia alcista en la segunda mitad
            change += 0.1

        current_price += change

        # Crear vela OHLC
        open_price = current_price
        high_price = open_price + abs(np.random.normal(0, 0.3))
        low_price = open_price - abs(np.random.normal(0, 0.3))
        close_price = open_price + np.random.normal(0, 0.2)

        data.append({
            'open': open_price,
            'high': max(open_price, high_price, close_price),
            'low': min(open_price, low_price, close_price),
            'close': close_price,
            'volume': np.random.randint(1000, 5000)
        })

    df = pd.DataFrame(data, index=dates)
    return df

def create_test_signals(df):
    """Crear señales de prueba para el backtesting"""
    signals = []

    # Generar algunas señales LONG
    for i in range(50, len(df), 50):  # Una señal cada 50 velas
        if i + 10 < len(df):  # Asegurar que hay espacio
            timestamp = df.index[i]
            entry_price = df.iloc[i]['close']

            # Crear señal LONG
            signal = TradeSignal(
                timestamp=timestamp,
                symbol="EURUSD",
                timeframe="15m",
                signal_type=SignalType.LONG,
                entry_price=entry_price,
                stop_loss=entry_price - 2.0,  # SL 2 puntos
                take_profit=entry_price + 4.0,  # TP 4 puntos (RR 1:2)
                risk_reward=2.0,
                confidence=0.8,
                setup_components={"test": True},
                confirmation_type=ConfirmationType.ENGULFING
            )
            signals.append(signal)

    # Generar algunas señales SHORT
    for i in range(75, len(df), 60):  # Una señal cada 60 velas
        if i + 10 < len(df):
            timestamp = df.index[i]
            entry_price = df.iloc[i]['close']

            # Crear señal SHORT
            signal = TradeSignal(
                timestamp=timestamp,
                symbol="EURUSD",
                timeframe="15m",
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=entry_price + 2.0,  # SL 2 puntos
                take_profit=entry_price - 4.0,  # TP 4 puntos (RR 1:2)
                risk_reward=2.0,
                confidence=0.7,
                setup_components={"test": True},
                confirmation_type=ConfirmationType.REJECTION_WICK
            )
            signals.append(signal)

    return signals

def test_backtester():
    """Probar el backtester con datos y señales de prueba"""
    print("🧪 === TEST DEL BACKTESTER SMC ===")
    print()

    # Crear datos de prueba
    print("📊 Creando datos de prueba...")
    df = create_test_data()
    print(f"   ✅ Creados {len(df)} puntos de datos")

    # Crear señales de prueba
    print("🎯 Creando señales de prueba...")
    signals = create_test_signals(df)
    print(f"   ✅ Creadas {len(signals)} señales de trading")

    # Probar backtester directo
    print("\n🔍 Probando SMCBacktester directo...")
    backtester = SMCBacktester(initial_capital=10000, risk_per_trade=2.0)
    results = backtester.run_backtest(df, signals)

    print(f"   📈 Total trades ejecutados: {results.total_trades}")
    print(f"   ✅ Trades ganadores: {results.winning_trades}")
    print(f"   ❌ Trades perdedores: {results.losing_trades}")
    print(f"   📊 Win rate: {results.win_rate:.1f}%")
    print(f"   💰 PnL total: {results.total_pnl:.2f} puntos")
    print(f"   📉 Drawdown máximo: {results.max_drawdown_percent:.1f}%")

    # Probar función de análisis integrada
    print("\n🔧 Probando función de análisis integrada...")
    backtest_analysis = run_backtest_analysis(df, signals, 10000, 2.0)

    if backtest_analysis['success']:
        print("   ✅ Análisis de backtesting exitoso")
        print(f"   📊 Trades: {backtest_analysis['results'].total_trades}")
        print(f"   💹 Win Rate: {backtest_analysis['results'].win_rate:.1f}%")
    else:
        print("   ❌ Error en análisis de backtesting")
        print(f"   📝 Reporte: {backtest_analysis['report']}")

    # Generar reporte
    print("\n📋 Generando reporte detallado...")
    report = backtester.generate_report()
    print(report)

    return results, backtest_analysis

if __name__ == "__main__":
    try:
        results, analysis = test_backtester()
        print("\n🎉 Test completado exitosamente!")

    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
