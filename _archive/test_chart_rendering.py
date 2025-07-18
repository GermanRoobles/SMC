#!/usr/bin/env python3
"""
Script de Prueba: Verificar Renderizado de Gráficos
=================================================

Este script verifica que los gráficos se rendericen correctamente
sin truncamiento o problemas de visualización.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Prueba de Renderizado de Gráficos",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Prueba de Renderizado de Gráficos")
st.markdown("---")

# Función para generar datos de prueba
def generate_test_data(num_points=100):
    """
    Generar datos de prueba para el gráfico

    Args:
        num_points: Número de puntos de datos

    Returns:
        DataFrame con datos OHLC
    """
    # Generar timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=num_points)

    timestamps = pd.date_range(start=start_time, end=end_time, periods=num_points)

    # Generar precios aleatorios
    np.random.seed(42)
    base_price = 50000
    returns = np.random.normal(0, 0.02, num_points)
    prices = base_price * np.exp(np.cumsum(returns))

    # Generar OHLC
    opens = prices
    closes = prices * (1 + np.random.normal(0, 0.01, num_points))
    highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, 0.01, num_points)))
    lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, 0.01, num_points)))

    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': np.random.randint(1000, 10000, num_points)
    })

    return df

# Función para validar datos
def validate_chart_data(df):
    """
    Validar datos del gráfico

    Args:
        df: DataFrame con datos OHLC

    Returns:
        DataFrame validado
    """
    if df.empty:
        return df

    # Crear copia
    df_fixed = df.copy()

    # Asegurar que timestamp es datetime
    if 'timestamp' in df_fixed.columns:
        df_fixed['timestamp'] = pd.to_datetime(df_fixed['timestamp'])

    # Eliminar filas con valores NaN
    df_fixed = df_fixed.dropna(subset=['open', 'high', 'low', 'close'])

    # Validar que high >= low
    invalid_rows = df_fixed[df_fixed['high'] < df_fixed['low']]
    if len(invalid_rows) > 0:
        df_fixed.loc[df_fixed['high'] < df_fixed['low'], 'high'] = df_fixed.loc[df_fixed['high'] < df_fixed['low'], 'low']

    # Validar que high >= max(open, close) y low <= min(open, close)
    df_fixed['high'] = df_fixed[['high', 'open', 'close']].max(axis=1)
    df_fixed['low'] = df_fixed[['low', 'open', 'close']].min(axis=1)

    # Ordenar por timestamp
    df_fixed = df_fixed.sort_values('timestamp').reset_index(drop=True)

    return df_fixed

# Función para crear gráfico de prueba
def create_test_chart(df, title="Gráfico de Prueba", height=600):
    """
    Crear gráfico de prueba con configuración optimizada

    Args:
        df: DataFrame con datos OHLC
        title: Título del gráfico
        height: Altura del gráfico

    Returns:
        Figura de plotly
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="white")
        )
        return fig

    # Crear gráfico de velas
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Precio",
            increasing=dict(line=dict(color='#26A69A', width=1), fillcolor='#26A69A'),
            decreasing=dict(line=dict(color='#EF5350', width=1), fillcolor='#EF5350'),
            line=dict(width=1),
            hovertext=[
                f"Apertura: ${row['open']:,.2f}<br>Máximo: ${row['high']:,.2f}<br>Mínimo: ${row['low']:,.2f}<br>Cierre: ${row['close']:,.2f}"
                for _, row in df.iterrows()
            ],
            hoverinfo='x+y'
        )
    ])

    # Configurar layout
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 18, 'color': '#FFFFFF', 'family': 'Arial'},
            'x': 0.5,
            'xanchor': 'center'
        },
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',

        xaxis=dict(
            showgrid=True,
            gridcolor='#2A2A2A',
            gridwidth=1,
            color='#FFFFFF',
            showspikes=True,
            spikecolor='#FFFFFF',
            spikesnap='cursor',
            spikemode='across',
            tickfont=dict(color='#FFFFFF'),
            title=dict(text='Tiempo', font=dict(color='#FFFFFF')),
            rangeslider=dict(visible=False),
            fixedrange=False
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor='#2A2A2A',
            gridwidth=1,
            color='#FFFFFF',
            showspikes=True,
            spikecolor='#FFFFFF',
            spikesnap='cursor',
            spikemode='across',
            tickfont=dict(color='#FFFFFF'),
            title=dict(text='Precio', font=dict(color='#FFFFFF')),
            side='right',
            fixedrange=False
        ),

        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=height,
        hovermode='x unified',
        margin=dict(l=10, r=80, t=60, b=40),
        autosize=True,

        xaxis_showspikes=True,
        yaxis_showspikes=True,
        spikedistance=1000,
        hoverdistance=100
    )

    return fig

# Sidebar: Configuración de prueba
st.sidebar.title("⚙️ Configuración de Prueba")
num_points = st.sidebar.slider("Número de puntos de datos", 50, 500, 100)
chart_height = st.sidebar.slider("Altura del gráfico", 400, 800, 600)

# Botón para generar datos
if st.sidebar.button("🔄 Generar Nuevos Datos", type="primary"):
    st.session_state.test_data = None

# Generar datos de prueba
if 'test_data' not in st.session_state or st.session_state.test_data is None:
    with st.spinner("📊 Generando datos de prueba..."):
        st.session_state.test_data = generate_test_data(num_points)
    st.success("✅ Datos de prueba generados")

# Validar datos
validated_data = validate_chart_data(st.session_state.test_data)

# Mostrar información de los datos
st.markdown("## 📊 Información de los Datos")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📈 Puntos de Datos", len(validated_data))

with col2:
    if not validated_data.empty:
        st.metric("💰 Precio Mínimo", f"${validated_data['low'].min():,.2f}")

with col3:
    if not validated_data.empty:
        st.metric("💰 Precio Máximo", f"${validated_data['high'].max():,.2f}")

with col4:
    if not validated_data.empty:
        st.metric("💰 Precio Actual", f"${validated_data['close'].iloc[-1]:,.2f}")

# Crear y mostrar gráfico principal
st.markdown("## 📊 Gráfico Principal")

if not validated_data.empty:
    fig_main = create_test_chart(validated_data, "Gráfico Principal - Prueba de Renderizado", chart_height)
    st.plotly_chart(fig_main, use_container_width=True, key="main_test_chart")
else:
    st.error("❌ No hay datos válidos para mostrar")

# Crear gráficos adicionales para probar múltiples renderizados
st.markdown("## 📊 Gráficos Adicionales")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Gráfico Pequeño")
    if not validated_data.empty:
        fig_small = create_test_chart(validated_data, "Gráfico Pequeño", 300)
        st.plotly_chart(fig_small, use_container_width=True, key="small_test_chart")

with col2:
    st.markdown("### 📈 Gráfico Mediano")
    if not validated_data.empty:
        fig_medium = create_test_chart(validated_data, "Gráfico Mediano", 400)
        st.plotly_chart(fig_medium, use_container_width=True, key="medium_test_chart")

# Probar tabs con gráficos
st.markdown("## 📊 Gráficos en Tabs")

tab1, tab2, tab3 = st.tabs(["📊 Tab 1", "📈 Tab 2", "📉 Tab 3"])

with tab1:
    st.markdown("### 📊 Gráfico en Tab 1")
    if not validated_data.empty:
        fig_tab1 = create_test_chart(validated_data, "Gráfico en Tab 1", 500)
        st.plotly_chart(fig_tab1, use_container_width=True, key="tab1_test_chart")

with tab2:
    st.markdown("### 📈 Gráfico en Tab 2")
    if not validated_data.empty:
        fig_tab2 = create_test_chart(validated_data, "Gráfico en Tab 2", 500)
        st.plotly_chart(fig_tab2, use_container_width=True, key="tab2_test_chart")

with tab3:
    st.markdown("### 📉 Gráfico en Tab 3")
    if not validated_data.empty:
        fig_tab3 = create_test_chart(validated_data, "Gráfico en Tab 3", 500)
        st.plotly_chart(fig_tab3, use_container_width=True, key="tab3_test_chart")

# Información de depuración
st.markdown("## 🔍 Información de Depuración")

with st.expander("📋 Detalles de los Datos"):
    if not validated_data.empty:
        st.write("**Primeras 5 filas:**")
        st.dataframe(validated_data.head())

        st.write("**Últimas 5 filas:**")
        st.dataframe(validated_data.tail())

        st.write("**Información del DataFrame:**")
        st.text(f"Forma: {validated_data.shape}")
        st.text(f"Columnas: {list(validated_data.columns)}")
        st.text(f"Tipos de datos: {validated_data.dtypes.to_dict()}")

        st.write("**Estadísticas básicas:**")
        st.dataframe(validated_data.describe())

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
📊 <b>Prueba de Renderizado de Gráficos</b><br>
Script para verificar que los gráficos se muestren correctamente<br>
<i>Sin truncamiento ni problemas de visualización</i>
</div>
""", unsafe_allow_html=True)
