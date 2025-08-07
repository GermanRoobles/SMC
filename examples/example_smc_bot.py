#!/usr/bin/env python3
"""
Ejemplo de uso del SMC Bot
==========================

Script de ejemplo que muestra cómo utilizar el bot de Smart Money Concepts
para detectar señales de trading según la estrategia SMC Simplified by TJR.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fetch_data import get_ohlcv
from smc_bot import SMCBot, SMCConfig, SignalType

def generate_sample_data():
    """
    Generar datos de ejemplo para probar el bot

    Returns:
        DataFrame con datos OHLC simulados
    """
    print("📊 Generando datos de ejemplo...")

    # Crear 500 velas de datos sintéticos
    dates = pd.date_range(start='2024-01-01', periods=500, freq='5T')

    # Simular precio base
    base_price = 50000

    # Generar datos OHLC con volatilidad
    np.random.seed(42)  # Para reproducibilidad

    data = []
    current_price = base_price

    for i, date in enumerate(dates):
        # Simular movimiento de precio
        change = np.random.normal(0, 0.005)  # 0.5% volatilidad promedio

        # Añadir tendencia subyacente
        if i < 100:
            trend = 0.0002  # Tendencia alcista
        elif i < 200:
            trend = -0.0001  # Tendencia bajista
        elif i < 300:
            trend = 0.0003  # Tendencia alcista fuerte
        else:
            trend = 0.0001  # Tendencia lateral

        current_price *= (1 + change + trend)

        # Generar OHLC
        volatility = current_price * 0.01  # 1% volatilidad intraday

        open_price = current_price + np.random.normal(0, volatility * 0.2)
        high_price = open_price + abs(np.random.normal(0, volatility))
        low_price = open_price - abs(np.random.normal(0, volatility))
        close_price = open_price + np.random.normal(0, volatility * 0.5)

        # Asegurar que high/low sean coherentes
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        # Volumen simulado
        volume = np.random.randint(50, 200)

        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })

        current_price = close_price

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)

    print(f"   ✅ Generados {len(df)} datos de ejemplo")
    return df

def run_smc_bot_example():
    """
    Ejecutar ejemplo completo del bot SMC
    """
    print("🚀 Iniciando ejemplo del SMC Bot")
    print("=" * 60)

    # Configurar bot personalizado
    config = SMCConfig(
        swing_length=8,          # Longitud de swing reducida para más señales
        equal_tolerance=0.2,     # Tolerancia de 0.2% para equal highs/lows
        min_rr=1.5,             # R:R mínimo de 1.5:1
        risk_per_trade=2.0,     # 2% riesgo por operación
        min_confirmation_body=0.5,  # 50% mínimo del cuerpo de confirmación
        fvg_min_size=0.1        # 0.1% mínimo para FVG
    )

    # Crear bot
    bot = SMCBot(config)

    # Opción 1: Usar datos reales (descomenta si tienes conexión)
    try:
        print("📡 Intentando obtener datos reales...")
        df = get_ohlcv("BTC/USDT", "5m")
        print(f"   ✅ Datos reales obtenidos: {len(df)} velas")
    except Exception as e:
        print(f"   ⚠️ Error obteniendo datos reales: {e}")
        print("   🔄 Usando datos de ejemplo...")
        df = generate_sample_data()

    # Ejecutar análisis completo
    print("\n" + "=" * 60)
    print("🔍 INICIANDO ANÁLISIS COMPLETO")
    print("=" * 60)

    analysis = bot.analyze_market(df)

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL ANÁLISIS")
    print("=" * 60)

    print(f"📈 Tendencia: {analysis['trend'].upper()}")
    print(f"🔍 Swings detectados: {analysis['swings']}")
    print(f"💧 Zonas de liquidez: {analysis['liquidity_zones']}")
    print(f"🌊 Barridos: {analysis['sweeps']}")
    print(f"🔄 CHoCH/BOS: {analysis['choch_bos']}")
    print(f"📦 Order Blocks: {analysis['order_blocks']}")
    print(f"⚡ Fair Value Gaps: {analysis['fvg_zones']}")
    print(f"🎯 Señales generadas: {analysis['signals']}")

    # Mostrar señales detalladas
    if bot.signals:
        print("\n" + "=" * 60)
        print("🚨 SEÑALES DE TRADING DETECTADAS")
        print("=" * 60)

        for i, signal in enumerate(bot.signals[-5:], 1):  # Últimas 5 señales
            print(f"\n🎯 SEÑAL #{i}:")
            bot.place_trade(signal)
    else:
        print("\n⚠️ No se detectaron señales de trading con los criterios actuales")

    # Mostrar información detallada de componentes
    print("\n" + "=" * 60)
    print("🔍 DETALLES DE COMPONENTES")
    print("=" * 60)

    # Zonas de liquidez
    if bot.liquidity_zones:
        print(f"\n💧 ZONAS DE LIQUIDEZ ({len(bot.liquidity_zones)}):")
        for i, zone in enumerate(bot.liquidity_zones[:3], 1):
            status = "🔴 BARRIDA" if zone['swept'] else "🟢 ACTIVA"
            print(f"   {i}. {zone['type'].upper()} - ${zone['price']:.2f} - {status}")

    # Order Blocks
    if hasattr(bot, 'order_blocks') and bot.order_blocks:
        print(f"\n📦 ORDER BLOCKS ({len(bot.order_blocks)}):")
        for i, ob in enumerate(bot.order_blocks[:3], 1):
            status = "🔴 MITIGADO" if ob.get('mitigated', False) else "🟢 ACTIVO"
            print(f"   {i}. {ob['type'].upper()} - ${ob['bottom']:.2f}-${ob['top']:.2f} - {status}")

    # FVG Zones
    if hasattr(bot, 'fvg_zones') and bot.fvg_zones:
        print(f"\n⚡ FAIR VALUE GAPS ({len(bot.fvg_zones)}):")
        for i, fvg in enumerate(bot.fvg_zones[:3], 1):
            status = "🔴 LLENADO" if fvg.get('filled', False) else "🟢 ACTIVO"
            print(f"   {i}. {fvg['type'].upper()} - ${fvg['bottom']:.2f}-${fvg['top']:.2f} - {status}")

    print("\n" + "=" * 60)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 60)

    return bot, analysis

def run_live_simulation():
    """
    Simular análisis en tiempo real
    """
    print("\n🔄 Iniciando simulación en tiempo real...")
    print("(Presiona Ctrl+C para detener)")

    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Analizando mercado...")

            # Obtener datos actuales
            try:
                df = get_ohlcv("BTC/USDT", "5m")

                # Crear bot con configuración rápida
                config = SMCConfig(swing_length=5, equal_tolerance=0.15, min_rr=1.5)
                bot = SMCBot(config)

                # Análisis rápido
                analysis = bot.analyze_market(df)

                # Mostrar solo si hay señales
                if bot.signals:
                    print("🚨 NUEVA SEÑAL DETECTADA:")
                    for signal in bot.signals[-1:]:  # Solo la última
                        bot.place_trade(signal)
                else:
                    print("   📊 Sin señales - Monitoreando...")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"   ⚠️ Error en análisis: {e}")

            import time
            time.sleep(60)  # Esperar 1 minuto

    except KeyboardInterrupt:
        print("\n\n⏹️ Simulación detenida por el usuario")

if __name__ == "__main__":
    # Ejecutar ejemplo principal
    bot, analysis = run_smc_bot_example()

    # Preguntar si ejecutar simulación en tiempo real
    print("\n" + "=" * 60)
    response = input("¿Ejecutar simulación en tiempo real? (s/n): ").lower().strip()

    if response in ['s', 'si', 'sí', 'y', 'yes']:
        run_live_simulation()
    else:
        print("👋 ¡Gracias por probar el SMC Bot!")
