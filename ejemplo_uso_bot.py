#!/usr/bin/env python3
"""
Ejemplo de uso del SMC Bot
==========================

Este archivo muestra cómo usar el bot SMC de manera independiente
para detectar señales de trading según la estrategia SMC Simplified by TJR.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from smc_bot import SMCBot, SMCConfig

def get_config_by_profile(profile):
    """
    Obtiene configuración por perfil
    """
    configs = {
        'conservative': SMCConfig(
            swing_length=7,
            equal_tolerance=0.05,
            min_rr=3.0,
            risk_per_trade=0.5
        ),
        'balanced': SMCConfig(
            swing_length=5,
            equal_tolerance=0.075,
            min_rr=2.0,
            risk_per_trade=1.0
        ),
        'aggressive': SMCConfig(
            swing_length=3,
            equal_tolerance=0.1,
            min_rr=1.5,
            risk_per_trade=2.0
        )
    }
    return configs.get(profile, configs['balanced'])

def generar_datos_ejemplo():
    """
    Genera datos OHLC de ejemplo para probar el bot
    """
    print("📊 Generando datos de ejemplo...")

    # Generar 200 velas de ejemplo
    np.random.seed(42)  # Para reproducibilidad

    dates = pd.date_range(start='2024-01-01', periods=200, freq='15T')

    # Precio inicial
    price = 100000.0

    # Arrays para OHLC
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []

    for i in range(200):
        # Simular movimiento de precio
        change = np.random.normal(0, 0.002)  # 0.2% volatilidad promedio

        # Añadir tendencia
        if i < 50:
            trend = 0.001  # Tendencia alcista
        elif i < 100:
            trend = -0.0015  # Tendencia bajista
        elif i < 150:
            trend = 0.0008  # Tendencia alcista suave
        else:
            trend = -0.0005  # Tendencia bajista suave

        # Calcular precios
        open_price = price
        close_price = price * (1 + change + trend)

        # High y Low con algún ruido
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))

        # Volumen aleatorio
        volume = np.random.randint(1000, 5000)

        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        closes.append(close_price)
        volumes.append(volume)

        price = close_price

    # Crear DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })

    df.set_index('timestamp', inplace=True)

    print(f"✅ Generados {len(df)} datos de ejemplo")
    print(f"   Precio inicial: ${opens[0]:,.2f}")
    print(f"   Precio final: ${closes[-1]:,.2f}")
    print(f"   Cambio total: {((closes[-1] - opens[0]) / opens[0] * 100):+.2f}%")

    return df

def probar_configuraciones():
    """
    Prueba diferentes configuraciones del bot
    """
    print("\n🔧 Probando diferentes configuraciones...")

    # Generar datos
    df = generar_datos_ejemplo()

    # Configuraciones a probar
    configs = {
        'conservador': get_config_by_profile('conservative'),
        'balanceado': get_config_by_profile('balanced'),
        'agresivo': get_config_by_profile('aggressive')
    }

    resultados = {}

    for nombre, config in configs.items():
        print(f"\n📊 Probando configuración: {nombre.upper()}")
        print("=" * 50)

        # Crear bot
        bot = SMCBot(config)

        # Analizar mercado
        analysis = bot.analyze_market(df)

        # Guardar resultados
        resultados[nombre] = {
            'config': config,
            'analysis': analysis,
            'signals': bot.signals,
            'swings': len([s for s in bot.swings['swing_high'] if s]) + len([s for s in bot.swings['swing_low'] if s]),
            'liquidity_zones': len(bot.liquidity_zones),
            'order_blocks': len(bot.order_blocks),
            'fvg_zones': len(bot.fvg_zones)
        }

        print(f"🎯 Señales encontradas: {len(bot.signals)}")

        # Mostrar señales
        for i, signal in enumerate(bot.signals):
            print(f"   {i+1}. {signal.signal_type.value.upper()}: ${signal.entry_price:.2f}")
            print(f"      SL: ${signal.stop_loss:.2f} | TP: ${signal.take_profit:.2f}")
            print(f"      R:R: {signal.risk_reward:.2f} | Confianza: {signal.confidence:.1%}")
            print(f"      Razón: {signal.reason}")

    return resultados

def analizar_resultados(resultados):
    """
    Analiza y compara los resultados de diferentes configuraciones
    """
    print("\n📈 ANÁLISIS COMPARATIVO")
    print("=" * 60)

    # Tabla comparativa
    print(f"{'Config':<12} {'Señales':<8} {'Swings':<8} {'Liquidez':<9} {'OB':<4} {'FVG':<4}")
    print("-" * 60)

    for nombre, resultado in resultados.items():
        print(f"{nombre:<12} {len(resultado['signals']):<8} {resultado['swings']:<8} "
              f"{resultado['liquidity_zones']:<9} {resultado['order_blocks']:<4} {resultado['fvg_zones']:<4}")

    print("\n🏆 RECOMENDACIONES:")

    # Encontrar la mejor configuración
    mejor_config = None
    max_signals = 0

    for nombre, resultado in resultados.items():
        if len(resultado['signals']) > max_signals:
            max_signals = len(resultado['signals'])
            mejor_config = nombre

    if mejor_config:
        print(f"✅ Configuración con más señales: {mejor_config.upper()} ({max_signals} señales)")

    # Mostrar configuración detallada de la mejor
    if mejor_config:
        config = resultados[mejor_config]['config']
        print(f"\n📋 Configuración {mejor_config.upper()}:")
        print(f"   Swing Length: {config.swing_length}")
        print(f"   Equal Tolerance: {config.equal_tolerance}%")
        print(f"   Min R:R: {config.min_rr}:1")
        print(f"   Risk per Trade: {config.risk_per_trade}%")

def ejemplo_uso_basico():
    """
    Ejemplo básico de uso del bot
    """
    print("\n🚀 EJEMPLO DE USO BÁSICO")
    print("=" * 40)

    # 1. Cargar datos (en este caso, generamos datos de ejemplo)
    df = generar_datos_ejemplo()

    # 2. Crear configuración personalizada
    config = SMCConfig(
        swing_length=5,
        equal_tolerance=0.1,
        min_rr=2.0,
        risk_per_trade=1.0
    )

    # 3. Inicializar bot
    bot = SMCBot(config)

    # 4. Analizar mercado
    print("\n🔍 Analizando mercado...")
    analysis = bot.analyze_market(df)

    # 5. Mostrar resultados
    print(f"\n📊 RESULTADOS DEL ANÁLISIS:")
    print(f"   Tendencia: {analysis['trend']}")
    print(f"   Swings: {analysis['swings']}")
    print(f"   Liquidez: {analysis['liquidity_zones']}")
    print(f"   Barridos: {analysis['sweeps']}")
    print(f"   CHoCH/BOS: {analysis['choch_bos']}")
    print(f"   Order Blocks: {analysis['order_blocks']}")
    print(f"   FVG: {analysis['fvg_zones']}")
    print(f"   Señales: {analysis['signals']}")

    # 6. Procesar señales
    if bot.signals:
        print(f"\n🎯 SEÑALES DETECTADAS:")
        for i, signal in enumerate(bot.signals):
            print(f"\n   📍 SEÑAL #{i+1}:")
            bot.place_trade(signal)
    else:
        print("\n⚠️ No se encontraron señales con los criterios actuales")

def main():
    """
    Función principal
    """
    print("🤖 SMC Bot - Ejemplo de Uso")
    print("=" * 50)

    # Ejecutar ejemplos
    print("\n1️⃣ Ejecutando ejemplo básico...")
    ejemplo_uso_basico()

    print("\n2️⃣ Probando diferentes configuraciones...")
    resultados = probar_configuraciones()

    print("\n3️⃣ Analizando resultados...")
    analizar_resultados(resultados)

    print("\n✅ Ejemplo completado!")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Conecta datos reales con fetch_data.py")
    print("   2. Personaliza la configuración según tu estilo")
    print("   3. Integra con tu broker para trading real")
    print("   4. Ejecuta la app Streamlit para visualización")

if __name__ == "__main__":
    main()
