#!/usr/bin/env python3
"""
Ejemplo de uso de las mejoras de visualización SMC Bot
=====================================================

Este script muestra cómo usar las nuevas funciones de visualización
mejoradas para el SMC Bot con estilo TradingView.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Importar módulos del bot SMC
from smc_integration import get_smc_bot_analysis, add_bot_signals_to_chart, add_signals_statistics_to_chart
from smc_visualization_advanced import enhance_signal_visualization
from fetch_data import get_ohlcv

def demo_advanced_visualization():
    """
    Demostración de la visualización avanzada del SMC Bot
    """
    print("🎯 Demostración de Visualización Avanzada SMC Bot")
    print("=" * 50)

    # 1. Obtener datos de ejemplo
    print("📊 Obteniendo datos de mercado...")
    try:
        df = get_ohlcv("BTC/USDT", "15m")
        print(f"   ✅ Datos obtenidos: {len(df)} velas")
    except Exception as e:
        print(f"   ❌ Error obteniendo datos: {e}")
        return

    # 2. Ejecutar análisis del bot
    print("\n🤖 Ejecutando análisis SMC Bot...")
    try:
        bot_analysis = get_smc_bot_analysis(df)
        signals = bot_analysis['signals']
        print(f"   ✅ Análisis completado: {len(signals)} señales detectadas")
    except Exception as e:
        print(f"   ❌ Error en análisis: {e}")
        return

    # 3. Crear gráfico base
    print("\n📈 Creando gráfico base...")
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Precio",
            increasing=dict(line=dict(color='#26A69A', width=1), fillcolor='#26A69A'),
            decreasing=dict(line=dict(color='#EF5350', width=1), fillcolor='#EF5350'),
        )
    ])

    # 4. Añadir señales básicas
    print("\n🎯 Añadiendo señales básicas...")
    add_bot_signals_to_chart(fig, df, bot_analysis)
    add_signals_statistics_to_chart(fig, bot_analysis)

    # 5. Aplicar mejoras avanzadas
    print("\n✨ Aplicando mejoras avanzadas...")
    enhance_signal_visualization(fig, df, bot_analysis)

    # 6. Configurar layout con estilo TradingView
    print("\n🎨 Configurando estilo TradingView...")
    fig.update_layout(
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',
        title={
            'text': "SMC Bot - Visualización Avanzada Demo",
            'font': {'size': 18, 'color': '#FFFFFF', 'family': 'Arial'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            showgrid=True,
            gridcolor='#2A2A2A',
            gridwidth=1,
            color='#FFFFFF',
            showspikes=True,
            spikecolor='#FFFFFF',
            spikesnap='cursor',
            spikemode='across',
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#2A2A2A',
            gridwidth=1,
            color='#FFFFFF',
            showspikes=True,
            spikecolor='#FFFFFF',
            spikesnap='cursor',
            spikemode='across',
        ),
        legend=dict(
            bgcolor='rgba(30, 30, 30, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.3)',
            font=dict(color='#FFFFFF'),
            borderwidth=1
        ),
        hovermode='x unified',
        showlegend=True,
        height=800,
        width=1200
    )

    # 7. Mostrar resultados
    print("\n📊 Resultados del análisis:")
    print(f"   • Señales detectadas: {len(signals)}")

    if signals:
        buy_signals = len([s for s in signals if s.signal_type.value == 'BUY'])
        sell_signals = len([s for s in signals if s.signal_type.value == 'SELL'])
        avg_rr = sum(s.risk_reward for s in signals) / len(signals)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)

        print(f"   • Señales BUY: {buy_signals}")
        print(f"   • Señales SELL: {sell_signals}")
        print(f"   • R:R promedio: {avg_rr:.2f}:1")
        print(f"   • Confianza promedio: {avg_confidence:.1%}")

        # Mostrar detalles de las señales
        print("\n📋 Detalle de señales:")
        for i, signal in enumerate(signals):
            timestamp_str = "N/A"
            if hasattr(signal.timestamp, 'strftime'):
                timestamp_str = signal.timestamp.strftime('%Y-%m-%d %H:%M')
            elif isinstance(signal.timestamp, (int, float)):
                timestamp_str = f"Índice: {signal.timestamp}"

            print(f"   {i+1}. {signal.signal_type.value} - Entry: ${signal.entry_price:.2f} - "
                  f"R:R: {signal.risk_reward:.1f}:1 - Conf: {signal.confidence:.0%} - {timestamp_str}")

    # 8. Guardar gráfico
    print("\n💾 Guardando gráfico...")
    try:
        fig.write_html("demo_smc_advanced_visualization.html")
        print("   ✅ Gráfico guardado como 'demo_smc_advanced_visualization.html'")
    except Exception as e:
        print(f"   ❌ Error guardando gráfico: {e}")

    print("\n🎉 Demostración completada!")
    print("   Abra el archivo HTML en su navegador para ver el resultado")

def compare_basic_vs_advanced():
    """
    Comparar visualización básica vs avanzada
    """
    print("\n🔍 Comparación: Básica vs Avanzada")
    print("=" * 40)

    # Características básicas
    print("\n📊 Visualización Básica:")
    print("   • Señales con flechas simples")
    print("   • Líneas de SL/TP básicas")
    print("   • Estadísticas simples")
    print("   • Información de hover básica")

    # Características avanzadas
    print("\n✨ Visualización Avanzada:")
    print("   • Señales con emojis y colores mejorados")
    print("   • Zonas de riesgo y ganancia destacadas")
    print("   • Etiquetas de calidad (R:R, Confianza)")
    print("   • Tracker de rendimiento en tiempo real")
    print("   • Indicador de sentimiento del mercado")
    print("   • Barras de fuerza de señal")
    print("   • Overlay de gestión de riesgo")
    print("   • Líneas de conexión entre señales")
    print("   • Timestamps y estado del bot")

def show_customization_options():
    """
    Mostrar opciones de personalización
    """
    print("\n🎨 Opciones de Personalización:")
    print("=" * 35)

    print("🎯 Configuración de Señales:")
    print("   - Colores personalizados")
    print("   - Tamaños de marcadores")
    print("   - Estilos de líneas")
    print("   - Transparencias")

    print("\n📊 Elementos Visuales:")
    print("   - Zonas de riesgo/ganancia")
    print("   - Etiquetas informativas")
    print("   - Indicadores de rendimiento")
    print("   - Sentimiento del mercado")

    print("\n⚙️ Controles de Usuario:")
    print("   - Activar/desactivar elementos")
    print("   - Cambiar timeframes")
    print("   - Configurar alertas")
    print("   - Exportar datos")

if __name__ == "__main__":
    print("🚀 SMC Bot - Demostración de Visualización Avanzada")
    print("=" * 55)

    # Ejecutar demostración
    demo_advanced_visualization()

    # Mostrar comparación
    compare_basic_vs_advanced()

    # Mostrar opciones de personalización
    show_customization_options()

    print("\n" + "=" * 55)
    print("🎯 Para usar en Streamlit:")
    print("   1. Ejecutar: streamlit run app_streamlit.py")
    print("   2. Activar 'SMC Bot' en la barra lateral")
    print("   3. Activar 'Visualización Avanzada'")
    print("   4. Experimentar con las opciones avanzadas")
    print("=" * 55)
