#!/usr/bin/env python3
"""
Versión simplificada de la aplicación principal para diagnosticar problemas
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from fetch_data import get_ohlcv_extended

def create_basic_chart(df):
    """Crear gráfico básico solo con velas"""
    if df.empty:
        return go.Figure()

    fig = go.Figure(data=[
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Precio",
            increasing=dict(line=dict(color='#26A69A'), fillcolor='#26A69A'),
            decreasing=dict(line=dict(color='#EF5350'), fillcolor='#EF5350')
        )
    ])

    # Configuración TradingView básica
    fig.update_layout(
        title=f"Gráfico Básico - {len(df)} velas",
        xaxis_title="Tiempo",
        yaxis_title="Precio",
        height=600,
        template="plotly_dark",
        xaxis=dict(
            rangeslider=dict(visible=False),
            type="date"
        ),
        yaxis=dict(
            side="right",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.3)"
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    return fig

def main():
    st.set_page_config(page_title="SMC Básico", layout="wide")
    st.title("📊 SMC Trading - Versión Básica")

    # Configuración
    col1, col2, col3 = st.columns(3)
    with col1:
        symbol = st.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT"])
    with col2:
        timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m"])
    with col3:
        days = st.selectbox("Días", [1, 3, 5, 7], index=2)

    # Cargar datos automáticamente
    try:
        with st.spinner(f"📊 Cargando {days} días de datos..."):
            df = get_ohlcv_extended(symbol, timeframe, days=days)
            st.success(f"✅ Cargados {len(df)} puntos de datos")

        # Información básica
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Puntos de Datos", len(df))
        with col2:
            st.metric("Precio Actual", f"${df['close'].iloc[-1]:,.2f}")
        with col3:
            st.metric("Máximo", f"${df['high'].max():,.2f}")
        with col4:
            st.metric("Mínimo", f"${df['low'].min():,.2f}")

        # Crear gráfico básico
        st.subheader("📈 Gráfico Principal")
        with st.spinner("Creando gráfico..."):
            fig = create_basic_chart(df)
            st.plotly_chart(fig, use_container_width=True)
            st.success("✅ Gráfico renderizado exitosamente")

        # Mostrar datos en tabla (solo últimos 10)
        st.subheader("📋 Datos Recientes")
        st.dataframe(df.tail(10))

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
