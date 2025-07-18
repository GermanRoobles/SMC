#!/usr/bin/env python3
"""
Test del Motor de Trading SMC
=============================
"""

import pandas as pd
from fetch_data import get_ohlcv_extended
from smc_integration import get_smc_bot_analysis
from smc_trade_engine import get_trade_engine_analysis

def test_trade_engine():
    """Test básico del motor de trading"""
    print("🚀 Testing Motor de Trading TJR...")

    # Obtener datos
    print("📊 Obteniendo datos...")
    df = get_ohlcv_extended("BTCUSDT", "15m", days=1)

    if df is None or df.empty:
        print("❌ No se pudieron obtener datos")
        return

    print(f"✅ Datos obtenidos: {len(df)} velas")

    # Análisis SMC
    print("🤖 Ejecutando análisis SMC...")
    smc_analysis = get_smc_bot_analysis(df)

    if not smc_analysis:
        print("❌ No se pudo obtener análisis SMC")
        return

    print("✅ Análisis SMC completado")

    # Motor de trading
    print("⚡ Ejecutando Motor de Trading TJR...")
    trade_analysis = get_trade_engine_analysis(df, smc_analysis)

    if not trade_analysis:
        print("❌ No se pudo ejecutar motor de trading")
        return

    print(f"✅ Motor TJR ejecutado: {trade_analysis['signal_count']} señales")

    # Mostrar resultados
    if trade_analysis['signal_count'] > 0:
        print("\n🎯 SEÑALES DETECTADAS:")
        for i, signal in enumerate(trade_analysis['signals']):
            print(f"""
📍 Señal #{i+1}:
  - Tipo: {signal.signal_type.value}
  - Entrada: ${signal.entry_price:.2f}
  - Stop Loss: ${signal.stop_loss:.2f}
  - Take Profit: ${signal.take_profit:.2f}
  - Risk/Reward: {signal.risk_reward:.1f}:1
  - Confianza: {signal.confidence:.1%}
  - Confirmación: {signal.confirmation_type.value}
  - Timestamp: {signal.timestamp}
            """)
    else:
        print("\n📊 No se detectaron señales de trading en este momento")

    print(f"\n📊 Estado del motor: {trade_analysis.get('engine_status', 'unknown')}")
    print("✅ Test del Motor de Trading completado exitosamente!")

if __name__ == "__main__":
    test_trade_engine()
