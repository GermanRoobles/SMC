#!/usr/bin/env python3
"""
Análisis detallado del SL/TP en el backtester
"""

import pandas as pd
from fetch_data import get_ohlcv
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import SMCBacktester

def analyze_sl_tp_execution():
    """Analizar por qué no se ejecutan SL/TP"""

    print("🔍 ANÁLISIS DE EJECUCIÓN SL/TP")
    print("="*50)

    # Obtener datos
    df = get_ohlcv("BTCUSDT", "1h", limit=100)

    # Crear una señal específica para análisis
    entry_idx = 20
    entry_price = df['close'].iloc[entry_idx]

    # Crear señal LONG con SL/TP claros
    signal = TradeSignal(
        timestamp=df['timestamp'].iloc[entry_idx],
        symbol="BTCUSDT",
        timeframe="1h",
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * 0.98,   # SL 2% abajo
        take_profit=entry_price * 1.04, # TP 4% arriba
        risk_reward=2.0,
        confidence=0.85,
        setup_components={'fvg': True},
        confirmation_type=ConfirmationType.ENGULFING
    )

    print(f"📊 SEÑAL DE ANÁLISIS:")
    print(f"   • Entry: ${entry_price:.2f}")
    print(f"   • Stop Loss: ${signal.stop_loss:.2f} ({((signal.stop_loss/entry_price-1)*100):.1f}%)")
    print(f"   • Take Profit: ${signal.take_profit:.2f} ({((signal.take_profit/entry_price-1)*100):.1f}%)")
    print(f"   • Timestamp: {signal.timestamp}")

    # Analizar las próximas velas manualmente
    print(f"\n📈 ANÁLISIS DE VELAS SIGUIENTES:")
    print(f"   Idx | Timestamp           | Open      | High      | Low       | Close     | SL Hit? | TP Hit?")
    print(f"   ----+---------------------+-----------+-----------+-----------+-----------+---------+---------")

    for i in range(entry_idx, min(entry_idx + 20, len(df))):
        candle = df.iloc[i]
        timestamp = candle['timestamp']
        open_price = candle['open']
        high_price = candle['high']
        low_price = candle['low']
        close_price = candle['close']

        # Para LONG: SL se ejecuta si low <= stop_loss, TP se ejecuta si high >= take_profit
        sl_hit = low_price <= signal.stop_loss
        tp_hit = high_price >= signal.take_profit

        status = ""
        if sl_hit:
            status += "SL! "
        if tp_hit:
            status += "TP! "

        print(f"   {i:3d} | {timestamp} | {open_price:9.2f} | {high_price:9.2f} | {low_price:9.2f} | {close_price:9.2f} | {str(sl_hit):7s} | {str(tp_hit):7s} {status}")

        # Si alguno se ejecuta, debería parar aquí
        if sl_hit or tp_hit:
            print(f"   >>> TRADE DEBERÍA CERRARSE EN ÍNDICE {i}")
            break

    print(f"\n🚀 EJECUTANDO BACKTESTING OFICIAL:")

    backtester = SMCBacktester(initial_capital=10000, risk_per_trade=1.0)
    results = backtester.run_backtest(df, [signal], max_trade_duration=48)

    trade = results.trades[0]
    print(f"   • Entry time: {trade.entry_time}")
    print(f"   • Exit time: {trade.exit_time}")
    print(f"   • Entry price: ${trade.entry_price:.2f}")
    print(f"   • Exit price: ${trade.exit_price:.2f}")
    print(f"   • Duration: {trade.duration_hours:.1f}h")
    print(f"   • Result: {trade.result}")

    # Encontrar el índice real de salida
    exit_idx = None
    for idx, timestamp in enumerate(df['timestamp']):
        if str(timestamp) == str(trade.exit_time):
            exit_idx = idx
            break

    if exit_idx:
        print(f"   • Índice de salida: {exit_idx}")
        print(f"   • Diferencia de índices: {exit_idx - entry_idx}")

        # Verificar si era correcto
        if exit_idx == len(df) - 1:
            print(f"   🚨 PROBLEMA: Salida forzada en último índice disponible")
        else:
            print(f"   ✅ Salida normal en índice {exit_idx}")

if __name__ == "__main__":
    analyze_sl_tp_execution()
