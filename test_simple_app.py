#!/usr/bin/env python3
"""
Aplicación de prueba simplificada para diagnosticar problemas de renderizado
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from fetch_data import get_ohlcv_extended

def create_simple_chart(df):
    """Crear gráfico básico sin optimizaciones pesadas"""
    if df.empty:
        return go.Figure()

    fig = go.Figure(data=[
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Precio"
        )
    ])

    # Configuración básica
    fig.update_layout(
        title="Gráfico de Prueba Simple",
        xaxis_title="Tiempo",
        yaxis_title="Precio",
        height=600,
        template="plotly_dark"
    )

    return fig

def main():
    st.set_page_config(page_title="Prueba Simple", layout="wide")
    st.title("🧪 Prueba de Renderizado Simple")

    # Configuración básica
    symbol = st.sidebar.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT"])
    timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m"])
    days = st.sidebar.slider("Días", 1, 7, 3)

    # Botón para cargar datos
    if st.button("🔄 Cargar Datos"):
        with st.spinner("Cargando datos..."):
            df = get_ohlcv_extended(symbol, timeframe, days=days)
            st.success(f"✅ Cargados {len(df)} puntos de datos")

            # Mostrar información básica
            st.write(f"**Rango de datos:** {df['timestamp'].min()} a {df['timestamp'].max()}")
            st.write(f"**Precio actual:** ${df['close'].iloc[-1]:,.2f}")

            # Crear y mostrar gráfico simple
            with st.spinner("Creando gráfico..."):
                fig = create_simple_chart(df)
                st.plotly_chart(fig, use_container_width=True)
                st.success("✅ Gráfico renderizado exitosamente")

    # Información adicional
    st.info("Esta es una versión simplificada para diagnosticar problemas de renderizado")

if __name__ == "__main__":
    main()
