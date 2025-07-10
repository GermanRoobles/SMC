#!/usr/bin/env python3
"""
Visualización Histórica SMC Bot - Versión Mejorada
=================================================

Este módulo proporciona funcionalidades avanzadas para visualizar el histórico
de señales e indicadores SMC en el gráfico de TradingView con navegación mejorada.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

from smc_historical import SMCHistoricalManager, HistoricalSnapshot, HistoricalPeriod
from smc_integration import add_bot_signals_to_chart, add_signals_statistics_to_chart
from smc_bot import SignalType

class HistoricalVisualizer:
    """
    Visualizador histórico para SMC Bot - Versión Mejorada
    """

    def __init__(self, manager: SMCHistoricalManager):
        self.manager = manager
        self.current_snapshot_index = 0
        self.playback_speed = 1.0
        self.is_playing = False
        self.auto_update_chart = True
        self.highlight_current_time = True
        self.show_time_zones = True

    def create_enhanced_historical_controls(self) -> Dict:
        """
        Crear controles de navegación histórica mejorados

        Returns:
            Dict con información del estado actual
        """
        if not self.manager.snapshots:
            st.warning("⚠️ No hay snapshots históricos disponibles")
            return {}

        # Contenedor principal para controles
        with st.container():
            st.markdown("### ⏰ Navegación Histórica Mejorada")

            # Información del snapshot actual
            current_snapshot = self.get_current_snapshot()
            if current_snapshot:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📅 Momento Actual",
                             current_snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                with col2:
                    st.metric("📊 Señales", len(current_snapshot.signals))
                with col3:
                    st.metric("🎯 Posición", f"{self.current_snapshot_index + 1} / {len(self.manager.snapshots)}")

            # Controles de navegación principal
            st.markdown("#### 🎮 Controles de Navegación")

            # Fila 1: Navegación básica
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("⏮️ Primero", help="Ir al primer snapshot"):
                    self.current_snapshot_index = 0
                    st.rerun()

            with col2:
                if st.button("⏪ Anterior", help="Snapshot anterior"):
                    if self.current_snapshot_index > 0:
                        self.current_snapshot_index -= 1
                        st.rerun()

            with col3:
                if st.button("⏸️ Pausar" if self.is_playing else "▶️ Reproducir",
                           help="Reproducir/pausar navegación automática"):
                    self.is_playing = not self.is_playing
                    st.rerun()

            with col4:
                if st.button("⏩ Siguiente", help="Próximo snapshot"):
                    if self.current_snapshot_index < len(self.manager.snapshots) - 1:
                        self.current_snapshot_index += 1
                        st.rerun()

            with col5:
                if st.button("⏭️ Último", help="Ir al último snapshot"):
                    self.current_snapshot_index = len(self.manager.snapshots) - 1
                    st.rerun()

            # Fila 2: Navegación por slider
            st.markdown("#### 🎚️ Navegación por Timeline")

            if len(self.manager.snapshots) > 1:
                # Crear etiquetas para el slider
                snapshot_labels = []
                for i, snapshot in enumerate(self.manager.snapshots):
                    timestamp_str = snapshot.timestamp.strftime('%m/%d %H:%M')
                    signals_count = len(snapshot.signals)
                    snapshot_labels.append(f"{timestamp_str} ({signals_count}🎯)")

                # Slider principal
                new_index = st.slider(
                    "📅 Seleccionar momento histórico:",
                    min_value=0,
                    max_value=len(self.manager.snapshots) - 1,
                    value=self.current_snapshot_index,
                    step=1,
                    format="%d",
                    help="Desliza para navegar por el histórico"
                )

                # Actualizar si cambió
                if new_index != self.current_snapshot_index:
                    self.current_snapshot_index = new_index
                    st.rerun()

                # Mostrar etiqueta del snapshot actual
                if 0 <= self.current_snapshot_index < len(snapshot_labels):
                    st.info(f"📍 **{snapshot_labels[self.current_snapshot_index]}**")

            # Fila 3: Controles avanzados
            st.markdown("#### ⚙️ Configuración Avanzada")

            col1, col2 = st.columns(2)

            with col1:
                # Velocidad de reproducción
                self.playback_speed = st.selectbox(
                    "🚀 Velocidad de Reproducción:",
                    [0.5, 1.0, 1.5, 2.0, 3.0],
                    index=1,
                    help="Velocidad para reproducción automática"
                )

                # Opciones de visualización
                self.highlight_current_time = st.checkbox(
                    "🔆 Resaltar Tiempo Actual",
                    value=self.highlight_current_time,
                    help="Marcar línea temporal actual"
                )

            with col2:
                # Saltos temporales
                jump_options = [
                    ("1 Hora", timedelta(hours=1)),
                    ("4 Horas", timedelta(hours=4)),
                    ("12 Horas", timedelta(hours=12)),
                    ("1 Día", timedelta(days=1)),
                    ("3 Días", timedelta(days=3)),
                    ("1 Semana", timedelta(weeks=1))
                ]

                selected_jump = st.selectbox(
                    "⏰ Salto Temporal:",
                    jump_options,
                    format_func=lambda x: x[0],
                    help="Saltar hacia adelante/atrás en el tiempo"
                )

                # Botones de salto
                col_back, col_forward = st.columns(2)

                with col_back:
                    if st.button("⏪ Saltar Atrás", help=f"Retroceder {selected_jump[0]}"):
                        self._jump_time(-selected_jump[1])
                        st.rerun()

                with col_forward:
                    if st.button("⏩ Saltar Adelante", help=f"Avanzar {selected_jump[0]}"):
                        self._jump_time(selected_jump[1])
                        st.rerun()

            # Fila 4: Marcadores temporales
            st.markdown("#### 🏷️ Marcadores Rápidos")

            if len(self.manager.snapshots) > 5:
                # Crear marcadores automáticos
                markers = self._create_time_markers()

                marker_cols = st.columns(len(markers))

                for i, (marker_label, marker_index) in enumerate(markers.items()):
                    with marker_cols[i]:
                        if st.button(f"📍 {marker_label}",
                                   help=f"Saltar a {marker_label}"):
                            self.current_snapshot_index = marker_index
                            st.rerun()

            # Información adicional
            st.markdown("#### 📊 Información del Período")

            if self.manager.snapshots:
                start_time = self.manager.snapshots[0].timestamp
                end_time = self.manager.snapshots[-1].timestamp
                duration = end_time - start_time

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.info(f"**🕐 Inicio:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

                with col2:
                    st.info(f"**🕘 Fin:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

                with col3:
                    st.info(f"**⏱️ Duración:** {str(duration).split('.')[0]}")

        return {
            'current_snapshot': current_snapshot,
            'position': self.current_snapshot_index,
            'total': len(self.manager.snapshots),
            'is_playing': self.is_playing,
            'speed': self.playback_speed
        }

    def _create_time_markers(self) -> Dict[str, int]:
        """
        Crear marcadores temporales automáticos

        Returns:
            Dict con marcadores y sus índices
        """
        if not self.manager.snapshots:
            return {}

        markers = {}
        total_snapshots = len(self.manager.snapshots)

        # Marcadores por posición
        markers["Inicio"] = 0
        markers["25%"] = max(0, int(total_snapshots * 0.25))
        markers["50%"] = max(0, int(total_snapshots * 0.5))
        markers["75%"] = max(0, int(total_snapshots * 0.75))
        markers["Final"] = total_snapshots - 1

        # Marcadores por señales (snapshots con más señales)
        signal_counts = [(i, len(snapshot.signals))
                        for i, snapshot in enumerate(self.manager.snapshots)]
        signal_counts.sort(key=lambda x: x[1], reverse=True)

        # Añadir los 2 snapshots con más señales
        if len(signal_counts) >= 2:
            markers["🎯 Max Señales"] = signal_counts[0][0]
            if signal_counts[1][1] > 0:
                markers["🎯 2da Max"] = signal_counts[1][0]

        return markers

    def _jump_time(self, delta: timedelta):
        """
        Saltar en el tiempo por un delta específico

        Args:
            delta: Delta de tiempo para saltar
        """
        if not self.manager.snapshots:
            return

        current_snapshot = self.get_current_snapshot()
        if not current_snapshot:
            return

        target_time = current_snapshot.timestamp + delta

        # Encontrar el snapshot más cercano al tiempo objetivo
        closest_index = 0
        min_diff = float('inf')

        for i, snapshot in enumerate(self.manager.snapshots):
            diff = abs((snapshot.timestamp - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_index = i

        self.current_snapshot_index = closest_index

    def add_enhanced_historical_signals_to_chart(self, fig: go.Figure, snapshot: HistoricalSnapshot,
                                               show_future_signals: bool = False,
                                               show_signal_evolution: bool = True):
        """
        Añadir señales históricas mejoradas al gráfico

        Args:
            fig: Figura de plotly
            snapshot: Snapshot histórico
            show_future_signals: Si mostrar señales futuras
            show_signal_evolution: Si mostrar evolución de señales
        """
        if not snapshot.signals:
            return

        # Añadir señales del snapshot actual
        add_bot_signals_to_chart(fig, snapshot.df, snapshot.bot_analysis)

        # Añadir marcador temporal mejorado
        if self.highlight_current_time:
            self._add_enhanced_time_marker(fig, snapshot)

        # Mostrar evolución de señales
        if show_signal_evolution:
            self._add_signal_evolution_trace(fig, snapshot)

        # Mostrar señales futuras si está habilitado
        if show_future_signals and len(self.manager.snapshots) > 1:
            self._add_future_signals_preview(fig, snapshot)

        # Añadir información contextual
        self._add_historical_context_info(fig, snapshot)

    def _add_enhanced_time_marker(self, fig: go.Figure, snapshot: HistoricalSnapshot):
        """
        Añadir marcador temporal mejorado

        Args:
            fig: Figura de plotly
            snapshot: Snapshot histórico
        """
        # Línea vertical principal
        fig.add_vline(
            x=snapshot.timestamp,
            line_dash="solid",
            line_color="rgba(255, 215, 0, 0.9)",  # Dorado
            line_width=4,
            annotation_text="📅 MOMENTO HISTÓRICO",
            annotation_position="top",
            annotation=dict(
                font=dict(size=14, color="gold", family="Arial Bold"),
                bgcolor="rgba(0, 0, 0, 0.8)",
                bordercolor="gold",
                borderwidth=2,
                borderpad=10,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="gold"
            )
        )

        # Zona de tiempo actual (área sombreada)
        if len(snapshot.df) > 0:
            time_range = timedelta(minutes=30)  # 30 minutos de zona
            start_time = snapshot.timestamp - time_range
            end_time = snapshot.timestamp + time_range

            fig.add_vrect(
                x0=start_time,
                x1=end_time,
                fillcolor="rgba(255, 215, 0, 0.1)",
                layer="below",
                line_width=0,
                annotation_text="🕐 ZONA TEMPORAL",
                annotation_position="bottom left",
                annotation=dict(
                    font=dict(size=10, color="gold"),
                    bgcolor="rgba(0, 0, 0, 0.6)",
                    bordercolor="gold",
                    borderwidth=1
                )
            )

    def _add_signal_evolution_trace(self, fig: go.Figure, snapshot: HistoricalSnapshot):
        """
        Añadir traza de evolución de señales

        Args:
            fig: Figura de plotly
            snapshot: Snapshot histórico
        """
        # Obtener snapshots previos para mostrar evolución
        prev_snapshots = [s for s in self.manager.snapshots
                         if s.timestamp <= snapshot.timestamp]

        if len(prev_snapshots) <= 1:
            return

        # Crear trazas para evolución de señales
        buy_signals_x = []
        buy_signals_y = []
        sell_signals_x = []
        sell_signals_y = []

        for prev_snapshot in prev_snapshots[-10:]:  # Últimos 10 snapshots
            for signal in prev_snapshot.signals:
                if hasattr(signal, 'timestamp') and hasattr(signal, 'price'):
                    if signal.signal_type == SignalType.BUY:
                        buy_signals_x.append(signal.timestamp)
                        buy_signals_y.append(signal.price)
                    elif signal.signal_type == SignalType.SELL:
                        sell_signals_x.append(signal.timestamp)
                        sell_signals_y.append(signal.price)

        # Añadir traza de evolución BUY
        if buy_signals_x:
            fig.add_trace(go.Scatter(
                x=buy_signals_x,
                y=buy_signals_y,
                mode='lines+markers',
                name='Evolución BUY',
                line=dict(color='rgba(38, 166, 154, 0.6)', width=2, dash='dot'),
                marker=dict(color='rgba(38, 166, 154, 0.8)', size=6, symbol='circle'),
                showlegend=False,
                hovertemplate="Señal BUY Histórica<br>Precio: %{y}<br>Tiempo: %{x}<extra></extra>"
            ))

        # Añadir traza de evolución SELL
        if sell_signals_x:
            fig.add_trace(go.Scatter(
                x=sell_signals_x,
                y=sell_signals_y,
                mode='lines+markers',
                name='Evolución SELL',
                line=dict(color='rgba(239, 83, 80, 0.6)', width=2, dash='dot'),
                marker=dict(color='rgba(239, 83, 80, 0.8)', size=6, symbol='circle'),
                showlegend=False,
                hovertemplate="Señal SELL Histórica<br>Precio: %{y}<br>Tiempo: %{x}<extra></extra>"
            ))

    def _add_historical_context_info(self, fig: go.Figure, snapshot: HistoricalSnapshot):
        """
        Añadir información contextual histórica

        Args:
            fig: Figura de plotly
            snapshot: Snapshot histórico
        """
        # Información en la esquina superior izquierda
        context_text = f"""
        <b>📅 ANÁLISIS HISTÓRICO</b><br>
        🕐 Momento: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
        🎯 Señales: {len(snapshot.signals)}<br>
        📊 Datos: {len(snapshot.df)} velas<br>
        🏦 Símbolo: {snapshot.symbol}<br>
        ⏰ Timeframe: {snapshot.timeframe}
        """

        fig.add_annotation(
            text=context_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            font=dict(size=11, color="white", family="Arial"),
            bgcolor="rgba(0, 0, 0, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.3)",
            borderwidth=1,
            borderpad=10,
            showarrow=False
        )

        # Información de condiciones del mercado
        if snapshot.market_conditions:
            market_text = f"""
            <b>🏦 CONDICIONES DEL MERCADO</b><br>
            💰 Precio: ${snapshot.market_conditions.get('price', 0):,.2f}<br>
            📈 Cambio: {snapshot.market_conditions.get('price_change', 0):+.2f}%<br>
            📊 Volatilidad: {snapshot.market_conditions.get('volatility', 0):.2f}%<br>
            📏 Rango: {snapshot.market_conditions.get('daily_range', 0):.2f}%
            """

            fig.add_annotation(
                text=market_text,
                xref="paper", yref="paper",
                x=0.02, y=0.78,
                xanchor="left", yanchor="top",
                font=dict(size=10, color="white", family="Arial"),
                bgcolor="rgba(0, 50, 100, 0.8)",
                bordercolor="rgba(100, 150, 255, 0.5)",
                borderwidth=1,
                borderpad=8,
                showarrow=False
            )

    def add_historical_signals_to_chart(self, fig: go.Figure, snapshot: HistoricalSnapshot,
                                      show_future_signals: bool = False):
        """
        Añadir señales históricas al gráfico

        Args:
            fig: Figura de plotly
            snapshot: Snapshot histórico
            show_future_signals: Si mostrar señales futuras (de otros snapshots)
        """
        if not snapshot.signals:
            return

        # Añadir señales del snapshot actual
        add_bot_signals_to_chart(fig, snapshot.df, snapshot.bot_analysis)

        # Añadir marcador temporal
        fig.add_vline(
            x=snapshot.timestamp,
            line_dash="solid",
            line_color="rgba(255, 255, 255, 0.8)",
            line_width=3,
            annotation_text="📅 TIEMPO ACTUAL",
            annotation_position="top",
            annotation=dict(
                font=dict(size=12, color="white", family="Arial Bold"),
                bgcolor="rgba(255, 255, 255, 0.2)",
                bordercolor="white",
                borderwidth=2,
                borderpad=8
            )
        )

        # Mostrar señales futuras si está habilitado
        if show_future_signals and len(self.manager.snapshots) > 1:
            self._add_future_signals_preview(fig, snapshot)

    def _add_future_signals_preview(self, fig: go.Figure, current_snapshot: HistoricalSnapshot):
        """
        Añadir preview de señales futuras

        Args:
            fig: Figura de plotly
            current_snapshot: Snapshot actual
        """
        current_time = current_snapshot.timestamp

        # Obtener snapshots futuros
        future_snapshots = [s for s in self.manager.snapshots if s.timestamp > current_time]

        for i, future_snapshot in enumerate(future_snapshots[:5]):  # Máximo 5 señales futuras
            for signal in future_snapshot.signals:
                # Determinar timestamp de la señal
                if hasattr(signal.timestamp, 'strftime'):
                    signal_timestamp = signal.timestamp
                elif isinstance(signal.timestamp, (int, float)):
                    signal_idx = int(signal.timestamp)
                    if 0 <= signal_idx < len(future_snapshot.df):
                        signal_timestamp = future_snapshot.df.index[signal_idx]
                    else:
                        continue
                else:
                    continue

                # Colores para señales futuras (más transparentes)
                if signal.signal_type == SignalType.BUY:
                    color = 'rgba(38, 166, 154, 0.4)'
                    emoji = '🔮🚀'
                else:
                    color = 'rgba(239, 83, 80, 0.4)'
                    emoji = '🔮🎯'

                # Añadir marcador de señal futura
                fig.add_scatter(
                    x=[signal_timestamp],
                    y=[signal.entry_price],
                    mode='markers+text',
                    marker=dict(
                        size=15,
                        color=color,
                        symbol='diamond',
                        line=dict(width=2, color='white'),
                        opacity=0.6
                    ),
                    text=[emoji],
                    textposition="middle center",
                    textfont=dict(size=8, color="white"),
                    name=f"Future {signal.signal_type.value}",
                    showlegend=False,
                    hovertemplate=f"<b>🔮 SEÑAL FUTURA</b><br>" +
                                 f"Tipo: {signal.signal_type.value}<br>" +
                                 f"Entry: ${signal.entry_price:.2f}<br>" +
                                 f"R:R: {signal.risk_reward:.1f}:1<br>" +
                                 f"Tiempo: %{{x}}<br>" +
                                 f"<i>Señal generada en el futuro</i><extra></extra>"
                )

    def add_historical_timeline_to_chart(self, fig: go.Figure):
        """
        Añadir timeline histórico al gráfico

        Args:
            fig: Figura de plotly
        """
        if not self.manager.snapshots:
            return

        # Crear línea de tiempo
        timestamps = [s.timestamp for s in self.manager.snapshots]
        signal_counts = [len(s.signals) for s in self.manager.snapshots]

        # Añadir puntos de timeline
        for i, (timestamp, count) in enumerate(zip(timestamps, signal_counts)):
            color = '#4CAF50' if count > 0 else '#9E9E9E'
            size = max(8, min(20, count * 3))  # Tamaño basado en número de señales

            fig.add_scatter(
                x=[timestamp],
                y=[fig.data[0].close.min() * 0.999],  # Parte inferior del gráfico
                mode='markers',
                marker=dict(
                    size=size,
                    color=color,
                    symbol='circle',
                    line=dict(width=1, color='white'),
                    opacity=0.8
                ),
                name=f"Timeline {i+1}",
                showlegend=False,
                hovertemplate=f"<b>📅 Punto Histórico #{i+1}</b><br>" +
                             f"Tiempo: %{{x}}<br>" +
                             f"Señales: {count}<br>" +
                             f"<i>Click para navegar</i><extra></extra>"
            )

    def create_historical_evolution_chart(self) -> go.Figure:
        """
        Crear gráfico de evolución histórica

        Returns:
            Figura con evolución histórica
        """
        evolution = self.manager.get_signals_evolution()

        if not evolution or not evolution['timestamps']:
            return go.Figure()

        fig = go.Figure()

        # Gráfico de señales totales
        fig.add_trace(go.Scatter(
            x=evolution['timestamps'],
            y=evolution['total_signals'],
            mode='lines+markers',
            name='Total Señales',
            line=dict(color='#2196F3', width=3),
            marker=dict(size=8)
        ))

        # Gráfico de señales BUY
        fig.add_trace(go.Scatter(
            x=evolution['timestamps'],
            y=evolution['buy_signals'],
            mode='lines+markers',
            name='Señales BUY',
            line=dict(color='#26A69A', width=2),
            marker=dict(size=6)
        ))

        # Gráfico de señales SELL
        fig.add_trace(go.Scatter(
            x=evolution['timestamps'],
            y=evolution['sell_signals'],
            mode='lines+markers',
            name='Señales SELL',
            line=dict(color='#EF5350', width=2),
            marker=dict(size=6)
        ))

        # Configurar layout
        fig.update_layout(
            title='📈 Evolución Histórica de Señales SMC',
            xaxis_title='Tiempo',
            yaxis_title='Número de Señales',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            font=dict(color='white'),
            hovermode='x unified',
            showlegend=True,
            height=400
        )

        return fig

    def create_rr_evolution_chart(self) -> go.Figure:
        """
        Crear gráfico de evolución R:R

        Returns:
            Figura con evolución R:R
        """
        evolution = self.manager.get_signals_evolution()

        if not evolution or not evolution['timestamps']:
            return go.Figure()

        fig = go.Figure()

        # Gráfico de R:R promedio
        fig.add_trace(go.Scatter(
            x=evolution['timestamps'],
            y=evolution['avg_rr'],
            mode='lines+markers',
            name='R:R Promedio',
            line=dict(color='#FF9800', width=3),
            marker=dict(size=8),
            fill='tonexty'
        ))

        # Línea de referencia R:R = 2
        fig.add_hline(
            y=2.0,
            line_dash="dash",
            line_color="#4CAF50",
            annotation_text="R:R Target (2:1)",
            annotation_position="right"
        )

        # Configurar layout
        fig.update_layout(
            title='📊 Evolución Risk:Reward Histórica',
            xaxis_title='Tiempo',
            yaxis_title='Risk:Reward Ratio',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            font=dict(color='white'),
            hovermode='x unified',
            showlegend=True,
            height=400
        )

        return fig

    def create_confidence_evolution_chart(self) -> go.Figure:
        """
        Crear gráfico de evolución de confianza

        Returns:
            Figura con evolución de confianza
        """
        evolution = self.manager.get_signals_evolution()

        if not evolution or not evolution['timestamps']:
            return go.Figure()

        fig = go.Figure()

        # Gráfico de confianza promedio
        confidence_pct = [c * 100 for c in evolution['avg_confidence']]

        fig.add_trace(go.Scatter(
            x=evolution['timestamps'],
            y=confidence_pct,
            mode='lines+markers',
            name='Confianza Promedio',
            line=dict(color='#9C27B0', width=3),
            marker=dict(size=8),
            fill='tozeroy'
        ))

        # Líneas de referencia
        fig.add_hline(y=80, line_dash="dash", line_color="#4CAF50",
                     annotation_text="Alta Confianza (80%)")
        fig.add_hline(y=60, line_dash="dash", line_color="#FF9800",
                     annotation_text="Confianza Media (60%)")

        # Configurar layout
        fig.update_layout(
            title='🎯 Evolución de Confianza Histórica',
            xaxis_title='Tiempo',
            yaxis_title='Confianza (%)',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            font=dict(color='white'),
            hovermode='x unified',
            showlegend=True,
            height=400
        )

        return fig

    def create_market_conditions_chart(self) -> go.Figure:
        """
        Crear gráfico de condiciones del mercado

        Returns:
            Figura con condiciones del mercado
        """
        if not self.manager.snapshots:
            return go.Figure()

        timestamps = [s.timestamp for s in self.manager.snapshots]
        prices = [s.market_conditions.get('price', 0) for s in self.manager.snapshots]
        volatilities = [s.market_conditions.get('volatility', 0) for s in self.manager.snapshots]

        fig = go.Figure()

        # Gráfico de precio
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=prices,
            mode='lines+markers',
            name='Precio',
            line=dict(color='#2196F3', width=3),
            marker=dict(size=6),
            yaxis='y'
        ))

        # Gráfico de volatilidad
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=volatilities,
            mode='lines+markers',
            name='Volatilidad (%)',
            line=dict(color='#FF5722', width=2),
            marker=dict(size=4),
            yaxis='y2'
        ))

        # Configurar layout con dos ejes Y
        fig.update_layout(
            title='🏦 Condiciones Históricas del Mercado',
            xaxis_title='Tiempo',
            yaxis=dict(
                title='Precio',
                title_font=dict(color='#2196F3'),
                tickfont=dict(color='#2196F3'),
                side='left'
            ),
            yaxis2=dict(
                title='Volatilidad (%)',
                title_font=dict(color='#FF5722'),
                tickfont=dict(color='#FF5722'),
                anchor='x',
                overlaying='y',
                side='right'
            ),
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            font=dict(color='white'),
            hovermode='x unified',
            showlegend=True,
            height=400
        )

        return fig

    def navigate_to_snapshot(self, index: int) -> Optional[HistoricalSnapshot]:
        """
        Navegar a un snapshot específico

        Args:
            index: Índice del snapshot

        Returns:
            Snapshot seleccionado
        """
        if 0 <= index < len(self.manager.snapshots):
            self.current_snapshot_index = index
            return self.manager.snapshots[index]
        return None

    def get_current_snapshot(self) -> Optional[HistoricalSnapshot]:
        """
        Obtener snapshot actual

        Returns:
            Snapshot actual
        """
        if self.manager.snapshots:
            return self.manager.snapshots[self.current_snapshot_index]
        return None

    def get_navigation_info(self) -> Dict:
        """
        Obtener información de navegación

        Returns:
            Información de navegación
        """
        if not self.manager.snapshots:
            return {}

        current = self.get_current_snapshot()

        return {
            'current_index': self.current_snapshot_index,
            'total_snapshots': len(self.manager.snapshots),
            'current_time': current.timestamp if current else None,
            'has_previous': self.current_snapshot_index > 0,
            'has_next': self.current_snapshot_index < len(self.manager.snapshots) - 1,
            'progress': (self.current_snapshot_index + 1) / len(self.manager.snapshots) * 100
        }

def create_historical_visualizer(manager: SMCHistoricalManager) -> HistoricalVisualizer:
    """
    Crear visualizador histórico

    Args:
        manager: Gestor histórico

    Returns:
        Visualizador histórico
    """
    return HistoricalVisualizer(manager)

def display_historical_controls(visualizer: HistoricalVisualizer) -> Dict:
    """
    Mostrar controles de navegación histórica

    Args:
        visualizer: Visualizador histórico

    Returns:
        Estado de los controles
    """
    nav_info = visualizer.get_navigation_info()

    if not nav_info:
        st.warning("⚠️ No hay datos históricos disponibles")
        return {}

    st.markdown("### 📅 Navegación Histórica")

    # Barra de progreso
    progress = nav_info['progress']
    st.progress(progress / 100)

    # Información actual
    current_time = nav_info['current_time']
    if current_time:
        st.info(f"📅 Tiempo actual: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Controles de navegación
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ Inicio", disabled=not nav_info['has_previous']):
            visualizer.navigate_to_snapshot(0)
            st.rerun()

    with col2:
        if st.button("⏪ Anterior", disabled=not nav_info['has_previous']):
            visualizer.navigate_to_snapshot(nav_info['current_index'] - 1)
            st.rerun()

    with col3:
        # Slider para navegación directa
        new_index = st.slider(
            "Posición en el tiempo",
            min_value=0,
            max_value=nav_info['total_snapshots'] - 1,
            value=nav_info['current_index'],
            key="historical_slider"
        )

        if new_index != nav_info['current_index']:
            visualizer.navigate_to_snapshot(new_index)
            st.rerun()

    with col4:
        if st.button("⏩ Siguiente", disabled=not nav_info['has_next']):
            visualizer.navigate_to_snapshot(nav_info['current_index'] + 1)
            st.rerun()

    with col5:
        if st.button("⏭️ Final", disabled=not nav_info['has_next']):
            visualizer.navigate_to_snapshot(nav_info['total_snapshots'] - 1)
            st.rerun()

    # Información de estado
    st.markdown(f"**Snapshot {nav_info['current_index'] + 1} de {nav_info['total_snapshots']}**")

    return nav_info

# Ejemplo de uso
if __name__ == "__main__":
    print("📅 Historical Visualizer - Ejemplo de uso")
    print("=" * 45)

    from smc_historical import create_historical_manager

    # Crear gestor y visualizador
    manager = create_historical_manager("BTC/USDT", "15m")
    visualizer = create_historical_visualizer(manager)

    # Generar datos históricos
    timeline = manager.generate_historical_timeline(HistoricalPeriod.HOURS_12, 6)

    print(f"📊 Timeline generado con {len(timeline)} puntos")
    print("   Funciones disponibles:")
    print("   - add_historical_signals_to_chart()")
    print("   - create_historical_evolution_chart()")
    print("   - create_rr_evolution_chart()")
    print("   - create_confidence_evolution_chart()")
    print("   - create_market_conditions_chart()")
    print("   - navigate_to_snapshot()")
    print("   - display_historical_controls()")
