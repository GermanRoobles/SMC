#!/usr/bin/env python3
"""
Análisis detallado de inconsistencias en el backtester
"""

import pandas as pd
from fetch_data import get_ohlcv
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import SMCBacktester

def analyze_backtester_issues():
    """Analizar en detalle las inconsistencias detectadas"""

    print("🔍 ANÁLISIS DETALLADO DE INCONSISTENCIAS DEL BACKTESTER")
    print("="*80)

    # 1. Obtener datos
    symbol = "BTCUSDT"
    timeframe = "1h"
    limit = 100

    df = get_ohlcv(symbol, timeframe, limit=limit)
    print(f"\n📊 DATOS OBTENIDOS:")
    print(f"   • Total velas: {len(df)}")
    print(f"   • Período: {df['timestamp'].min()} a {df['timestamp'].max()}")
    print(f"   • Primeras 5 timestamps:")
    for i in range(5):
        print(f"     [{i}] {df['timestamp'].iloc[i]}")

    # 2. Crear señales específicas para análisis
    print(f"\n⚡ CREANDO SEÑALES PARA ANÁLISIS:")
    signals = []

    # Señal 1: índice 20
    entry_price = df['close'].iloc[20]
    timestamp_20 = df['timestamp'].iloc[20]
    signals.append(TradeSignal(
        timestamp=timestamp_20,
        symbol=symbol,
        timeframe=timeframe,
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * 0.985,
        take_profit=entry_price * 1.045,
        risk_reward=3.0,
        confidence=0.85,
        setup_components={'fvg': True, 'order_block': True},
        confirmation_type=ConfirmationType.ENGULFING
    ))

    # Señal 2: índice 40
    entry_price = df['close'].iloc[40]
    timestamp_40 = df['timestamp'].iloc[40]
    signals.append(TradeSignal(
        timestamp=timestamp_40,
        symbol=symbol,
        timeframe=timeframe,
        signal_type=SignalType.SHORT,
        entry_price=entry_price,
        stop_loss=entry_price * 1.02,
        take_profit=entry_price * 0.94,
        risk_reward=3.0,
        confidence=0.75,
        setup_components={'fvg': True, 'liquidity': True},
        confirmation_type=ConfirmationType.REJECTION_WICK
    ))

    # Señal 3: índice 60
    entry_price = df['close'].iloc[60]
    timestamp_60 = df['timestamp'].iloc[60]
    signals.append(TradeSignal(
        timestamp=timestamp_60,
        symbol=symbol,
        timeframe=timeframe,
        signal_type=SignalType.SHORT,
        entry_price=entry_price,
        stop_loss=entry_price * 1.015,
        take_profit=entry_price * 0.97,
        risk_reward=2.0,
        confidence=0.80,
        setup_components={'order_block': True, 'bos': True},
        confirmation_type=ConfirmationType.HAMMER
    ))

    print(f"   • Señal 1: {timestamp_20} (índice 20)")
    print(f"   • Señal 2: {timestamp_40} (índice 40)")
    print(f"   • Señal 3: {timestamp_60} (índice 60)")

    # 3. Análisis de diferencias de tiempo
    print(f"\n⏰ ANÁLISIS DE DIFERENCIAS DE TIEMPO:")
    diff_1_2 = pd.to_datetime(timestamp_40) - pd.to_datetime(timestamp_20)
    diff_2_3 = pd.to_datetime(timestamp_60) - pd.to_datetime(timestamp_40)

    print(f"   • Diferencia señal 1-2: {diff_1_2} ({diff_1_2.total_seconds()/3600:.1f} horas)")
    print(f"   • Diferencia señal 2-3: {diff_2_3} ({diff_2_3.total_seconds()/3600:.1f} horas)")

    # 4. Simular manualmente el primer trade para ver qué pasa
    print(f"\n🔍 SIMULACIÓN MANUAL DEL PRIMER TRADE:")

    # Encontrar índice de entrada para señal 1
    entry_idx = None
    for idx, timestamp in enumerate(df['timestamp']):
        if pd.to_datetime(timestamp) >= pd.to_datetime(timestamp_20):
            entry_idx = idx
            break

    print(f"   • Timestamp señal: {timestamp_20}")
    print(f"   • Índice de entrada encontrado: {entry_idx}")
    print(f"   • Timestamp entrada real: {df['timestamp'].iloc[entry_idx]}")

    # Ver qué pasa con la duración máxima
    max_duration = 48  # horas
    max_duration_candles = min(max_duration * 1, len(df) - entry_idx - 1)  # 1 vela por hora para 1h
    print(f"   • Duración máxima: {max_duration} horas")
    print(f"   • Velas máximas disponibles: {max_duration_candles}")

    # Simular salida forzada
    if entry_idx is not None:
        final_idx = min(entry_idx + max_duration_candles, len(df) - 1)
        if final_idx <= entry_idx:
            final_idx = min(entry_idx + 1, len(df) - 1)

        entry_time = df['timestamp'].iloc[entry_idx]
        exit_time = df['timestamp'].iloc[final_idx]

        print(f"   • Índice final: {final_idx}")
        print(f"   • Timestamp salida: {exit_time}")

        # Calcular duración
        duration = pd.to_datetime(exit_time) - pd.to_datetime(entry_time)
        duration_hours = duration.total_seconds() / 3600

        print(f"   • Duración calculada: {duration_hours:.1f} horas")
        print(f"   • Diferencia de índices: {final_idx - entry_idx} velas")

    # 5. Ejecutar backtesting oficial
    print(f"\n🚀 EJECUTANDO BACKTESTING OFICIAL:")

    backtester = SMCBacktester(
        initial_capital=10000,
        risk_per_trade=1.0
    )

    results = backtester.run_backtest(df, signals, max_trade_duration=48)

    print(f"\n📊 RESULTADOS DETALLADOS:")
    print(f"   • Total trades: {results.total_trades}")

    for i, trade in enumerate(results.trades):
        print(f"\n   Trade {i+1}:")
        print(f"     • Entry time: {trade.entry_time}")
        print(f"     • Exit time: {trade.exit_time}")
        print(f"     • Duration: {trade.duration_hours:.1f}h")
        print(f"     • Entry price: ${trade.entry_price:.2f}")
        print(f"     • Exit price: ${trade.exit_price:.2f}")
        print(f"     • Result: {trade.result}")

        # Análisis específico
        if trade.entry_time and trade.exit_time:
            entry_dt = pd.to_datetime(trade.entry_time)
            exit_dt = pd.to_datetime(trade.exit_time)
            calculated_duration = (exit_dt - entry_dt).total_seconds() / 3600
            print(f"     • Duración recalculada: {calculated_duration:.1f}h")

    # 6. Diagnóstico final
    print(f"\n⚠️ DIAGNÓSTICO DE INCONSISTENCIAS:")

    # Verificar si todas las salidas tienen el mismo precio
    exit_prices = [trade.exit_price for trade in results.trades]
    if len(set(exit_prices)) == 1:
        print(f"   🚨 PROBLEMA: Todos los trades tienen el mismo precio de salida: ${exit_prices[0]:.2f}")
        print(f"   📋 Esto indica que todos los trades se están cerrando en el mismo timestamp")

    # Verificar patrón de duraciones
    durations = [trade.duration_hours for trade in results.trades]
    if len(durations) >= 2:
        diff_pattern = []
        for i in range(1, len(durations)):
            diff = durations[i-1] - durations[i]
            diff_pattern.append(diff)

        if len(set(diff_pattern)) == 1:
            print(f"   🚨 PROBLEMA: Patrón de duración demasiado regular")
            print(f"   📋 Diferencias: {diff_pattern}")
            print(f"   📋 Esto sugiere un error en el cálculo o simulación")

if __name__ == "__main__":
    analyze_backtester_issues()
