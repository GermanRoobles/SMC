#!/usr/bin/env python3
"""
Integración del SMC Bot con Streamlit
====================================

Integración del bot de Smart Money Concepts con la        # 6. Calcular entrada, SL y TP usando método TJR
        entry_price = current_row['close']

        # Buscar Order Block relevante
        relevant_ob = None
        for ob in order_blocks:
            if (not ob['mitigated'] and
                current_row['low'] <= ob['top'] and current_row['high'] >= ob['bottom']):
                relevant_ob = ob
                break

        # Buscar sweep relevante
        relevant_sweep = None
        for sweep in sweeps:
            if (current_idx - sweep['timestamp']).total_seconds() / 3600 <= 4:  # Últim            # Contar swings de forma segura
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
                            swing_highs = len([s for s in swings_data.get('swing_high', []) if s])
                            swing_lows = len([s for s in swings_data.get('swing_low', []) if s])
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
            st.metric("💧 Liquidez", liquidity_count) = 0
            if 'swings' in bot_analysis:
                swings_data = bot_analysis['swings']
                try:
                    if isinstance(swings_data, dict):
                        # Si es un diccionario con swing_high y swing_low
                        swing_highs = 0
                        swing_lows = 0

                        if 'swing_high' in swings_data:
                            swing_high_data = swings_data['swing_high']
                            if hasattr(swing_high_data, '__len__'):
                                if isinstance(swing_high_data, pd.Series):
                                    swing_highs = swing_high_data.notna().sum()
                                elif isinstance(swing_high_data, list):
                                    swing_highs = len([s for s in swing_high_data if s])
                                else:
                                    swing_highs = len(swing_high_data) if swing_high_data is not None else 0

                        if 'swing_low' in swings_data:
                            swing_low_data = swings_data['swing_low']
                            if hasattr(swing_low_data, '__len__'):
                                if isinstance(swing_low_data, pd.Series):
                                    swing_lows = swing_low_data.notna().sum()
                                elif isinstance(swing_low_data, list):
                                    swing_lows = len([s for s in swing_low_data if s])
                                else:
                                    swing_lows = len(swing_low_data) if swing_low_data is not None else 0

                        swing_count = swing_highs + swing_lows
                    elif hasattr(swings_data, '__len__'):
                        # Si es una lista o similar
                        swing_count = len(swings_data)
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
            st.metric("💧 Liquidez", liquidity_count)           relevant_sweep = sweep
                break

        try:
            sl, tp, rr = calculate_sl_tp_advanced(
                entry_price,
                signal_type.value,
                atr,
                config.min_rr,
                order_block=relevant_ob,
                sweep_info=relevant_sweep,
                swings=recent_data,  # Pasar datos de swings
                use_tjr_method=True  # Usar método TJR
            )
        except Exception as e:
            print(f"Error en cálculo SL/TP: {e}")
            continueStreamlit
para mostrar señales de trading en tiempo real
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
from fetch_data import get_ohlcv
from smc_bot import SMCBot, SMCConfig, TradingSignal, SignalType
from smc_advanced import (
    detect_choch_bos_advanced,
    detect_order_blocks_advanced,
    detect_fvg_advanced,
    detect_confirmation_patterns,
    calculate_sl_tp_advanced,
    calculate_atr
)

def integrate_smc_bot_with_data(df: pd.DataFrame) -> Dict:
    """
    Integrar el bot SMC con los datos del gráfico

    Args:
        df: DataFrame con datos OHLC

    Returns:
        Diccionario con análisis completo del bot
    """
    # Configurar bot con parámetros mejorados
    config = SMCConfig(
        swing_length=5,              # 5 velas (2 izq + 2 der)
        equal_tolerance=0.075,       # 0.075% tolerancia balanceada
        min_rr=2.0,                 # R:R mínimo 2:1
        risk_per_trade=1.0,
        min_confirmation_body=0.6,
        fvg_min_size=0.05,
        htf_timeframe="4h",         # HTF para estructura
        ltf_timeframe="15m",        # LTF para entrada
        enable_engulfing=True,      # Habilitar engulfing
        enable_pinbar=True,         # Habilitar pinbar/hammer
        enable_rejection_wick=True, # Habilitar rechazo
        min_wick_ratio=2.0         # Ratio mínimo mecha/cuerpo
    )

    # Inicializar bot
    bot = SMCBot(config)

    # Análisis básico
    bot.df = df.copy()
    bot.swings = bot.detect_swings()
    bot.structure = bot.detect_structure()
    bot.trend = bot.determine_trend()
    bot.liquidity_zones = bot.detect_liquidity_zones()
    sweeps = bot.detect_sweeps()

    # Análisis avanzado
    choch_bos = detect_choch_bos_advanced(df, bot.swings, bot.structure)
    order_blocks = detect_order_blocks_advanced(df, bot.swings, choch_bos)
    fvg_zones = detect_fvg_advanced(df, config.fvg_min_size)

    # Calcular ATR para SL/TP
    atr = calculate_atr(df)
    current_atr = atr.iloc[-1] if not atr.empty else df['close'].iloc[-1] * 0.01

    # Generar señales de trading
    signals = generate_trading_signals(
        df, bot.liquidity_zones, sweeps, choch_bos,
        order_blocks, fvg_zones, current_atr, config
    )

    return {
        'bot': bot,
        'trend': bot.trend,
        'swings': bot.swings,
        'structure': bot.structure,
        'liquidity_zones': bot.liquidity_zones,
        'sweeps': sweeps,
        'choch_bos': choch_bos,
        'order_blocks': order_blocks,
        'fvg_zones': fvg_zones,
        'signals': signals,
        'atr': current_atr
    }

def generate_trading_signals(df: pd.DataFrame, liquidity_zones: List, sweeps: List,
                           choch_bos: List, order_blocks: List, fvg_zones: List,
                           atr: float, config: SMCConfig) -> List[TradingSignal]:
    """
    Generar señales de trading basadas en la estrategia SMC completa

    Lógica: Barrida de liquidez + CHoCH + (OB o FVG tocado) + vela de confirmación
    """
    signals = []

    # Verificar que tenemos suficientes datos
    if len(df) < 10:
        return signals

    # Buscar configuraciones de trading en las últimas 10 velas
    recent_data = df.tail(10)

    # Simplificar: buscar señales solo en las últimas 3 velas
    for i in range(max(2, len(recent_data) - 3), len(recent_data)):
        if i >= len(recent_data):
            continue

        current_idx = recent_data.index[i]
        current_row = recent_data.iloc[i]

        # Condiciones simplificadas
        has_liquidity = len(liquidity_zones) > 0
        has_sweep = len(sweeps) > 0
        has_choch = len([event for event in choch_bos if event['type'] == 'CHoCH']) > 0
        has_ob_or_fvg = len(order_blocks) > 0 or len(fvg_zones) > 0

        # Si no hay condiciones básicas, continuar
        if not (has_liquidity and has_sweep and has_choch and has_ob_or_fvg):
            continue

        # Verificar confirmación de vela
        try:
            confirmation = detect_confirmation_patterns(recent_data, i, config)
            if not confirmation['confirmed']:
                continue
        except:
            continue

        # Determinar tipo de señal basado en la tendencia general
        signal_type = None
        confidence = 0.6

        # Análisis simple de tendencia
        if len(recent_data) >= 5:
            trend_up = recent_data.iloc[-1]['close'] > recent_data.iloc[-5]['close']

            if trend_up and confirmation['type'] in ['bullish_engulfing', 'hammer', 'strong_bullish']:
                signal_type = SignalType.BUY
                confidence = 0.7
            elif not trend_up and confirmation['type'] in ['bearish_engulfing', 'shooting_star', 'strong_bearish']:
                signal_type = SignalType.SELL
                confidence = 0.7

        if signal_type is None:
            continue

        # Calcular entrada, SL y TP
        entry_price = current_row['close']

        try:
            sl, tp, rr = calculate_sl_tp_advanced(
                entry_price,
                signal_type.value,
                atr,
                config.min_rr
            )
        except:
            continue

        # Verificar R:R mínimo
        if rr < config.min_rr:
            continue

        # Crear señal
        reason_parts = []
        if has_sweep:
            reason_parts.append("Barrido de liquidez")
        if has_choch:
            reason_parts.append("CHoCH detectado")
        if has_ob_or_fvg:
            reason_parts.append("OB/FVG disponible")
        reason_parts.append(f"Confirmación: {confirmation['type']}")

        signal = TradingSignal(
            signal_type=signal_type,
            entry_price=entry_price,
            stop_loss=sl,
            take_profit=tp,
            risk_reward=rr,
            confidence=confidence,
            reason=" + ".join(reason_parts),
            timestamp=current_idx if hasattr(current_idx, 'strftime') else recent_data.index[i]
        )

        signals.append(signal)

    return signals

def add_bot_signals_to_chart(fig: go.Figure, df: pd.DataFrame, bot_analysis: Dict):
    """
    Añadir las señales del bot al gráfico con estilo TradingView profesional mejorado

    Args:
        fig: Figura de plotly
        df: DataFrame con datos OHLC
        bot_analysis: Análisis del bot SMC
    """
    signals = bot_analysis['signals']

    if not signals:
        return

    print(f"🎯 Añadiendo {len(signals)} señales al gráfico...")

    valid_signals_count = 0

    for i, signal in enumerate(signals):
        # Validar señal antes de procesarla
        is_valid, signal_timestamp, signal_price = validate_signal_data(signal, df)

        if not is_valid:
            print(f"⚠️ Señal #{i+1} no válida, omitiendo...")
            continue

        valid_signals_count += 1

        # Calcular timestamp final para las zonas (definir temprano)
        if isinstance(signal_timestamp, pd.Timestamp):
            end_timestamp = signal_timestamp + pd.Timedelta(hours=4)
        else:
            end_timestamp = signal_timestamp

        # Colores profesionales TradingView
        if signal.signal_type == SignalType.BUY:
            signal_color = '#26A69A'  # Verde TradingView
            signal_color_rgb = (38, 166, 154)
            arrow_symbol = '🚀'
            arrow_direction = 'up'
            sl_color = '#F23645'      # Rojo para SL
            tp_color = '#26A69A'      # Verde para TP
        else:  # SELL
            signal_color = '#EF5350'  # Rojo TradingView
            signal_color_rgb = (239, 83, 80)
            arrow_symbol = '🎯'
            arrow_direction = 'down'
            sl_color = '#F23645'      # Rojo para SL
            tp_color = '#26A69A'      # Verde para TP# ==================== SEÑAL PRINCIPAL MEJORADA ====================

        # Añadir punto de entrada más prominente
        fig.add_trace(
            go.Scatter(
                x=[signal_timestamp],
                y=[signal_price],
                mode='markers+text',
                marker=dict(
                    size=20,
                    color=signal_color,
                    symbol='circle',
                    line=dict(width=3, color='white'),
                    opacity=0.9
                ),
                text=[f"{signal.signal_type.value.upper()}<br>#{i+1}"],
                textposition="middle center",
                textfont=dict(
                    size=10,
                    color="white",
                    family="Arial Black"
                ),
                name=f"Signal {signal.signal_type.value.upper()} #{i+1}",
                showlegend=True,
                hovertemplate=f"<b>🎯 {signal.signal_type.value.upper()} Signal #{i+1}</b><br>" +
                             f"💰 Entry: ${signal.entry_price:.2f}<br>" +
                             f"🛑 Stop Loss: ${signal.stop_loss:.2f}<br>" +
                             f"🎯 Take Profit: ${signal.take_profit:.2f}<br>" +
                             f"📊 R:R: {signal.risk_reward:.2f}:1<br>" +
                             f"🔒 Confidence: {signal.confidence:.1%}<br>" +
                             f"⏰ Time: %{{x}}<br>" +
                             f"💡 Reason: {signal.reason}<extra></extra>"
            )
        )

        # Flecha decorativa adicional
        arrow_y = signal_price * 1.005 if signal.signal_type == SignalType.BUY else signal_price * 0.995
        fig.add_annotation(
            x=signal_timestamp,
            y=arrow_y,
            text=arrow_symbol,
            showarrow=False,
            font=dict(
                size=20,
                color=signal_color,
                family="Arial"
            ),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=signal_color,
            borderwidth=2,
            borderpad=4,
            opacity=0.9
        )

        # Etiqueta de información mejorada
        info_text = f"<b>{signal.signal_type.value.upper()} #{i+1}</b><br>"
        info_text += f"💰 Entry: ${signal.entry_price:.2f}<br>"
        info_text += f"📊 R:R: {signal.risk_reward:.1f}:1<br>"
        info_text += f"🔒 Conf: {signal.confidence:.0%}"

        # Posición de la etiqueta mejorada
        label_x_offset = 60 if signal.signal_type == SignalType.BUY else -60
        label_y_offset = -80 if signal.signal_type == SignalType.BUY else 80

        fig.add_annotation(
            x=signal_timestamp,
            y=signal_price,
            text=info_text,
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor=signal_color,
            ax=label_x_offset,
            ay=label_y_offset,
            font=dict(size=11, color="white", family="Arial"),
            bgcolor=f"rgba{signal_color_rgb + (0.9,)}",
            bordercolor=signal_color,
            borderwidth=2,
            borderpad=10,
            opacity=0.95
        )

        # ==================== STOP LOSS MEJORADO ====================

        # Línea horizontal de SL con estilo profesional mejorado usando add_shape
        fig.add_shape(
            type="line",
            x0=signal_timestamp,
            x1=end_timestamp,
            y0=signal.stop_loss,
            y1=signal.stop_loss,
            line=dict(
                color=sl_color,
                width=3,
                dash="dash"
            ),
            opacity=0.9
        )

        # Anotación para SL
        fig.add_annotation(
            x=end_timestamp,
            y=signal.stop_loss,
            text=f"🛑 SL: ${signal.stop_loss:.2f} (Risk)",
            showarrow=False,
            xanchor="left",
            font=dict(size=12, color="white", family="Arial Bold"),
            bgcolor=sl_color,
            bordercolor="white",
            borderwidth=2,
            borderpad=6
        )

        # Zona de riesgo mejorada
        if signal.signal_type == SignalType.BUY:
            risk_top = signal.entry_price
            risk_bottom = signal.stop_loss
        else:
            risk_top = signal.stop_loss
            risk_bottom = signal.entry_price

        fig.add_shape(
            type="rect",
            x0=signal_timestamp,
            y0=risk_bottom,
            x1=end_timestamp,
            y1=risk_top,
            fillcolor="rgba(242, 54, 69, 0.15)",
            line=dict(color=sl_color, width=1, dash="dot"),
            layer="below",
            opacity=0.8
        )

        # Etiqueta de zona de riesgo
        risk_center_y = (risk_top + risk_bottom) / 2
        # Calcular posición x para la etiqueta
        if isinstance(signal_timestamp, pd.Timestamp):
            label_x = signal_timestamp + pd.Timedelta(hours=2)
        else:
            label_x = signal_timestamp

        fig.add_annotation(
            x=label_x,
            y=risk_center_y,
            text="⚠️ RISK ZONE",
            showarrow=False,
            font=dict(size=11, color="white", family="Arial Black"),
            bgcolor="rgba(242, 54, 69, 0.8)",
            bordercolor="white",
            borderwidth=1,
            borderpad=4,
            opacity=0.9
        )

        # ==================== TAKE PROFIT MEJORADO ====================

        # Línea horizontal de TP con estilo profesional mejorado usando add_shape
        fig.add_shape(
            type="line",
            x0=signal_timestamp,
            x1=end_timestamp,
            y0=signal.take_profit,
            y1=signal.take_profit,
            line=dict(
                color=tp_color,
                width=3,
                dash="dash"
            ),
            opacity=0.9
        )

        # Anotación para TP
        fig.add_annotation(
            x=end_timestamp,
            y=signal.take_profit,
            text=f"🎯 TP: ${signal.take_profit:.2f} (Profit)",
            showarrow=False,
            xanchor="left",
            font=dict(size=12, color="white", family="Arial Bold"),
            bgcolor=tp_color,
            bordercolor="white",
            borderwidth=2,
            borderpad=6
        )

        # Zona de ganancia mejorada
        if signal.signal_type == SignalType.BUY:
            profit_top = signal.take_profit
            profit_bottom = signal.entry_price
        else:
            profit_top = signal.entry_price
            profit_bottom = signal.take_profit

        fig.add_shape(
            type="rect",
            x0=signal_timestamp,
            y0=profit_bottom,
            x1=end_timestamp,
            y1=profit_top,
            fillcolor="rgba(38, 166, 154, 0.15)",
            line=dict(color=tp_color, width=1, dash="dot"),
            layer="below",
            opacity=0.8
        )

        # Etiqueta de zona de ganancia
        profit_center_y = (profit_top + profit_bottom) / 2
        fig.add_annotation(
            x=label_x,
            y=profit_center_y,
            text="💰 PROFIT ZONE",
            showarrow=False,
            font=dict(size=11, color="white", family="Arial Black"),
            bgcolor="rgba(38, 166, 154, 0.8)",
            bordercolor="white",
            borderwidth=1,
            borderpad=4,
            opacity=0.9
        )

        # ==================== LÍNEA DE ENTRADA MEJORADA ====================

        # Línea vertical en el momento de la señal usando add_shape
        fig.add_shape(
            type="line",
            x0=signal_timestamp,
            x1=signal_timestamp,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(
                color=signal_color,
                width=3,
                dash="solid"
            ),
            opacity=0.8
        )

        # Añadir anotación para la línea de entrada
        fig.add_annotation(
            x=signal_timestamp,
            y=signal_price * 1.01,
            text=f"📍 Entry #{valid_signals_count}",
            showarrow=False,
            font=dict(size=11, color="white", family="Arial Bold"),
            bgcolor=signal_color,
            bordercolor="white",
            borderwidth=2,
            borderpad=4
        )

        # Línea horizontal de entrada usando add_shape
        fig.add_shape(
            type="line",
            x0=signal_timestamp,
            x1=end_timestamp,
            y0=signal.entry_price,
            y1=signal.entry_price,
            line=dict(
                color=signal_color,
                width=2,
                dash="solid"
            ),
            opacity=0.9
        )

        # ==================== INFORMACIÓN ADICIONAL MEJORADA ====================

        # Badge mejorado con información de R:R
        rr_color = '#4CAF50' if signal.risk_reward >= 2.0 else '#FF9800'
        rr_text = f"R:R {signal.risk_reward:.1f}:1"
        if signal.risk_reward >= 3.0:
            rr_text += " 🔥"
        elif signal.risk_reward >= 2.0:
            rr_text += " ✅"
        else:
            rr_text += " ⚠️"

        fig.add_annotation(
            x=signal_timestamp,
            y=signal.entry_price + (signal.take_profit - signal.entry_price) * 0.7 if signal.signal_type == SignalType.BUY else signal.entry_price - (signal.entry_price - signal.take_profit) * 0.7,
            text=rr_text,
            showarrow=False,
            font=dict(size=12, color="white", family="Arial Black"),
            bgcolor=rr_color,
            bordercolor="white",
            borderwidth=2,
            borderpad=6,
            opacity=0.95
        )

        # Badge de confianza
        confidence_color = '#4CAF50' if signal.confidence >= 0.8 else '#FF9800' if signal.confidence >= 0.6 else '#F44336'
        confidence_text = f"📊 {signal.confidence:.0%}"
        if signal.confidence >= 0.8:
            confidence_text += " 🌟"
        elif signal.confidence >= 0.6:
            confidence_text += " 👍"
        else:
            confidence_text += " 💡"

        fig.add_annotation(
            x=signal_timestamp,
            y=signal.entry_price + (signal.take_profit - signal.entry_price) * 0.3 if signal.signal_type == SignalType.BUY else signal.entry_price - (signal.entry_price - signal.take_profit) * 0.3,
            text=confidence_text,
            showarrow=False,
            font=dict(size=10, color="white", family="Arial"),
            bgcolor=confidence_color,
            bordercolor="white",
            borderwidth=1,
            borderpad=4,
            opacity=0.9
        )

    print(f"   ✅ {valid_signals_count}/{len(signals)} señales válidas añadidas al gráfico")

def add_signals_statistics_to_chart(fig: go.Figure, bot_analysis: Dict):
    """
    Añadir estadísticas de señales al gráfico con estilo TradingView mejorado

    Args:
        fig: Figura de plotly
        bot_analysis: Análisis del bot SMC
    """
    signals = bot_analysis['signals']

    if not signals:
        return

    # Calcular estadísticas avanzadas
    total_signals = len(signals)
    buy_signals = len([s for s in signals if s.signal_type == SignalType.BUY])
    sell_signals = len([s for s in signals if s.signal_type == SignalType.SELL])
    avg_rr = sum(s.risk_reward for s in signals) / total_signals
    avg_confidence = sum(s.confidence for s in signals) / total_signals

    # Clasificar señales por calidad
    high_quality = len([s for s in signals if s.confidence >= 0.8 and s.risk_reward >= 2.0])
    medium_quality = len([s for s in signals if s.confidence >= 0.6 and s.risk_reward >= 1.5])

    # Crear texto de estadísticas mejorado
    stats_text = f"""<b>🎯 SMC Trading Bot - Live Signals</b><br>
<br>
📊 <b>Signal Overview:</b><br>
• Total Signals: <b>{total_signals}</b><br>
• 🟢 Buy Signals: <b>{buy_signals}</b><br>
• 🔴 Sell Signals: <b>{sell_signals}</b><br>
<br>
📈 <b>Quality Metrics:</b><br>
• Avg R:R: <b>{avg_rr:.2f}:1</b><br>
• Avg Confidence: <b>{avg_confidence:.1%}</b><br>
• 🌟 High Quality: <b>{high_quality}</b><br>
• 👍 Medium Quality: <b>{medium_quality}</b><br>
<br>
💡 <b>Bot Status:</b> <span style="color: #4CAF50;">ACTIVE</span>"""

    # Añadir cuadro de estadísticas principal
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        text=stats_text,
        showarrow=False,
        font=dict(size=12, color="white", family="Arial"),
        bgcolor="rgba(30, 30, 30, 0.95)",
        bordercolor="rgba(38, 166, 154, 0.8)",
        borderwidth=3,
        borderpad=15,
        align="left",
        opacity=0.95
    )

    # Añadir indicador de estado del bot
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        text="🤖 SMC BOT",
        showarrow=False,
        font=dict(size=14, color="white", family="Arial Black"),
        bgcolor="rgba(38, 166, 154, 0.9)",
        bordercolor="white",
        borderwidth=2,
        borderpad=8,
        opacity=0.95
    )

    # Añadir mini-gráfico de distribución de señales
    if total_signals > 0:
        distribution_text = f"""<b>📊 Signal Distribution</b><br>
Buy/Sell Ratio: {buy_signals}/{sell_signals}<br>
Quality Score: {((high_quality + medium_quality) / total_signals):.1%}"""

        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            text=distribution_text,
            showarrow=False,
            font=dict(size=10, color="white", family="Arial"),
            bgcolor="rgba(45, 45, 45, 0.9)",
            bordercolor="rgba(255, 255, 255, 0.3)",
            borderwidth=1,
            borderpad=8,
            align="right",
            opacity=0.9
        )

    # Añadir timestamp del análisis
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M:%S")

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=0.02,
        text=f"🕐 Last Update: {current_time}",
        showarrow=False,
        font=dict(size=10, color="rgba(255, 255, 255, 0.7)", family="Arial"),
        bgcolor="rgba(0, 0, 0, 0.5)",
        bordercolor="rgba(255, 255, 255, 0.2)",
        borderwidth=1,
        borderpad=5,
        opacity=0.8
    )

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
            if 'trend' in bot_analysis and bot_analysis['trend']:
                st.metric("📈 Tendencia", bot_analysis['trend'].value.upper())
            else:
                st.metric("� Tendencia", "N/A")

            # Contar swings de forma segura
            swing_count = 0
            if 'swings' in bot_analysis and bot_analysis['swings']:
                try:
                    swing_highs = len([s for s in bot_analysis['swings']['swing_high'] if s])
                    swing_lows = len([s for s in bot_analysis['swings']['swing_low'] if s])
                    swing_count = swing_highs + swing_lows
                except:
                    swing_count = 0
            st.metric("� Swings", swing_count)

            # Contar liquidez de forma segura
            liquidity_count = 0
            if 'liquidity_zones' in bot_analysis and bot_analysis['liquidity_zones']:
                liquidity_count = len(bot_analysis['liquidity_zones'])
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
                            signal_color = "🟢" if signal.signal_type == SignalType.BUY else "🔴"

                            # Formatear timestamp de manera segura
                            timestamp_str = "N/A"
                            try:
                                if hasattr(signal.timestamp, 'strftime'):
                                    timestamp_str = signal.timestamp.strftime('%H:%M')
                                elif isinstance(signal.timestamp, (int, float)):
                                    timestamp_str = f"Índice: {signal.timestamp}"
                            except:
                                timestamp_str = "N/A"

                            # Validar precios antes de mostrar
                            entry_price = signal.entry_price if hasattr(signal, 'entry_price') and signal.entry_price > 0 else 0
                            stop_loss = signal.stop_loss if hasattr(signal, 'stop_loss') and signal.stop_loss > 0 else 0
                            take_profit = signal.take_profit if hasattr(signal, 'take_profit') and signal.take_profit > 0 else 0
                            risk_reward = signal.risk_reward if hasattr(signal, 'risk_reward') and signal.risk_reward > 0 else 0
                            confidence = signal.confidence if hasattr(signal, 'confidence') else 0

                            st.sidebar.markdown(f"""
                            **{signal_color} {signal.signal_type.value.upper()} #{i+1}**
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

# Función para integrar con la aplicación principal
def get_smc_bot_analysis(df: pd.DataFrame) -> Dict:
    """
    Función principal para obtener análisis del bot SMC

    Args:
        df: DataFrame con datos OHLC

    Returns:
        Diccionario con análisis completo
    """
    return integrate_smc_bot_with_data(df)

def validate_signal_data(signal, df):
    """
    Validar que una señal tiene datos válidos para ser añadida al gráfico

    Args:
        signal: TradingSignal a validar
        df: DataFrame con datos OHLC

    Returns:
        tuple: (es_valida, timestamp, precio)
    """
    try:
        # Validar precios básicos
        if not all([signal.entry_price > 0, signal.stop_loss > 0, signal.take_profit > 0]):
            return False, None, None

        # Validar timestamp
        signal_timestamp = None
        signal_price = signal.entry_price

        if hasattr(signal.timestamp, 'strftime'):
            signal_timestamp = signal.timestamp
        elif isinstance(signal.timestamp, (int, float)):
            signal_idx = int(signal.timestamp)
            if 0 <= signal_idx < len(df):
                signal_timestamp = df.iloc[signal_idx]['timestamp']
                signal_price = df.iloc[signal_idx]['close']
            else:
                return False, None, None
        else:
            return False, None, None

        # Validar que el timestamp está en el rango de datos
        if isinstance(signal_timestamp, pd.Timestamp):
            min_time = df['timestamp'].min()
            max_time = df['timestamp'].max()
            if not (min_time <= signal_timestamp <= max_time):
                return False, None, None

        # Validar risk/reward
        if signal.risk_reward <= 0:
            return False, None, None

        return True, signal_timestamp, signal_price

    except Exception as e:
        print(f"❌ Error validando señal: {e}")
        return False, None, None
