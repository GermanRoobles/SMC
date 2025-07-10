#!/usr/bin/env python3
"""
Demo: Sistema Histórico SMC Mejorado
===================================

Este script demuestra las mejoras del sistema histórico SMC con:
- Navegación mejorada con controles avanzados
- Timeline detallado con cache
- Análisis de rendimiento histórico
- Visualización de evolución de señales
- Marcadores temporales automáticos
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time

# Configuración de la página
st.set_page_config(
    page_title="Demo: Sistema Histórico SMC Mejorado",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Demo: Sistema Histórico SMC Mejorado")
st.markdown("---")

# Importar módulos
try:
    from smc_historical import SMCHistoricalManager, HistoricalPeriod, create_historical_manager
    from smc_historical_viz import HistoricalVisualizer, create_historical_visualizer
    from fetch_data import get_ohlcv
    from smc_integration import get_smc_bot_analysis

    st.success("✅ Todos los módulos importados correctamente")
except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    st.stop()

# Sidebar: Configuración
st.sidebar.title("⚙️ Configuración")
symbol = st.sidebar.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT", "ADA/USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h"])

# Configuración histórica
st.sidebar.markdown("### 📅 Configuración Histórica")
historical_period = st.sidebar.selectbox(
    "Período Histórico",
    [
        ("1 Hora", HistoricalPeriod.HOUR_1),
        ("4 Horas", HistoricalPeriod.HOURS_4),
        ("12 Horas", HistoricalPeriod.HOURS_12),
        ("1 Día", HistoricalPeriod.DAY_1),
        ("3 Días", HistoricalPeriod.DAYS_3),
        ("1 Semana", HistoricalPeriod.WEEK_1)
    ],
    format_func=lambda x: x[0],
    index=2
)

timeline_intervals = st.sidebar.slider(
    "Intervalos de Timeline",
    min_value=5,
    max_value=25,
    value=15,
    help="Número de puntos temporales en el timeline"
)

# Botón para generar demo
if st.sidebar.button("🚀 Iniciar Demo", type="primary"):
    st.session_state.demo_started = True
    st.session_state.manager = None
    st.session_state.visualizer = None

# Demo principal
if st.session_state.get('demo_started', False):

    # Crear manager histórico
    if st.session_state.get('manager') is None:
        with st.spinner("📊 Creando manager histórico..."):
            st.session_state.manager = create_historical_manager(symbol, timeframe)
            st.session_state.visualizer = create_historical_visualizer(st.session_state.manager)

        st.success("✅ Manager histórico creado")

    # Generar timeline
    if not st.session_state.manager.snapshots:
        with st.spinner("📅 Generando timeline histórico detallado..."):
            # Intentar cargar desde cache
            timeline = st.session_state.manager.load_timeline_from_cache(historical_period[1])

            if timeline:
                st.session_state.manager.snapshots = timeline
                st.success(f"📂 Timeline cargado desde cache: {len(timeline)} puntos")
            else:
                # Generar nuevo timeline
                timeline = st.session_state.manager.create_detailed_historical_timeline(
                    historical_period[1],
                    intervals=timeline_intervals
                )

                if timeline:
                    st.success(f"✅ Timeline generado: {len(timeline)} puntos históricos")
                else:
                    st.error("❌ Error generando timeline")
                    st.stop()

    # Mostrar controles de navegación mejorados
    st.markdown("## 🎮 Controles de Navegación Histórica")

    nav_info = st.session_state.visualizer.create_enhanced_historical_controls()

    # Obtener snapshot actual
    current_snapshot = st.session_state.visualizer.get_current_snapshot()

    if current_snapshot:
        # Crear gráfico
        st.markdown("## 📊 Gráfico Histórico")

        # Crear gráfico base
        fig = go.Figure(data=[
            go.Candlestick(
                x=current_snapshot.df["timestamp"],
                open=current_snapshot.df["open"],
                high=current_snapshot.df["high"],
                low=current_snapshot.df["low"],
                close=current_snapshot.df["close"],
                name="Precio",
                increasing=dict(line=dict(color='#26A69A'), fillcolor='#26A69A'),
                decreasing=dict(line=dict(color='#EF5350'), fillcolor='#EF5350')
            )
        ])

        # Añadir señales históricas mejoradas
        st.session_state.visualizer.add_enhanced_historical_signals_to_chart(
            fig,
            current_snapshot,
            show_future_signals=True,
            show_signal_evolution=True
        )

        # Añadir timeline al gráfico
        st.session_state.visualizer.add_historical_timeline_to_chart(fig)

        # Configurar layout
        fig.update_layout(
            title=f"{symbol} • {timeframe} • Análisis Histórico",
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            font=dict(color='white'),
            height=600,
            xaxis_rangeslider_visible=False
        )

        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Mostrar información del snapshot
        st.markdown("### 📋 Información del Snapshot Actual")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"""
            **⏰ Tiempo:**
            {current_snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

            **📊 Datos:**
            {len(current_snapshot.df)} velas
            """)

        with col2:
            st.info(f"""
            **🎯 Señales:**
            {len(current_snapshot.signals)} total

            **💰 Precio:**
            ${current_snapshot.df['close'].iloc[-1]:,.2f}
            """)

        with col3:
            if current_snapshot.market_conditions:
                st.info(f"""
                **📈 Mercado:**
                Cambio: {current_snapshot.market_conditions.get('price_change', 0):+.2f}%

                **📊 Volatilidad:**
                {current_snapshot.market_conditions.get('volatility', 0):.2f}%
                """)

    # Mostrar estadísticas históricas
    if st.session_state.manager.snapshots:
        st.markdown("## 📈 Estadísticas Históricas")

        stats = st.session_state.manager.get_signal_statistics()

        if stats:
            # Métricas principales
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("📊 Total Señales", stats['total_signals'])

            with col2:
                st.metric("🟢 Señales BUY", stats['buy_signals'])

            with col3:
                st.metric("🔴 Señales SELL", stats['sell_signals'])

            with col4:
                st.metric("💎 R:R Promedio", f"{stats['avg_rr']:.2f}:1")

            with col5:
                st.metric("🎯 Confianza Media", f"{stats['avg_confidence']:.1%}")

            # Información detallada
            st.markdown("### 📋 Análisis Detallado")

            col1, col2 = st.columns(2)

            with col1:
                st.info(f"""
                **📊 Estadísticas del Timeline:**
                - Snapshots: {stats['snapshots_count']}
                - Señales por snapshot: {stats['total_signals']/max(stats['snapshots_count'], 1):.1f}
                - Ratio BUY/SELL: {stats['buy_signals']/max(stats['sell_signals'], 1):.2f}
                """)

            with col2:
                duration = stats['timespan']['duration']
                st.info(f"""
                **⏰ Período Analizado:**
                - Inicio: {stats['timespan']['start'].strftime('%Y-%m-%d %H:%M')}
                - Fin: {stats['timespan']['end'].strftime('%Y-%m-%d %H:%M')}
                - Duración: {str(duration).split('.')[0]}
                """)

    # Mostrar gráficos de evolución
    st.markdown("## 📈 Gráficos de Evolución Histórica")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Evolución Señales", "💰 Risk:Reward", "🎯 Confianza", "🏦 Mercado"])

    with tab1:
        try:
            evolution_chart = st.session_state.visualizer.create_historical_evolution_chart()
            if evolution_chart and evolution_chart.data:
                st.plotly_chart(evolution_chart, use_container_width=True)
            else:
                st.info("📊 No hay datos suficientes para evolución de señales")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab2:
        try:
            rr_chart = st.session_state.visualizer.create_rr_evolution_chart()
            if rr_chart and rr_chart.data:
                st.plotly_chart(rr_chart, use_container_width=True)
            else:
                st.info("💰 No hay datos suficientes para evolución R:R")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab3:
        try:
            confidence_chart = st.session_state.visualizer.create_confidence_evolution_chart()
            if confidence_chart and confidence_chart.data:
                st.plotly_chart(confidence_chart, use_container_width=True)
            else:
                st.info("🎯 No hay datos suficientes para evolución de confianza")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab4:
        try:
            market_chart = st.session_state.visualizer.create_market_conditions_chart()
            if market_chart and market_chart.data:
                st.plotly_chart(market_chart, use_container_width=True)
            else:
                st.info("🏦 No hay datos suficientes para condiciones del mercado")
        except Exception as e:
            st.error(f"Error: {e}")

else:
    # Pantalla de inicio
    st.markdown("""
    ## 🎯 Características del Sistema Histórico Mejorado:

    ### 🎮 Navegación Mejorada:
    - **Controles intuitivos**: Botones de navegación (primero, anterior, siguiente, último)
    - **Slider temporal**: Navegación suave por timeline
    - **Reproducción automática**: Con velocidad configurable
    - **Saltos temporales**: Navegación por períodos específicos
    - **Marcadores automáticos**: Acceso rápido a puntos importantes

    ### 📊 Visualización Avanzada:
    - **Marcadores temporales**: Línea dorada que marca el momento actual
    - **Evolución de señales**: Trazas que muestran la evolución histórica
    - **Señales futuras**: Preview de señales que se generarán
    - **Contexto histórico**: Información detallada en cada momento

    ### 💾 Sistema de Cache:
    - **Cache inteligente**: Guarda timelines para acceso rápido
    - **Recuperación automática**: Carga desde cache cuando está disponible
    - **Expiración automática**: Actualiza cache cuando es necesario

    ### 📈 Análisis Estadístico:
    - **Métricas detalladas**: Análisis completo de rendimiento
    - **Estadísticas temporales**: Evolución de métricas en el tiempo
    - **Gráficos de evolución**: Visualización de tendencias históricas

    ### 🔍 Búsqueda Temporal:
    - **Búsqueda por tiempo**: Encontrar snapshots específicos
    - **Rangos temporales**: Filtrar por períodos de interés
    - **Navegación precisa**: Acceso a cualquier momento histórico

    ---

    **👈 Configura los parámetros en la barra lateral y haz clic en "Iniciar Demo" para comenzar.**
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
📅 <b>Sistema Histórico SMC Mejorado</b><br>
Navegación avanzada por el historial de señales SMC<br>
<i>Desarrollado con ❤️ para análisis técnico avanzado</i>
</div>
""", unsafe_allow_html=True)
