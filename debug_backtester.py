#!/usr/bin/env python3
"""
DEBUG DEL BACKTESTER
===================

Debug para identificar por qué el backtester no está ejecutando trades.
"""

from fetch_data import get_ohlcv
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import SMCBacktester
import pandas as pd
from datetime import datetime

def debug_backtester():
    """Debug del backtester paso a paso"""

    print("="*60)
    print("🔧 DEBUG DEL BACKTESTER SMC")
    print("="*60)

    # 1. Datos básicos
    df = get_ohlcv('BTCUSDT', '1h', limit=50)
    print(f"\n📊 DataFrame info:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Index type: {type(df.index)}")
    print(f"   Timestamp column type: {type(df['timestamp'].iloc[0])}")
    print(f"   Index sample: {df.index[:3].tolist()}")
    print(f"   Timestamp sample: {df['timestamp'].head(3).tolist()}")

    # 2. Crear una señal simple
    entry_time = df['timestamp'].iloc[10]
    entry_price = df['close'].iloc[10]

    signal = TradeSignal(
        timestamp=entry_time,
        symbol='BTCUSDT',
        timeframe='1h',
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * 0.98,
        take_profit=entry_price * 1.04,
        risk_reward=2.0,
        confidence=0.8,
        setup_components={'test': True},
        confirmation_type=ConfirmationType.ENGULFING
    )

    print(f"\n⚡ Señal creada:")
    print(f"   Timestamp: {signal.timestamp}")
    print(f"   Entry price: ${signal.entry_price:.2f}")
    print(f"   Signal type: {signal.signal_type}")

    # 3. Probar la simulación directamente
    backtester = SMCBacktester(10000, 2.0)

    print(f"\n🔍 Simulando trade...")

    # Debug del método _simulate_trade
    try:
        signal_time = signal.timestamp
        print(f"   Signal time: {signal_time} (type: {type(signal_time)})")

        # Buscar índice de entrada
        entry_idx = None
        print(f"   Buscando entrada en DataFrame...")

        for idx, row_time in enumerate(df.index):
            dt_row_time = pd.to_datetime(row_time)
            dt_signal_time = pd.to_datetime(signal_time)
            print(f"     Índice {idx}: {row_time} -> {dt_row_time} vs {dt_signal_time}")
            if dt_row_time >= dt_signal_time:
                entry_idx = idx
                print(f"   ✅ Entry index encontrado: {entry_idx}")
                break

        if entry_idx is None:
            print(f"   ❌ No se encontró entry index")

            # Intentar buscar por columna timestamp
            print(f"   🔍 Buscando por columna timestamp...")
            for idx, ts in enumerate(df['timestamp']):
                if pd.to_datetime(ts) >= pd.to_datetime(signal_time):
                    entry_idx = idx
                    print(f"   ✅ Entry index encontrado por timestamp: {entry_idx}")
                    break

        if entry_idx is not None:
            print(f"   📊 Datos de entrada (índice {entry_idx}):")
            print(f"      Timestamp: {df['timestamp'].iloc[entry_idx]}")
            print(f"      OHLC: O={df['open'].iloc[entry_idx]:.2f}, "
                  f"H={df['high'].iloc[entry_idx]:.2f}, "
                  f"L={df['low'].iloc[entry_idx]:.2f}, "
                  f"C={df['close'].iloc[entry_idx]:.2f}")

    except Exception as e:
        print(f"   ❌ Error en simulación: {e}")
        import traceback
        traceback.print_exc()

    # 4. Probar backtesting completo
    print(f"\n🎯 Ejecutando backtesting completo...")

    results = backtester.run_backtest(df, [signal])

    print(f"   Total trades: {results.total_trades}")
    print(f"   Trades list length: {len(results.trades)}")

    if len(results.trades) > 0:
        trade = results.trades[0]
        print(f"   Primer trade:")
        print(f"      Entry time: {trade.entry_time}")
        print(f"      Entry price: ${trade.entry_price:.2f}")
        print(f"      Result: {trade.result}")
    else:
        print(f"   ❌ No se generaron trades")

if __name__ == "__main__":
    debug_backtester()
