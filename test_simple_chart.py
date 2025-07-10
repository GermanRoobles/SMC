#!/usr/bin/env python3
"""
Test de Renderizado de Gráficos - Versión Simple
===============================================

Script simple para probar que los gráficos se rendericen correctamente
sin señales que puedan causar problemas.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Test Gráfico Simple", layout="wide")
st.title("🧪 Test de Renderizado de Gráfico Simple")

# Generar datos de prueba simples
@st.cache_data
def generate_test_data():
    """Generar datos OHLC de prueba"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=1), periods=100, freq='5min')

    # Precio base
    base_price = 50000

    # Generar precio aleatorio con tendencia
    price_changes = np.random.randn(100) * 100  # Variaciones de ±100
    prices = base_price + np.cumsum(price_changes)

    data = []
    for i, date in enumerate(dates):
        open_price = prices[i]
        close_price = prices[i] + np.random.randn() * 50
        high_price = max(open_price, close_price) + abs(np.random.randn() * 30)
        low_price = min(open_price, close_price) - abs(np.random.randn() * 30)

        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': np.random.randint(1000, 10000)
        })

    return pd.DataFrame(data)

# Crear datos de prueba
df_test = generate_test_data()

st.info(f"📊 Datos generados: {len(df_test)} velas")

# Crear gráfico simple
fig = go.Figure()

# Añadir velas japonesas
fig.add_trace(go.Candlestick(
    x=df_test['timestamp'],
    open=df_test['open'],
    high=df_test['high'],
    low=df_test['low'],
    close=df_test['close'],
    name="Precio Test",
    increasing=dict(line=dict(color='#26A69A'), fillcolor='#26A69A'),
    decreasing=dict(line=dict(color='#EF5350'), fillcolor='#EF5350')
))

# Configurar layout
fig.update_layout(
    title="Gráfico de Prueba - Sin Señales",
    paper_bgcolor='#1E1E1E',
    plot_bgcolor='#1E1E1E',
    font=dict(color='white'),
    xaxis=dict(
        showgrid=True,
        gridcolor='#2A2A2A',
        color='#FFFFFF',
        rangeslider=dict(visible=False)
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#2A2A2A',
        color='#FFFFFF',
        side='right'
    ),
    height=600,
    margin=dict(l=10, r=80, t=60, b=40)
)

# Mostrar gráfico
st.plotly_chart(fig, use_container_width=True, key="test_chart_simple")

# Información del test
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📊 Total Velas", len(df_test))

with col2:
    st.metric("💰 Precio Actual", f"${df_test['close'].iloc[-1]:,.2f}")

with col3:
    st.metric("📈 Cambio", f"{((df_test['close'].iloc[-1] - df_test['close'].iloc[0]) / df_test['close'].iloc[0] * 100):+.2f}%")

# Test con botón para añadir líneas simples
st.markdown("### 🧪 Test de Líneas Adicionales")

if st.button("➕ Añadir Líneas de Prueba"):
    # Añadir líneas horizontales simples
    current_price = df_test['close'].iloc[-1]

    fig.add_hline(
        y=current_price * 1.02,
        line_dash="dash",
        line_color="green",
        line_width=2,
        annotation_text="Resistencia +2%"
    )

    fig.add_hline(
        y=current_price * 0.98,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text="Soporte -2%"
    )

    # Mostrar gráfico actualizado
    st.plotly_chart(fig, use_container_width=True, key="test_chart_with_lines")
    st.success("✅ Líneas añadidas correctamente")

# Test de datos
st.markdown("### 📋 Muestra de Datos")
st.dataframe(df_test.head(10), use_container_width=True)

# Verificaciones
st.markdown("### ✅ Verificaciones")

checks = [
    ("Datos OHLC válidos", len(df_test) > 0),
    ("Precios positivos", (df_test[['open', 'high', 'low', 'close']] > 0).all().all()),
    ("High >= Low", (df_test['high'] >= df_test['low']).all()),
    ("High >= max(Open, Close)", (df_test['high'] >= df_test[['open', 'close']].max(axis=1)).all()),
    ("Low <= min(Open, Close)", (df_test['low'] <= df_test[['open', 'close']].min(axis=1)).all()),
    ("Timestamps ordenados", df_test['timestamp'].is_monotonic_increasing)
]

for check_name, is_valid in checks:
    if is_valid:
        st.success(f"✅ {check_name}")
    else:
        st.error(f"❌ {check_name}")

st.markdown("---")
st.info("💡 Este es un test básico para verificar que el renderizado de gráficos funciona correctamente sin señales complejas.")
