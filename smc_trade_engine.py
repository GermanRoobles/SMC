#!/usr/bin/env python3
"""
Motor de Entrada SMC - Estrategia TJR
====================================

Sistema de trading automático que implementa la estrategia TJR (Tom Joseph Ross)
con Smart Money Concepts para generar entradas, stop loss y take profit.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json

class SignalType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class ConfirmationType(Enum):
    ENGULFING = "ENGULFING"
    REJECTION_WICK = "REJECTION_WICK"
    INSIDE_BAR = "INSIDE_BAR"
    HAMMER = "HAMMER"
    DOJI = "DOJI"

@dataclass
class TradeSignal:
    """Estructura de señal de trading"""
    timestamp: datetime
    symbol: str
    timeframe: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float
    setup_components: Dict[str, Any]
    confirmation_type: ConfirmationType

class SMCTradeEngine:
    """Motor de trading SMC con estrategia TJR"""

    def __init__(self, min_rr: float = 2.0, max_risk_percent: float = 1.0):
        self.min_rr = min_rr
        self.max_risk_percent = max_risk_percent
        self.active_signals = []
        self.trade_history = []

    def analyze_for_entry(self, df: pd.DataFrame, smc_analysis: Dict) -> List[TradeSignal]:
        """
        Analizar datos para detectar oportunidades de entrada según TJR
        Si se detecta un gap extremo, solo genera señales conservadoras o ninguna.
        """
        signals = []
        if df.empty or len(df) < 20:
            return signals
        # --- Manejo de gaps extremos ---
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]
        high_low_gap = high - low
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        gap_threshold = atr * 3
        if high_low_gap > gap_threshold:
            print(f"[GAP][WARN] Gap extremo detectado (gap={high_low_gap:.2f}, ATR={atr:.2f}) - Generando señales conservadoras")
            # Estrategia conservadora: no generar señales o solo señales con RR>=3
            return []
        try:
            # 1. Detectar liquidez tomada (sweeps)
            sweeps = self._detect_liquidity_sweeps(df, smc_analysis)

            # 2. Verificar CHoCH/BOS
            structure_breaks = self._detect_structure_breaks(df, smc_analysis)

            # 3. Identificar OB/FVG relevantes
            relevant_zones = self._identify_relevant_zones(df, smc_analysis)

            # 4. Buscar confirmaciones de vela
            confirmations = self._detect_candle_confirmations(df)

            # 5. Combinar condiciones para generar señales
            signals = self._generate_trade_signals(
                df, sweeps, structure_breaks, relevant_zones, confirmations
            )

            # Validar y ajustar SL/TP automáticamente
            from smc_backtester import validate_sl_tp_levels, calculate_adaptive_levels

            signals = []
            for signal in signals:
                report = validate_sl_tp_levels(df, signal.entry_price, signal.stop_loss, signal.take_profit, signal.signal_type.value)
                if report.result != 'VALID':
                    # Ajustar niveles automáticamente si fuera necesario
                    new_sl, new_tp = calculate_adaptive_levels(df, signal.entry_price, signal.signal_type.value)
                    signal.stop_loss = new_sl
                    signal.take_profit = new_tp
                    print(f"[ADJUST] SL/TP ajustados a rango histórico: SL={new_sl}, TP={new_tp}")

            return signals

        except Exception as e:
            print(f"Error en análisis de entrada: {e}")
            return []

    def _detect_liquidity_sweeps(self, df: pd.DataFrame, smc_analysis: Dict) -> List[Dict]:
        """Detectar liquidez tomada (equal highs/lows swept)"""
        sweeps = []

        try:
            # Obtener swing highs y lows
            if 'swing_highs_lows' in smc_analysis:
                swings_data = smc_analysis['swing_highs_lows']

                if not swings_data.empty and 'HighLow' in swings_data.columns:
                    # Detectar equal highs/lows
                    highs = []
                    lows = []

                    for idx, row in swings_data.iterrows():
                        if pd.notna(row['HighLow']):
                            if row['HighLow'] == 1:  # Swing high
                                highs.append({'index': idx, 'level': row['Level']})
                            elif row['HighLow'] == -1:  # Swing low
                                lows.append({'index': idx, 'level': row['Level']})

                    # Buscar equal highs swept
                    for i in range(len(highs) - 1):
                        for j in range(i + 1, len(highs)):
                            high1 = highs[i]
                            high2 = highs[j]

                            # Si son niveles similares (equal highs)
                            if abs(high1['level'] - high2['level']) / high1['level'] < 0.002:  # 0.2% tolerance
                                # Verificar si fue swept (precio fue arriba)
                                max_idx = max(high1['index'], high2['index'])
                                if max_idx < len(df) - 1:
                                    subsequent_high = df['high'].iloc[max_idx + 1:].max()
                                    if subsequent_high > max(high1['level'], high2['level']):
                                        sweeps.append({
                                            'type': 'high_sweep',
                                            'level': max(high1['level'], high2['level']),
                                            'index': max_idx,
                                            'timestamp': df.index[max_idx] if max_idx < len(df) else df.index[-1]
                                        })

                    # Buscar equal lows swept
                    for i in range(len(lows) - 1):
                        for j in range(i + 1, len(lows)):
                            low1 = lows[i]
                            low2 = lows[j]

                            # Si son niveles similares (equal lows)
                            if abs(low1['level'] - low2['level']) / low1['level'] < 0.002:  # 0.2% tolerance
                                # Verificar si fue swept (precio fue abajo)
                                max_idx = max(low1['index'], low2['index'])
                                if max_idx < len(df) - 1:
                                    subsequent_low = df['low'].iloc[max_idx + 1:].min()
                                    if subsequent_low < min(low1['level'], low2['level']):
                                        sweeps.append({
                                            'type': 'low_sweep',
                                            'level': min(low1['level'], low2['level']),
                                            'index': max_idx,
                                            'timestamp': df.index[max_idx] if max_idx < len(df) else df.index[-1]
                                        })

        except Exception as e:
            print(f"Error detectando sweeps: {e}")

        return sweeps

    def _detect_structure_breaks(self, df: pd.DataFrame, smc_analysis: Dict) -> List[Dict]:
        """Detectar CHoCH/BOS confirmados"""
        breaks = []

        try:
            if 'bos_choch' in smc_analysis:
                bos_choch_data = smc_analysis['bos_choch']

                if not bos_choch_data.empty:
                    for idx, row in bos_choch_data.iterrows():
                        if pd.notna(row.get('BOS')):
                            breaks.append({
                                'type': 'BOS',
                                'level': row.get('Level', 0),
                                'index': idx,
                                'timestamp': df.index[idx] if idx < len(df) else df.index[-1]
                            })

                        if pd.notna(row.get('CHOCH')):
                            breaks.append({
                                'type': 'CHOCH',
                                'level': row.get('Level', 0),
                                'index': idx,
                                'timestamp': df.index[idx] if idx < len(df) else df.index[-1]
                            })

        except Exception as e:
            print(f"Error detectando structure breaks: {e}")

        return breaks

    def _identify_relevant_zones(self, df: pd.DataFrame, smc_analysis: Dict) -> List[Dict]:
        """Identificar OB/FVG relevantes para entrada"""
        zones = []

        try:
            # Order Blocks relevantes
            if 'orderblocks' in smc_analysis:
                ob_data = smc_analysis['orderblocks']

                if not ob_data.empty:
                    for idx, row in ob_data.iterrows():
                        if pd.notna(row.get('OB')):
                            zones.append({
                                'type': 'OB',
                                'top': row.get('Top', 0),
                                'bottom': row.get('Bottom', 0),
                                'index': idx,
                                'timestamp': df.index[idx] if idx < len(df) else df.index[-1],
                                'mitigated': pd.notna(row.get('MitigatedIndex'))
                            })

            # FVG relevantes
            if 'fvg' in smc_analysis:
                fvg_data = smc_analysis['fvg']

                if not fvg_data.empty:
                    for idx, row in fvg_data.iterrows():
                        if pd.notna(row.get('FVG')):
                            zones.append({
                                'type': 'FVG',
                                'top': row.get('Top', 0),
                                'bottom': row.get('Bottom', 0),
                                'index': idx,
                                'timestamp': df.index[idx] if idx < len(df) else df.index[-1],
                                'mitigated': pd.notna(row.get('MitigatedIndex'))
                            })

        except Exception as e:
            print(f"Error identificando zonas relevantes: {e}")

        return zones

    def _detect_candle_confirmations(self, df: pd.DataFrame) -> List[Dict]:
        """Detectar patrones de confirmación de vela"""
        confirmations = []

        try:
            for i in range(1, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i-1]

                # Engulfing bullish
                if (current['close'] > current['open'] and  # Vela verde
                    previous['close'] < previous['open'] and  # Vela roja anterior
                    current['open'] < previous['close'] and  # Abre por debajo del cierre anterior
                    current['close'] > previous['open']):    # Cierra por encima de apertura anterior

                    confirmations.append({
                        'type': ConfirmationType.ENGULFING,
                        'direction': 'bullish',
                        'index': i,
                        'timestamp': df.index[i],
                        'strength': self._calculate_engulfing_strength(current, previous)
                    })

                # Engulfing bearish
                elif (current['close'] < current['open'] and  # Vela roja
                      previous['close'] > previous['open'] and  # Vela verde anterior
                      current['open'] > previous['close'] and  # Abre por encima del cierre anterior
                      current['close'] < previous['open']):    # Cierra por debajo de apertura anterior

                    confirmations.append({
                        'type': ConfirmationType.ENGULFING,
                        'direction': 'bearish',
                        'index': i,
                        'timestamp': df.index[i],
                        'strength': self._calculate_engulfing_strength(current, previous)
                    })

                # Rejection wick
                body_size = abs(current['close'] - current['open'])
                upper_wick = current['high'] - max(current['open'], current['close'])
                lower_wick = min(current['open'], current['close']) - current['low']

                # Upper rejection (bearish)
                if upper_wick > body_size * 2 and upper_wick > lower_wick * 2:
                    confirmations.append({
                        'type': ConfirmationType.REJECTION_WICK,
                        'direction': 'bearish',
                        'index': i,
                        'timestamp': df.index[i],
                        'strength': upper_wick / body_size if body_size > 0 else 5
                    })

                # Lower rejection (bullish)
                elif lower_wick > body_size * 2 and lower_wick > upper_wick * 2:
                    confirmations.append({
                        'type': ConfirmationType.REJECTION_WICK,
                        'direction': 'bullish',
                        'index': i,
                        'timestamp': df.index[i],
                        'strength': lower_wick / body_size if body_size > 0 else 5
                    })

        except Exception as e:
            print(f"Error detectando confirmaciones: {e}")

        return confirmations

    def _calculate_engulfing_strength(self, current: pd.Series, previous: pd.Series) -> float:
        """Calcular la fuerza de un patrón engulfing"""
        try:
            current_body = abs(current['close'] - current['open'])
            previous_body = abs(previous['close'] - previous['open'])

            if previous_body > 0:
                return current_body / previous_body
            return 1.0
        except:
            return 1.0

    def _generate_trade_signals(self, df: pd.DataFrame, sweeps: List[Dict],
                               breaks: List[Dict], zones: List[Dict],
                               confirmations: List[Dict]) -> List[TradeSignal]:
        """Generar señales de trading combinando todas las condiciones TJR"""
        signals = []

        try:
            current_price = df['close'].iloc[-1]
            current_time = df.index[-1]

            # Buscar setups LONG
            for sweep in sweeps:
                if sweep['type'] == 'low_sweep':  # Liquidez baja tomada (bullish setup)

                    # Buscar CHoCH/BOS bullish después del sweep
                    for structure_break in breaks:
                        if (structure_break['timestamp'] > sweep['timestamp'] and
                            structure_break['type'] in ['BOS', 'CHOCH']):

                            # Buscar OB/FVG relevante
                            for zone in zones:
                                if (zone['timestamp'] > sweep['timestamp'] and
                                    zone['bottom'] <= current_price <= zone['top'] and
                                    not zone['mitigated']):

                                    # Buscar confirmación de vela bullish
                                    for confirmation in confirmations:
                                        if (confirmation['timestamp'] > zone['timestamp'] and
                                            confirmation['direction'] == 'bullish' and
                                            confirmation['strength'] >= 1.2):

                                            # ¡SETUP COMPLETO! Calcular entrada
                                            signal = self._calculate_long_entry(
                                                df, sweep, zone, confirmation, current_price
                                            )

                                            if signal and signal.risk_reward >= self.min_rr:
                                                signals.append(signal)

            # Buscar setups SHORT
            for sweep in sweeps:
                if sweep['type'] == 'high_sweep':  # Liquidez alta tomada (bearish setup)

                    # Buscar CHoCH/BOS bearish después del sweep
                    for structure_break in breaks:
                        if (structure_break['timestamp'] > sweep['timestamp'] and
                            structure_break['type'] in ['BOS', 'CHOCH']):

                            # Buscar OB/FVG relevante
                            for zone in zones:
                                if (zone['timestamp'] > sweep['timestamp'] and
                                    zone['bottom'] <= current_price <= zone['top'] and
                                    not zone['mitigated']):

                                    # Buscar confirmación de vela bearish
                                    for confirmation in confirmations:
                                        if (confirmation['timestamp'] > zone['timestamp'] and
                                            confirmation['direction'] == 'bearish' and
                                            confirmation['strength'] >= 1.2):

                                            # ¡SETUP COMPLETO! Calcular entrada
                                            signal = self._calculate_short_entry(
                                                df, sweep, zone, confirmation, current_price
                                            )

                                            if signal and signal.risk_reward >= self.min_rr:
                                                signals.append(signal)

        except Exception as e:
            print(f"Error generando señales: {e}")

        return signals

    def _calculate_long_entry(self, df: pd.DataFrame, sweep: Dict, zone: Dict,
                             confirmation: Dict, current_price: float) -> Optional[TradeSignal]:
        """Calcular entrada LONG según estrategia TJR"""
        try:
            # ENTRADA: Precio actual (después de confirmación)
            entry_price = current_price

            # STOP LOSS: Debajo del sweep low o bottom de la zona
            sl_level = min(sweep['level'], zone['bottom'])
            stop_loss = sl_level - (sl_level * 0.001)  # Buffer 0.1%

            # TAKE PROFIT: RR 2:1 o nivel estructural
            risk_distance = abs(entry_price - stop_loss)
            take_profit = entry_price + (risk_distance * self.min_rr)

            # Calcular RR y confianza
            risk_reward = risk_distance / risk_distance if risk_distance > 0 else 0
            risk_reward = self.min_rr  # Forzar RR mínimo

            confidence = self._calculate_signal_confidence(sweep, zone, confirmation)

            return TradeSignal(
                timestamp=confirmation['timestamp'],
                symbol="BTC/USDT",  # TODO: Hacer dinámico
                timeframe="15m",    # TODO: Hacer dinámico
                signal_type=SignalType.LONG,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward=risk_reward,
                confidence=confidence,
                setup_components={
                    'sweep': sweep,
                    'zone': zone,
                    'confirmation': confirmation
                },
                confirmation_type=confirmation['type']
            )

        except Exception as e:
            print(f"Error calculando entrada LONG: {e}")
            return None

    def _calculate_short_entry(self, df: pd.DataFrame, sweep: Dict, zone: Dict,
                              confirmation: Dict, current_price: float) -> Optional[TradeSignal]:
        """Calcular entrada SHORT según estrategia TJR"""
        try:
            # ENTRADA: Precio actual (después de confirmación)
            entry_price = current_price

            # STOP LOSS: Encima del sweep high o top de la zona
            sl_level = max(sweep['level'], zone['top'])
            stop_loss = sl_level + (sl_level * 0.001)  # Buffer 0.1%

            # TAKE PROFIT: RR 2:1 o nivel estructural
            risk_distance = abs(stop_loss - entry_price)
            take_profit = entry_price - (risk_distance * self.min_rr)

            # Calcular RR y confianza
            risk_reward = self.min_rr  # Forzar RR mínimo

            confidence = self._calculate_signal_confidence(sweep, zone, confirmation)

            return TradeSignal(
                timestamp=confirmation['timestamp'],
                symbol="BTC/USDT",  # TODO: Hacer dinámico
                timeframe="15m",    # TODO: Hacer dinámico
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward=risk_reward,
                confidence=confidence,
                setup_components={
                    'sweep': sweep,
                    'zone': zone,
                    'confirmation': confirmation
                },
                confirmation_type=confirmation['type']
            )

        except Exception as e:
            print(f"Error calculando entrada SHORT: {e}")
            return None

    def _calculate_signal_confidence(self, sweep: Dict, zone: Dict, confirmation: Dict) -> float:
        """Calcular confianza de la señal basada en la calidad de los componentes"""
        try:
            confidence = 0.5  # Base

            # Bonus por strength de confirmación
            if confirmation['strength'] >= 2.0:
                confidence += 0.2
            elif confirmation['strength'] >= 1.5:
                confidence += 0.1

            # Bonus por tipo de zona
            if zone['type'] == 'OB':
                confidence += 0.15  # Order blocks más confiables
            else:  # FVG
                confidence += 0.1

            # Bonus por tipo de confirmación
            if confirmation['type'] == ConfirmationType.ENGULFING:
                confidence += 0.15
            elif confirmation['type'] == ConfirmationType.REJECTION_WICK:
                confidence += 0.1

            return min(confidence, 1.0)  # Max 100%

        except Exception as e:
            print(f"Error calculando confianza: {e}")
            return 0.5

# Funciones de utilidad para integración
def get_trade_engine_analysis(df: pd.DataFrame, smc_analysis: Dict) -> Dict:
    """
    Función principal para obtener análisis del motor de trading

    Args:
        df: DataFrame con datos OHLC
        smc_analysis: Análisis SMC completo

    Returns:
        Diccionario con señales de trading y estadísticas
    """
    try:
        engine = SMCTradeEngine(min_rr=2.0, max_risk_percent=1.0)
        signals = engine.analyze_for_entry(df, smc_analysis)

        return {
            'signals': signals,
            'signal_count': len(signals),
            'engine_status': 'active',
            'last_analysis': datetime.now(),
            'settings': {
                'min_rr': engine.min_rr,
                'max_risk_percent': engine.max_risk_percent
            }
        }

    except Exception as e:
        print(f"Error en motor de trading: {e}")
        return {
            'signals': [],
            'signal_count': 0,
            'engine_status': 'error',
            'error': str(e)
        }

# Exportar clases y funciones principales
__all__ = [
    'SMCTradeEngine',
    'TradeSignal',
    'SignalType',
    'ConfirmationType',
    'get_trade_engine_analysis'
]
