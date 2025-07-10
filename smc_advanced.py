#!/usr/bin/env python3
"""
SMC Bot - Implementación completa de funciones avanzadas
======================================================

Implementación completa de todas las funciones de detección
para el bot de Smart Money Concepts Simplified by TJR
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# ==================== FUNCIONES AVANZADAS DE DETECCIÓN ====================

def detect_choch_bos_advanced(df: pd.DataFrame, swings: pd.DataFrame, structure: List[Dict]) -> List[Dict]:
    """
    Detectar cambios de estructura (CHoCH) y rupturas de estructura (BOS) avanzado

    Args:
        df: DataFrame con datos OHLC
        swings: DataFrame con swings detectados
        structure: Lista con puntos de estructura

    Returns:
        Lista con CHoCH y BOS detectados
    """
    choch_bos = []

    if len(structure) < 4:
        return choch_bos

    # Analizar cambios en la estructura
    for i in range(2, len(structure)):
        current = structure[i]
        previous = structure[i-1]
        prev_prev = structure[i-2]

        # CHoCH: Cambio de carácter (de alcista a bajista o viceversa)
        if (prev_prev['type'].value in ['higher_high', 'higher_low'] and
            previous['type'].value in ['lower_low', 'lower_high']):

            choch_bos.append({
                'type': 'CHoCH',
                'direction': 'bearish',
                'price': current['price'],
                'timestamp': current['timestamp'],
                'strength': 'high'
            })

        elif (prev_prev['type'].value in ['lower_low', 'lower_high'] and
              previous['type'].value in ['higher_high', 'higher_low']):

            choch_bos.append({
                'type': 'CHoCH',
                'direction': 'bullish',
                'price': current['price'],
                'timestamp': current['timestamp'],
                'strength': 'high'
            })

        # BOS: Ruptura de estructura (continuación de tendencia)
        elif (prev_prev['type'].value in ['higher_high', 'higher_low'] and
              current['type'].value in ['higher_high', 'higher_low']):

            choch_bos.append({
                'type': 'BOS',
                'direction': 'bullish',
                'price': current['price'],
                'timestamp': current['timestamp'],
                'strength': 'medium'
            })

        elif (prev_prev['type'].value in ['lower_low', 'lower_high'] and
              current['type'].value in ['lower_low', 'lower_high']):

            choch_bos.append({
                'type': 'BOS',
                'direction': 'bearish',
                'price': current['price'],
                'timestamp': current['timestamp'],
                'strength': 'medium'
            })

    return choch_bos

def detect_order_blocks_advanced(df: pd.DataFrame, swings: pd.DataFrame, choch_bos: List[Dict]) -> List[Dict]:
    """
    Detectar Order Blocks (última vela contraria antes de movimiento impulsivo)

    Args:
        df: DataFrame con datos OHLC
        swings: DataFrame con swings detectados
        choch_bos: Lista con CHoCH y BOS detectados

    Returns:
        Lista con Order Blocks detectados
    """
    order_blocks = []

    for event in choch_bos:
        event_timestamp = event['timestamp']
        event_direction = event['direction']

        # Buscar hacia atrás desde el evento
        prior_data = df[df.index < event_timestamp].tail(20)  # Últimas 20 velas

        if len(prior_data) < 5:
            continue

        # Encontrar la última vela contraria antes del movimiento impulsivo
        if event_direction == 'bullish':
            # Buscar última vela bajista (roja) antes del movimiento alcista
            for i in range(len(prior_data)-1, -1, -1):
                row = prior_data.iloc[i]
                if row['close'] < row['open']:  # Vela bajista
                    # Verificar que hay movimiento impulsivo después
                    future_data = df[df.index > prior_data.index[i]].head(10)
                    if len(future_data) > 0:
                        max_high = future_data['high'].max()
                        if max_high > row['high'] * 1.005:  # 0.5% de movimiento mínimo
                            order_blocks.append({
                                'type': 'bullish_ob',
                                'top': row['high'],
                                'bottom': row['low'],
                                'timestamp': prior_data.index[i],
                                'event_timestamp': event_timestamp,
                                'mitigated': False,
                                'strength': 'high' if event['type'] == 'CHoCH' else 'medium'
                            })
                            break

        else:  # bearish
            # Buscar última vela alcista (verde) antes del movimiento bajista
            for i in range(len(prior_data)-1, -1, -1):
                row = prior_data.iloc[i]
                if row['close'] > row['open']:  # Vela alcista
                    # Verificar que hay movimiento impulsivo después
                    future_data = df[df.index > prior_data.index[i]].head(10)
                    if len(future_data) > 0:
                        min_low = future_data['low'].min()
                        if min_low < row['low'] * 0.995:  # 0.5% de movimiento mínimo
                            order_blocks.append({
                                'type': 'bearish_ob',
                                'top': row['high'],
                                'bottom': row['low'],
                                'timestamp': prior_data.index[i],
                                'event_timestamp': event_timestamp,
                                'mitigated': False,
                                'strength': 'high' if event['type'] == 'CHoCH' else 'medium'
                            })
                            break

    # Verificar mitigación de Order Blocks
    for ob in order_blocks:
        ob_timestamp = ob['timestamp']
        future_data = df[df.index > ob_timestamp]

        for idx, row in future_data.iterrows():
            if ob['type'] == 'bullish_ob':
                # OB alcista se mitiga cuando el precio vuelve a la zona
                if row['low'] <= ob['top'] and row['high'] >= ob['bottom']:
                    ob['mitigated'] = True
                    ob['mitigation_timestamp'] = idx
                    break
            else:  # bearish_ob
                # OB bajista se mitiga cuando el precio vuelve a la zona
                if row['low'] <= ob['top'] and row['high'] >= ob['bottom']:
                    ob['mitigated'] = True
                    ob['mitigation_timestamp'] = idx
                    break

    return order_blocks

def detect_fvg_advanced(df: pd.DataFrame, min_size_pct: float = 0.05) -> List[Dict]:
    """
    Detectar Fair Value Gaps entre tres velas consecutivas

    Args:
        df: DataFrame con datos OHLC
        min_size_pct: Tamaño mínimo del FVG como porcentaje del precio

    Returns:
        Lista con FVG detectados
    """
    fvg_zones = []

    for i in range(2, len(df)):
        candle1 = df.iloc[i-2]  # Vela 1
        candle2 = df.iloc[i-1]  # Vela 2 (vela del medio)
        candle3 = df.iloc[i]    # Vela 3

        # FVG Alcista: High de vela 1 < Low de vela 3
        if candle1['high'] < candle3['low']:
            gap_size = candle3['low'] - candle1['high']
            gap_size_pct = gap_size / candle2['close'] * 100

            if gap_size_pct >= min_size_pct:
                fvg_zones.append({
                    'type': 'bullish_fvg',
                    'top': candle3['low'],
                    'bottom': candle1['high'],
                    'timestamp': df.index[i],
                    'size_pct': gap_size_pct,
                    'filled': False,
                    'strength': 'high' if gap_size_pct > 0.2 else 'medium'
                })

        # FVG Bajista: Low de vela 1 > High de vela 3
        elif candle1['low'] > candle3['high']:
            gap_size = candle1['low'] - candle3['high']
            gap_size_pct = gap_size / candle2['close'] * 100

            if gap_size_pct >= min_size_pct:
                fvg_zones.append({
                    'type': 'bearish_fvg',
                    'top': candle1['low'],
                    'bottom': candle3['high'],
                    'timestamp': df.index[i],
                    'size_pct': gap_size_pct,
                    'filled': False,
                    'strength': 'high' if gap_size_pct > 0.2 else 'medium'
                })

    # Verificar llenado de FVG
    for fvg in fvg_zones:
        fvg_timestamp = fvg['timestamp']
        future_data = df[df.index > fvg_timestamp]

        for idx, row in future_data.iterrows():
            if fvg['type'] == 'bullish_fvg':
                # FVG alcista se llena cuando el precio vuelve al gap
                if row['low'] <= fvg['top'] and row['high'] >= fvg['bottom']:
                    fvg['filled'] = True
                    fvg['fill_timestamp'] = idx
                    break
            else:  # bearish_fvg
                # FVG bajista se llena cuando el precio vuelve al gap
                if row['low'] <= fvg['top'] and row['high'] >= fvg['bottom']:
                    fvg['filled'] = True
                    fvg['fill_timestamp'] = idx
                    break

    return fvg_zones

def detect_confirmation_patterns(df: pd.DataFrame, index: int, config) -> Dict:
    """
    Detectar patrones de velas de confirmación mejorados

    Args:
        df: DataFrame con datos OHLC
        index: Índice de la vela a analizar
        config: Configuración SMC con parámetros

    Returns:
        Diccionario con información de confirmación
    """
    if index < 1 or index >= len(df):
        return {'confirmed': False, 'type': None, 'strength': 0}

    current = df.iloc[index]
    previous = df.iloc[index-1]

    # Calcular métricas básicas
    body_size = abs(current['close'] - current['open'])
    total_range = current['high'] - current['low']
    body_pct = body_size / total_range if total_range > 0 else 0

    upper_wick = current['high'] - max(current['open'], current['close'])
    lower_wick = min(current['open'], current['close']) - current['low']

    # 1. BULLISH ENGULFING
    if (hasattr(config, 'enable_engulfing') and config.enable_engulfing and
        current['close'] > current['open'] and
        previous['close'] < previous['open'] and
        current['open'] <= previous['close'] and
        current['close'] >= previous['open']):

        strength = 0.9 if body_pct > 0.8 else 0.7
        return {
            'confirmed': True,
            'type': 'bullish_engulfing',
            'strength': strength,
            'description': 'Engulfing alcista completo'
        }

    # 2. BEARISH ENGULFING
    elif (hasattr(config, 'enable_engulfing') and config.enable_engulfing and
          current['close'] < current['open'] and
          previous['close'] > previous['open'] and
          current['open'] >= previous['close'] and
          current['close'] <= previous['open']):

        strength = 0.9 if body_pct > 0.8 else 0.7
        return {
            'confirmed': True,
            'type': 'bearish_engulfing',
            'strength': strength,
            'description': 'Engulfing bajista completo'
        }

    # 3. HAMMER / PINBAR (Long Lower Wick)
    elif (hasattr(config, 'enable_pinbar') and config.enable_pinbar and
          lower_wick > body_size * getattr(config, 'min_wick_ratio', 2.0) and
          upper_wick < body_size * 0.5 and
          body_pct < 0.4):

        return {
            'confirmed': True,
            'type': 'hammer',
            'strength': 0.85,
            'description': 'Hammer - Rechazo alcista'
        }

    # 4. INVERTED HAMMER / SHOOTING STAR (Long Upper Wick)
    elif (hasattr(config, 'enable_pinbar') and config.enable_pinbar and
          upper_wick > body_size * getattr(config, 'min_wick_ratio', 2.0) and
          lower_wick < body_size * 0.5 and
          body_pct < 0.4):

        return {
            'confirmed': True,
            'type': 'shooting_star',
            'strength': 0.85,
            'description': 'Shooting Star - Rechazo bajista'
        }

    # 5. STRONG BULLISH REJECTION (Large Green Body)
    elif (hasattr(config, 'enable_rejection_wick') and config.enable_rejection_wick and
          current['close'] > current['open'] and
          body_pct > getattr(config, 'min_confirmation_body', 0.6) and
          lower_wick > body_size * 0.5):

        return {
            'confirmed': True,
            'type': 'strong_bullish_rejection',
            'strength': 0.75,
            'description': 'Rechazo alcista fuerte'
        }

    # 6. STRONG BEARISH REJECTION (Large Red Body)
    elif (hasattr(config, 'enable_rejection_wick') and config.enable_rejection_wick and
          current['close'] < current['open'] and
          body_pct > getattr(config, 'min_confirmation_body', 0.6) and
          upper_wick > body_size * 0.5):

        return {
            'confirmed': True,
            'type': 'strong_bearish_rejection',
            'strength': 0.75,
            'description': 'Rechazo bajista fuerte'
        }

    # 7. STRONG DIRECTIONAL MOVE (Simple but effective)
    elif body_pct > getattr(config, 'min_confirmation_body', 0.6):
        if current['close'] > current['open']:
            return {
                'confirmed': True,
                'type': 'strong_bullish',
                'strength': 0.65,
                'description': 'Movimiento alcista fuerte'
            }
        else:
            return {
                'confirmed': True,
                'type': 'strong_bearish',
                'strength': 0.65,
                'description': 'Movimiento bajista fuerte'
            }

    return {
        'confirmed': False,
        'type': None,
        'strength': 0,
        'description': 'Sin confirmación clara'
    }

def calculate_sl_tp_advanced(entry_price: float, signal_type: str, atr: float,
                           min_rr: float = 2.0, order_block: Dict = None,
                           sweep_info: Dict = None, swings: pd.DataFrame = None,
                           use_tjr_method: bool = True) -> Tuple[float, float, float]:
    """
    Calcular Stop Loss y Take Profit - Método TJR vs ATR

    Args:
        entry_price: Precio de entrada
        signal_type: Tipo de señal ('buy' o 'sell')
        atr: Average True Range
        min_rr: Risk-Reward mínimo
        order_block: Order Block usado (para método TJR)
        sweep_info: Información del sweep (para método TJR)
        swings: DataFrame con swings (para método TJR)
        use_tjr_method: Si usar método TJR (True) o ATR (False)

    Returns:
        Tupla con (stop_loss, take_profit, risk_reward)
    """

    # ==================== MÉTODO TJR (RECOMENDADO) ====================
    if use_tjr_method and order_block is not None:
        return calculate_sl_tp_tjr(entry_price, signal_type, order_block,
                                  sweep_info, swings, min_rr)

    # ==================== MÉTODO ATR (FALLBACK) ====================
    # Stop Loss basado en ATR
    sl_distance = atr * 1.5  # 1.5x ATR para SL

    if signal_type == 'buy':
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + (sl_distance * min_rr)
    else:  # sell
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - (sl_distance * min_rr)

    # Calcular R:R real
    if signal_type == 'buy':
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - take_profit

    risk_reward = reward / risk if risk > 0 else 0

    return stop_loss, take_profit, risk_reward

def calculate_sl_tp_tjr(entry_price: float, signal_type: str,
                       order_block: Dict, sweep_info: Dict,
                       swings: pd.DataFrame, min_rr: float = 2.0) -> Tuple[float, float, float]:
    """
    Calcular SL/TP según la estrategia SMC Simplified by TJR

    Args:
        entry_price: Precio de entrada
        signal_type: Tipo de señal ('buy' o 'sell')
        order_block: Información del Order Block usado
        sweep_info: Información del sweep de liquidez
        swings: DataFrame con swing highs/lows
        min_rr: Risk-Reward mínimo

    Returns:
        Tupla con (stop_loss, take_profit, risk_reward)
    """

    if signal_type == 'buy':
        # ==================== LONG POSITION ====================

        # 🛑 STOP LOSS (Zona de invalidación según TJR)
        # Opción 1: Debajo del Order Block (preferido)
        if order_block:
            stop_loss = order_block['bottom'] - (order_block['bottom'] * 0.001)  # Small buffer
        # Opción 2: Debajo del mínimo del sweep
        elif sweep_info and 'sweep_low' in sweep_info:
            stop_loss = sweep_info['sweep_low'] - (sweep_info['sweep_low'] * 0.001)
        else:
            # Fallback: 1% debajo de la entrada
            stop_loss = entry_price * 0.99

        # 🎯 TAKE PROFIT (Objetivo lógico según TJR)
        # Buscar el próximo swing high (HH) como objetivo
        if swings is not None and 'swing_high_price' in swings.columns:
            swing_highs = swings[swings['swing_high'] == True]['swing_high_price']
            swing_highs = swing_highs[swing_highs > entry_price]  # Solo los que están arriba

            if not swing_highs.empty:
                # Usar el swing high más cercano
                take_profit = swing_highs.iloc[0]
            else:
                # Si no hay swing highs, usar R:R fijo
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * min_rr)
        else:
            # Si no hay swings, usar R:R fijo
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * min_rr)

    else:  # sell
        # ==================== SHORT POSITION ====================

        # 🛑 STOP LOSS (Zona de invalidación según TJR)
        # Opción 1: Encima del Order Block (preferido)
        if order_block:
            stop_loss = order_block['top'] + (order_block['top'] * 0.001)  # Small buffer
        # Opción 2: Encima del máximo del sweep
        elif sweep_info and 'sweep_high' in sweep_info:
            stop_loss = sweep_info['sweep_high'] + (sweep_info['sweep_high'] * 0.001)
        else:
            # Fallback: 1% encima de la entrada
            stop_loss = entry_price * 1.01

        # 🎯 TAKE PROFIT (Objetivo lógico según TJR)
        # Buscar el próximo swing low (LL) como objetivo
        if swings is not None and 'swing_low_price' in swings.columns:
            swing_lows = swings[swings['swing_low'] == True]['swing_low_price']
            swing_lows = swing_lows[swing_lows < entry_price]  # Solo los que están abajo

            if not swing_lows.empty:
                # Usar el swing low más cercano
                take_profit = swing_lows.iloc[-1]  # El último (más cercano)
            else:
                # Si no hay swing lows, usar R:R fijo
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * min_rr)
        else:
            # Si no hay swings, usar R:R fijo
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * min_rr)

    # Calcular R:R real
    if signal_type == 'buy':
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - take_profit

    risk_reward = reward / risk if risk > 0 else 0

    return stop_loss, take_profit, risk_reward

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcular Average True Range

    Args:
        df: DataFrame con datos OHLC
        period: Período para el cálculo

    Returns:
        Serie con valores ATR
    """
    high_low = df['high'] - df['low']
    high_close_prev = np.abs(df['high'] - df['close'].shift(1))
    low_close_prev = np.abs(df['low'] - df['close'].shift(1))

    true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
    atr = true_range.rolling(window=period).mean()

    return atr
