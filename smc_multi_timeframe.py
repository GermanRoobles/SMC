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
        # Timeframes soportados por Yahoo Finance - orden correcto para el layout
        self.timeframes = ["1w", "1d", "4h", "1h", "15m"]
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
        """Crear dashboard multi-timeframe - LAYOUT COMPLETO"""
        try:
            # Crear subplots: 3 filas x 2 columnas
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=["Análisis 1W", "Análisis 1D", "Análisis 4H", "Análisis 1H", "Análisis 15M"],
                vertical_spacing=0.15,
                horizontal_spacing=0.1,
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}],
                       [{"colspan": 2, "secondary_y": False}, None]]
            )
            
            # Agregar 1W (fila 1, columna 1)
            if "1w" in analyses:
                df_1w = analyses["1w"]["data"].copy()
                if not df_1w.empty:
                    df_1w = df_1w.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    df_1w = df_1w.reset_index(drop=True)
                    
                    print(f"📊 1W: {len(df_1w)} velas")
                    
                    if len(df_1w) > 0:
                        fig.add_trace(
                            go.Candlestick(
                                x=df_1w['timestamp'],
                                open=df_1w['open'],
                                high=df_1w['high'],
                                low=df_1w['low'],
                                close=df_1w['close'],
                                name="1W",
                                showlegend=False
                            ),
                            row=1, col=1
                        )
            
            # Agregar 1D (fila 1, columna 2)
            if "1d" in analyses:
                df_1d = analyses["1d"]["data"].copy()
                if not df_1d.empty:
                    df_1d = df_1d.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    df_1d = df_1d.reset_index(drop=True)
                    
                    print(f"📊 1D: {len(df_1d)} velas")
                    
                    if len(df_1d) > 0:
                        fig.add_trace(
                            go.Candlestick(
                                x=df_1d['timestamp'],
                                open=df_1d['open'],
                                high=df_1d['high'],
                                low=df_1d['low'],
                                close=df_1d['close'],
                                name="1D",
                                showlegend=False
                            ),
                            row=1, col=2
                        )
            
            # Agregar 4H (fila 2, columna 1)
            if "4h" in analyses:
                df_4h = analyses["4h"]["data"].copy()
                if not df_4h.empty:
                    df_4h = df_4h.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    df_4h = df_4h.reset_index(drop=True)
                    
                    print(f"📊 4H: {len(df_4h)} velas")
                    
                    if len(df_4h) > 0:
                        fig.add_trace(
                            go.Candlestick(
                                x=df_4h['timestamp'],
                                open=df_4h['open'],
                                high=df_4h['high'],
                                low=df_4h['low'],
                                close=df_4h['close'],
                                name="4H",
                                showlegend=False
                            ),
                            row=2, col=1
                        )
            
            # Agregar 1H (fila 2, columna 2)
            if "1h" in analyses:
                df_1h = analyses["1h"]["data"].copy()
                if not df_1h.empty:
                    df_1h = df_1h.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    df_1h = df_1h.reset_index(drop=True)
                    
                    print(f"📊 1H: {len(df_1h)} velas")
                    
                    if len(df_1h) > 0:
                        fig.add_trace(
                            go.Candlestick(
                                x=df_1h['timestamp'],
                                open=df_1h['open'],
                                high=df_1h['high'],
                                low=df_1h['low'],
                                close=df_1h['close'],
                                name="1H",
                                showlegend=False
                            ),
                            row=2, col=2
                        )
            
            # Agregar 15M (fila 3, ocupando ambas columnas)
            if "15m" in analyses:
                df_15m = analyses["15m"]["data"].copy()
                if not df_15m.empty:
                    df_15m = df_15m.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    df_15m = df_15m.reset_index(drop=True)
                    
                    print(f"📊 15M: {len(df_15m)} velas")
                    
                    if len(df_15m) > 0:
                        fig.add_trace(
                            go.Candlestick(
                                x=df_15m['timestamp'],
                                open=df_15m['open'],
                                high=df_15m['high'],
                                low=df_15m['low'],
                                close=df_15m['close'],
                                name="15M",
                                showlegend=False
                            ),
                            row=3, col=1
                        )
            
            # Layout completo
            fig.update_layout(
                title="Multi-Timeframe Analysis Dashboard - LAYOUT COMPLETO",
                height=1000,
                xaxis_rangeslider_visible=False,
                showlegend=False,
                margin=dict(l=50, r=50, t=100, b=50),
                plot_bgcolor='black',
                paper_bgcolor='black'
            )
            
            # Deshabilitar rangeslider para todos los ejes
            for i in range(1, 4):
                for j in range(1, 3):
                    if i == 3 and j == 2:
                        continue  # Skip the empty subplot
                    fig.update_xaxes(rangeslider_visible=False, row=i, col=j)
                    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='darkgray', row=i, col=j)
            
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
def display_multi_timeframe_dashboard(symbol: str = "BTC/USDT", days: int = 3):
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
