import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from fetch_data import get_ohlcv
from smc_analysis import analyze, get_current_session, get_session_color

# ⚡️ Optimización 2: Cache para datos
@st.cache_data(ttl=30)
def cached_get_ohlcv(symbol, timeframe, limit=100):
    """Cache de datos OHLCV para evitar llamadas redundantes a la API"""
    return get_ohlcv(symbol, timeframe, limit)

# 🧼 Optimización 6: Funciones refactorizadas
def add_fvg_indicators(fig, df, fvg_data):
    """Función para añadir indicadores FVG al gráfico"""
    fvg_count = 0
    if not fvg_data.empty:
        for i, row in fvg_data.iterrows():
            if pd.notna(row["FVG"]):
                fvg_count += 1
                is_bullish = row["FVG"] == 1
                color = '#2962FF' if is_bullish else '#FF6D00'

                # Añadir rectángulo FVG
                fig.add_shape(
                    type="rect",
                    x0=df.iloc[i]["timestamp"],
                    x1=df.iloc[min(i+8, len(df)-1)]["timestamp"],
                    y0=row["Bottom"],
                    y1=row["Top"],
                    fillcolor=color,
                    opacity=0.15,
                    line=dict(color=color, width=1, dash="dot")
                )

                # Añadir texto identificativo
                fig.add_annotation(
                    x=df.iloc[min(i+2, len(df)-1)]["timestamp"],
                    y=(row["Top"] + row["Bottom"]) / 2,
                    text="FVG",
                    showarrow=False,
                    font=dict(size=10, color=color, family="Arial Black"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor=color,
                    borderwidth=1
                )
    return fvg_count

def add_order_blocks(fig, df, ob_data):
    """Función para añadir Order Blocks al gráfico"""
    ob_count = 0
    if not ob_data.empty:
        for i, row in ob_data.iterrows():
            if pd.notna(row["OB"]):
                ob_count += 1
                is_bullish = row["OB"] == 1
                color = '#4CAF50' if is_bullish else '#F44336'

                # Añadir rectángulo Order Block
                fig.add_shape(
                    type="rect",
                    x0=df.iloc[i]["timestamp"],
                    x1=df.iloc[min(i+12, len(df)-1)]["timestamp"],
                    y0=row["Bottom"],
                    y1=row["Top"],
                    fillcolor=color,
                    opacity=0.2,
                    line=dict(color=color, width=2)
                )

                # Añadir texto identificativo
                fig.add_annotation(
                    x=df.iloc[min(i+3, len(df)-1)]["timestamp"],
                    y=(row["Top"] + row["Bottom"]) / 2,
                    text="OB",
                    showarrow=False,
                    font=dict(size=12, color="white", family="Arial Black"),
                    bgcolor=color,
                    bordercolor=color,
                    borderwidth=1
                )
    return ob_count

def add_bos_choch(fig, df, bos_choch_data):
    """Función para añadir BOS/CHoCH al gráfico"""
    bos_choch_count = 0
    if not bos_choch_data.empty:
        for i, row in bos_choch_data.iterrows():
            signal = row.get("Signal", row.get("BOS", row.get("CHoCH", None)))
            if pd.notna(signal):
                bos_choch_count += 1

                # Línea vertical para BOS/CHoCH
                fig.add_shape(
                    type="line",
                    x0=df.iloc[i]["timestamp"],
                    x1=df.iloc[i]["timestamp"],
                    y0=df.iloc[i]["low"] * 0.999,
                    y1=df.iloc[i]["high"] * 1.001,
                    line=dict(color="#9C27B0", width=3, dash="dash")
                )

                # Añadir texto identificativo
                fig.add_annotation(
                    x=df.iloc[i]["timestamp"],
                    y=df.iloc[i]["high"] * 1.002,
                    text="BOS" if "BOS" in str(signal) else "CHoCH",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="#9C27B0",
                    font=dict(size=10, color="white", family="Arial Black"),
                    bgcolor="#9C27B0",
                    bordercolor="#9C27B0",
                    borderwidth=1
                )
    return bos_choch_count

def add_liquidity_sweeps(fig, df, liq_data):
    """Función para añadir Liquidity Sweeps al gráfico"""
    liq_count = 0
    if not liq_data.empty:
        for i, row in liq_data.iterrows():
            sweep = row.get("Sweep", row.get("Liquidity", None))
            if pd.notna(sweep):
                liq_count += 1
                price = row.get("Price", df.iloc[i]["high"])

                # Línea horizontal para Liquidity
                fig.add_shape(
                    type="line",
                    x0=df.iloc[max(0, i-5)]["timestamp"],
                    x1=df.iloc[min(i+5, len(df)-1)]["timestamp"],
                    y0=price,
                    y1=price,
                    line=dict(color="#FFD700", width=2, dash="solid")
                )

                # Añadir texto identificativo
                fig.add_annotation(
                    x=df.iloc[i]["timestamp"],
                    y=price,
                    text="LIQ",
                    showarrow=False,
                    font=dict(size=9, color="black", family="Arial Black"),
                    bgcolor="#FFD700",
                    bordercolor="#FFD700",
                    borderwidth=1
                )
    return liq_count

def add_swing_points(fig, df, swing_data):
    """Función para añadir Swing Highs/Lows al gráfico"""
    swing_high_count = 0
    swing_low_count = 0

    if not swing_data.empty:
        for i, row in swing_data.iterrows():
            if pd.notna(row["HighLow"]):
                if row["HighLow"] == 1:  # Swing High
                    swing_high_count += 1
                    fig.add_trace(go.Scatter(
                        x=[df.iloc[i]["timestamp"]],
                        y=[df.iloc[i]["high"]],
                        mode="markers+text",
                        marker=dict(color="#FF5722", size=12, symbol="triangle-down", line=dict(color="white", width=1)),
                        text=["H"],
                        textposition="middle center",
                        textfont=dict(color="white", size=8, family="Arial Black"),
                        name="Swing High",
                        showlegend=False,
                        hovertemplate="Swing High<br>Price: %{y}<br>Time: %{x}<extra></extra>"
                    ))
                elif row["HighLow"] == -1:  # Swing Low
                    swing_low_count += 1
                    fig.add_trace(go.Scatter(
                        x=[df.iloc[i]["timestamp"]],
                        y=[df.iloc[i]["low"]],
                        mode="markers+text",
                        marker=dict(color="#4CAF50", size=12, symbol="triangle-up", line=dict(color="white", width=1)),
                        text=["L"],
                        textposition="middle center",
                        textfont=dict(color="white", size=8, family="Arial Black"),
                        name="Swing Low",
                        showlegend=False,
                        hovertemplate="Swing Low<br>Price: %{y}<br>Time: %{x}<extra></extra>"
                    ))

    return swing_high_count, swing_low_count

# ⚡️ Optimización 1: Agrupar sesiones contiguas
def add_session_background(fig, df):
    """Función optimizada para añadir fondo de sesiones agrupadas"""
    session_count = 0
    shapes = []

    if len(df) > 0:
        current_session = None
        start_ts = None

        for i, row in df.iterrows():
            ts = row["timestamp"]
            session = get_current_session(ts)

            if session != current_session:
                # Añadir la sesión anterior si existe
                if current_session is not None and start_ts is not None:
                    color = get_session_color(current_session)
                    shapes.append(dict(
                        type="rect",
                        x0=start_ts,
                        x1=prev_ts,
                        yref="paper",
                        y0=0,
                        y1=1,
                        fillcolor=color,
                        opacity=0.08,
                        line_width=0,
                        layer="below"
                    ))
                    session_count += 1

                current_session = session
                start_ts = ts

            prev_ts = ts

        # Añadir la última sesión
        if current_session is not None and start_ts is not None:
            color = get_session_color(current_session)
            shapes.append(dict(
                type="rect",
                x0=start_ts,
                x1=prev_ts,
                yref="paper",
                y0=0,
                y1=1,
                fillcolor=color,
                opacity=0.08,
                line_width=0,
                layer="below"
            ))
            session_count += 1

    # Añadir todas las formas de una vez
    for shape in shapes:
        fig.add_shape(**shape)

    return session_count

# Configuración de página
st.set_page_config(layout="wide", page_title="Smart Money Concepts - TradingView Style")
st.title("📊 Smart Money Concepts - TradingView Style")

# Configuración de la barra lateral
symbol = st.sidebar.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m"])

# 🔄 Optimización 3: Auto-refresh mejorado
st.sidebar.markdown("🔁 Refrescar cada:")
refresh_interval = st.sidebar.selectbox("Intervalo (segundos)", [0, 30, 60, 120], index=0)

if refresh_interval > 0:
    st.sidebar.success(f"🔄 Auto-refresh cada {refresh_interval}s")
    st_autorefresh(interval=refresh_interval * 1000, limit=None, key="smc_refresh")

# 📊 Optimización 5: Métricas de rendimiento
start_time = time.time()

# Obtener datos y análisis con cache
df = cached_get_ohlcv(symbol, timeframe)
signals = analyze(df)

# 📌 Optimización 4: Validaciones y fallback
if df.empty:
    st.error("⚠️ No se pudieron obtener datos. Intentando de nuevo...")
    st.stop()

# Crear gráfico base con estilo TradingView
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
        line=dict(width=1)
    )
])

# Añadir fondo de sesiones optimizado
session_count = add_session_background(fig, df)

# Añadir indicadores usando funciones refactorizadas
fvg_count = add_fvg_indicators(fig, df, signals["fvg"])
ob_count = add_order_blocks(fig, df, signals["orderblocks"])
bos_choch_count = add_bos_choch(fig, df, signals["bos_choch"])
liq_count = add_liquidity_sweeps(fig, df, signals["liquidity"])
swing_high_count, swing_low_count = add_swing_points(fig, df, signals["swing_highs_lows"])

# Configurar el layout con estilo TradingView
fig.update_layout(
    paper_bgcolor='#1E1E1E',
    plot_bgcolor='#1E1E1E',
    title={
        'text': f"{symbol} • {timeframe} • Smart Money Concepts",
        'font': {'size': 18, 'color': '#FFFFFF', 'family': 'Arial'},
        'x': 0.5,
        'xanchor': 'center'
    },
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
        title=dict(text='Tiempo', font=dict(color='#FFFFFF'))
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
        side='right'
    ),
    xaxis_rangeslider_visible=False,
    showlegend=False,
    height=650,
    hovermode='x unified',
    margin=dict(l=0, r=60, t=50, b=0),
    xaxis_showspikes=True,
    yaxis_showspikes=True,
    spikedistance=1000,
    hoverdistance=100
)

# Mostrar el gráfico
st.plotly_chart(fig, use_container_width=True, config={
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
    'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawrect'],
    'scrollZoom': True
})

# Calcular tiempo de carga
load_time = time.time() - start_time

# Panel de métricas mejorado
st.sidebar.markdown("### 📊 Indicadores SMC Detectados")
col1, col2 = st.sidebar.columns(2)

with col1:
    st.metric("🔹 FVGs", fvg_count, help="Fair Value Gaps detectados")
    st.metric("🔸 Order Blocks", ob_count, help="Order Blocks detectados")
    st.metric("🔹 BOS/CHoCH", bos_choch_count, help="Break of Structure / Change of Character")

with col2:
    st.metric("🔸 Liquidity", liq_count, help="Barridos de liquidez")
    st.metric("🔹 Swing Highs", swing_high_count, help="Máximos de swing")
    st.metric("🔸 Swing Lows", swing_low_count, help="Mínimos de swing")

# Información adicional con métricas de rendimiento
current_session = get_current_session(df.iloc[-1]["timestamp"])
st.sidebar.markdown("### ℹ️ Información del Mercado")
st.sidebar.info(f"""
**Símbolo:** {symbol}
**Timeframe:** {timeframe}
**Velas:** {len(df)} datos
**Sesión actual:** {current_session}
**Última actualización:** {df.iloc[-1]['timestamp'].strftime('%H:%M:%S')}
**Precio actual:** ${df.iloc[-1]['close']:,.2f}
**Cambio:** {((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100):+.2f}%
""")

# 📊 Optimización 5: Métricas de rendimiento
st.sidebar.markdown("### ⚡ Rendimiento")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("📶 Latencia (s)", f"{load_time:.2f}")
with col2:
    st.metric("🎯 Sesiones", session_count)

# Leyenda de colores
st.sidebar.markdown("### 🎨 Leyenda de Indicadores")
st.sidebar.markdown("""
<div style="background-color: #1E1E1E; padding: 10px; border-radius: 5px; color: white;">
<b>FVG (Fair Value Gaps):</b><br>
🔹 <span style="color: #2962FF;">Azul</span> = Alcista<br>
🔸 <span style="color: #FF6D00;">Naranja</span> = Bajista<br><br>

<b>Order Blocks:</b><br>
🔹 <span style="color: #4CAF50;">Verde</span> = Alcista<br>
🔸 <span style="color: #F44336;">Rojo</span> = Bajista<br><br>

<b>Sesiones:</b><br>
🔹 <span style="color: #FF9800;">Tokio</span> = Naranja<br>
🔸 <span style="color: #2196F3;">Londres</span> = Azul<br>
🔹 <span style="color: #4CAF50;">Nueva York</span> = Verde<br>
</div>
""", unsafe_allow_html=True)

# Controles de la aplicación
st.sidebar.markdown("### ⚙️ Controles")
if st.sidebar.button("🔄 Refrescar Datos", help="Actualizar datos del mercado"):
    st.cache_data.clear()
    st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
💡 <b>TradingView Style SMC</b><br>
Smart Money Concepts optimizado<br>
<i>Desarrollado con ❤️ para traders</i>
</div>
""", unsafe_allow_html=True)
