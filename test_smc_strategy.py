#!/usr/bin/env python3
"""
Test SMC Strategy - Estrategia SMC Simplified by TJR
===================================================

Script para probar el bot SMC con datos reales y mostrar señales detectadas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fetch_data import get_ohlcv
from smc_bot import SMCBot, SMCConfig
from smc_integration import get_smc_bot_analysis

def test_smc_strategy():
    """
    Probar la estrategia SMC con datos reales
    """
    print("🚀 Probando Estrategia SMC Simplified by TJR")
    print("=" * 60)

    # Configuración optimizada según recomendaciones
    config = SMCConfig(
        swing_length=5,              # 5 velas (2 izq + 2 der)
        equal_tolerance=0.075,       # 0.075% tolerancia balanceada
        min_rr=2.0,                 # R:R mínimo 2:1
        risk_per_trade=1.0,
        min_confirmation_body=0.6,   # 60% cuerpo mínimo
        fvg_min_size=0.05,          # 5% FVG mínimo
        htf_timeframe="4h",         # HTF para estructura
        ltf_timeframe="15m",        # LTF para entrada
        enable_engulfing=True,      # Habilitar engulfing
        enable_pinbar=True,         # Habilitar pinbar/hammer
        enable_rejection_wick=True, # Habilitar rechazo
        min_wick_ratio=2.0         # Ratio mínimo mecha/cuerpo
    )

    print("⚙️ Configuración del Bot:")
    print(f"   📊 Swing Length: {config.swing_length} velas")
    print(f"   📏 Tolerancia Equal: {config.equal_tolerance}%")
    print(f"   💰 Min R:R: {config.min_rr}:1")
    print(f"   🎯 HTF: {config.htf_timeframe} | LTF: {config.ltf_timeframe}")
    print(f"   🔍 Confirmaciones: Engulfing={config.enable_engulfing}, Pinbar={config.enable_pinbar}")
    print()

    # Obtener datos de prueba
    print("📊 Obteniendo datos de mercado...")

    try:
        # Datos para análisis
        df = get_ohlcv("BTC/USDT", "15m")
        print(f"   ✅ Datos obtenidos: {len(df)} velas")
        print(f"   📈 Precio actual: ${df.iloc[-1]['close']:,.2f}")
        print(f"   📅 Desde: {df.iloc[0]['timestamp']} hasta {df.iloc[-1]['timestamp']}")
        print()

        # Ejecutar análisis SMC
        print("🔍 Ejecutando análisis SMC...")
        bot_analysis = get_smc_bot_analysis(df)

        # Mostrar resultados
        print("📋 RESULTADOS DEL ANÁLISIS:")
        print(f"   📈 Tendencia: {bot_analysis['trend'].value.upper()}")
        print(f"   🔍 Swings detectados: {len([s for s in bot_analysis['swings']['swing_high'] if s]) + len([s for s in bot_analysis['swings']['swing_low'] if s])}")
        print(f"   💧 Zonas de liquidez: {len(bot_analysis['liquidity_zones'])}")
        print(f"   🌊 Barridos detectados: {len(bot_analysis['sweeps'])}")
        print(f"   🔄 CHoCH/BOS: {len(bot_analysis['choch_bos'])}")
        print(f"   📦 Order Blocks: {len(bot_analysis['order_blocks'])}")
        print(f"   ⚡ FVG: {len(bot_analysis['fvg_zones'])}")
        print(f"   🎯 SEÑALES DETECTADAS: {len(bot_analysis['signals'])}")
        print()

        # Mostrar señales en detalle
        if bot_analysis['signals']:
            print("🚨 SEÑALES DE TRADING DETECTADAS:")
            print("=" * 60)

            for i, signal in enumerate(bot_analysis['signals'], 1):
                print(f"📢 SEÑAL #{i}:")
                print(f"   🎯 Tipo: {signal.signal_type.value.upper()}")
                print(f"   💰 Entrada: ${signal.entry_price:.2f}")
                print(f"   🛑 Stop Loss: ${signal.stop_loss:.2f}")
                print(f"   🎯 Take Profit: ${signal.take_profit:.2f}")
                print(f"   📊 R:R: {signal.risk_reward:.2f}:1")
                print(f"   🔒 Confianza: {signal.confidence:.1%}")
                print(f"   📝 Razón: {signal.reason}")
                print(f"   ⏰ Timestamp: {signal.timestamp}")
                print(f"   💲 Riesgo: ${abs(signal.entry_price - signal.stop_loss):.2f}")
                print(f"   💰 Recompensa: ${abs(signal.take_profit - signal.entry_price):.2f}")
                print("-" * 40)
        else:
            print("⚠️ No se detectaron señales de trading en este momento.")
            print("   Esperando mejores configuraciones del mercado...")

        print()

        # Mostrar liquidez y barridos
        if bot_analysis['liquidity_zones']:
            print("💧 ZONAS DE LIQUIDEZ:")
            for i, zone in enumerate(bot_analysis['liquidity_zones'][:5], 1):
                status = "🌊 BARRIDA" if zone['swept'] else "🔍 ACTIVA"
                print(f"   {i}. {zone['type'].replace('_', ' ').title()}: ${zone['price']:.2f} - {status}")

        if bot_analysis['order_blocks']:
            print("📦 ORDER BLOCKS:")
            for i, ob in enumerate(bot_analysis['order_blocks'][:3], 1):
                status = "✅ MITIGADO" if ob['mitigated'] else "🔍 ACTIVO"
                print(f"   {i}. {ob['type'].replace('_', ' ').title()}: ${ob['bottom']:.2f} - ${ob['top']:.2f} - {status}")

        if bot_analysis['fvg_zones']:
            print("⚡ FAIR VALUE GAPS:")
            for i, fvg in enumerate(bot_analysis['fvg_zones'][:3], 1):
                status = "✅ LLENADO" if fvg['filled'] else "🔍 ACTIVO"
                print(f"   {i}. {fvg['type'].replace('_', ' ').title()}: ${fvg['bottom']:.2f} - ${fvg['top']:.2f} - {status}")

        print()
        print("✅ Análisis SMC completado con éxito!")

    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

def simulate_trading_session():
    """
    Simular una sesión de trading completa
    """
    print("\n🎮 SIMULANDO SESIÓN DE TRADING")
    print("=" * 40)

    # Obtener datos
    df = get_ohlcv("BTC/USDT", "15m")

    # Configurar bot
    config = SMCConfig(
        swing_length=5,
        equal_tolerance=0.075,
        min_rr=2.5,  # R:R más conservador
        risk_per_trade=0.5,  # Riesgo reducido
        min_confirmation_body=0.7,  # Confirmación más estricta
        fvg_min_size=0.05,
        enable_engulfing=True,
        enable_pinbar=True,
        enable_rejection_wick=True,
        min_wick_ratio=2.0
    )

    bot = SMCBot(config)

    print("📊 Ejecutando análisis conservador...")
    analysis = bot.analyze_market(df)

    print("📋 Resumen de la sesión:")
    for key, value in analysis.items():
        print(f"   {key}: {value}")

    return analysis

if __name__ == "__main__":
    # Ejecutar prueba principal
    test_smc_strategy()

    # Ejecutar simulación
    simulate_trading_session()

    print("\n🎉 ¡Prueba completada!")
    print("💡 Para usar en producción, ajusta los parámetros según tu tolerancia al riesgo.")
