#!/usr/bin/env python3
"""
Integración del SMC Bot con Streamlit
====================================

Integración del bot de Smart Money Concepts con la aplicación Streamlit
para análisis en tiempo real y visualización de señales de trading.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json

# Importaciones locales
import smc_analysis

# Mejorar logging de liquidez en integración
import logging
logging.basicConfig(level=logging.INFO)

def display_bot_metrics(bot_analysis: Dict):
    """
    Mostrar métricas del bot en la barra lateral

    Args:
        bot_analysis: Análisis del bot SMC
    """
    try:
        # Calcular métricas consolidadas al inicio para garantizar consistencia
        from app_streamlit import consolidate_smc_metrics
        consolidated_metrics = consolidate_smc_metrics(bot_analysis, bot_analysis)

        # Generar un timestamp único para evitar colisiones de IDs
        import time
        unique_id = int(time.time() * 1000)

        st.sidebar.markdown("### 🤖 SMC Bot Analysis")

        # Métricas principales
        col1, col2 = st.sidebar.columns(2)

        with col1:
            # Validar que tenemos tendencia
            trend_value = "N/A"
            if 'trend' in bot_analysis and bot_analysis['trend']:
                trend_value = str(bot_analysis['trend']).upper()
            st.metric("📈 Tendencia", trend_value)

            # Contar swings de forma segura
            swing_count = 0
            if 'swing_highs_lows' in bot_analysis:
                swings_data = bot_analysis['swing_highs_lows']
                try:
                    if swings_data is not None and not swings_data.empty:
                        # Contar swing highs y lows
                        swing_highs = swings_data['HighLow'].notna().sum() if 'HighLow' in swings_data.columns else 0
                        swing_count = swing_highs
                except Exception as e:
                    print(f"Error contando swings: {e}")
                    swing_count = 0
            st.metric("🔍 Swings", swing_count)

            # Contar liquidez de forma segura
            liquidity_count = 0
            if 'liquidity' in bot_analysis:
                liquidity_data = bot_analysis['liquidity']
                try:
                    if liquidity_data is not None and not liquidity_data.empty:
                        # Contar solo valores válidos en la columna 'Liquidity'
                        if 'Liquidity' in liquidity_data.columns:
                            liquidity_count = liquidity_data['Liquidity'].notna().sum()
                            logging.info(f"[LIQUIDITY] Valores válidos: {liquidity_count}")
                        else:
                            liquidity_count = 0
                except Exception as e:
                    print(f"Error contando liquidez: {e}")
                    liquidity_count = 0
            st.metric("💧 Liquidez", liquidity_count)

        with col2:
            # Usar métricas consolidadas para FVG (consistencia con dashboard)
            fvg_count = consolidated_metrics['fvg_count']
            st.metric("🔹 FVGs", fvg_count)

            # Usar métricas consolidadas para CHoCH/BOS (consistencia con dashboard)
            choch_count = consolidated_metrics['bos_choch_count']
            st.metric("🔄 CHoCH/BOS", choch_count)

            # Usar métricas consolidadas para Order Blocks (consistencia con dashboard)
            ob_count = consolidated_metrics['order_blocks_count']
            st.metric("🟦 Order Blocks", ob_count)

        # Información adicional usando métricas consolidadas
        st.sidebar.markdown("### 📊 Análisis Técnico")

        try:
            st.sidebar.info(f"""
            **Order Blocks:** {consolidated_metrics['order_blocks_count']}
            **FVG Zones:** {consolidated_metrics['fvg_count']}
            **Sesiones:** {len(bot_analysis.get('sessions', {}))}
            """)
        except Exception as e:
            st.sidebar.error(f"Error mostrando análisis técnico: {str(e)}")

    except Exception as e:
        # Generar un timestamp único si no existe
        try:
            unique_id
        except NameError:
            import time
            unique_id = int(time.time() * 1000)

        st.sidebar.error(f"❌ Error en display_bot_metrics: {str(e)}")
        st.sidebar.warning("⚠️ Algunas métricas no están disponibles")

def get_smc_bot_analysis(df: pd.DataFrame) -> Dict:
    """
    Función principal para obtener análisis del bot SMC

    Args:
        df: DataFrame con datos OHLC

    Returns:
        Diccionario con análisis completo del bot
    """
    try:
        # Validar datos básicos
        if df.empty or len(df) < 20:
            return {}

        # Realizar análisis SMC usando el módulo existente
        analysis_result = smc_analysis.analyze(df)

        # Determinar tendencia básica usando precios de cierre
        trend = "NEUTRAL"
        if len(df) >= 20:
            recent_close = df['close'].iloc[-1]
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            if recent_close > sma_20:
                trend = "BULLISH"
            elif recent_close < sma_20:
                trend = "BEARISH"

        # Estructurar resultado para la aplicación
        bot_analysis = {
            'trend': trend,
            'fvg': analysis_result.get('fvg', pd.DataFrame()),
            'orderblocks': analysis_result.get('orderblocks', pd.DataFrame()),
            'bos_choch': analysis_result.get('bos_choch', pd.DataFrame()),
            'liquidity': analysis_result.get('liquidity', pd.DataFrame()),
            'sessions': analysis_result.get('sessions', {}),
            'swing_highs_lows': analysis_result.get('swing_highs_lows', pd.DataFrame())
        }

        return bot_analysis

    except Exception as e:
        st.error(f"Error en análisis SMC: {str(e)}")
        return {}

def add_bot_signals_to_chart(fig, bot_analysis: Dict, df: pd.DataFrame):
    """
    Agregar señales del bot al gráfico (función placeholder)

    Args:
        fig: Figura de Plotly
        bot_analysis: Análisis del bot
        df: DataFrame con datos
    """
    # Esta función es un placeholder para mantener compatibilidad
    # Las señales se agregan desde smc_visualization_advanced.py
    pass

def add_signals_statistics_to_chart(fig, signals: List):
    """
    Agregar estadísticas de señales al gráfico (función placeholder)

    Args:
        fig: Figura de Plotly
        signals: Lista de señales
    """
    # Esta función es un placeholder para mantener compatibilidad
    pass

# Exportar funciones principales
__all__ = [
    'display_bot_metrics',
    'get_smc_bot_analysis',
    'add_bot_signals_to_chart',
    'add_signals_statistics_to_chart'
]
