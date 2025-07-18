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
from enum import Enum
import json

# Importaciones locales
import smc_analysis

class DataProcessor:
    """Procesador de datos para el análisis SMC"""
    
    @staticmethod
    def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Preparar datos para análisis SMC
        
        Args:
            df: DataFrame con datos OHLC
            
        Returns:
            DataFrame preparado
        """
        try:
            # Validar datos básicos
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"DataFrame debe contener columnas: {required_columns}")
            
            # Limpiar datos
            df_clean = df.copy()
            df_clean = df_clean.dropna()
            
            # Validar que tengamos suficientes datos
            if len(df_clean) < 20:
                raise ValueError("Insuficientes datos para análisis (mínimo 20 velas)")
            
            # Convertir índice a datetime si no lo es
            if not isinstance(df_clean.index, pd.DatetimeIndex):
                df_clean.index = pd.to_datetime(df_clean.index)
            
            return df_clean
            
        except Exception as e:
            st.error(f"Error preparando datos: {str(e)}")
            return pd.DataFrame()

def display_bot_metrics(bot_analysis: Dict):
    """
    Mostrar métricas del bot en la barra lateral

    Args:
        bot_analysis: Análisis del bot SMC
    """
    try:
        st.sidebar.markdown("### 🤖 SMC Bot Analysis")

        # Métricas principales
        col1, col2 = st.sidebar.columns(2)

        with col1:
            # Validar que tenemos tendencia
            trend_value = "N/A"
            if 'trend' in bot_analysis and bot_analysis['trend']:
                if hasattr(bot_analysis['trend'], 'value'):
                    trend_value = bot_analysis['trend'].value.upper()
                else:
                    trend_value = str(bot_analysis['trend']).upper()
            st.metric("📈 Tendencia", trend_value)

            # Contar swings de forma segura
            swing_count = 0
            if 'swings' in bot_analysis:
                swings_data = bot_analysis['swings']
                try:
                    if swings_data is not None and hasattr(swings_data, '__len__'):
                        if isinstance(swings_data, pd.DataFrame):
                            # Es un DataFrame, contar swing_high y swing_low
                            swing_highs = 0
                            swing_lows = 0
                            if 'swing_high' in swings_data.columns:
                                swing_highs = swings_data['swing_high'].notna().sum()
                            if 'swing_low' in swings_data.columns:
                                swing_lows = swings_data['swing_low'].notna().sum()
                            swing_count = swing_highs + swing_lows
                        elif isinstance(swings_data, dict):
                            # Es un diccionario
                            swing_highs = len([s for s in swings_data.get('swing_high', []) if s is not None])
                            swing_lows = len([s for s in swings_data.get('swing_low', []) if s is not None])
                            swing_count = swing_highs + swing_lows
                        else:
                            swing_count = len(swings_data) if swings_data else 0
                except Exception as e:
                    print(f"Error contando swings: {e}")
                    swing_count = 0
            st.metric("🔍 Swings", swing_count)

            # Contar liquidez de forma segura
            liquidity_count = 0
            if 'liquidity_zones' in bot_analysis:
                liquidity_data = bot_analysis['liquidity_zones']
                try:
                    if liquidity_data is not None and hasattr(liquidity_data, '__len__'):
                        if isinstance(liquidity_data, (pd.DataFrame, pd.Series)):
                            liquidity_count = len(liquidity_data) if not liquidity_data.empty else 0
                        else:
                            liquidity_count = len(liquidity_data)
                except Exception as e:
                    print(f"Error contando liquidez: {e}")
                    liquidity_count = 0
            st.metric("💧 Liquidez", liquidity_count)

        with col2:
            # Contar barridos de forma segura
            sweeps_count = 0
            if 'sweeps' in bot_analysis:
                sweeps_data = bot_analysis['sweeps']
                try:
                    if sweeps_data is not None and hasattr(sweeps_data, '__len__'):
                        if isinstance(sweeps_data, (pd.DataFrame, pd.Series)):
                            sweeps_count = len(sweeps_data) if not sweeps_data.empty else 0
                        else:
                            sweeps_count = len(sweeps_data)
                except Exception as e:
                    print(f"Error contando barridos: {e}")
                    sweeps_count = 0
            st.metric("🌊 Barridos", sweeps_count)

            # Contar CHoCH/BOS de forma segura
            choch_count = 0
            if 'choch_bos' in bot_analysis:
                choch_data = bot_analysis['choch_bos']
                try:
                    if choch_data is not None and hasattr(choch_data, '__len__'):
                        if isinstance(choch_data, (pd.DataFrame, pd.Series)):
                            choch_count = len(choch_data) if not choch_data.empty else 0
                        else:
                            choch_count = len(choch_data)
                except Exception as e:
                    print(f"Error contando CHoCH/BOS: {e}")
                    choch_count = 0
            st.metric("🔄 CHoCH/BOS", choch_count)

            # Contar señales de forma segura
            signals_count = 0
            if 'signals' in bot_analysis:
                signals_data = bot_analysis['signals']
                try:
                    if signals_data is not None and hasattr(signals_data, '__len__'):
                        if isinstance(signals_data, (pd.DataFrame, pd.Series)):
                            signals_count = len(signals_data) if not signals_data.empty else 0
                        else:
                            signals_count = len(signals_data)
                except Exception as e:
                    print(f"Error contando señales: {e}")
                    signals_count = 0
            st.metric("🎯 Señales", signals_count)

        # Mostrar señales activas de forma segura
        if 'signals' in bot_analysis:
            signals_data = bot_analysis['signals']
            try:
                # Verificar si tenemos señales válidas
                valid_signals = []
                if signals_data is not None and hasattr(signals_data, '__len__'):
                    if isinstance(signals_data, (pd.DataFrame, pd.Series)):
                        if not signals_data.empty:
                            valid_signals = signals_data.tolist() if hasattr(signals_data, 'tolist') else [signals_data]
                    else:
                        valid_signals = signals_data if signals_data else []

                if valid_signals:
                    st.sidebar.markdown("### 🚨 Señales Activas")

                    for i, signal in enumerate(valid_signals[-3:]):  # Últimas 3 señales
                        try:
                            # Validar tipo de señal
                            signal_type = "BUY"
                            signal_color = "🟢"
                            
                            if hasattr(signal, 'signal_type'):
                                if hasattr(signal.signal_type, 'value'):
                                    signal_type = signal.signal_type.value.upper()
                                else:
                                    signal_type = str(signal.signal_type).upper()
                                signal_color = "🟢" if signal_type == "BUY" else "🔴"

                            # Formatear timestamp de manera segura
                            timestamp_str = "N/A"
                            try:
                                if hasattr(signal, 'timestamp'):
                                    if hasattr(signal.timestamp, 'strftime'):
                                        timestamp_str = signal.timestamp.strftime('%H:%M')
                                    elif isinstance(signal.timestamp, (int, float)):
                                        timestamp_str = f"Índice: {signal.timestamp}"
                            except:
                                timestamp_str = "N/A"

                            # Validar precios antes de mostrar
                            entry_price = getattr(signal, 'entry_price', 0) if hasattr(signal, 'entry_price') else 0
                            stop_loss = getattr(signal, 'stop_loss', 0) if hasattr(signal, 'stop_loss') else 0
                            take_profit = getattr(signal, 'take_profit', 0) if hasattr(signal, 'take_profit') else 0
                            risk_reward = getattr(signal, 'risk_reward', 0) if hasattr(signal, 'risk_reward') else 0
                            confidence = getattr(signal, 'confidence', 0) if hasattr(signal, 'confidence') else 0

                            st.sidebar.markdown(f"""
                            **{signal_color} {signal_type} #{i+1}**
                            - 💰 Entrada: ${entry_price:.2f}
                            - 🛑 SL: ${stop_loss:.2f}
                            - 🎯 TP: ${take_profit:.2f}
                            - 📊 R:R: {risk_reward:.1f}:1
                            - 🔒 Confianza: {confidence:.0%}
                            - ⏰ {timestamp_str}
                            """)
                        except Exception as signal_error:
                            st.sidebar.error(f"Error mostrando señal #{i+1}: {str(signal_error)}")
            except Exception as e:
                st.sidebar.error(f"Error procesando señales: {str(e)}")

        # Información adicional de forma segura
        st.sidebar.markdown("### 📊 Análisis Técnico")

        try:
            order_blocks_count = len(bot_analysis.get('order_blocks', []))
            fvg_zones_count = len(bot_analysis.get('fvg_zones', []))
            atr_value = bot_analysis.get('atr', 0)

            st.sidebar.info(f"""
            **Order Blocks:** {order_blocks_count}
            **FVG Zones:** {fvg_zones_count}
            **ATR Actual:** ${atr_value:.2f}
            """)
        except Exception as e:
            st.sidebar.error(f"Error mostrando análisis técnico: {str(e)}")

    except Exception as e:
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
        # Preparar datos
        data_processor = DataProcessor()
        clean_df = data_processor.prepare_data(df)
        
        if clean_df.empty:
            return {}

        # Inicializar analizador SMC
        analyzer = SMCAnalyzer()
        
        # Realizar análisis completo
        analysis_result = analyzer.analyze(clean_df)
        
        # Estructurar resultado para la aplicación
        bot_analysis = {
            'trend': analysis_result.get('trend', TrendDirection.NEUTRAL),
            'swings': analysis_result.get('swings', {}),
            'liquidity_zones': analysis_result.get('liquidity_zones', []),
            'sweeps': analysis_result.get('sweeps', []),
            'choch_bos': analysis_result.get('choch_bos', []),
            'order_blocks': analysis_result.get('order_blocks', []),
            'fvg_zones': analysis_result.get('fvg_zones', []),
            'signals': analysis_result.get('signals', []),
            'atr': analysis_result.get('atr', 0.0),
            'session_zones': analysis_result.get('session_zones', [])
        }
        
        return bot_analysis
        
    except Exception as e:
        st.error(f"Error en análisis SMC: {str(e)}")
        return {}

def calculate_signal_metrics(signals: List[SMCSignal]) -> Dict[str, float]:
    """
    Calcular métricas de rendimiento de las señales

    Args:
        signals: Lista de señales generadas

    Returns:
        Diccionario con métricas calculadas
    """
    try:
        if not signals:
            return {
                'total_signals': 0,
                'win_rate': 0.0,
                'avg_risk_reward': 0.0,
                'avg_confidence': 0.0
            }

        total_signals = len(signals)
        
        # Calcular win rate (simplificado - en producción se necesitaría seguimiento real)
        win_signals = sum(1 for signal in signals if signal.confidence > 0.7)
        win_rate = (win_signals / total_signals) * 100 if total_signals > 0 else 0
        
        # Promedio de risk/reward
        risk_rewards = [signal.risk_reward for signal in signals if signal.risk_reward > 0]
        avg_risk_reward = np.mean(risk_rewards) if risk_rewards else 0
        
        # Promedio de confianza
        confidences = [signal.confidence for signal in signals]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            'total_signals': total_signals,
            'win_rate': win_rate,
            'avg_risk_reward': avg_risk_reward,
            'avg_confidence': avg_confidence * 100  # Convertir a porcentaje
        }
        
    except Exception as e:
        print(f"Error calculando métricas de señales: {e}")
        return {
            'total_signals': 0,
            'win_rate': 0.0,
            'avg_risk_reward': 0.0,
            'avg_confidence': 0.0
        }

def display_signal_performance(signals: List[SMCSignal]):
    """
    Mostrar rendimiento de las señales en la interfaz

    Args:
        signals: Lista de señales para analizar
    """
    try:
        metrics = calculate_signal_metrics(signals)
        
        st.sidebar.markdown("### 📈 Rendimiento Señales")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric("🎯 Total", metrics['total_signals'])
            st.metric("✅ Win Rate", f"{metrics['win_rate']:.1f}%")
        
        with col2:
            st.metric("📊 R:R Avg", f"{metrics['avg_risk_reward']:.1f}:1")
            st.metric("🔒 Confianza", f"{metrics['avg_confidence']:.0f}%")
            
    except Exception as e:
        st.sidebar.error(f"Error mostrando rendimiento: {str(e)}")

def format_signal_for_display(signal: SMCSignal) -> Dict[str, Any]:
    """
    Formatear señal para mostrar en la interfaz

    Args:
        signal: Señal SMC a formatear

    Returns:
        Diccionario con datos formateados
    """
    try:
        return {
            'type': signal.signal_type.value.upper(),
            'entry': f"${signal.entry_price:.2f}",
            'stop_loss': f"${signal.stop_loss:.2f}",
            'take_profit': f"${signal.take_profit:.2f}",
            'risk_reward': f"{signal.risk_reward:.1f}:1",
            'confidence': f"{signal.confidence:.0%}",
            'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(signal.timestamp, 'strftime') else str(signal.timestamp)
        }
    except Exception as e:
        print(f"Error formateando señal: {e}")
        return {
            'type': 'UNKNOWN',
            'entry': '$0.00',
            'stop_loss': '$0.00',
            'take_profit': '$0.00',
            'risk_reward': '0:1',
            'confidence': '0%',
            'timestamp': 'N/A'
        }

# Exportar funciones principales
__all__ = [
    'DataProcessor',
    'display_bot_metrics',
    'get_smc_bot_analysis',
    'calculate_signal_metrics',
    'display_signal_performance',
    'format_signal_for_display'
]
