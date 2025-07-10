#!/usr/bin/env python3
"""
Cálculo de SL/TP según estrategia SMC Simplified by TJR
====================================================

Implementación correcta del cálculo de Stop Loss y Take Profit
basado en la lógica de estructura del mercado según TJR.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

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

        # 🛑 STOP LOSS (Zona de invalidación)
        # Opción 1: Debajo del Order Block (preferido)
        if order_block:
            stop_loss = order_block['bottom'] - (order_block['bottom'] * 0.001)  # Small buffer
        # Opción 2: Debajo del mínimo del sweep
        elif sweep_info:
            stop_loss = sweep_info['sweep_low'] - (sweep_info['sweep_low'] * 0.001)
        else:
            # Fallback: 1% debajo de la entrada
            stop_loss = entry_price * 0.99

        # 🎯 TAKE PROFIT (Objetivo lógico)
        # Buscar el próximo swing high (HH) como objetivo
        swing_highs = swings[swings['swing_high'] == True]['swing_high_price']
        swing_highs = swing_highs[swing_highs > entry_price]  # Solo los que están arriba

        if not swing_highs.empty:
            # Usar el swing high más cercano
            take_profit = swing_highs.iloc[0]
        else:
            # Si no hay swing highs, usar R:R fijo
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * min_rr)

    else:  # sell
        # ==================== SHORT POSITION ====================

        # 🛑 STOP LOSS (Zona de invalidación)
        # Opción 1: Encima del Order Block (preferido)
        if order_block:
            stop_loss = order_block['top'] + (order_block['top'] * 0.001)  # Small buffer
        # Opción 2: Encima del máximo del sweep
        elif sweep_info:
            stop_loss = sweep_info['sweep_high'] + (sweep_info['sweep_high'] * 0.001)
        else:
            # Fallback: 1% encima de la entrada
            stop_loss = entry_price * 1.01

        # 🎯 TAKE PROFIT (Objetivo lógico)
        # Buscar el próximo swing low (LL) como objetivo
        swing_lows = swings[swings['swing_low'] == True]['swing_low_price']
        swing_lows = swing_lows[swing_lows < entry_price]  # Solo los que están abajo

        if not swing_lows.empty:
            # Usar el swing low más cercano
            take_profit = swing_lows.iloc[-1]  # El último (más cercano)
        else:
            # Si no hay swing lows, usar R:R fijo
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

def calculate_sl_tp_tjr_advanced(entry_price: float, signal_type: str,
                                order_block: Dict, sweep_info: Dict,
                                swings: pd.DataFrame, liquidity_zones: List[Dict],
                                fvg_zones: List[Dict], min_rr: float = 2.0) -> Tuple[float, float, float]:
    """
    Cálculo avanzado de SL/TP con múltiples opciones según TJR

    Args:
        entry_price: Precio de entrada
        signal_type: Tipo de señal ('buy' o 'sell')
        order_block: Order Block usado para la entrada
        sweep_info: Información del sweep
        swings: Swing highs/lows
        liquidity_zones: Zonas de liquidez
        fvg_zones: Fair Value Gaps
        min_rr: Risk-Reward mínimo

    Returns:
        Tupla con (stop_loss, take_profit, risk_reward)
    """

    if signal_type == 'buy':
        # ==================== LONG POSITION ====================

        # 🛑 STOP LOSS - Lógica de invalidación TJR
        stop_loss_options = []

        # Opción 1: Debajo del Order Block (más conservador)
        if order_block:
            stop_loss_options.append(order_block['bottom'] - (order_block['bottom'] * 0.0005))

        # Opción 2: Debajo del sweep low (más agresivo)
        if sweep_info and 'sweep_low' in sweep_info:
            stop_loss_options.append(sweep_info['sweep_low'] - (sweep_info['sweep_low'] * 0.0005))

        # Seleccionar el SL más conservador (más alto)
        stop_loss = max(stop_loss_options) if stop_loss_options else entry_price * 0.99

        # 🎯 TAKE PROFIT - Múltiples opciones TJR
        take_profit_options = []

        # Opción 1: Próximo swing high (HH)
        swing_highs = swings[swings['swing_high'] == True]['swing_high_price']
        future_highs = swing_highs[swing_highs > entry_price]
        if not future_highs.empty:
            take_profit_options.append(future_highs.iloc[0])

        # Opción 2: Próxima zona de liquidez arriba (equal highs)
        for zone in liquidity_zones:
            if zone['type'] == 'equal_highs' and zone['price'] > entry_price:
                take_profit_options.append(zone['price'])
                break

        # Opción 3: Próximo FVG bajista (resistencia)
        for fvg in fvg_zones:
            if fvg['type'] == 'bearish_fvg' and fvg['bottom'] > entry_price:
                take_profit_options.append(fvg['bottom'])
                break

        # Seleccionar el TP más cercano (más conservador)
        if take_profit_options:
            take_profit = min(take_profit_options)
        else:
            # Si no hay objetivos lógicos, usar R:R fijo
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * min_rr)

    else:  # sell
        # ==================== SHORT POSITION ====================

        # 🛑 STOP LOSS - Lógica de invalidación TJR
        stop_loss_options = []

        # Opción 1: Encima del Order Block (más conservador)
        if order_block:
            stop_loss_options.append(order_block['top'] + (order_block['top'] * 0.0005))

        # Opción 2: Encima del sweep high (más agresivo)
        if sweep_info and 'sweep_high' in sweep_info:
            stop_loss_options.append(sweep_info['sweep_high'] + (sweep_info['sweep_high'] * 0.0005))

        # Seleccionar el SL más conservador (más bajo)
        stop_loss = min(stop_loss_options) if stop_loss_options else entry_price * 1.01

        # 🎯 TAKE PROFIT - Múltiples opciones TJR
        take_profit_options = []

        # Opción 1: Próximo swing low (LL)
        swing_lows = swings[swings['swing_low'] == True]['swing_low_price']
        future_lows = swing_lows[swing_lows < entry_price]
        if not future_lows.empty:
            take_profit_options.append(future_lows.iloc[-1])

        # Opción 2: Próxima zona de liquidez abajo (equal lows)
        for zone in liquidity_zones:
            if zone['type'] == 'equal_lows' and zone['price'] < entry_price:
                take_profit_options.append(zone['price'])
                break

        # Opción 3: Próximo FVG alcista (soporte)
        for fvg in fvg_zones:
            if fvg['type'] == 'bullish_fvg' and fvg['top'] < entry_price:
                take_profit_options.append(fvg['top'])
                break

        # Seleccionar el TP más cercano (más conservador)
        if take_profit_options:
            take_profit = max(take_profit_options)
        else:
            # Si no hay objetivos lógicos, usar R:R fijo
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

def validate_sl_tp_tjr(entry_price: float, stop_loss: float, take_profit: float,
                      signal_type: str, min_rr: float = 1.5) -> bool:
    """
    Validar que el SL/TP cumple con los criterios TJR

    Args:
        entry_price: Precio de entrada
        stop_loss: Stop Loss calculado
        take_profit: Take Profit calculado
        signal_type: Tipo de señal
        min_rr: Risk-Reward mínimo

    Returns:
        True si la configuración SL/TP es válida
    """

    # Validar que SL y TP están en la dirección correcta
    if signal_type == 'buy':
        if stop_loss >= entry_price or take_profit <= entry_price:
            return False
    else:  # sell
        if stop_loss <= entry_price or take_profit >= entry_price:
            return False

    # Validar R:R mínimo
    if signal_type == 'buy':
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - take_profit

    if risk <= 0 or reward <= 0:
        return False

    risk_reward = reward / risk

    return risk_reward >= min_rr

def get_sl_tp_explanation(entry_price: float, stop_loss: float, take_profit: float,
                         signal_type: str, order_block: Dict, sweep_info: Dict) -> str:
    """
    Generar explicación del cálculo SL/TP según TJR

    Returns:
        Explicación textual del cálculo
    """

    if signal_type == 'buy':
        sl_reason = "Debajo del Order Block" if order_block else "Debajo del sweep low"
        tp_reason = "Próximo swing high"
    else:
        sl_reason = "Encima del Order Block" if order_block else "Encima del sweep high"
        tp_reason = "Próximo swing low"

    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    rr = reward / risk if risk > 0 else 0

    explanation = f"""
📊 CÁLCULO SL/TP SEGÚN TJR:
   💰 Entrada: ${entry_price:.2f}
   🛑 SL: ${stop_loss:.2f} ({sl_reason})
   🎯 TP: ${take_profit:.2f} ({tp_reason})
   📈 Riesgo: ${risk:.2f}
   📈 Recompensa: ${reward:.2f}
   📊 R:R: {rr:.2f}:1
   ✅ Lógica: Estructura del mercado SMC
    """

    return explanation
