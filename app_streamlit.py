import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fetch_data import get_ohlcv, get_ohlcv_extended
from smc_analysis import analyze, get_current_session, get_session_color
from smc_integration import get_smc_bot_analysis, add_bot_signals_to_chart, display_bot_metrics, add_signals_statistics_to_chart
from smc_historical import create_historical_manager, HistoricalPeriod
from smc_historical_viz import create_historical_visualizer, display_historical_controls
from smc_trade_engine import get_trade_engine_analysis, TradeSignal, SignalType
from smc_backtester import run_backtest_analysis

# Advertencia Streamlit: missing ScriptRunContext
# Solución: ignorar warning si aparece, pero loguear para debug
import warnings
try:
    import streamlit.runtime.scriptrunner
except ImportError:
    pass
else:
    warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")

# Funciones auxiliares para validar datos y crear gráficos optimizados
def validate_and_fix_chart_data(df):
    """
    Validar y corregir datos del gráfico para evitar problemas de renderizado

    Args:
        df: DataFrame con datos OHLC

    Returns:
        DataFrame corregido
    """
    if df.empty:
        return df

    # Crear copia para evitar modificar el original
    df_fixed = df.copy()

    # Asegurar que timestamp es datetime
    if 'timestamp' in df_fixed.columns:
        df_fixed['timestamp'] = pd.to_datetime(df_fixed['timestamp'])

    # Validar que tenemos las columnas necesarias
    required_columns = ['open', 'high', 'low', 'close', 'timestamp']
    missing_columns = [col for col in required_columns if col not in df_fixed.columns]

    if missing_columns:
        st.error(f"❌ Faltan columnas requeridas: {missing_columns}")
        return pd.DataFrame()

    # Eliminar filas con valores NaN en precios
    df_fixed = df_fixed.dropna(subset=['open', 'high', 'low', 'close'])

    # Validar que high >= low
    invalid_rows = df_fixed[df_fixed['high'] < df_fixed['low']]
    if len(invalid_rows) > 0:
        st.warning(f"⚠️ Corrigiendo {len(invalid_rows)} filas con high < low")
        df_fixed.loc[df_fixed['high'] < df_fixed['low'], 'high'] = df_fixed.loc[df_fixed['high'] < df_fixed['low'], 'low']

    # Validar que high >= max(open, close) y low <= min(open, close)
    df_fixed['high'] = df_fixed[['high', 'open', 'close']].max(axis=1)
    df_fixed['low'] = df_fixed[['low', 'open', 'close']].min(axis=1)

    # Ordenar por timestamp
    df_fixed = df_fixed.sort_values('timestamp')

    # Resetear índice
    df_fixed = df_fixed.reset_index(drop=True)

    return df_fixed

def create_optimized_chart(df):
    """
    Crear gráfico optimizado con configuración mejorada

    Args:
        df: DataFrame con datos OHLC validados

    Returns:
        Figura de plotly optimizada
    """
    if df.empty:
        # Crear gráfico vacío si no hay datos
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
            # Configuración de hover mejorada
            hoverinfo='x+y',
            hovertext=[f"Apertura: ${row['open']:,.2f}<br>Máximo: ${row['high']:,.2f}<br>Mínimo: ${row['low']:,.2f}<br>Cierre: ${row['close']:,.2f}"
                      for _, row in df.iterrows()]
        )
    ])

    return fig

def show_temp_message(message_type, message, duration=5):
    """
    Mostrar mensaje temporal (simplificado para evitar acumulación)

    Args:
        message_type: 'success', 'info', 'warning', 'error'
        message: texto del mensaje
        duration: duración en segundos (no implementado, solo para compatibilidad)
    """
    # Para evitar acumulación de mensajes, solo mostramos los más importantes
    # y usamos un enfoque más discreto
    if message_type == 'error':
        st.error(message)
    elif 'completado' in message.lower() or 'renderizado' in message.lower():
        # Solo mostrar mensajes importantes
        st.success(message)
    # Los demás mensajes se omiten para evitar spam

def consolidate_smc_metrics(smc_analysis, bot_analysis):
    """
    Consolidar métricas SMC para evitar duplicaciones y inconsistencias

    Args:
        smc_analysis: Análisis SMC básico
        bot_analysis: Análisis del bot SMC

    Returns:
        Dict con métricas consolidadas
    """
    consolidated = {
        'fvg_count': 0,
        'order_blocks_count': 0,
        'bos_choch_count': 0,
        'liquidity_count': 0,
        'swing_highs_count': 0,
        'swing_lows_count': 0,
        'total_swings': 0
    }

    try:
        # Contar FVGs
        if 'fvg' in smc_analysis and smc_analysis['fvg'] is not None:
            fvg_data = smc_analysis['fvg']
            if hasattr(fvg_data, 'FVG') and hasattr(fvg_data['FVG'], 'notna'):
                consolidated['fvg_count'] = int(fvg_data['FVG'].notna().sum())

        # Contar Order Blocks
        if 'orderblocks' in smc_analysis and smc_analysis['orderblocks'] is not None:
            ob_data = smc_analysis['orderblocks']
            if hasattr(ob_data, 'OB') and hasattr(ob_data['OB'], 'notna'):
                consolidated['order_blocks_count'] = int(ob_data['OB'].notna().sum())

        # Contar BOS/CHoCH
        if 'bos_choch' in smc_analysis and smc_analysis['bos_choch'] is not None:
            bos_data = smc_analysis['bos_choch']
            if hasattr(bos_data, 'BOS') and hasattr(bos_data['BOS'], 'notna'):
                # Contar ambas columnas BOS y CHOCH (igual que en display_bot_metrics)
                bos_count = int(bos_data['BOS'].notna().sum())
                choch_count = 0
                if hasattr(bos_data, 'CHOCH') and hasattr(bos_data['CHOCH'], 'notna'):
                    choch_count = int(bos_data['CHOCH'].notna().sum())
                consolidated['bos_choch_count'] = bos_count + choch_count

        # Contar Liquidity
        if 'liquidity' in smc_analysis and smc_analysis['liquidity'] is not None:
            liq_data = smc_analysis['liquidity']
            if hasattr(liq_data, 'Liquidity') and hasattr(liq_data['Liquidity'], 'notna'):
                consolidated['liquidity_count'] = int(liq_data['Liquidity'].notna().sum())

        # Contar Swings
        if 'swing_highs_lows' in smc_analysis and smc_analysis['swing_highs_lows'] is not None:
            swings_data = smc_analysis['swing_highs_lows']
            if hasattr(swings_data, 'HighLow') and hasattr(swings_data['HighLow'], 'notna'):
                total_swings = int(swings_data['HighLow'].notna().sum())
                consolidated['total_swings'] = total_swings
                # Separar highs y lows aproximadamente
                consolidated['swing_highs_count'] = total_swings // 2
                consolidated['swing_lows_count'] = total_swings // 2

    except Exception as e:
        st.error(f"Error consolidando métricas: {e}")
        # En caso de error, devolver valores por defecto
        pass

    return consolidated

def display_trade_signals(trade_analysis: Dict):
    """Mostrar señales del motor de trading en el sidebar"""
    if not trade_analysis or trade_analysis['signal_count'] == 0:
        st.sidebar.info("📊 No hay señales de trading activas")
        return

    st.sidebar.markdown("### ⚡ Señales de Trading TJR")

    signals = trade_analysis['signals']

    for i, signal in enumerate(signals[:3]):  # Mostrar máximo 3 señales
        signal_color = "🟢" if signal.signal_type == SignalType.LONG else "🔴"
        confidence_percent = signal.confidence * 100

        with st.sidebar.expander(f"{signal_color} {signal.signal_type.value} #{i+1} ({confidence_percent:.0f}%)", expanded=True):
            st.markdown(f"""
            **💰 Entrada:** ${signal.entry_price:.2f}
            **🛑 Stop Loss:** ${signal.stop_loss:.2f}
            **🎯 Take Profit:** ${signal.take_profit:.2f}
            **📊 Risk/Reward:** {signal.risk_reward:.1f}:1
            **🔒 Confianza:** {confidence_percent:.0f}%
            **⏰ Tiempo:** {signal.timestamp.strftime('%H:%M:%S')}
            **🎨 Confirmación:** {signal.confirmation_type.value}

            **📋 Setup Detectado:**
            - Sweep: {signal.setup_components['sweep']['type']}
            - Zona: {signal.setup_components['zone']['type']}
            - Confirmación: {signal.setup_components['confirmation']['direction']}
            """)

    # Estadísticas del motor
    if trade_analysis.get('engine_status') == 'active':
        st.sidebar.markdown("### 📊 Estado del Motor")
        settings = trade_analysis.get('settings', {})
        st.sidebar.info(f"""
        **Motor:** ✅ Activo
        **RR Mínimo:** {settings.get('min_rr', 'N/A')}:1
        **Riesgo Máx:** {settings.get('max_risk_percent', 'N/A')}%
        **Última Actualización:** {datetime.now().strftime('%H:%M:%S')}
        """)

st.set_page_config(layout="wide", page_title="Smart Money Concepts - TradingView Style")
st.title("📊 Smart Money Concepts - TradingView Style")

# --- SIDEBAR CONTROLS ---

# --- CONTROLES SIDEBAR ---
symbol = st.sidebar.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m"])
data_days = st.sidebar.selectbox("Días de datos", [1, 3, 5, 7, 14, 30], index=2)
refresh_interval = st.sidebar.selectbox("Intervalo de refresco (seg)", [0, 30, 60, 120], index=0)
bot_enabled = st.sidebar.checkbox("Habilitar SMC Bot", value=True)
show_signals = st.sidebar.checkbox("Mostrar Señales", value=True)
show_bot_metrics = st.sidebar.checkbox("Mostrar Métricas", value=True)
trade_engine_enabled = st.sidebar.checkbox("Habilitar Motor de Trading", value=False)
if trade_engine_enabled:
    min_risk_reward = st.sidebar.slider("Risk/Reward Mínimo", 1.5, 5.0, 2.0, 0.5)
    max_risk_percent = st.sidebar.slider("Riesgo Máximo (%)", 0.5, 5.0, 1.0, 0.5)
    show_trade_signals = st.sidebar.checkbox("Mostrar Señales de Trading", value=True)
    show_trade_stats = st.sidebar.checkbox("Estadísticas de Trading", value=True)
backtesting_enabled = st.sidebar.checkbox("Habilitar Backtesting", value=False)
if backtesting_enabled:
    initial_capital = st.sidebar.number_input("Capital Inicial ($)", min_value=1000, max_value=1000000, value=10000, step=1000)
    risk_per_trade = st.sidebar.slider("Riesgo por Trade (%)", 0.5, 5.0, 1.0, 0.5)
    show_backtest_chart = st.sidebar.checkbox("Mostrar Gráfico de Performance", value=True)
    show_backtest_report = st.sidebar.checkbox("Mostrar Reporte Detallado", value=True)

# --- CONTROL PARA OPEN INTEREST ---
show_open_interest = st.sidebar.checkbox("Mostrar Open Interest (Binance Futures)", value=False, help="Overlay de interés abierto real sobre el gráfico principal.")

# Configuración histórica
st.sidebar.markdown("### 📅 Historical Analysis")
enable_historical = st.sidebar.checkbox("Habilitar Análisis Histórico", value=False, help="Navegar por el histórico del par")
historical_period = st.sidebar.selectbox(
    "Período Histórico",
    options=[
        ("1 Hora", HistoricalPeriod.HOUR_1),
        ("4 Horas", HistoricalPeriod.HOURS_4),
        ("12 Horas", HistoricalPeriod.HOURS_12),
        ("1 Día", HistoricalPeriod.DAY_1),
        ("3 Días", HistoricalPeriod.DAYS_3),
        ("1 Semana", HistoricalPeriod.WEEK_1),
        ("2 Semanas", HistoricalPeriod.WEEKS_2),
        ("1 Mes", HistoricalPeriod.MONTH_1)
    ],
    format_func=lambda x: x[0],
    index=3,  # Default: 1 Día
    help="Período histórico para el análisis"
)

show_future_signals = st.sidebar.checkbox("Mostrar Señales Futuras", value=False, help="Preview de señales futuras (solo en modo histórico)")
show_historical_charts = st.sidebar.checkbox("Gráficos Históricos", value=False, help="Mostrar gráficos de evolución histórica")

# --- TABS PRINCIPALES ---
tab_overview, tab_setups, tab_signals, tab_backtest, tab_config = st.tabs([
    "Visión General", "Setups & Confluencias", "Señales y Trading", "Backtesting & Histórico", "Configuración"
])

# --- VISIÓN GENERAL ---
with tab_overview:
    st.header("Visión General del Mercado")

    # Obtener datos y análisis
    if enable_historical:
        # Modo histórico
        if 'historical_manager' not in st.session_state:
            st.session_state.historical_manager = create_historical_manager(symbol, timeframe)
            st.session_state.historical_visualizer = create_historical_visualizer(st.session_state.historical_manager)

        # Generar timeline si no existe
        if not st.session_state.historical_manager.snapshots:
            with st.spinner("📅 Generando timeline histórico detallado..."):
                # Intentar cargar desde cache primero
                timeline = st.session_state.historical_manager.load_timeline_from_cache(historical_period[1])

                if timeline:
                    st.session_state.historical_manager.snapshots = timeline
                    st.success(f"📂 Timeline cargado desde cache: {len(timeline)} puntos históricos")
                else:
                    # Generar nuevo timeline
                    timeline = st.session_state.historical_manager.create_detailed_historical_timeline(
                        historical_period[1],
                        intervals=15  # Más puntos para mejor navegación
                    )
                    st.success(f"✅ Timeline generado con {len(timeline)} puntos históricos")

        # Controles de navegación histórica
        nav_info = st.session_state.historical_visualizer.create_enhanced_historical_controls()

        # Obtener snapshot actual
        current_snapshot = st.session_state.historical_visualizer.get_current_snapshot()

        if current_snapshot:
            df = current_snapshot.df
            bot_analysis = current_snapshot.bot_analysis

            # Mostrar información del snapshot
            st.info(f"📅 Mostrando datos históricos para: {current_snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            # Análisis básico (para compatibilidad con el resto del código)
            signals = analyze(df)
        else:
            st.error("❌ No se pudo obtener snapshot histórico")
            df = pd.DataFrame()
            signals = {}
            bot_analysis = None
    else:
        # Modo tiempo real
        with st.spinner(f"📊 Cargando {data_days} días de datos para {symbol}..."):
            df = get_ohlcv_extended(symbol, timeframe, days=data_days)
            if len(df) > 0:
                show_temp_message('success', f"✅ Cargados {len(df)} puntos de datos desde {df['timestamp'].min().strftime('%Y-%m-%d %H:%M')} hasta {df['timestamp'].max().strftime('%Y-%m-%d %H:%M')}")
            else:
                st.error("❌ No se pudieron cargar los datos")
                st.stop()

        # Análisis básico
        with st.spinner("🔍 Analizando datos..."):
            signals = analyze(df)
            show_temp_message('success', "✅ Análisis básico completado")

        # Análisis del bot SMC
        bot_analysis = None
        if bot_enabled:
            try:
                with st.spinner("🤖 Ejecutando análisis SMC Bot..."):
                    bot_analysis = get_smc_bot_analysis(df)
                    show_temp_message('success', "✅ Análisis SMC Bot completado")
            except Exception as e:
                st.sidebar.error(f"Error en SMC Bot: {e}")
                st.error(f"❌ Error detallado en SMC Bot: {str(e)}")
                bot_analysis = None

        # Análisis del Motor de Trading TJR
        trade_analysis = None
        if trade_engine_enabled and bot_analysis:
            try:
                with st.spinner("⚡ Ejecutando Motor de Trading TJR..."):
                    trade_analysis = get_trade_engine_analysis(df, bot_analysis)
                    if trade_analysis['signal_count'] > 0:
                        show_temp_message('success', f"✅ Motor TJR: {trade_analysis['signal_count']} señales detectadas")
                    else:
                        st.info("ℹ️ Motor TJR: No hay señales en este momento")
            except Exception as e:
                st.sidebar.error(f"Error en Motor TJR: {e}")
                st.error(f"❌ Error detallado en Motor TJR: {str(e)}")
                trade_analysis = None

        # Backtesting Analysis
        backtest_analysis = None
        if backtesting_enabled and trade_analysis and trade_analysis['signal_count'] > 0:
            try:
                with st.spinner("📈 Ejecutando Backtesting..."):
                    backtest_analysis = run_backtest_analysis(
                        df,
                        trade_analysis['signals'],
                        initial_capital,
                        risk_per_trade
                    )
                    if backtest_analysis['success']:
                        results = backtest_analysis['results']
                        st.success(f"✅ Backtesting: {results.total_trades} trades, Win Rate: {results.win_rate:.1f}%")
                    else:
                        st.warning("⚠️ Backtesting: No se pudieron procesar señales")
            except Exception as e:
                st.sidebar.error(f"Error en Backtesting: {e}")
                st.error(f"❌ Error detallado en Backtesting: {str(e)}")
                backtest_analysis = None

    # Verificar que tenemos datos y validarlos
    if df.empty:
        st.error("❌ No hay datos disponibles para mostrar")
        st.stop()

    st.info(f"🔍 Validando datos: {len(df)} filas")

    # Validar y corregir datos del gráfico
    with st.spinner("🔧 Validando y corrigiendo datos del gráfico..."):
        df_fixed = validate_and_fix_chart_data(df)
        show_temp_message('success', f"✅ Datos validados: {len(df_fixed)} filas válidas")

    if df_fixed.empty:
        st.error("❌ Los datos no son válidos para crear el gráfico")
        st.stop()

    # Usar datos validados para el resto del análisis
    df = df_fixed


    # Crear gráfico base con estilo TradingView
    with st.spinner("📊 Creando gráfico base..."):
        fig = create_optimized_chart(df)
        show_temp_message('success', "✅ Gráfico base creado")

    # --- OVERLAY OPEN INTEREST (si está activado) ---
    if show_open_interest:
        try:
            oi_df = pd.read_csv("open_interest_btcusdt.csv")
            oi_df['timestamp'] = pd.to_datetime(oi_df['timestamp'])
            # Filtrar por rango de fechas del gráfico principal
            min_time = df['timestamp'].min()
            max_time = df['timestamp'].max()
            oi_df = oi_df[(oi_df['timestamp'] >= min_time) & (oi_df['timestamp'] <= max_time)]
            # Añadir traza de Open Interest (línea, eje secundario)
            fig.add_trace(go.Scatter(
                x=oi_df['timestamp'],
                y=oi_df['sumOpenInterest'].astype(float),
                mode='lines',
                name='Open Interest',
                line=dict(color='#FFD700', width=2, dash='dot'),
                yaxis='y2',
                hovertemplate='Open Interest: %{y}<br>Time: %{x}<extra></extra>'
            ))
            # Configurar eje secundario
            fig.update_layout(
                yaxis2=dict(
                    title=dict(text='Open Interest', font=dict(color='#FFD700')),
                    overlaying='y',
                    side='left',
                    showgrid=False,
                    tickfont=dict(color='#FFD700'),
                )
            )
            st.info("🟡 Open Interest overlay añadido (Binance Futures)")
        except Exception as e:
            st.warning(f"No se pudo cargar el Open Interest: {e}")

    # Renderizado condicional basado en volumen de datos
    data_points = len(df)
    render_full_features = data_points < 200  # Solo características completas si hay pocos datos

    if render_full_features:
        st.info(f"🎨 Renderizado completo habilitado ({data_points} puntos de datos)")
    else:
        st.info(f"⚡ Renderizado optimizado habilitado ({data_points} puntos de datos)")

    # 📊 Calcular métricas consolidadas para evitar duplicaciones e inconsistencias
    consolidated_metrics = consolidate_smc_metrics(signals, bot_analysis)

    # 🌍 Obtener sesión actual
    current_session = get_current_session(datetime.now())
    session_names_full = {
        "tokyo": "Sesión de Tokio 🇯🇵",
        "london": "Sesión de Londres 🇬🇧",
        "new_york": "Sesión de Nueva York 🇺🇸",
        "between_sessions": "Entre Sesiones 💤"
    }

    # ➕ Añadir FVGs con renderizado condicional
    with st.spinner("📊 Añadiendo FVGs..."):
        fvg_data = signals["fvg"]
        fvg_count = 0

        if render_full_features:
            # Versión completa - todos los FVGs con annotations
            for i, row in fvg_data.iterrows():
                if pd.notna(row["FVG"]):
                    fvg_count += 1
                    is_bullish = row["FVG"] == 1

                    # Colores TradingView para FVG
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

                    # Añadir texto identificativo "FVG" solo para algunos
                    if fvg_count % 3 == 0:
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

            show_temp_message('success', f"✅ {fvg_count} FVGs añadidos (completos)")
        else:
            # Versión optimizada - todos los FVGs pero sin annotations excesivas
            for i, row in fvg_data.iterrows():
                if pd.notna(row["FVG"]):
                    fvg_count += 1
                    is_bullish = row["FVG"] == 1

                    # Colores TradingView para FVG
                    color = '#2962FF' if is_bullish else '#FF6D00'

                    # Añadir rectángulo FVG
                    fig.add_shape(
                        type="rect",
                        x0=df.iloc[i]["timestamp"],
                        x1=df.iloc[min(i+8, len(df)-1)]["timestamp"],
                        y0=row["Bottom"],
                        y1=row["Top"],
                        fillcolor=color,
                        opacity=0.2,
                        line=dict(color=color, width=1)
                    )

                    # Añadir texto solo para los FVGs más importantes (cada 10)
                    if fvg_count % 10 == 0:
                        fig.add_annotation(
                            x=df.iloc[min(i+2, len(df)-1)]["timestamp"],
                            y=(row["Top"] + row["Bottom"]) / 2,
                            text="FVG",
                            showarrow=False,
                            font=dict(size=8, color=color, family="Arial Black"),
                            bgcolor="rgba(255,255,255,0.6)",
                            bordercolor=color,
                            borderwidth=1
                        )

            show_temp_message('success', f"✅ {fvg_count} FVGs añadidos (optimizados)")

    # ➕ Añadir Order Blocks con estilo TradingView y texto identificativo
    ob_data = signals["orderblocks"]
    ob_count = 0
    for i, row in ob_data.iterrows():
        if pd.notna(row["OB"]):
            ob_count += 1
            is_bullish = row["OB"] == 1

            # Colores TradingView para Order Blocks
            color = '#4CAF50' if is_bullish else '#F44336'  # Verde/Rojo TradingView

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

            # Añadir texto identificativo "OB"
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

    # ➕ Añadir BOS/CHoCH con estilo TradingView
    bos_choch_data = signals["bos_choch"]
    bos_choch_count = 0
    for i, row in bos_choch_data.iterrows():
        if pd.notna(row.get("Signal", row.get("BOS", row.get("CHoCH", None)))):
            bos_choch_count += 1
            signal_value = row.get("Signal", row.get("BOS", row.get("CHoCH", "BOS")))

            # Línea vertical para BOS/CHoCH
            fig.add_shape(
                type="line",
                x0=df.iloc[i]["timestamp"],
                x1=df.iloc[i]["timestamp"],
                y0=df.iloc[i]["low"] * 0.999,
                y1=df.iloc[i]["high"] * 1.001,
                line=dict(color="#9C27B0", width=3, dash="dash")  # Púrpura TradingView
            )

            # Añadir texto identificativo
            fig.add_annotation(
                x=df.iloc[i]["timestamp"],
                y=df.iloc[i]["high"] * 1.002,
                text=f"BOS" if "BOS" in str(signal_value) else "CHoCH",
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

    # ➕ Añadir Liquidity Sweeps con estilo TradingView
    liq_data = signals["liquidity"]
    liq_count = 0
    for i, row in liq_data.iterrows():
        if pd.notna(row.get("Sweep", row.get("Liquidity", None))):
            liq_count += 1
            price = row.get("Price", df.iloc[i]["high"])

            # Línea horizontal para Liquidity
            fig.add_shape(
                type="line",
                x0=df.iloc[max(0, i-5)]["timestamp"],
                x1=df.iloc[min(i+5, len(df)-1)]["timestamp"],
                y0=price,
                y1=price,
                line=dict(color="#FFD700", width=2, dash="solid")  # Dorado TradingView
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

    # ➕ Añadir Swing Highs/Lows con estilo TradingView
    swing_data = signals["swing_highs_lows"]
    swing_high_count = 0
    swing_low_count = 0
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

    # Configurar el layout con estilo TradingView
    fig.update_layout(
        # Fondo oscuro como TradingView
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',

        # Título y configuración
        title={
            'text': f"{symbol} • {timeframe} • Smart Money Concepts",
            'font': {'size': 18, 'color': '#FFFFFF', 'family': 'Arial'},
            'x': 0.5,
            'xanchor': 'center'
        },

        # Configuración de ejes
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
            rangeslider=dict(visible=False),  # Asegurar que no haya rangeslider
            fixedrange=False  # Permitir zoom
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
            side='right',  # Precio a la derecha como TradingView
            fixedrange=False  # Permitir zoom
        ),

        # Configuración general
        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=650,

        # Hover mode
        hovermode='x unified',

        # Márgenes ajustados para evitar truncamiento
        margin=dict(l=10, r=80, t=60, b=40),

        # Configuración del crosshair
        xaxis_showspikes=True,
        yaxis_showspikes=True,
        spikedistance=1000,
        hoverdistance=100,

        # Configuración de autosize
        autosize=True
    )

    # Configurar hover template personalizado para las velas
    fig.update_traces(
        hovertext=f"Precio: %{{y}}<br>Tiempo: %{{x}}",
        selector=dict(type="candlestick")
    )

    # Información de depuración antes del renderizado
    st.info(f"🎯 Renderizando gráfico con {len(fig.data)} trazas y {len(fig.layout.shapes)} shapes")

    # Mostrar el gráfico principal
    with st.spinner("🎨 Renderizando gráfico..."):
        st.plotly_chart(fig, use_container_width=True, key="main_chart_display", config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawrect'],
            'scrollZoom': True
        })
        show_temp_message('success', "✅ Gráfico renderizado exitosamente")


# --- SETUPS & CONFLUENCIAS ---
with tab_setups:
    st.header("Setups & Confluencias")
    # Mostrar setups del snapshot histórico si está en modo histórico y snapshot seleccionado
    show_setups = False
    setups_data = None
    if enable_historical and 'historical_manager' in st.session_state and st.session_state.historical_manager.snapshots:
        idx = st.session_state.get('snap_idx', 0)
        snapshot = st.session_state.historical_manager.snapshots[idx]
        bot_analysis_hist = getattr(snapshot, 'bot_analysis', None)
        if bot_analysis_hist and 'setups' in bot_analysis_hist and bot_analysis_hist['setups'] is not None:
            setups_data = bot_analysis_hist['setups']
            show_setups = True
    elif bot_analysis and 'setups' in bot_analysis and bot_analysis['setups'] is not None:
        setups_data = bot_analysis['setups']
        show_setups = True
    if show_setups and setups_data is not None and not setups_data.empty:
        st.subheader("Setups Detectados")
        st.dataframe(setups_data, use_container_width=True)
    else:
        st.info("No hay setups detectados.")


# --- SEÑALES Y TRADING ---
with tab_signals:
    st.header("Señales y Trading")
    # Mostrar señales del snapshot histórico si está en modo histórico y snapshot seleccionado
    show_signals_tab = False
    signals_list = None
    if enable_historical and 'historical_manager' in st.session_state and st.session_state.historical_manager.snapshots:
        idx = st.session_state.get('snap_idx', 0)
        snapshot = st.session_state.historical_manager.snapshots[idx]
        if hasattr(snapshot, 'signals') and snapshot.signals:
            signals_list = snapshot.signals
            show_signals_tab = True
    elif trade_engine_enabled and bot_analysis:
        try:
            trade_analysis = get_trade_engine_analysis(df, bot_analysis)
            if trade_analysis['signal_count'] > 0:
                signals_list = trade_analysis['signals']
                show_signals_tab = True
        except Exception as e:
            st.error(f"Error al obtener señales de trading: {e}")
    if show_signals_tab and signals_list:
        st.subheader("Señales Activas")
        for i, signal in enumerate(signals_list):
            st.write(f"{i+1}. {signal.signal_type.value} | Entrada: {signal.entry_price} | SL: {signal.stop_loss} | TP: {signal.take_profit} | Confianza: {signal.confidence:.2f}")
    else:
        st.info("No hay señales activas.")

# --- BACKTESTING & HISTÓRICO ---
with tab_backtest:
    st.header("Backtesting & Histórico")
    modo = st.radio(
        "Selecciona el modo:",
        ["Solo histórico", "Indicadores históricos", "Backtest"],
        index=0,
        help="Elige si solo quieres navegar el histórico, ver los indicadores que se habrían generado o simular el backtest de señales."
    )
    # Controles de periodo y timeframe
    st.markdown("#### Parámetros de histórico")
    symbol_hist = st.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT"], key="symbol_hist")
    timeframe_hist = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"], key="tf_hist")
    period_hist = st.selectbox(
        "Período Histórico",
        options=[
            ("1 Hora", HistoricalPeriod.HOUR_1),
            ("4 Horas", HistoricalPeriod.HOURS_4),
            ("12 Horas", HistoricalPeriod.HOURS_12),
            ("1 Día", HistoricalPeriod.DAY_1),
            ("3 Días", HistoricalPeriod.DAYS_3),
            ("1 Semana", HistoricalPeriod.WEEK_1),
            ("2 Semanas", HistoricalPeriod.WEEKS_2),
            ("1 Mes", HistoricalPeriod.MONTH_1)
        ],
        format_func=lambda x: x[0],
        index=3,
        key="period_hist"
    )
    intervals_hist = st.slider("Intervalos históricos", 5, 30, 15, 1, key="intervals_hist")
    if st.button("Cargar histórico", key="load_hist") or (
        'historical_manager' not in st.session_state or
        st.session_state.get('last_hist_params', None) != (symbol_hist, timeframe_hist, period_hist, intervals_hist)
    ):
        st.session_state.historical_manager = create_historical_manager(symbol_hist, timeframe_hist)
        st.session_state.historical_visualizer = create_historical_visualizer(st.session_state.historical_manager)
        st.session_state.historical_manager.create_detailed_historical_timeline(period_hist[1], intervals=intervals_hist)
        st.session_state.last_hist_params = (symbol_hist, timeframe_hist, period_hist, intervals_hist)
    # Mostrar timeline cargado
    if 'historical_manager' in st.session_state and st.session_state.historical_manager.snapshots:
        snapshots = st.session_state.historical_manager.snapshots
        st.success(f"Timeline cargado con {len(snapshots)} snapshots.")
        # Selector de snapshot
        idx = st.slider("Selecciona snapshot", 0, len(snapshots)-1, 0, 1, key="snap_idx")
        snapshot = snapshots[idx]
        st.info(f"Snapshot: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        # Mostrar gráfico OHLC
        # --- VISUALIZACIÓN DE INDICADORES EN EL GRÁFICO HISTÓRICO ---
        # Usar el mismo renderizado visual que en tiempo real, pero con los datos del snapshot
        df_hist = snapshot.df
        signals_hist = snapshot.bot_analysis if hasattr(snapshot, 'bot_analysis') else None
        if signals_hist is None:
            st.plotly_chart(create_optimized_chart(df_hist), use_container_width=True)
            st.info("No hay análisis de indicadores para este snapshot.")
        else:
            # Validar y corregir datos
            df_hist_fixed = validate_and_fix_chart_data(df_hist)
            fig_hist = create_optimized_chart(df_hist_fixed)
            # Renderizar indicadores visuales si existen
            try:
                # FVGs
                if 'fvg' in signals_hist and signals_hist['fvg'] is not None:
                    fvg_data = signals_hist['fvg']
                    fvg_count = 0
                    for i, row in fvg_data.iterrows():
                        if pd.notna(row.get('FVG', None)):
                            fvg_count += 1
                            is_bullish = row['FVG'] == 1
                            color = '#2962FF' if is_bullish else '#FF6D00'
                            fig_hist.add_shape(
                                type="rect",
                                x0=df_hist_fixed.iloc[i]["timestamp"],
                                x1=df_hist_fixed.iloc[min(i+8, len(df_hist_fixed)-1)]["timestamp"],
                                y0=row["Bottom"],
                                y1=row["Top"],
                                fillcolor=color,
                                opacity=0.15,
                                line=dict(color=color, width=1, dash="dot")
                            )
                            # Anotación FVG cada 3
                            if fvg_count % 3 == 0:
                                fig_hist.add_annotation(
                                    x=df_hist_fixed.iloc[min(i+2, len(df_hist_fixed)-1)]["timestamp"],
                                    y=(row["Top"] + row["Bottom"]) / 2,
                                    text="FVG",
                                    showarrow=False,
                                    font=dict(size=10, color=color, family="Arial Black"),
                                    bgcolor="rgba(255,255,255,0.8)",
                                    bordercolor=color,
                                    borderwidth=1
                                )
                # Order Blocks
                if 'orderblocks' in signals_hist and signals_hist['orderblocks'] is not None:
                    ob_data = signals_hist['orderblocks']
                    ob_count = 0
                    for i, row in ob_data.iterrows():
                        if pd.notna(row.get('OB', None)):
                            ob_count += 1
                            is_bullish = row['OB'] == 1
                            color = '#4CAF50' if is_bullish else '#F44336'
                            fig_hist.add_shape(
                                type="rect",
                                x0=df_hist_fixed.iloc[i]["timestamp"],
                                x1=df_hist_fixed.iloc[min(i+12, len(df_hist_fixed)-1)]["timestamp"],
                                y0=row["Bottom"],
                                y1=row["Top"],
                                fillcolor=color,
                                opacity=0.2,
                                line=dict(color=color, width=2)
                            )
                            # Anotación OB
                            fig_hist.add_annotation(
                                x=df_hist_fixed.iloc[min(i+3, len(df_hist_fixed)-1)]["timestamp"],
                                y=(row["Top"] + row["Bottom"]) / 2,
                                text="OB",
                                showarrow=False,
                                font=dict(size=12, color="white", family="Arial Black"),
                                bgcolor=color,
                                bordercolor=color,
                                borderwidth=1
                            )
                # BOS/CHoCH
                if 'bos_choch' in signals_hist and signals_hist['bos_choch'] is not None:
                    bos_choch_data = signals_hist['bos_choch']
                    bos_choch_count = 0
                    for i, row in bos_choch_data.iterrows():
                        val = row.get("Signal", row.get("BOS", row.get("CHoCH", None)))
                        if pd.notna(val):
                            bos_choch_count += 1
                            fig_hist.add_shape(
                                type="line",
                                x0=df_hist_fixed.iloc[i]["timestamp"],
                                x1=df_hist_fixed.iloc[i]["timestamp"],
                                y0=df_hist_fixed.iloc[i]["low"] * 0.999,
                                y1=df_hist_fixed.iloc[i]["high"] * 1.001,
                                line=dict(color="#9C27B0", width=3, dash="dash")
                            )
                            fig_hist.add_annotation(
                                x=df_hist_fixed.iloc[i]["timestamp"],
                                y=df_hist_fixed.iloc[i]["high"] * 1.002,
                                text=f"BOS" if "BOS" in str(val) else "CHoCH",
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
                # Liquidity
                if 'liquidity' in signals_hist and signals_hist['liquidity'] is not None:
                    liq_data = signals_hist['liquidity']
                    liq_count = 0
                    for i, row in liq_data.iterrows():
                        val = row.get("Sweep", row.get("Liquidity", None))
                        if pd.notna(val):
                            liq_count += 1
                            price = row.get("Price", row.get("Level", df_hist_fixed.iloc[i]["high"]))
                            fig_hist.add_shape(
                                type="line",
                                x0=df_hist_fixed.iloc[max(0, i-5)]["timestamp"],
                                x1=df_hist_fixed.iloc[min(i+5, len(df_hist_fixed)-1)]["timestamp"],
                                y0=price,
                                y1=price,
                                line=dict(color="#FFD700", width=2, dash="solid")
                            )
                            fig_hist.add_annotation(
                                x=df_hist_fixed.iloc[i]["timestamp"],
                                y=price,
                                text="LIQ",
                                showarrow=False,
                                font=dict(size=9, color="black", family="Arial Black"),
                                bgcolor="#FFD700",
                                bordercolor="#FFD700",
                                borderwidth=1
                            )
                # Swings
                if 'swing_highs_lows' in signals_hist and signals_hist['swing_highs_lows'] is not None:
                    swing_data = signals_hist['swing_highs_lows']
                    for i, row in swing_data.iterrows():
                        if pd.notna(row.get("HighLow", None)):
                            if row["HighLow"] == 1:
                                fig_hist.add_trace(go.Scatter(
                                    x=[df_hist_fixed.iloc[i]["timestamp"]],
                                    y=[df_hist_fixed.iloc[i]["high"]],
                                    mode="markers+text",
                                    marker=dict(color="#FF5722", size=12, symbol="triangle-down", line=dict(color="white", width=1)),
                                    text=["H"],
                                    textposition="middle center",
                                    textfont=dict(color="white", size=8, family="Arial Black"),
                                    name="Swing High",
                                    showlegend=False,
                                    hovertemplate="Swing High<br>Price: %{y}<br>Time: %{x}<extra></extra>"
                                ))
                            elif row["HighLow"] == -1:
                                fig_hist.add_trace(go.Scatter(
                                    x=[df_hist_fixed.iloc[i]["timestamp"]],
                                    y=[df_hist_fixed.iloc[i]["low"]],
                                    mode="markers+text",
                                    marker=dict(color="#4CAF50", size=12, symbol="triangle-up", line=dict(color="white", width=1)),
                                    text=["L"],
                                    textposition="middle center",
                                    textfont=dict(color="white", size=8, family="Arial Black"),
                                    name="Swing Low",
                                    showlegend=False,
                                    hovertemplate="Swing Low<br>Price: %{y}<br>Time: %{x}<extra></extra>"
                                ))
            except Exception as e:
                st.warning(f"Error al renderizar indicadores históricos: {e}")
            st.plotly_chart(fig_hist, use_container_width=True)
        if modo == "Solo histórico":
            st.write("Visualización simple del histórico del par.")
        elif modo == "Indicadores históricos":
            st.write("Indicadores generados en ese punto histórico:")
            st.json(snapshot.bot_analysis)
        elif modo == "Backtest":
            st.write("Señales generadas y resultados de backtest:")
            if snapshot.signals:
                st.write(f"Señales encontradas: {len(snapshot.signals)}")
                for i, sig in enumerate(snapshot.signals):
                    st.write(f"{i+1}. {sig.signal_type.value} | Entrada: {sig.entry_price} | SL: {sig.stop_loss} | TP: {sig.take_profit} | Confianza: {sig.confidence:.2f}")
            else:
                st.info("No hay señales en este snapshot.")
    else:
        st.warning("No hay timeline histórico cargado o no hay snapshots válidos.")

# --- CONFIGURACIÓN ---
with tab_config:
    st.header("Configuración de la App")
    st.write("Ajusta los parámetros y preferencias desde la barra lateral.")
    st.write("- Símbolo, timeframe, días de datos, refresco, SMC Bot, Motor de Trading, Backtesting, Histórico, etc.")
    st.write("- Usa la barra lateral para cambiar la configuración y refrescar los datos.")

# ➕ Panel de métricas mejorado con estilo TradingView
st.markdown("""
<style>
.metric-container {
    background-color: #1E1E1E;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #2A2A2A;
    margin: 5px 0;
}
.metric-title {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: bold;
}
.metric-value {
    color: #26A69A;
    font-size: 18px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📊 Indicadores SMC Detectados")
col1, col2 = st.sidebar.columns(2)

with col1:
    st.metric("🔹 FVGs", consolidated_metrics['fvg_count'], help="Fair Value Gaps detectados")
    st.metric("🔸 Order Blocks", consolidated_metrics['order_blocks_count'], help="Order Blocks detectados")
    st.metric("🔹 BOS/CHoCH", consolidated_metrics['bos_choch_count'], help="Break of Structure / Change of Character")

with col2:
    st.metric("🔸 Liquidity", consolidated_metrics['liquidity_count'], help="Barridos de liquidez")
    st.metric("🔹 Swing Highs", consolidated_metrics['swing_highs_count'], help="Máximos de swing")
    st.metric("🔸 Swing Lows", consolidated_metrics['swing_lows_count'], help="Mínimos de swing")

# ➕ Información de sesión actual
st.sidebar.markdown("### 🌍 Sesión Actual")
session_info = session_names_full.get(current_session, "Desconocida")
session_color_hex = {
    "tokyo": "#FFC107",
    "london": "#4CAF50",
    "new_york": "#2196F3",
    "between_sessions": "#9E9E9E"
}
color = session_color_hex.get(current_session, "#9E9E9E")

st.sidebar.markdown(f"""
<div style="background: linear-gradient(90deg, {color}22 0%, {color}11 100%);
           padding: 15px; border-radius: 10px; border-left: 4px solid {color};">
    <h4 style="color: {color}; margin: 0;">{session_info}</h4>
    <p style="color: #888; margin: 5px 0 0 0; font-size: 12px;">
        Horarios de sesión en UTC:<br>
        🇯🇵 Tokyo: 23:00 - 08:00<br>
        🇬🇧 London: 08:00 - 16:00<br>
        🇺🇸 NY: 13:00 - 22:00
    </p>
</div>
""", unsafe_allow_html=True)

# ➕ Información adicional con estilo TradingView
st.sidebar.markdown("### ℹ️ Información del Mercado")
st.sidebar.info(f"""
**Símbolo:** {symbol}
**Timeframe:** {timeframe}
**Velas:** {len(df)} datos
**Última actualización:** {df.iloc[-1]['timestamp'].strftime('%H:%M:%S')}
**Precio actual:** ${df.iloc[-1]['close']:,.2f}
**Cambio:** {((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100):+.2f}%
""")

# ➕ Leyenda de colores estilo TradingView
st.sidebar.markdown("### 🎨 Leyenda de Indicadores")
st.sidebar.markdown("""
<div style="background-color: #1E1E1E; padding: 10px; border-radius: 5px; color: white;">
<b>Sesiones de Trading:</b><br>
🇯🇵 <span style="color: #FFC107;">Tokyo</span> - Amarillo suave<br>
🇬🇧 <span style="color: #4CAF50;">London</span> - Verde suave<br>
🇺🇸 <span style="color: #2196F3;">NY</span> - Azul suave<br><br>

<b>FVG (Fair Value Gaps):</b><br>
🔹 <span style="color: #2962FF;">Azul</span> = Alcista<br>
🔸 <span style="color: #FF6D00;">Naranja</span> = Bajista<br><br>

<b>Order Blocks:</b><br>
🔹 <span style="color: #4CAF50;">Verde</span> = Alcista<br>
🔸 <span style="color: #F44336;">Rojo</span> = Bajista<br><br>

<b>Otros Indicadores:</b><br>
🔹 <span style="color: #9C27B0;">Púrpura</span> = BOS/CHoCH<br>
🔸 <span style="color: #FFD700;">Dorado</span> = Liquidez<br>
🔹 <span style="color: #FF5722;">Rojo</span> = Swing High<br>
🔸 <span style="color: #4CAF50;">Verde</span> = Swing Low<br>
</div>
""", unsafe_allow_html=True)

# ➕ Controles de la aplicación
st.sidebar.markdown("### ⚙️ Controles")
if st.sidebar.button("🔄 Refrescar Datos", help="Actualizar datos del mercado"):
    st.rerun()

# ➕ Integración del bot SMC
if bot_enabled and bot_analysis:
    if show_signals:
        if enable_historical and current_snapshot:
            # Modo histórico - usar visualizador histórico mejorado
            st.session_state.historical_visualizer.add_enhanced_historical_signals_to_chart(
                fig, current_snapshot, show_future_signals, show_signal_evolution=True
            )
            # Añadir timeline al gráfico
            st.session_state.historical_visualizer.add_historical_timeline_to_chart(fig)
        else:
            # Modo tiempo real - visualización normal
            add_bot_signals_to_chart(fig, df, bot_analysis)

        # Añadir estadísticas de señales al gráfico
        add_signals_statistics_to_chart(fig, bot_analysis)

# ➕ Mostrar gráficos históricos si están habilitados
if enable_historical and show_historical_charts and 'historical_visualizer' in st.session_state:
    st.markdown("## 📈 Análisis Histórico Avanzado")

    # Crear tabs para diferentes gráficos
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Evolución Señales", "💰 Risk:Reward", "🎯 Confianza", "🏦 Mercado"])

    with tab1:
        st.markdown("### 📊 Evolución de Señales en el Tiempo")
        try:
            evolution_chart = st.session_state.historical_visualizer.create_historical_evolution_chart()
            if evolution_chart and evolution_chart.data:
                st.plotly_chart(evolution_chart, use_container_width=True, key="evolution_chart")
            else:
                st.info("📊 No hay datos suficientes para mostrar evolución de señales")
        except Exception as e:
            st.error(f"Error creando gráfico de evolución: {e}")

    with tab2:
        st.markdown("### 💰 Evolución Risk:Reward")
        try:
            rr_chart = st.session_state.historical_visualizer.create_rr_evolution_chart()
            if rr_chart and rr_chart.data:
                st.plotly_chart(rr_chart, use_container_width=True, key="rr_chart")
            else:
                st.info("💰 No hay datos suficientes para mostrar evolución R:R")
        except Exception as e:
            st.error(f"Error creando gráfico R:R: {e}")

    with tab3:
        st.markdown("### 🎯 Evolución de Confianza")
        try:
            confidence_chart = st.session_state.historical_visualizer.create_confidence_evolution_chart()
            if confidence_chart and confidence_chart.data:
                st.plotly_chart(confidence_chart, use_container_width=True, key="confidence_chart")
            else:
                st.info("🎯 No hay datos suficientes para mostrar evolución de confianza")
        except Exception as e:
            st.error(f"Error creando gráfico de confianza: {e}")

    with tab4:
        st.markdown("### 🏦 Condiciones del Mercado")
        try:
            market_chart = st.session_state.historical_visualizer.create_market_conditions_chart()
            if market_chart and market_chart.data:
                st.plotly_chart(market_chart, use_container_width=True, key="market_chart")
            else:
                st.info("🏦 No hay datos suficientes para mostrar condiciones del mercado")
        except Exception as e:
            st.error(f"Error creando gráfico de mercado: {e}")

    # Mostrar análisis de rendimiento histórico
    if st.session_state.historical_manager.snapshots:
        st.markdown("### 📋 Análisis de Rendimiento Histórico Detallado")

        # Obtener estadísticas detalladas
        stats = st.session_state.historical_manager.get_signal_statistics()

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

            # Información adicional en tabs
            tab1, tab2, tab3 = st.tabs(["📈 Estadísticas", "⏰ Período", "🔍 Detalles"])

            with tab1:
                col1, col2 = st.columns(2)

                with col1:
                    st.info(f"""
                    **🎯 Calidad de Señales:**
                    - Total snapshots: {stats['snapshots_count']}
                    - Señales por snapshot: {stats['total_signals']/max(stats['snapshots_count'], 1):.1f}
                    - Ratio BUY/SELL: {stats['buy_signals']/max(stats['sell_signals'], 1):.2f}
                    """)

                with col2:
                    st.info(f"""
                    **💰 Métricas de Riesgo:**
                    - R:R Promedio: {stats['avg_rr']:.2f}:1
                    - Confianza Media: {stats['avg_confidence']:.1%}
                    - Señales BUY: {stats['buy_signals']/max(stats['total_signals'], 1):.1%}
                    """)

            with tab2:
                duration = stats['timespan']['duration']
                hours = duration.total_seconds() / 3600

                st.info(f"""
                **⏱️ Período Analizado:**
                - Inicio: {stats['timespan']['start'].strftime('%Y-%m-%d %H:%M:%S')}
                - Fin: {stats['timespan']['end'].strftime('%Y-%m-%d %H:%M:%S')}
                - Duración: {str(duration).split('.')[0]}
                - Horas totales: {hours:.1f}h
                """)

            with tab3:
                st.info(f"""
                **🔍 Análisis Detallado:**
                - Símbolo: {symbol}
                - Timeframe: {timeframe}
                - Período histórico: {historical_period[0]}
                - Snapshots generados: {stats['snapshots_count']}
                - Datos por snapshot: ~{100} velas
                """)

            # Progreso del análisis histórico
            if len(st.session_state.historical_manager.snapshots) > 0:
                current_pos = st.session_state.historical_visualizer.current_snapshot_index
                total_pos = len(st.session_state.historical_manager.snapshots)
                progress = (current_pos + 1) / total_pos

                st.progress(progress, text=f"Navegación histórica: {current_pos + 1}/{total_pos}")
        else:
            st.warning("⚠️ No hay estadísticas históricas disponibles")

# ➕ Función para auto-navegación histórica
def auto_navigate_historical():
    """
    Función para navegación automática en modo histórico
    """
    if 'historical_visualizer' in st.session_state:
        visualizer = st.session_state.historical_visualizer

        if visualizer.is_playing and len(visualizer.manager.snapshots) > 0:
            # Avanzar al siguiente snapshot
            max_index = len(visualizer.manager.snapshots) - 1

            if visualizer.current_snapshot_index < max_index:
                visualizer.current_snapshot_index += 1
                time.sleep(2.0 / visualizer.playback_speed)  # Velocidad controlada
                st.rerun()
            else:
                # Llegamos al final, detener reproducción
                visualizer.is_playing = False
                st.success("🎬 Reproducción histórica completada")
                st.rerun()

# Añadir auto-navegación si está habilitada
if enable_historical and 'historical_visualizer' in st.session_state:
    if st.session_state.historical_visualizer.is_playing:
        auto_navigate_historical()

# ➕ Auto-refresh con estilo TradingView (solo en modo tiempo real)
if not enable_historical and refresh_interval > 0:
    st.sidebar.success(f"🔄 Auto-refresh cada {refresh_interval}s")
    time.sleep(refresh_interval)
    st.rerun()

# ➕ Footer con información
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align: center; color: #888; font-size: 12px;">
💡 <b>TradingView Style SMC</b><br>
Smart Money Concepts en tiempo real<br>
<i>Sesión actual: {session_info}</i><br>
<i>Desarrollado con ❤️ para traders</i>
</div>
""", unsafe_allow_html=True)
