#!/usr/bin/env python3
"""
Ejemplo de Uso: Análisis Histórico SMC Bot
==========================================

Este script demuestra cómo usar el módulo de análisis histórico
para navegar por el historial de un par y ver señales pasadas.
"""

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Importar módulos del bot SMC
from smc_historical import create_historical_manager, HistoricalPeriod, analyze_historical_performance
from smc_historical_viz import create_historical_visualizer
from fetch_data import get_ohlcv

def demo_historical_analysis():
    """
    Demostración completa del análisis histórico
    """
    print("🔍 Demostración de Análisis Histórico SMC Bot")
    print("=" * 50)

    # 1. Crear gestor histórico
    print("📊 Creando gestor histórico...")
    symbol = "BTC/USDT"
    timeframe = "15m"

    manager = create_historical_manager(symbol, timeframe)
    visualizer = create_historical_visualizer(manager)

    print(f"   ✅ Gestor creado para {symbol} en {timeframe}")

    # 2. Generar timeline histórico
    print("\n📅 Generando timeline histórico...")
    period = HistoricalPeriod.DAY_1
    intervals = 8

    timeline = manager.generate_historical_timeline(period, intervals)

    if not timeline:
        print("   ❌ No se pudo generar timeline")
        return

    print(f"   ✅ Timeline generado con {len(timeline)} snapshots")

    # 3. Analizar rendimiento histórico
    print("\n📈 Analizando rendimiento histórico...")
    performance = analyze_historical_performance(timeline)

    if performance:
        print(f"   📊 Total señales: {performance['total_signals']}")
        print(f"   🟢 Señales BUY: {performance['buy_signals']}")
        print(f"   🔴 Señales SELL: {performance['sell_signals']}")
        print(f"   💎 R:R promedio: {performance['avg_rr']:.2f}:1")
        print(f"   🎯 Confianza promedio: {performance['avg_confidence']:.1%}")

        timespan = performance['timespan']
        print(f"   ⏱️ Período: {timespan['start']} a {timespan['end']}")
        print(f"   📏 Duración: {timespan['duration']}")

    # 4. Navegar por los snapshots
    print("\n🧭 Navegando por snapshots históricos...")

    for i, snapshot in enumerate(timeline):
        print(f"\n   📅 Snapshot {i+1}/{len(timeline)}")
        print(f"      Tiempo: {snapshot.timestamp}")
        print(f"      Señales: {len(snapshot.signals)}")
        print(f"      Precio: ${snapshot.market_conditions.get('price', 0):.2f}")
        print(f"      Tendencia: {snapshot.market_conditions.get('trend', 'N/A')}")
        print(f"      Volatilidad: {snapshot.market_conditions.get('volatility', 0):.2f}%")

        # Mostrar detalles de señales
        if snapshot.signals:
            print("      🎯 Señales detectadas:")
            for j, signal in enumerate(snapshot.signals):
                print(f"         {j+1}. {signal.signal_type.value} - "
                      f"Entry: ${signal.entry_price:.2f} - "
                      f"R:R: {signal.risk_reward:.1f}:1 - "
                      f"Conf: {signal.confidence:.0%}")

    # 5. Crear gráficos de ejemplo
    print("\n📊 Creando gráficos históricos...")

    try:
        # Gráfico de evolución de señales
        evolution_chart = visualizer.create_historical_evolution_chart()
        if evolution_chart.data:
            evolution_chart.write_html("historical_evolution.html")
            print("   ✅ Gráfico de evolución guardado como 'historical_evolution.html'")

        # Gráfico de R:R
        rr_chart = visualizer.create_rr_evolution_chart()
        if rr_chart.data:
            rr_chart.write_html("historical_rr.html")
            print("   ✅ Gráfico R:R guardado como 'historical_rr.html'")

        # Gráfico de confianza
        confidence_chart = visualizer.create_confidence_evolution_chart()
        if confidence_chart.data:
            confidence_chart.write_html("historical_confidence.html")
            print("   ✅ Gráfico de confianza guardado como 'historical_confidence.html'")

        # Gráfico de condiciones del mercado
        market_chart = visualizer.create_market_conditions_chart()
        if market_chart.data:
            market_chart.write_html("historical_market.html")
            print("   ✅ Gráfico de mercado guardado como 'historical_market.html'")

    except Exception as e:
        print(f"   ❌ Error creando gráficos: {e}")

    # 6. Guardar datos históricos
    print("\n💾 Guardando datos históricos...")
    cache_file = manager.save_historical_data()

    if cache_file:
        print(f"   ✅ Datos guardados en: {cache_file}")

    # 7. Ejemplo de navegación
    print("\n🎮 Ejemplo de navegación:")
    print("   - Usar visualizer.navigate_to_snapshot(index)")
    print("   - Obtener snapshot actual: visualizer.get_current_snapshot()")
    print("   - Información de navegación: visualizer.get_navigation_info()")

    # Demostrar navegación
    print("\n🧭 Demostrando navegación...")

    # Ir al primer snapshot
    first_snapshot = visualizer.navigate_to_snapshot(0)
    if first_snapshot:
        print(f"   📅 Navegado al primer snapshot: {first_snapshot.timestamp}")

    # Ir al último snapshot
    last_index = len(timeline) - 1
    last_snapshot = visualizer.navigate_to_snapshot(last_index)
    if last_snapshot:
        print(f"   📅 Navegado al último snapshot: {last_snapshot.timestamp}")

    # Información de navegación
    nav_info = visualizer.get_navigation_info()
    if nav_info:
        print(f"   📊 Snapshot actual: {nav_info['current_index'] + 1}/{nav_info['total_snapshots']}")
        print(f"   📈 Progreso: {nav_info['progress']:.1f}%")

    print("\n🎉 Demostración completada!")

def test_historical_cache():
    """
    Probar funcionalidad de cache histórico
    """
    print("\n🗄️ Probando funcionalidad de cache...")

    manager = create_historical_manager("ETH/USDT", "1h")

    # Generar algunos datos
    timeline = manager.generate_historical_timeline(HistoricalPeriod.HOURS_12, 5)

    if timeline:
        # Guardar en cache
        cache_file = manager.save_historical_data("test_cache.pkl")
        print(f"   ✅ Cache guardado: {cache_file}")

        # Crear nuevo gestor y cargar cache
        new_manager = create_historical_manager("ETH/USDT", "1h")
        loaded = new_manager.load_historical_data("test_cache.pkl")

        if loaded:
            print(f"   ✅ Cache cargado: {len(new_manager.snapshots)} snapshots")
        else:
            print("   ❌ Error cargando cache")

        # Listar archivos de cache
        cache_files = manager.get_available_cache_files()
        print(f"   📁 Archivos de cache disponibles: {len(cache_files)}")
        for file in cache_files:
            print(f"      - {file}")

def create_sample_historical_chart():
    """
    Crear gráfico de ejemplo con datos históricos
    """
    print("\n📊 Creando gráfico de ejemplo con datos históricos...")

    # Obtener datos actuales
    df = get_ohlcv("BTC/USDT", "15m")

    if df.empty:
        print("   ❌ No hay datos disponibles")
        return

    # Crear gráfico base
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="BTC/USDT",
            increasing=dict(line=dict(color='#26A69A'), fillcolor='#26A69A'),
            decreasing=dict(line=dict(color='#EF5350'), fillcolor='#EF5350'),
        )
    ])

    # Simular navegación histórica
    current_time = df['timestamp'].iloc[-1]  # Usar último timestamp del DataFrame
    historical_points = []

    for i in range(5):
        # Buscar timestamps que existan en el DataFrame
        if i < len(df):
            hist_time = df['timestamp'].iloc[-(i+1)]  # Retroceder en el DataFrame
            historical_points.append(hist_time)

    # Añadir marcadores históricos
    for i, hist_time in enumerate(historical_points):
        fig.add_vline(
            x=hist_time,
            line_dash="dot",
            line_color="rgba(255, 255, 255, 0.5)",
            line_width=1,
            annotation_text=f"H{i+1}",
            annotation_position="top",
            annotation=dict(
                font=dict(size=10, color="white"),
                bgcolor="rgba(0, 0, 0, 0.7)",
                bordercolor="white",
                borderwidth=1
            )
        )

    # Configurar layout
    fig.update_layout(
        title="📅 Ejemplo de Navegación Histórica - BTC/USDT",
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',
        font=dict(color='white'),
        xaxis=dict(showgrid=True, gridcolor='#2A2A2A'),
        yaxis=dict(showgrid=True, gridcolor='#2A2A2A'),
        height=600
    )

    # Guardar gráfico
    fig.write_html("sample_historical_chart.html")
    print("   ✅ Gráfico de ejemplo guardado como 'sample_historical_chart.html'")

if __name__ == "__main__":
    print("🚀 Demostración de Análisis Histórico SMC Bot")
    print("=" * 55)

    # Ejecutar demostración principal
    demo_historical_analysis()

    # Probar funcionalidad de cache
    test_historical_cache()

    # Crear gráfico de ejemplo
    create_sample_historical_chart()

    print("\n" + "=" * 55)
    print("✅ Funcionalidades históricas implementadas:")
    print("   📅 Navegación por timeline histórico")
    print("   🔍 Análisis de señales pasadas")
    print("   📊 Gráficos de evolución")
    print("   💾 Cache de datos históricos")
    print("   🎮 Controles de navegación")
    print("   📈 Métricas de rendimiento")
    print("\n💡 Para usar en Streamlit:")
    print("   1. Activar 'Habilitar Análisis Histórico'")
    print("   2. Seleccionar período histórico")
    print("   3. Usar controles de navegación")
    print("   4. Activar 'Gráficos Históricos' para análisis avanzado")
    print("=" * 55)
