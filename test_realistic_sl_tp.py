#!/usr/bin/env python3
"""
Test del backtester con niveles de SL/TP realistas
"""

import pandas as pd
from fetch_data import get_ohlcv
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import SMCBacktester

def test_realistic_sl_tp():
    """Test con niveles realistas de SL/TP"""

    print("🎯 TEST CON NIVELES REALISTAS DE SL/TP")
    print("="*60)

    # Obtener datos
    df = get_ohlcv("BTCUSDT", "1h", limit=100)

    # Analizar rango de precios
    price_min = df['low'].min()
    price_max = df['high'].max()
    price_range = price_max - price_min

    print(f"📊 RANGO DE PRECIOS:")
    print(f"   • Mínimo: ${price_min:.2f}")
    print(f"   • Máximo: ${price_max:.2f}")
    print(f"   • Rango: ${price_range:.2f} ({(price_range/price_min)*100:.2f}%)")

    # Crear señales con niveles realistas
    signals = []

    # Señal 1: LONG con SL/TP dentro del rango
    entry_price = df['close'].iloc[20]
    signals.append(TradeSignal(
        timestamp=df['timestamp'].iloc[20],
        symbol="BTCUSDT",
        timeframe="1h",
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * 0.995,   # SL 0.5% abajo
        take_profit=entry_price * 1.005, # TP 0.5% arriba
        risk_reward=1.0,
        confidence=0.85,
        setup_components={'fvg': True},
        confirmation_type=ConfirmationType.ENGULFING
    ))

    # Señal 2: SHORT con SL/TP dentro del rango
    entry_price = df['close'].iloc[40]
    signals.append(TradeSignal(
        timestamp=df['timestamp'].iloc[40],
        symbol="BTCUSDT",
        timeframe="1h",
        signal_type=SignalType.SHORT,
        entry_price=entry_price,
        stop_loss=entry_price * 1.005,   # SL 0.5% arriba
        take_profit=entry_price * 0.995, # TP 0.5% abajo
        risk_reward=1.0,
        confidence=0.75,
        setup_components={'order_block': True},
        confirmation_type=ConfirmationType.REJECTION_WICK
    ))

    # Señal 3: LONG con SL/TP más amplios pero realistas
    entry_price = df['close'].iloc[60]
    signals.append(TradeSignal(
        timestamp=df['timestamp'].iloc[60],
        symbol="BTCUSDT",
        timeframe="1h",
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * 0.992,   # SL 0.8% abajo
        take_profit=entry_price * 1.008, # TP 0.8% arriba
        risk_reward=1.0,
        confidence=0.80,
        setup_components={'liquidity': True},
        confirmation_type=ConfirmationType.HAMMER
    ))

    print(f"\n⚡ SEÑALES CREADAS CON NIVELES REALISTAS:")
    for i, signal in enumerate(signals):
        sl_pct = ((signal.stop_loss/signal.entry_price - 1) * 100)
        tp_pct = ((signal.take_profit/signal.entry_price - 1) * 100)
        print(f"   {i+1}. {signal.signal_type.value} en ${signal.entry_price:.2f}")
        print(f"      SL: ${signal.stop_loss:.2f} ({sl_pct:+.1f}%)")
        print(f"      TP: ${signal.take_profit:.2f} ({tp_pct:+.1f}%)")

    # Ejecutar backtesting
    print(f"\n🚀 EJECUTANDO BACKTESTING:")

    backtester = SMCBacktester(initial_capital=10000, risk_per_trade=1.0)
    results = backtester.run_backtest(df, signals, max_trade_duration=48)

    print(f"\n📊 RESULTADOS:")
    print(f"   • Total trades: {results.total_trades}")
    print(f"   • Win rate: {results.win_rate:.1f}%")
    print(f"   • Capital final: ${results.final_capital:.2f}")
    print(f"   • Retorno total: {results.total_return:.2f}%")

    print(f"\n📋 DETALLE DE TRADES:")
    for i, trade in enumerate(results.trades):
        print(f"   Trade {i+1}:")
        print(f"     • Entry: ${trade.entry_price:.2f} at {trade.entry_time}")
        print(f"     • Exit: ${trade.exit_price:.2f} at {trade.exit_time}")
        print(f"     • Duration: {trade.duration_hours:.1f}h")
        print(f"     • Result: {trade.result}")
        print(f"     • P&L: {trade.pnl_percent:.3f}%")

        # Verificar si salió por timeout
        exit_idx = None
        for idx, timestamp in enumerate(df['timestamp']):
            if str(timestamp) == str(trade.exit_time):
                exit_idx = idx
                break

        if exit_idx == len(df) - 1:
            print(f"     ⚠️ SALIDA FORZADA POR TIMEOUT")
        else:
            print(f"     ✅ SALIDA NORMAL POR SL/TP")

if __name__ == "__main__":
    test_realistic_sl_tp()
