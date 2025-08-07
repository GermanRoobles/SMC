#!/usr/bin/env python3
"""
Multi-Timeframe Analysis Dashboard - SMC TradingView
Análisis comparativo de múltiples timeframes
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import streamlit as st

from fetch_data import get_ohlcv_extended
from smc_analysis import analyze

class MultiTimeframeAnalyzer:
    """Analizador multi-timeframe para SMC"""
    
    def __init__(self):
        # Timeframes soportados por Yahoo Finance
        self.timeframes = ["15m", "1h", "4h", "1d", "1w"]
        self.analysis_cache = {}
        
    def get_multi_timeframe_data(self, symbol: str, days: int = 30) -> Dict[str, pd.DataFrame]:
        """Obtener datos para múltiples timeframes"""
        try:
            data = {}
            
            for tf in self.timeframes:
                # Verificar si el timeframe está soportado
                if not self._is_timeframe_supported(tf):
                    print(f"⚠️ Timeframe {tf} no soportado por Yahoo Finance")
                    continue
                
                # Ajustar días según timeframe
                tf_days = self._adjust_days_for_timeframe(tf, days)
                
                df = get_ohlcv_extended(symbol, tf, tf_days)
                if df is not None and not df.empty:
                    data[tf] = df
                    print(f"✅ Datos obtenidos para {tf}: {len(df)} velas")
                else:
                    print(f"⚠️ No se pudieron obtener datos para {tf} (timeframe no soportado o sin datos)")
            
            return data
            
        except Exception as e:
            print(f"❌ Error obteniendo datos multi-timeframe: {e}")
            return {}
    
    def _adjust_days_for_timeframe(self, timeframe: str, base_days: int) -> int:
        """Ajustar días según timeframe para obtener datos apropiados"""
        adjustments = {
            "15m": min(base_days, 7),    # Limitar a 7 días para evitar demasiadas velas
            "1h": min(base_days * 2, 14),  # Máximo 14 días
            "4h": min(base_days, 30),     # Máximo 30 días
            "1d": min(base_days, 60),     # Máximo 60 días
            "1w": max(base_days // 2, 10)  # Menos datos para timeframes mayores
        }
        return adjustments.get(timeframe, base_days)
    
    def _is_timeframe_supported(self, timeframe: str) -> bool:
        """Verificar si el timeframe está soportado por Yahoo Finance"""
        supported_timeframes = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "4h", "1d", "5d", "1w", "1wk", "1mo", "3mo"]
        return timeframe in supported_timeframes
    
    def analyze_all_timeframes(self, symbol: str, days: int = 30) -> Dict[str, Dict]:
        """Analizar todos los timeframes"""
        try:
            data = self.get_multi_timeframe_data(symbol, days)
            analyses = {}
            
            for tf, df in data.items():
                print(f"🔍 Analizando {tf}...")
                analysis = analyze(df, tf)
                analyses[tf] = {
                    'data': df,
                    'analysis': analysis
                }
                print(f"✅ Análisis {tf} completado")
            
            return analyses
            
        except Exception as e:
            print(f"❌ Error en análisis multi-timeframe: {e}")
            return {}
    
    def create_multi_timeframe_dashboard(self, analyses: Dict[str, Dict]) -> go.Figure:
        """Crear dashboard multi-timeframe"""
        try:
            # Crear subplots para cada timeframe
            fig = make_subplots(
                rows=len(analyses), cols=1,
                subplot_titles=[f"Análisis {tf.upper()}" for tf in analyses.keys()],
                vertical_spacing=0.05,
                shared_xaxes=True
            )
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for i, (tf, analysis_data) in enumerate(analyses.items()):
                df = analysis_data['data']
                analysis = analysis_data['analysis']
                
                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df['timestamp'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=f"{tf} OHLC",
                        showlegend=False
                    ),
                    row=i+1, col=1
                )
                
                # Agregar FVGs
                if 'fvg' in analysis and isinstance(analysis['fvg'], list) and len(analysis['fvg']) > 0:
                    for fvg in analysis['fvg']:
                        fig.add_trace(
                            go.Scatter(
                                x=[fvg['start_time'], fvg['end_time']],
                                y=[fvg['high'], fvg['high']],
                                mode='lines',
                                line=dict(color='green', width=2),
                                name=f"{tf} FVG High",
                                showlegend=False
                            ),
                            row=i+1, col=1
                        )
                        
                        fig.add_trace(
                            go.Scatter(
                                x=[fvg['start_time'], fvg['end_time']],
                                y=[fvg['low'], fvg['low']],
                                mode='lines',
                                line=dict(color='red', width=2),
                                name=f"{tf} FVG Low",
                                showlegend=False
                            ),
                            row=i+1, col=1
                        )
                
                # Agregar Order Blocks
                if 'orderblocks' in analysis and isinstance(analysis['orderblocks'], list) and len(analysis['orderblocks']) > 0:
                    for ob in analysis['orderblocks']:
                        fig.add_trace(
                            go.Scatter(
                                x=[ob['start_time'], ob['end_time']],
                                y=[ob['high'], ob['high']],
                                mode='lines',
                                line=dict(color='blue', width=3),
                                name=f"{tf} OB High",
                                showlegend=False
                            ),
                            row=i+1, col=1
                        )
                        
                        fig.add_trace(
                            go.Scatter(
                                x=[ob['start_time'], ob['end_time']],
                                y=[ob['low'], ob['low']],
                                mode='lines',
                                line=dict(color='blue', width=3),
                                name=f"{tf} OB Low",
                                showlegend=False
                            ),
                            row=i+1, col=1
                        )
            
            # Actualizar layout
            fig.update_layout(
                title="Multi-Timeframe Analysis Dashboard",
                height=300 * len(analyses),
                xaxis_rangeslider_visible=False,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            print(f"❌ Error creando dashboard multi-timeframe: {e}")
            return go.Figure()
    
    def create_timeframe_comparison_chart(self, analyses: Dict[str, Dict]) -> go.Figure:
        """Crear chart de comparación entre timeframes"""
        try:
            fig = go.Figure()
            
            for tf, analysis_data in analyses.items():
                df = analysis_data['data']
                
                # Normalizar precios para comparación
                normalized_close = (df['close'] - df['close'].min()) / (df['close'].max() - df['close'].min())
                
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=normalized_close,
                        mode='lines',
                        name=f"{tf.upper()}",
                        line=dict(width=2)
                    )
                )
            
            fig.update_layout(
                title="Comparación de Timeframes (Precios Normalizados)",
                xaxis_title="Tiempo",
                yaxis_title="Precio Normalizado",
                height=500
            )
            
            return fig
            
        except Exception as e:
            print(f"❌ Error creando comparación de timeframes: {e}")
            return go.Figure()
    
    def create_signal_confirmation_chart(self, analyses: Dict[str, Dict]) -> go.Figure:
        """Crear chart de confirmación de señales multi-timeframe"""
        try:
            fig = go.Figure()
            
            # Analizar señales en cada timeframe
            signals = {}
            
            for tf, analysis_data in analyses.items():
                analysis = analysis_data['analysis']
                signals[tf] = self._extract_signals(analysis, tf)
            
            # Crear matriz de confirmación
            timeframes = list(signals.keys())
            confirmation_matrix = []
            
            for i, tf1 in enumerate(timeframes):
                row = []
                for j, tf2 in enumerate(timeframes):
                    if i == j:
                        row.append(1.0)  # Diagonal
                    else:
                        # Calcular correlación de señales
                        correlation = self._calculate_signal_correlation(signals[tf1], signals[tf2])
                        row.append(correlation)
                confirmation_matrix.append(row)
            
            # Crear heatmap
            fig = px.imshow(
                confirmation_matrix,
                x=timeframes,
                y=timeframes,
                color_continuous_scale='RdYlGn',
                title="Matriz de Confirmación de Señales Multi-Timeframe"
            )
            
            fig.update_layout(height=500)
            
            return fig
            
        except Exception as e:
            print(f"❌ Error creando chart de confirmación: {e}")
            return go.Figure()
    
    def _extract_signals(self, analysis: Dict, timeframe: str) -> List[Dict]:
        """Extraer señales de un análisis"""
        signals = []
        
        # Extraer señales de FVGs
        if 'fvg' in analysis and isinstance(analysis['fvg'], list):
            for fvg in analysis['fvg']:
                if isinstance(fvg, dict) and 'start_time' in fvg and 'high' in fvg and 'low' in fvg:
                    signals.append({
                        'type': 'FVG',
                        'timeframe': timeframe,
                        'timestamp': fvg['start_time'],
                        'price': fvg['high'],
                        'direction': 'bullish' if fvg['high'] > fvg['low'] else 'bearish'
                    })
        
        # Extraer señales de Order Blocks
        if 'orderblocks' in analysis and isinstance(analysis['orderblocks'], list):
            for ob in analysis['orderblocks']:
                if isinstance(ob, dict) and 'start_time' in ob and 'high' in ob and 'low' in ob:
                    signals.append({
                        'type': 'OB',
                        'timeframe': timeframe,
                        'timestamp': ob['start_time'],
                        'price': ob['high'],
                        'direction': 'bullish' if ob['high'] > ob['low'] else 'bearish'
                    })
        
        return signals
    
    def _calculate_signal_correlation(self, signals1: List[Dict], signals2: List[Dict]) -> float:
        """Calcular correlación entre señales de dos timeframes"""
        try:
            if not signals1 or not signals2:
                return 0.0
            
            # Crear series temporales de señales
            timestamps1 = [s['timestamp'] for s in signals1]
            timestamps2 = [s['timestamp'] for s in signals2]
            
            # Encontrar señales cercanas en tiempo
            correlations = []
            
            for signal1 in signals1:
                for signal2 in signals2:
                    time_diff = abs((signal1['timestamp'] - signal2['timestamp']).total_seconds())
                    
                    # Si las señales están dentro de 1 hora
                    if time_diff < 3600:
                        # Calcular correlación basada en dirección
                        if signal1['direction'] == signal2['direction']:
                            correlations.append(1.0)
                        else:
                            correlations.append(-1.0)
            
            if correlations:
                return np.mean(correlations)
            else:
                return 0.0
                
        except Exception as e:
            print(f"⚠️ Error calculando correlación: {e}")
            return 0.0
    
    def get_multi_timeframe_summary(self, analyses: Dict[str, Dict]) -> Dict:
        """Obtener resumen multi-timeframe"""
        try:
            summary = {
                'timeframes_analyzed': len(analyses),
                'total_signals': 0,
                'signal_distribution': {},
                'trend_alignment': {},
                'key_levels': {}
            }
            
            for tf, analysis_data in analyses.items():
                analysis = analysis_data['analysis']
                
                # Contar señales
                signals_count = 0
                if 'fvg' in analysis and isinstance(analysis['fvg'], list):
                    signals_count += len(analysis['fvg'])
                if 'orderblocks' in analysis and isinstance(analysis['orderblocks'], list):
                    signals_count += len(analysis['orderblocks'])
                
                summary['total_signals'] += signals_count
                summary['signal_distribution'][tf] = signals_count
                
                # Analizar tendencia
                if 'market_structure' in analysis and isinstance(analysis['market_structure'], dict):
                    summary['trend_alignment'][tf] = analysis['market_structure'].get('trend', 'neutral')
                else:
                    summary['trend_alignment'][tf] = 'neutral'
                
                # Niveles clave
                key_levels = []
                if 'fvg' in analysis and isinstance(analysis['fvg'], list):
                    for fvg in analysis['fvg']:
                        if isinstance(fvg, dict) and 'high' in fvg:
                            key_levels.append({
                                'type': 'FVG',
                                'price': fvg['high'],
                                'timeframe': tf
                            })
                
                summary['key_levels'][tf] = key_levels
            
            return summary
            
        except Exception as e:
            print(f"❌ Error generando resumen multi-timeframe: {e}")
            return {}

def create_multi_timeframe_analyzer() -> MultiTimeframeAnalyzer:
    """Crear instancia del analizador multi-timeframe"""
    return MultiTimeframeAnalyzer()

# Funciones de utilidad para Streamlit
def display_multi_timeframe_dashboard(symbol: str = "BTC/USDT", days: int = 30):
    """Mostrar dashboard multi-timeframe en Streamlit"""
    try:
        st.header("📊 Multi-Timeframe Analysis Dashboard")
        
        # Crear analizador
        analyzer = create_multi_timeframe_analyzer()
        
        with st.spinner("🔄 Analizando múltiples timeframes..."):
            # Realizar análisis
            analyses = analyzer.analyze_all_timeframes(symbol, days)
            
            if not analyses:
                st.error("❌ No se pudieron obtener datos para análisis multi-timeframe")
                return
            
            # Mostrar resumen
            summary = analyzer.get_multi_timeframe_summary(analyses)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Timeframes Analizados", summary['timeframes_analyzed'])
            with col2:
                st.metric("Total de Señales", summary['total_signals'])
            with col3:
                st.metric("Símbolo", symbol)
            
            # Mostrar distribución de señales
            st.subheader("📈 Distribución de Señales por Timeframe")
            signal_df = pd.DataFrame([
                {'Timeframe': tf, 'Señales': count}
                for tf, count in summary['signal_distribution'].items()
            ])
            st.bar_chart(signal_df.set_index('Timeframe'))
            
            # Mostrar dashboard principal
            st.subheader("📊 Análisis Multi-Timeframe")
            dashboard_fig = analyzer.create_multi_timeframe_dashboard(analyses)
            st.plotly_chart(dashboard_fig, use_container_width=True, key="multi_timeframe_dashboard")
            
            # Mostrar comparación de timeframes
            st.subheader("🔄 Comparación de Timeframes")
            comparison_fig = analyzer.create_timeframe_comparison_chart(analyses)
            st.plotly_chart(comparison_fig, use_container_width=True, key="timeframe_comparison")
            
            # Mostrar matriz de confirmación
            st.subheader("✅ Matriz de Confirmación de Señales")
            confirmation_fig = analyzer.create_signal_confirmation_chart(analyses)
            st.plotly_chart(confirmation_fig, use_container_width=True, key="signal_confirmation")
            
            # Mostrar niveles clave
            st.subheader("🎯 Niveles Clave Multi-Timeframe")
            for tf, levels in summary['key_levels'].items():
                if levels:
                    st.write(f"**{tf.upper()}:**")
                    for level in levels[:5]:  # Mostrar solo los primeros 5
                        st.write(f"  - {level['type']}: ${level['price']:.2f}")
            
            st.success("✅ Análisis multi-timeframe completado")
            
    except Exception as e:
        st.error(f"❌ Error en dashboard multi-timeframe: {e}")

if __name__ == "__main__":
    # Test del módulo
    analyzer = create_multi_timeframe_analyzer()
    analyses = analyzer.analyze_all_timeframes("BTC/USDT", 30)
    print(f"✅ Análisis multi-timeframe completado: {len(analyses)} timeframes")
