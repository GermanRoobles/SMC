#!/usr/bin/env python3
"""
Market Structure Analysis - SMC TradingView
Análisis profundo de estructura de mercado con niveles clave
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

class MarketStructureAnalyzer:
    """Analizador de estructura de mercado para SMC"""
    
    def __init__(self):
        self.structure_levels = {}
        self.trend_changes = []
        self.key_zones = []
        
    def analyze_market_structure(self, df: pd.DataFrame, timeframe: str = "1h") -> Dict:
        """Analizar estructura de mercado completa"""
        try:
            # Análisis SMC básico
            smc_analysis = analyze(df, timeframe)
            
            # Análisis de estructura específico
            structure_analysis = {
                'swing_points': self._identify_swing_points(df),
                'trend_structure': self._analyze_trend_structure(df),
                'key_levels': self._identify_key_levels(df, smc_analysis),
                'support_resistance': self._find_support_resistance(df),
                'breakout_zones': self._identify_breakout_zones(df),
                'accumulation_distribution': self._analyze_accumulation_distribution(df),
                'market_phases': self._identify_market_phases(df),
                'structure_score': self._calculate_structure_score(df, smc_analysis)
            }
            
            return structure_analysis
            
        except Exception as e:
            print(f"❌ Error analizando estructura de mercado: {e}")
            return {}
    
    def _identify_swing_points(self, df: pd.DataFrame) -> List[Dict]:
        """Identificar puntos de swing (highs y lows)"""
        try:
            swing_points = []
            
            # Identificar highs y lows
            for i in range(2, len(df) - 2):
                # Swing High
                if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                    df['high'].iloc[i] > df['high'].iloc[i-2] and
                    df['high'].iloc[i] > df['high'].iloc[i+1] and
                    df['high'].iloc[i] > df['high'].iloc[i+2]):
                    
                    swing_points.append({
                        'type': 'swing_high',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['high'].iloc[i],
                        'index': i,
                        'strength': self._calculate_swing_strength(df, i, 'high')
                    })
                
                # Swing Low
                elif (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                      df['low'].iloc[i] < df['low'].iloc[i-2] and
                      df['low'].iloc[i] < df['low'].iloc[i+1] and
                      df['low'].iloc[i] < df['low'].iloc[i+2]):
                    
                    swing_points.append({
                        'type': 'swing_low',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['low'].iloc[i],
                        'index': i,
                        'strength': self._calculate_swing_strength(df, i, 'low')
                    })
            
            # Ordenar por fuerza
            swing_points.sort(key=lambda x: x['strength'], reverse=True)
            
            return swing_points
            
        except Exception as e:
            print(f"⚠️ Error identificando swing points: {e}")
            return []
    
    def _calculate_swing_strength(self, df: pd.DataFrame, index: int, swing_type: str) -> float:
        """Calcular fuerza de un swing point"""
        try:
            if swing_type == 'high':
                price = df['high'].iloc[index]
                left_min = df['low'].iloc[max(0, index-5):index].min()
                right_min = df['low'].iloc[index+1:min(len(df), index+6)].min()
                
                # Fuerza basada en la diferencia con mínimos cercanos
                strength = (price - left_min) + (price - right_min)
                
            else:  # swing_low
                price = df['low'].iloc[index]
                left_max = df['high'].iloc[max(0, index-5):index].max()
                right_max = df['high'].iloc[index+1:min(len(df), index+6)].max()
                
                # Fuerza basada en la diferencia con máximos cercanos
                strength = (left_max - price) + (right_max - price)
            
            return strength
            
        except Exception as e:
            print(f"⚠️ Error calculando fuerza de swing: {e}")
            return 0.0
    
    def _analyze_trend_structure(self, df: pd.DataFrame) -> Dict:
        """Analizar estructura de tendencia"""
        try:
            # Identificar cambios de tendencia
            trend_changes = []
            current_trend = 'neutral'
            
            # Calcular medias móviles para tendencia
            ma_20 = df['close'].rolling(20).mean()
            ma_50 = df['close'].rolling(50).mean()
            
            for i in range(50, len(df)):
                # Cambio a tendencia alcista
                if (ma_20.iloc[i] > ma_50.iloc[i] and 
                    ma_20.iloc[i-1] <= ma_50.iloc[i-1]):
                    
                    trend_changes.append({
                        'type': 'bullish_break',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'strength': abs(ma_20.iloc[i] - ma_50.iloc[i])
                    })
                    current_trend = 'bullish'
                
                # Cambio a tendencia bajista
                elif (ma_20.iloc[i] < ma_50.iloc[i] and 
                      ma_20.iloc[i-1] >= ma_50.iloc[i-1]):
                    
                    trend_changes.append({
                        'type': 'bearish_break',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'strength': abs(ma_20.iloc[i] - ma_50.iloc[i])
                    })
                    current_trend = 'bearish'
            
            return {
                'current_trend': current_trend,
                'trend_changes': trend_changes,
                'trend_strength': self._calculate_trend_strength(df),
                'trend_duration': self._calculate_trend_duration(df, current_trend)
            }
            
        except Exception as e:
            print(f"⚠️ Error analizando estructura de tendencia: {e}")
            return {}
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calcular fuerza de la tendencia actual"""
        try:
            # Usar RSI para medir fuerza de tendencia
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Fuerza basada en RSI y volatilidad
            current_rsi = rsi.iloc[-1]
            volatility = df['close'].pct_change().std() * np.sqrt(252)
            
            # Normalizar fuerza entre 0 y 1
            strength = min(1.0, (current_rsi / 100) * volatility * 10)
            
            return strength
            
        except Exception as e:
            print(f"⚠️ Error calculando fuerza de tendencia: {e}")
            return 0.5
    
    def _calculate_trend_duration(self, df: pd.DataFrame, current_trend: str) -> int:
        """Calcular duración de la tendencia actual"""
        try:
            if current_trend == 'neutral':
                return 0
            
            # Contar períodos desde el último cambio de tendencia
            duration = 0
            for i in range(len(df) - 1, 0, -1):
                if current_trend == 'bullish':
                    if df['close'].iloc[i] < df['close'].iloc[i-1]:
                        break
                else:  # bearish
                    if df['close'].iloc[i] > df['close'].iloc[i-1]:
                        break
                duration += 1
            
            return duration
            
        except Exception as e:
            print(f"⚠️ Error calculando duración de tendencia: {e}")
            return 0
    
    def _identify_key_levels(self, df: pd.DataFrame, smc_analysis: Dict) -> List[Dict]:
        """Identificar niveles clave de estructura"""
        try:
            key_levels = []
            
            # Agregar FVGs como niveles clave
            if 'fvg' in smc_analysis and isinstance(smc_analysis['fvg'], list) and len(smc_analysis['fvg']) > 0:
                for fvg in smc_analysis['fvg']:
                    if isinstance(fvg, dict) and 'high' in fvg and 'low' in fvg:
                        key_levels.append({
                            'type': 'FVG',
                            'price_high': fvg['high'],
                            'price_low': fvg['low'],
                            'timestamp': fvg.get('start_time', df['timestamp'].iloc[0]),
                            'strength': abs(fvg['high'] - fvg['low']),
                            'direction': 'bullish' if fvg['high'] > fvg['low'] else 'bearish'
                        })
            
            # Agregar Order Blocks como niveles clave
            if 'orderblocks' in smc_analysis and isinstance(smc_analysis['orderblocks'], list) and len(smc_analysis['orderblocks']) > 0:
                for ob in smc_analysis['orderblocks']:
                    if isinstance(ob, dict) and 'high' in ob and 'low' in ob:
                        key_levels.append({
                            'type': 'OrderBlock',
                            'price_high': ob['high'],
                            'price_low': ob['low'],
                            'timestamp': ob.get('start_time', df['timestamp'].iloc[0]),
                            'strength': abs(ob['high'] - ob['low']),
                            'direction': 'bullish' if ob['high'] > ob['low'] else 'bearish'
                        })
            
            # Agregar niveles de soporte/resistencia
            support_resistance = self._find_support_resistance(df)
            key_levels.extend(support_resistance)
            
            # Ordenar por fuerza
            key_levels.sort(key=lambda x: x['strength'], reverse=True)
            
            return key_levels
            
        except Exception as e:
            print(f"⚠️ Error identificando niveles clave: {e}")
            return []
    
    def _find_support_resistance(self, df: pd.DataFrame) -> List[Dict]:
        """Encontrar niveles de soporte y resistencia"""
        try:
            levels = []
            
            # Identificar niveles de soporte (lows significativos)
            for i in range(2, len(df) - 2):
                if (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                    df['low'].iloc[i] < df['low'].iloc[i-2] and
                    df['low'].iloc[i] < df['low'].iloc[i+1] and
                    df['low'].iloc[i] < df['low'].iloc[i+2]):
                    
                    # Verificar si es un nivel de soporte válido
                    touches = 0
                    for j in range(len(df)):
                        if abs(df['low'].iloc[j] - df['low'].iloc[i]) < df['low'].iloc[i] * 0.01:
                            touches += 1
                    
                    if touches >= 2:
                        levels.append({
                            'type': 'Support',
                            'price': df['low'].iloc[i],
                            'timestamp': df['timestamp'].iloc[i],
                            'strength': touches,
                            'touches': touches
                        })
            
            # Identificar niveles de resistencia (highs significativos)
            for i in range(2, len(df) - 2):
                if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                    df['high'].iloc[i] > df['high'].iloc[i-2] and
                    df['high'].iloc[i] > df['high'].iloc[i+1] and
                    df['high'].iloc[i] > df['high'].iloc[i+2]):
                    
                    # Verificar si es un nivel de resistencia válido
                    touches = 0
                    for j in range(len(df)):
                        if abs(df['high'].iloc[j] - df['high'].iloc[i]) < df['high'].iloc[i] * 0.01:
                            touches += 1
                    
                    if touches >= 2:
                        levels.append({
                            'type': 'Resistance',
                            'price': df['high'].iloc[i],
                            'timestamp': df['timestamp'].iloc[i],
                            'strength': touches,
                            'touches': touches
                        })
            
            return levels
            
        except Exception as e:
            print(f"⚠️ Error encontrando soporte/resistencia: {e}")
            return []
    
    def _identify_breakout_zones(self, df: pd.DataFrame) -> List[Dict]:
        """Identificar zonas de breakout"""
        try:
            breakouts = []
            
            # Identificar breakouts de soporte/resistencia
            for i in range(1, len(df)):
                # Breakout alcista
                if (df['close'].iloc[i] > df['high'].iloc[i-1] and
                    df['volume'].iloc[i] > df['volume'].rolling(20).mean().iloc[i]):
                    
                    breakouts.append({
                        'type': 'bullish_breakout',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'volume': df['volume'].iloc[i],
                        'strength': df['volume'].iloc[i] / df['volume'].rolling(20).mean().iloc[i]
                    })
                
                # Breakout bajista
                elif (df['close'].iloc[i] < df['low'].iloc[i-1] and
                      df['volume'].iloc[i] > df['volume'].rolling(20).mean().iloc[i]):
                    
                    breakouts.append({
                        'type': 'bearish_breakout',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'volume': df['volume'].iloc[i],
                        'strength': df['volume'].iloc[i] / df['volume'].rolling(20).mean().iloc[i]
                    })
            
            return breakouts
            
        except Exception as e:
            print(f"⚠️ Error identificando zonas de breakout: {e}")
            return []
    
    def _analyze_accumulation_distribution(self, df: pd.DataFrame) -> Dict:
        """Analizar acumulación y distribución"""
        try:
            # Calcular indicador de acumulación/distribución
            ad_line = 0
            ad_values = []
            
            for i in range(len(df)):
                # Money Flow Multiplier
                mfm = ((df['close'].iloc[i] - df['low'].iloc[i]) - (df['high'].iloc[i] - df['close'].iloc[i])) / (df['high'].iloc[i] - df['low'].iloc[i])
                
                # Money Flow Volume
                mfv = mfm * df['volume'].iloc[i]
                
                ad_line += mfv
                ad_values.append(ad_line)
            
            # Analizar patrones de acumulación/distribución
            recent_ad = ad_values[-20:]
            ad_trend = 'neutral'
            
            if recent_ad[-1] > recent_ad[0] * 1.1:
                ad_trend = 'accumulation'
            elif recent_ad[-1] < recent_ad[0] * 0.9:
                ad_trend = 'distribution'
            
            return {
                'ad_line': ad_values,
                'current_ad': ad_values[-1],
                'ad_trend': ad_trend,
                'accumulation_score': self._calculate_accumulation_score(df)
            }
            
        except Exception as e:
            print(f"⚠️ Error analizando acumulación/distribución: {e}")
            return {}
    
    def _calculate_accumulation_score(self, df: pd.DataFrame) -> float:
        """Calcular score de acumulación"""
        try:
            # Score basado en volumen y precio
            volume_ma = df['volume'].rolling(20).mean()
            price_ma = df['close'].rolling(20).mean()
            
            recent_volume = df['volume'].iloc[-5:].mean()
            recent_price = df['close'].iloc[-5:].mean()
            
            volume_score = recent_volume / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1.0
            price_score = recent_price / price_ma.iloc[-1] if price_ma.iloc[-1] > 0 else 1.0
            
            # Score combinado
            score = (volume_score + price_score) / 2
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            print(f"⚠️ Error calculando score de acumulación: {e}")
            return 0.5
    
    def _identify_market_phases(self, df: pd.DataFrame) -> List[Dict]:
        """Identificar fases del mercado"""
        try:
            phases = []
            
            # Calcular indicadores para identificar fases
            rsi = self._calculate_rsi(df['close'])
            macd = self._calculate_macd(df['close'])
            
            # Identificar fases
            for i in range(50, len(df)):
                current_rsi = rsi.iloc[i]
                current_macd = macd['macd'].iloc[i]
                current_signal = macd['signal'].iloc[i]
                
                # Fase de acumulación
                if current_rsi < 30 and current_macd < current_signal:
                    phases.append({
                        'type': 'accumulation',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'strength': 1 - (current_rsi / 100)
                    })
                
                # Fase de distribución
                elif current_rsi > 70 and current_macd > current_signal:
                    phases.append({
                        'type': 'distribution',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'strength': current_rsi / 100
                    })
                
                # Fase de tendencia alcista
                elif current_rsi > 50 and current_macd > current_signal:
                    phases.append({
                        'type': 'uptrend',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'strength': current_rsi / 100
                    })
                
                # Fase de tendencia bajista
                elif current_rsi < 50 and current_macd < current_signal:
                    phases.append({
                        'type': 'downtrend',
                        'timestamp': df['timestamp'].iloc[i],
                        'price': df['close'].iloc[i],
                        'strength': 1 - (current_rsi / 100)
                    })
            
            return phases
            
        except Exception as e:
            print(f"⚠️ Error identificando fases del mercado: {e}")
            return []
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcular RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception:
            return pd.Series([50] * len(prices))
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calcular MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': macd_line - signal_line
            }
        except Exception:
            return {
                'macd': pd.Series([0] * len(prices)),
                'signal': pd.Series([0] * len(prices)),
                'histogram': pd.Series([0] * len(prices))
            }
    
    def _calculate_structure_score(self, df: pd.DataFrame, smc_analysis: Dict) -> float:
        """Calcular score de estructura de mercado"""
        try:
            score = 0.0
            factors = 0
            
            # Factor 1: Calidad de FVGs
            if 'fvg' in smc_analysis and isinstance(smc_analysis['fvg'], list) and len(smc_analysis['fvg']) > 0:
                fvg_quality = len(smc_analysis['fvg']) / 10  # Normalizar
                score += min(1.0, fvg_quality)
                factors += 1
            
            # Factor 2: Calidad de Order Blocks
            if 'orderblocks' in smc_analysis and isinstance(smc_analysis['orderblocks'], list) and len(smc_analysis['orderblocks']) > 0:
                ob_quality = len(smc_analysis['orderblocks']) / 5  # Normalizar
                score += min(1.0, ob_quality)
                factors += 1
            
            # Factor 3: Volatilidad
            volatility = df['close'].pct_change().std()
            vol_score = min(1.0, volatility * 100)
            score += vol_score
            factors += 1
            
            # Factor 4: Tendencia clara
            trend_structure = self._analyze_trend_structure(df)
            if isinstance(trend_structure, dict) and 'trend_strength' in trend_structure:
                score += trend_structure['trend_strength']
                factors += 1
            
            # Normalizar score
            if factors > 0:
                return score / factors
            else:
                return 0.5
                
        except Exception as e:
            print(f"⚠️ Error calculando score de estructura: {e}")
            return 0.5
    
    def create_market_structure_chart(self, df: pd.DataFrame, structure_analysis: Dict) -> go.Figure:
        """Crear chart de estructura de mercado"""
        try:
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=['Precio y Estructura', 'Niveles Clave', 'Fases del Mercado'],
                vertical_spacing=0.05,
                shared_xaxes=True
            )
            
            # Chart principal
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='OHLC'
                ),
                row=1, col=1
            )
            
            # Agregar niveles clave
            if 'key_levels' in structure_analysis:
                for level in structure_analysis['key_levels'][:10]:  # Top 10
                    color = 'green' if level['type'] in ['FVG', 'Support'] else 'red'
                    fig.add_trace(
                        go.Scatter(
                            x=[df['timestamp'].iloc[0], df['timestamp'].iloc[-1]],
                            y=[level['price_high'], level['price_high']],
                            mode='lines',
                            line=dict(color=color, width=2, dash='dash'),
                            name=f"{level['type']} {level['price_high']:.2f}"
                        ),
                        row=1, col=1
                    )
            
            # Chart de niveles clave
            if 'key_levels' in structure_analysis:
                levels_df = pd.DataFrame(structure_analysis['key_levels'])
                fig.add_trace(
                    go.Scatter(
                        x=levels_df['timestamp'],
                        y=levels_df['price_high'],
                        mode='markers',
                        marker=dict(size=8, color='red'),
                        name='Niveles Clave'
                    ),
                    row=2, col=1
                )
            
            # Chart de fases del mercado
            if 'market_phases' in structure_analysis:
                phases_df = pd.DataFrame(structure_analysis['market_phases'])
                fig.add_trace(
                    go.Scatter(
                        x=phases_df['timestamp'],
                        y=phases_df['price'],
                        mode='markers',
                        marker=dict(size=6, color='blue'),
                        name='Fases del Mercado'
                    ),
                    row=3, col=1
                )
            
            fig.update_layout(
                title="Market Structure Analysis",
                height=800,
                xaxis_rangeslider_visible=False
            )
            
            return fig
            
        except Exception as e:
            print(f"❌ Error creando chart de estructura de mercado: {e}")
            return go.Figure()

def create_market_structure_analyzer() -> MarketStructureAnalyzer:
    """Crear instancia del analizador de estructura de mercado"""
    return MarketStructureAnalyzer()

# Funciones de utilidad para Streamlit
def display_market_structure_analysis(symbol: str = "BTC/USDT", timeframe: str = "1h", days: int = 30):
    """Mostrar análisis de estructura de mercado en Streamlit"""
    try:
        st.header("🔍 Market Structure Analysis")
        
        # Obtener datos
        df = get_ohlcv_extended(symbol, timeframe, days)
        if df is None or df.empty:
            st.error("❌ No se pudieron obtener datos para análisis")
            return
        
        # Crear analizador
        analyzer = create_market_structure_analyzer()
        
        with st.spinner("🔄 Analizando estructura de mercado..."):
            # Realizar análisis
            structure_analysis = analyzer.analyze_market_structure(df, timeframe)
            
            if not structure_analysis:
                st.error("❌ Error en análisis de estructura de mercado")
                return
            
            # Mostrar métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                score = structure_analysis.get('structure_score', 0.5)
                st.metric("Structure Score", f"{score:.2f}")
            
            with col2:
                trend = structure_analysis.get('trend_structure', {}).get('current_trend', 'neutral')
                st.metric("Current Trend", trend.title())
            
            with col3:
                key_levels = len(structure_analysis.get('key_levels', []))
                st.metric("Key Levels", key_levels)
            
            with col4:
                phases = len(structure_analysis.get('market_phases', []))
                st.metric("Market Phases", phases)
            
            # Mostrar chart principal
            st.subheader("📊 Market Structure Chart")
            chart_fig = analyzer.create_market_structure_chart(df, structure_analysis)
            st.plotly_chart(chart_fig, use_container_width=True)
            
            # Mostrar detalles de estructura
            st.subheader("🏗️ Estructura Detallada")
            
            # Swing Points
            if 'swing_points' in structure_analysis:
                st.write("**Swing Points:**")
                swing_df = pd.DataFrame(structure_analysis['swing_points'][:10])
                if not swing_df.empty:
                    st.dataframe(swing_df[['type', 'price', 'strength']].head())
            
            # Key Levels
            if 'key_levels' in structure_analysis:
                st.write("**Niveles Clave:**")
                levels_df = pd.DataFrame(structure_analysis['key_levels'][:10])
                if not levels_df.empty:
                    st.dataframe(levels_df[['type', 'price_high', 'strength']].head())
            
            # Market Phases
            if 'market_phases' in structure_analysis:
                st.write("**Fases del Mercado:**")
                phases_df = pd.DataFrame(structure_analysis['market_phases'][-10:])
                if not phases_df.empty:
                    st.dataframe(phases_df[['type', 'price', 'strength']].head())
            
            st.success("✅ Análisis de estructura de mercado completado")
            
    except Exception as e:
        st.error(f"❌ Error en análisis de estructura de mercado: {e}")

if __name__ == "__main__":
    # Test del módulo
    analyzer = create_market_structure_analyzer()
    df = get_ohlcv_extended("BTC/USDT", "1h", 30)
    if df is not None:
        analysis = analyzer.analyze_market_structure(df, "1h")
        print(f"✅ Análisis de estructura de mercado completado: {len(analysis)} componentes")
