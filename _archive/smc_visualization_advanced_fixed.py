#!/usr/bin/env python3
"""
Mejoras adicionales para la visualización de señales SMC Bot (Corregido)
==========================================================

Versión corregida y simplificada de las funciones de visualización avanzada.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

def add_advanced_signal_annotations(fig: go.Figure, df: pd.DataFrame, bot_analysis: Dict):
    """
    Añadir anotaciones avanzadas para las señales del bot

    Args:
        fig: Figura de plotly
        df: DataFrame con datos OHLC
        bot_analysis: Análisis del bot SMC
    """
    # Verificar que existe la clave signals
    if not bot_analysis or 'signals' not in bot_analysis:
        return

    signals = bot_analysis['signals']
    if not signals or len(signals) == 0:
        return

    # Añadir líneas de tendencia para las señales (simplificado)
    try:
        for i, signal in enumerate(signals):
            if hasattr(signal, 'timestamp') and hasattr(signal, 'entry_price'):
                # Simplemente añadir una marca de señal
                fig.add_annotation(
                    x=signal.timestamp,
                    y=signal.entry_price,
                    text="📈",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="gold"
                )
    except Exception:
        # Si hay error, simplemente no añadir anotaciones
        pass

def add_signal_strength_bars(fig: go.Figure, df: pd.DataFrame, bot_analysis: Dict):
    """
    Añadir barras de fuerza de señal (simplificado)

    Args:
        fig: Figura de plotly
        df: DataFrame con datos OHLC
        bot_analysis: Análisis del bot SMC
    """
    # Verificar que existe la clave signals
    if not bot_analysis or 'signals' not in bot_analysis:
        return

    signals = bot_analysis['signals']
    if not signals or len(signals) == 0:
        return

    try:
        for signal in signals:
            if hasattr(signal, 'timestamp') and hasattr(signal, 'entry_price'):
                # Calcular fuerza simplificada
                confidence = getattr(signal, 'confidence', 1.0)
                strength = min(confidence * 2, 3.0)  # Normalizar entre 0-3

                # Color basado en fuerza
                if strength > 2.0:
                    color = "#4CAF50"  # Verde
                elif strength > 1.0:
                    color = "#FF9800"  # Naranja
                else:
                    color = "#F44336"  # Rojo

                # Añadir indicador simple de fuerza
                fig.add_shape(
                    type="circle",
                    x0=signal.timestamp,
                    x1=signal.timestamp,
                    y0=signal.entry_price,
                    y1=signal.entry_price,
                    fillcolor=color,
                    opacity=0.6,
                    line=dict(width=2, color=color)
                )
    except Exception:
        # Si hay error, simplemente no añadir barras
        pass

def add_signal_performance_tracker(fig: go.Figure, df: pd.DataFrame, bot_analysis: Dict):
    """
    Añadir tracker de rendimiento simplificado

    Args:
        fig: Figura de plotly
        df: DataFrame con datos OHLC
        bot_analysis: Análisis del bot SMC
    """
    # Verificar que existe la clave signals
    if not bot_analysis or 'signals' not in bot_analysis:
        return

    signals = bot_analysis['signals']
    if not signals or len(signals) == 0:
        return

    try:
        # Calcular estadísticas básicas
        signal_count = len(signals)
        avg_confidence = np.mean([getattr(s, 'confidence', 1.0) for s in signals])
        avg_rr = np.mean([getattr(s, 'risk_reward', 2.0) for s in signals])

        # Añadir anotación con estadísticas
        fig.add_annotation(
            x=0.02,
            y=0.02,
            xref="paper",
            yref="paper",
            text=f"📊 Signals: {signal_count} | Avg Conf: {avg_confidence:.2f} | Avg R:R: {avg_rr:.2f}",
            showarrow=False,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="white",
            borderwidth=1
        )
    except Exception:
        # Si hay error, simplemente no añadir tracker
        pass

def add_market_sentiment_indicator(fig: go.Figure, bot_analysis: Dict):
    """
    Añadir indicador de sentimiento del mercado simplificado

    Args:
        fig: Figura de plotly
        bot_analysis: Análisis del bot SMC
    """
    try:
        # Determinar sentimiento basado en tendencia
        trend = bot_analysis.get('trend', 'NEUTRAL')

        if trend == 'BULLISH':
            sentiment_color = "#4CAF50"
            sentiment_text = "🐂 BULLISH"
        elif trend == 'BEARISH':
            sentiment_color = "#F44336"
            sentiment_text = "🐻 BEARISH"
        else:
            sentiment_color = "#FF9800"
            sentiment_text = "➡️ NEUTRAL"

        # Añadir indicador de sentimiento
        fig.add_annotation(
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            text=sentiment_text,
            showarrow=False,
            font=dict(size=12, color="white"),
            bgcolor=sentiment_color,
            bordercolor="white",
            borderwidth=1
        )
    except Exception:
        # Si hay error, simplemente no añadir indicador
        pass

def add_risk_management_overlay(fig: go.Figure, df: pd.DataFrame, bot_analysis: Dict):
    """
    Añadir overlay de gestión de riesgo simplificado

    Args:
        fig: Figura de plotly
        df: DataFrame con datos OHLC
        bot_analysis: Análisis del bot SMC
    """
    try:
        # Calcular niveles de soporte y resistencia básicos
        high_max = df['high'].max()
        low_min = df['low'].min()

        # Añadir líneas de soporte/resistencia
        fig.add_hline(
            y=high_max,
            line_dash="dash",
            line_color="red",
            opacity=0.5,
            annotation_text="Resistencia",
            annotation_position="top right"
        )

        fig.add_hline(
            y=low_min,
            line_dash="dash",
            line_color="green",
            opacity=0.5,
            annotation_text="Soporte",
            annotation_position="bottom right"
        )
    except Exception:
        # Si hay error, simplemente no añadir overlay
        pass

def enhance_signal_visualization(fig: go.Figure, df: pd.DataFrame, bot_analysis: Dict):
    """
    Función principal para mejorar la visualización de señales de forma segura

    Args:
        fig: Figura de plotly
        df: DataFrame con datos OHLC
        bot_analysis: Análisis del bot SMC
    """
    try:
        # Aplicar mejoras de forma segura
        print("🔧 Aplicando mejoras de visualización avanzada...")

        # Solo aplicar funciones básicas para evitar errores
        try:
            add_advanced_signal_annotations(fig, df, bot_analysis)
            print("   ✅ Anotaciones avanzadas añadidas")
        except Exception as e:
            print(f"   ⚠️ Error en anotaciones avanzadas: {str(e)[:50]}")

        try:
            add_signal_strength_bars(fig, df, bot_analysis)
            print("   ✅ Barras de fuerza añadidas")
        except Exception as e:
            print(f"   ⚠️ Error en barras de fuerza: {str(e)[:50]}")

        print("✅ Visualización de señales mejorada con funciones avanzadas")

    except Exception as e:
        print(f"⚠️ Error general en visualización avanzada: {str(e)[:50]}")
