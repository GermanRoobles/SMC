import streamlit as st
import plotly.graph_objects as go
import pandas as pd
# --- APP START/END TELEGRAM ALERTS ---
import time
from datetime import datetime, timedelta
import requests
# --- TELEGRAM ALERTS ---
TELEGRAM_TOKEN = "7861899054:AAG0rpHiCwIPOu0o1C_7BnlUCnjD-ckew2k"
TELEGRAM_CHAT_ID = "-1002755466186"

def send_telegram_alert(message: str):
    """Send a message to Telegram via bot API."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or '<' in TELEGRAM_TOKEN:
        print(f"[TELEGRAM][SKIP] {message}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=payload, timeout=5)
        if resp.status_code != 200:
            print(f"[TELEGRAM][ERROR] {resp.text}")
    except Exception as e:
        print(f"[TELEGRAM][EXC] {e}")

# Send Telegram alert when app starts (after function is defined)
try:
    send_telegram_alert("🚀 SMC Streamlit app has started running.")
except Exception as e:
    print(f"[TELEGRAM][START][EXC] {e}")
from typing import Dict, List, Optional
from fetch_data import get_ohlcv, get_ohlcv_extended, get_ohlcv_with_cache
from smc_analysis import analyze, get_current_session, get_session_color
from smc_integration import get_smc_bot_analysis, add_bot_signals_to_chart, display_bot_metrics, add_signals_statistics_to_chart
from smc_historical import create_historical_manager, HistoricalPeriod
from smc_historical_viz import create_historical_visualizer, display_historical_controls
from smc_trade_engine import get_trade_engine_analysis, TradeSignal, SignalType
from smc_backtester import run_backtest_analysis

# --- SFP DETECTION ---
# --- SFP DETECTION ---
def detect_sfps(
    df,
    lookback=200,
    market_structure='neutral',  # 'bullish', 'bearish', or 'neutral'
    fvgs=None,
    obs=None,
    choch_list=None,
    min_body_ratio=0,
    max_zone_distance_pct=0.05,  # ultra-relaxed for debug
    require_choch=False,
    symbol=None,
    timeframe=None,
):
    """
    Detect Swing Failure Patterns (SFPs) with validity filters and send Telegram alerts.
    """
    sfps = []
    if len(df) < 3:
        print("[SFP] DataFrame too short")
        return sfps

    fvgs = fvgs or []
    obs = obs or []
    choch_list = choch_list or []

    df = df.iloc[-lookback:]
    idxs = df.index if not isinstance(df.index, pd.RangeIndex) else df['timestamp'] if 'timestamp' in df.columns else df.index

    def is_near_zone(price, zones):
        if not zones:
            return True
        return any(abs(price - z['mid']) / price < max_zone_distance_pct for z in zones if 'mid' in z)

    def is_body_strong(i):
        return True

    def has_choch_after(ts, sfp_type):
        direction = 'Bullish' if sfp_type == 'Bullish SFP' else 'Bearish'
        for c in choch_list:
            c_type = c.get('type', None)
            if c['timestamp'] > ts and isinstance(c_type, str) and direction in c_type:
                return True
        return False

    swing_high_candidates = 0
    swing_high_passed = 0
    swing_low_candidates = 0
    swing_low_passed = 0


    # --- ALERTS: Only send if event is recent (e.g., last 5 minutes) ---
    ALERT_TIME_WINDOW_MINUTES = 5
    def is_recent(ts):
        try:
            now = datetime.utcnow()
            # ts puede ser datetime o string o timestamp
            if isinstance(ts, (int, float)):
                ts_dt = datetime.utcfromtimestamp(ts)
            elif isinstance(ts, str):
                ts_dt = pd.to_datetime(ts, utc=True)
            elif isinstance(ts, pd.Timestamp):
                ts_dt = ts.to_pydatetime()
            elif isinstance(ts, datetime):
                ts_dt = ts
            else:
                return False
            return (now - ts_dt).total_seconds() < ALERT_TIME_WINDOW_MINUTES * 60
        except Exception:
            return False

    def alert_liquidity_sweep(ts, sweep_type, price):
        if is_recent(ts):
            msg = f"[TJR][{symbol or ''} {timeframe or ''}] Liquidity sweep detected: {sweep_type} at {price:.2f} ({ts})"
            send_telegram_alert(msg)

    def alert_zone_created(ts, zone_type, price):
        if is_recent(ts):
            msg = f"[TJR][{symbol or ''} {timeframe or ''}] {zone_type} created at {price:.2f} ({ts})"
            send_telegram_alert(msg)

    def alert_sfp(ts, sfp_type, swept_level, close):
        if is_recent(ts):
            msg = f"[SFP][{symbol or ''} {timeframe or ''}] {sfp_type} | Sweep: {swept_level:.2f} | Close: {close:.2f} | {ts}"
            send_telegram_alert(msg)

    def alert_choch(ts, choch_type, price):
        if is_recent(ts):
            msg = f"[CHoCH][{symbol or ''} {timeframe or ''}] {choch_type} at {price:.2f} ({ts})"
            send_telegram_alert(msg)

    print(f"[SFP][DEBUG] market_structure: {market_structure}, #FVGs: {len(fvgs)}, #OBs: {len(obs)}")

    def get_row_timestamp(row, fallback):
        # Robustly extract a timestamp from a row or fallback
        ts = None
        if isinstance(row, dict):
            ts = row.get('timestamp', fallback)
        elif hasattr(row, 'get'):
            try:
                ts = row.get('timestamp', fallback)
            except Exception:
                ts = fallback
        elif hasattr(row, '__getitem__'):
            try:
                ts = row['timestamp'] if 'timestamp' in row else fallback
            except Exception:
                ts = fallback
        else:
            ts = fallback
        return ts

    # Helper to get safe fallback for timestamp
    def get_fallback_idx(i):
        # If idxs is a RangeIndex, fallback should be i (int), else idxs[i]
        import pandas as pd
        if isinstance(idxs, pd.RangeIndex):
            return i
        else:
            return idxs.iloc[i]

    for i in range(1, len(df) - 1):
        prev, curr, next_ = df.iloc[i - 1], df.iloc[i], df.iloc[i + 1]

        # --- Step 1: Sweep/Liquidity ---
        fallback_idx = get_fallback_idx(i)
        if curr['high'] > prev['high'] and curr['high'] > next_['high']:
            swing_high = curr['high']
            ts_curr = get_row_timestamp(curr, fallback_idx)
            alert_liquidity_sweep(ts_curr, 'High', swing_high)
            # Step 2: OB/FVG after sweep (simulate, real logic should check for new OB/FVG after sweep)
            if obs:
                alert_zone_created(ts_curr, 'Order Block', swing_high)
            elif fvgs:
                alert_zone_created(ts_curr, 'FVG', swing_high)
            for j in range(i + 1, len(df)):
                high_j = df.iloc[j]['high']
                close_j = df.iloc[j]['close']
                fallback_j = get_fallback_idx(j)
                ts_j = get_row_timestamp(df.iloc[j], fallback_j)
                if high_j > swing_high and close_j < swing_high:
                    swing_high_candidates += 1
                    choch_ok = has_choch_after(ts_j, 'Bearish SFP') if require_choch else True
                    if not choch_ok:
                        print(f"[SFP][Bearish] Candidate at {ts_j} rejected: no_choch")
                        break
                    swing_high_passed += 1
                    sfps.append({
                        'timestamp': ts_j,
                        'type': 'Bearish SFP',
                        'swept_level': swing_high,
                        'close': close_j
                    })
                    alert_sfp(ts_j, 'Bearish SFP', swing_high, close_j)
                    # Step 3: CHoCH after SFP (simulate, real logic should check for CHoCH)
                    if choch_list:
                        for c in choch_list:
                            c_type = c.get('type', None)
                            if c['timestamp'] > ts_j and isinstance(c_type, str) and 'Bearish' in c_type:
                                alert_choch(c['timestamp'], c['type'], swing_high)
                                break
                    break

        if curr['low'] < prev['low'] and curr['low'] < next_['low']:
            swing_low = curr['low']
            ts_curr = get_row_timestamp(curr, fallback_idx)
            alert_liquidity_sweep(ts_curr, 'Low', swing_low)
            if obs:
                alert_zone_created(ts_curr, 'Order Block', swing_low)
            elif fvgs:
                alert_zone_created(ts_curr, 'FVG', swing_low)
            for j in range(i + 1, len(df)):
                low_j = df.iloc[j]['low']
                close_j = df.iloc[j]['close']
                fallback_j = get_fallback_idx(j)
                ts_j = get_row_timestamp(df.iloc[j], fallback_j)
                if low_j < swing_low and close_j > swing_low:
                    swing_low_candidates += 1
                    choch_ok = has_choch_after(ts_j, 'Bullish SFP') if require_choch else True
                    if not choch_ok:
                        print(f"[SFP][Bullish] Candidate at {ts_j} rejected: no_choch")
                        break
                    swing_low_passed += 1
                    sfps.append({
                        'timestamp': ts_j,
                        'type': 'Bullish SFP',
                        'swept_level': swing_low,
                        'close': close_j
                    })
                    alert_sfp(ts_j, 'Bullish SFP', swing_low, close_j)
                    if choch_list:
                        for c in choch_list:
                            c_type = c.get('type', None)
                            if c['timestamp'] > ts_j and isinstance(c_type, str) and 'Bullish' in c_type:
                                alert_choch(c['timestamp'], c['type'], swing_low)
                                break
                    break

    print(f"[SFP] swing_high_candidates: {swing_high_candidates}, swing_high_passed: {swing_high_passed}")
    print(f"[SFP] swing_low_candidates: {swing_low_candidates}, swing_low_passed: {swing_low_passed}")
    print(f"[SFP] Total SFPs detected: {len(sfps)}")
    return sfps

# Advertencia Streamlit: missing ScriptRunContext
# Solución: ignorar warning si aparece, pero loguear para debug
import warnings
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


    # Crear copia y resetear el índice para evitar problemas de alineación
    df_fixed = df.copy()
    # Si columnas es MultiIndex, aplanar
    if isinstance(df_fixed.columns, pd.MultiIndex):
        df_fixed.columns = df_fixed.columns.get_level_values(-1)
    # Si el índice es MultiIndex o tiene nombre, resetear
    if isinstance(df_fixed.index, pd.MultiIndex) or df_fixed.index.name is not None:
        df_fixed = df_fixed.reset_index(drop=True)

    # Asegurar que timestamp es datetime
    if 'timestamp' in df_fixed.columns:
        df_fixed['timestamp'] = pd.to_datetime(df_fixed['timestamp'])

    # Validar que tenemos las columnas necesarias
    required_columns = ['open', 'high', 'low', 'close', 'timestamp']
    missing_columns = [col for col in required_columns if col not in df_fixed.columns]

    if missing_columns:
        st.error(f"❌ Faltan columnas requeridas: {missing_columns}")
        return pd.DataFrame()

    # Si hay columnas requeridas pero alguna es tipo tuple (por error de yfinance), eliminar filas con ese problema
    for col in ['open', 'high', 'low', 'close']:
        if col in df_fixed.columns:
            try:
                mask = df_fixed[col].apply(lambda x: not isinstance(x, tuple))
                df_fixed = df_fixed[mask].reset_index(drop=True)
            except Exception as e:
                raise

    # Eliminar filas con valores NaN en precios
    df_fixed = df_fixed.dropna(subset=['open', 'high', 'low', 'close']).reset_index(drop=True)

    # Validar que high >= low
    invalid_rows = df_fixed[df_fixed['high'] < df_fixed['low']]
    if len(invalid_rows) > 0:
        st.warning(f"⚠️ Corrigiendo {len(invalid_rows)} filas con high < low")
        # Corrige los valores de 'high' donde high < low
        idxs = df_fixed[df_fixed['high'] < df_fixed['low']].index
        df_fixed.loc[idxs, 'high'] = df_fixed.loc[idxs, 'low']

    # Validar que high >= max(open, close) y low <= min(open, close)
    df_fixed['high'] = df_fixed[['high', 'open', 'close']].max(axis=1)
    df_fixed['low'] = df_fixed[['low', 'open', 'close']].min(axis=1)

    # Ordenar por timestamp
    df_fixed = df_fixed.sort_values('timestamp').reset_index(drop=True)

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


# --- Overlays toggles ---
#############################


# --- Responsive controls: sidebar for PC, top controls for mobile ---
st.set_page_config(layout="wide", page_title="SMC - Panal")
st.title("📊 SMC - Panal")

# Detect mobile by screen width (Streamlit workaround)
import streamlit as st
query_params = st.query_params
screen_width = int(query_params.get("w", ["0"])[0]) if "w" in query_params else None

def is_mobile():
    # If width is not available, fallback to user agent (not always possible)
    if screen_width and screen_width < 800:
        return True
    # Fallback: try to detect mobile from user agent
    import os
    user_agent = os.environ.get("HTTP_USER_AGENT", "")
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        return True
    return False

if is_mobile():
    # Controls in main body (top)
    with st.expander("🔧 Controles principales", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.selectbox("Symbol", [
                "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
                "EUR/USD", "GBP/USD", "XAU/USD", "SP500"
            ])
            timeframe = st.selectbox(
                "Timeframe",
                ["1m", "5m", "15m", "1h", "2h", "4h", "1d", "1w", "1M"],
                index=2
            )
            data_days = st.selectbox(
                "Data days",
                [1, 3, 5, 7, 14, 30, 60, 90, 180, 365],
                index=5
            )
        with col2:
            st.markdown("### Overlays to show")
            show_fvg = st.checkbox("FVG (Fair Value Gaps)", value=True)
            show_ob = st.checkbox("Order Blocks", value=True)
            show_liq = st.checkbox("Liquidity", value=True)
            show_bos = st.checkbox("BOS/CHoCH", value=True)
            show_swings = st.checkbox("Swings", value=True)
            show_sfp = st.checkbox("SFP (Swing Failure Patterns)", value=True)
        with col3:
            st.markdown("### Bot & Backtest")
            bot_enabled = st.checkbox("Enable SMC Bot", value=True)
            show_signals = st.checkbox("Show Signals", value=True)
            show_bot_metrics = st.checkbox("Show Metrics", value=True)
            trade_engine_enabled = st.checkbox("Enable Trading Engine", value=False)
            htf_enabled = st.checkbox("Use HTF context", value=False, help="Filter signals according to higher timeframe context")
            htf_timeframe = st.selectbox("HTF Timeframe", ["1h", "2h", "4h", "1d", "1w", "1M"], index=2, help="Higher timeframe for HTF context") if htf_enabled else None
            if trade_engine_enabled:
                min_risk_reward = st.slider("Minimum Risk/Reward", 1.5, 5.0, 2.0, 0.5)
                max_risk_percent = st.slider("Maximum Risk (%)", 0.5, 5.0, 1.0, 0.5)
                show_trade_signals = st.checkbox("Show Trading Signals", value=True)
                show_trade_stats = st.checkbox("Show Trading Stats", value=True)
            backtesting_enabled = st.checkbox("Enable Backtesting", value=False)
            if backtesting_enabled:
                initial_capital = st.number_input("Initial Capital ($)", min_value=1000, max_value=1000000, value=10000, step=1000)
                risk_per_trade = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5)
                show_backtest_chart = st.checkbox("Show Performance Chart", value=True)
                show_backtest_report = st.checkbox("Show Detailed Report", value=True)
            show_open_interest = st.checkbox("Show Open Interest (Binance Futures)", value=False, help="Real open interest overlay on the main chart.")
            st.markdown("### 📅 Historical Analysis")
            enable_historical = st.checkbox("Enable Historical Analysis", value=False, help="Navigate the pair's history")
            historical_period = st.selectbox(
                "Historical Period",
                options=[
                    ("1 Hour", HistoricalPeriod.HOUR_1),
                    ("4 Hours", HistoricalPeriod.HOURS_4),
                    ("12 Hours", HistoricalPeriod.HOURS_12),
                    ("1 Day", HistoricalPeriod.DAY_1),
                    ("3 Days", HistoricalPeriod.DAYS_3),
                    ("1 Week", HistoricalPeriod.WEEK_1),
                    ("2 Weeks", HistoricalPeriod.WEEKS_2),
                    ("1 Month", HistoricalPeriod.MONTH_1)
                ],
                format_func=lambda x: x[0],
                index=3,
                help="Historical period for analysis"
            )
            show_future_signals = st.checkbox("Show Future Signals", value=False, help="Preview of future signals (only in historical mode)")
            show_historical_charts = st.checkbox("Historical Charts", value=False, help="Show historical evolution charts")
            require_choch_sfp = st.checkbox("Require CHoCH for SFPs", value=False, help="Only show SFPs if a CHoCH occurs after the sweep.")
            show_htf_zones = st.checkbox("Show HTF FVGs/OBs (Weekly/Monthly) on 4H", value=False)
            enable_htf_alerts = st.checkbox("HTF Alerts (FVG/OB/SFP)", value=False)
            htf_timeframes = st.multiselect("HTF for overlays", ["1w", "1M"], default=["1w"])
else:
    # PC: sidebar controls as before
    st.sidebar.markdown("### Overlays to show")
    show_fvg = st.sidebar.checkbox("FVG (Fair Value Gaps)", value=True)
    show_ob = st.sidebar.checkbox("Order Blocks", value=True)
    show_liq = st.sidebar.checkbox("Liquidity", value=True)
    show_bos = st.sidebar.checkbox("BOS/CHoCH", value=True)
    show_swings = st.sidebar.checkbox("Swings", value=True)
    show_sfp = st.sidebar.checkbox("SFP (Swing Failure Patterns)", value=True)
    st.sidebar.markdown("### HTF Overlays & Alerts")
    show_htf_zones = st.sidebar.checkbox("Show HTF FVGs/OBs (Weekly/Monthly) on 4H", value=False)
    enable_htf_alerts = st.sidebar.checkbox("HTF Alerts (FVG/OB/SFP)", value=False)
    htf_timeframes = st.sidebar.multiselect("HTF for overlays", ["1w", "1M"], default=["1w"])
    require_choch_sfp = st.sidebar.checkbox("Require CHoCH for SFPs", value=False, help="Only show SFPs if a CHoCH occurs after the sweep.")
    symbol = st.sidebar.selectbox("Symbol", [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
        "EUR/USD", "GBP/USD", "XAU/USD", "SP500"
    ])
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        ["1m", "5m", "15m", "1h", "2h", "4h", "1d", "1w", "1M"],
        index=2
    )
    data_days = st.sidebar.selectbox(
        "Data days",
        [1, 3, 5, 7, 14, 30, 60, 90, 180, 365],
        index=5
    )
    refresh_interval = st.sidebar.selectbox("Refresh interval (sec)", [0, 30, 60, 120], index=0)
    bot_enabled = st.sidebar.checkbox("Enable SMC Bot", value=True)
    show_signals = st.sidebar.checkbox("Show Signals", value=True)
    show_bot_metrics = st.sidebar.checkbox("Show Metrics", value=True)
    trade_engine_enabled = st.sidebar.checkbox("Enable Trading Engine", value=False)
    htf_enabled = st.sidebar.checkbox("Use HTF context", value=False, help="Filter signals according to higher timeframe context")
    htf_timeframe = st.sidebar.selectbox("HTF Timeframe", ["1h", "2h", "4h", "1d", "1w", "1M"], index=2, help="Higher timeframe for HTF context") if htf_enabled else None
    if trade_engine_enabled:
        min_risk_reward = st.sidebar.slider("Minimum Risk/Reward", 1.5, 5.0, 2.0, 0.5)
        max_risk_percent = st.sidebar.slider("Maximum Risk (%)", 0.5, 5.0, 1.0, 0.5)
        show_trade_signals = st.sidebar.checkbox("Show Trading Signals", value=True)
        show_trade_stats = st.sidebar.checkbox("Show Trading Stats", value=True)
    backtesting_enabled = st.sidebar.checkbox("Enable Backtesting", value=False)
    if backtesting_enabled:
        initial_capital = st.sidebar.number_input("Initial Capital ($)", min_value=1000, max_value=1000000, value=10000, step=1000)
        risk_per_trade = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5)
        show_backtest_chart = st.sidebar.checkbox("Show Performance Chart", value=True)
        show_backtest_report = st.sidebar.checkbox("Show Detailed Report", value=True)
    show_open_interest = st.sidebar.checkbox("Show Open Interest (Binance Futures)", value=False, help="Real open interest overlay on the main chart.")
    st.sidebar.markdown("### 📅 Historical Analysis")
    enable_historical = st.sidebar.checkbox("Enable Historical Analysis", value=False, help="Navigate the pair's history")
    historical_period = st.sidebar.selectbox(
        "Historical Period",
        options=[
            ("1 Hour", HistoricalPeriod.HOUR_1),
            ("4 Hours", HistoricalPeriod.HOURS_4),
            ("12 Hours", HistoricalPeriod.HOURS_12),
            ("1 Day", HistoricalPeriod.DAY_1),
            ("3 Days", HistoricalPeriod.DAYS_3),
            ("1 Week", HistoricalPeriod.WEEK_1),
            ("2 Weeks", HistoricalPeriod.WEEKS_2),
            ("1 Month", HistoricalPeriod.MONTH_1)
        ],
        format_func=lambda x: x[0],
        index=3,
        help="Historical period for analysis"
    )
    show_future_signals = st.sidebar.checkbox("Show Future Signals", value=False, help="Preview of future signals (only in historical mode)")
    show_historical_charts = st.sidebar.checkbox("Historical Charts", value=False, help="Show historical evolution charts")

# --- MAIN TABS (ENGLISH) ---
tab_overview, tab_setups, tab_signals, tab_backtest, tab_config, tab_example, tab_realtime = st.tabs([
    "Market Overview", "Setups & Confluences", "Signals & Trading", "Backtesting & History", "Configuration", "Visual Example", "Real-Time Multi-Chart"
])

# Register app end alert (when Streamlit script finishes)
import atexit
def send_app_end_alert():
    try:
        send_telegram_alert("🛑 SMC Streamlit app has stopped running.")
    except Exception as e:
        print(f"[TELEGRAM][END][EXC] {e}")
atexit.register(send_app_end_alert)

# --- NUEVA PESTAÑA: TIEMPO REAL MULTI-CHART ---
with tab_realtime:
    st.header("🟢 Real-Time Multi-Chart (15m)")
    st.markdown("""
    View SMC indicators in real time for BTC/USDT, ETH/USDT, EUR/USD, and SP500 on the 15m timeframe.
    """)
    symbols_rt = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"]
    cols = st.columns(2)
    for idx, symbol_rt in enumerate(symbols_rt):
        with cols[idx % 2]:
            st.subheader(f"{symbol_rt} (15m)")
            # Usar caché incremental para datos en tiempo real
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=2)
            df_rt = get_ohlcv_with_cache(symbol_rt, "15m", start_dt, end_dt)
            df_rt = validate_and_fix_chart_data(df_rt)
            # Normalizar timestamp a tz-aware para overlays HTF si se usan
            if 'timestamp' in df_rt.columns:
                df_rt['timestamp'] = pd.to_datetime(df_rt['timestamp'], utc=True)
            if df_rt.empty:
                st.warning("No data available for this symbol.")
                continue
            signals_rt = analyze(df_rt)
            fig_rt = create_optimized_chart(df_rt)
            # --- Añadir overlays igual que en la pestaña principal ---
            # FVG
            if show_fvg and "fvg" in signals_rt:
                fvg_data = signals_rt["fvg"]
                for i, row in fvg_data.iterrows():
                    if pd.notna(row["FVG"]):
                        is_bullish = row["FVG"] == 1
                        color = '#2962FF' if is_bullish else '#FF6D00'
                        fig_rt.add_shape(
                            type="rect",
                            x0=df_rt.iloc[i]["timestamp"],
                            x1=df_rt.iloc[min(i+8, len(df_rt)-1)]["timestamp"],
                            y0=row["Bottom"],
                            y1=row["Top"],
                            fillcolor=color,
                            opacity=0.15,
                            line=dict(color=color, width=1, dash="dot")
                        )
                        if i % 3 == 0:
                            fig_rt.add_annotation(
                                x=df_rt.iloc[min(i+2, len(df_rt)-1)]["timestamp"],
                                y=(row["Top"] + row["Bottom"]) / 2,
                                text="FVG",
                                showarrow=False,
                                font=dict(size=10, color=color, family="Arial Black"),
                                bgcolor="rgba(255,255,255,0.8)",
                                bordercolor=color,
                                borderwidth=1
                                )
            if show_ob and "orderblocks" in signals_rt:
                ob_data = signals_rt["orderblocks"]
                for i, row in ob_data.iterrows():
                    if pd.notna(row["OB"]):
                        is_bullish = row["OB"] == 1
                        color = '#4CAF50' if is_bullish else '#F44336'
                        fig_rt.add_shape(
                            type="rect",
                            x0=df_rt.iloc[i]["timestamp"],
                            x1=df_rt.iloc[min(i+12, len(df_rt)-1)]["timestamp"],
                            y0=row["Bottom"],
                            y1=row["Top"],
                            fillcolor=color,
                            opacity=0.2,
                            line=dict(color=color, width=2)
                        )
                        fig_rt.add_annotation(
                            x=df_rt.iloc[min(i+3, len(df_rt)-1)]["timestamp"],
                            y=(row["Top"] + row["Bottom"]) / 2,
                            text="OB",
                            showarrow=False,
                            font=dict(size=12, color="white", family="Arial Black"),
                            bgcolor=color,
                            bordercolor=color,
                            borderwidth=1
                        )
            if show_bos and "bos_choch" in signals_rt:
                bos_choch_data = signals_rt["bos_choch"]
                for i, row in bos_choch_data.iterrows():
                    val = row.get("Signal", row.get("BOS", row.get("CHoCH", None)))
                    if pd.notna(val):
                        label = "BOS" if "BOS" in str(val) else "CHoCH"
                        fig_rt.add_shape(
                            type="line",
                            x0=df_rt.iloc[i]["timestamp"],
                            x1=df_rt.iloc[i]["timestamp"],
                            y0=df_rt.iloc[i]["low"] * 0.999,
                            y1=df_rt.iloc[i]["high"] * 1.001,
                            line=dict(color="#9C27B0", width=3, dash="dash")
                        )
                        fig_rt.add_annotation(
                            x=df_rt.iloc[i]["timestamp"],
                            y=df_rt.iloc[i]["high"] * 1.002,
                            text=label,
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
            if show_liq and "liquidity" in signals_rt:
                liq_data = signals_rt["liquidity"]
                if liq_data is not None:
                    for i, row in liq_data.iterrows():
                        trigger = row.get("Sweep", row.get("Liquidity", None))
                        if pd.notna(trigger):
                            price = row.get("Price", row.get("Level", df_rt.iloc[i]["high"]))
                            fig_rt.add_shape(
                                type="line",
                                x0=df_rt.iloc[max(0, i-5)]["timestamp"],
                                x1=df_rt.iloc[min(i+5, len(df_rt)-1)]["timestamp"],
                                y0=price,
                                y1=price,
                                line=dict(color="#FFD700", width=2, dash="solid")
                            )
            if show_swings and "swing_highs_lows" in signals_rt:
                swing_data = signals_rt.get("swing_highs_lows", None)
                if swing_data is not None and hasattr(swing_data, 'iterrows'):
                    for i, row in swing_data.iterrows():
                        highlow = row.get("HighLow", None) if hasattr(row, 'get') else row["HighLow"] if "HighLow" in row else None
                        if pd.notna(highlow):
                            color = "#00BFFF" if highlow == "high" else "#FF8C00"
                            fig_rt.add_shape(
                                type="circle",
                                xref="x", yref="y",
                                x0=df_rt.iloc[i]["timestamp"],
                                x1=df_rt.iloc[i]["timestamp"],
                                y0=df_rt.iloc[i]["high"] * 1.001 if highlow == "high" else df_rt.iloc[i]["low"] * 0.999,
                                y1=df_rt.iloc[i]["high"] * 1.002 if highlow == "high" else df_rt.iloc[i]["low"] * 0.998,
                                line=dict(color=color, width=2),
                                fillcolor=color,
                                opacity=0.5
                            )
            # --- SFP Overlay (Real-Time Chart, filtered) ---
            # Get market structure, FVGs, OBs, CHoCH for RT chart
            market_structure_rt = signals_rt.get('market_structure', 'neutral')
            fvgs_rt = []
            obs_rt = []
            choch_rt = []
            if 'fvg' in signals_rt and hasattr(signals_rt['fvg'], 'iterrows'):
                fvgs_rt = [
                    {'mid': (row['Top'] + row['Bottom']) / 2}
                    for _, row in signals_rt['fvg'].iterrows() if pd.notna(row.get('FVG', None))
                ]
            if 'orderblocks' in signals_rt and hasattr(signals_rt['orderblocks'], 'iterrows'):
                obs_rt = [
                    {'mid': (row['Top'] + row['Bottom']) / 2}
                    for _, row in signals_rt['orderblocks'].iterrows() if pd.notna(row.get('OB', None))
                ]
            if 'bos_choch' in signals_rt and hasattr(signals_rt['bos_choch'], 'iterrows'):
                choch_rt = [
                    {'timestamp': row['timestamp'] if 'timestamp' in row else df_rt.iloc[i]['timestamp'], 'type': row.get('Signal', row.get('BOS', row.get('CHoCH', '')))}
                    for i, row in signals_rt['bos_choch'].iterrows() if pd.notna(row.get('Signal', row.get('BOS', row.get('CHoCH', None))))
                ]
            # Mostrar SFP solo si el toggle está activo
            if show_sfp:
                sfps_rt = detect_sfps(
                    df_rt,
                    lookback=200,
                    market_structure=market_structure_rt,
                    fvgs=fvgs_rt,
                    obs=obs_rt,
                    choch_list=choch_rt,
                    require_choch=require_choch_sfp
                )
                for sfp in sfps_rt:
                    ts = sfp['timestamp']
                    if 'Bullish' in sfp['type']:
                        fig_rt.add_annotation(
                            x=ts,
                            y=sfp['swept_level'],
                            text="🟢 SFP",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1.2,
                            arrowwidth=2,
                            arrowcolor="#26A69A",
                            font=dict(size=11, color="#26A69A", family="Arial Black"),
                            bgcolor="#232323",
                            bordercolor="#26A69A",
                            borderwidth=1
                        )
                    elif 'Bearish' in sfp['type']:
                        fig_rt.add_annotation(
                            x=ts,
                            y=sfp['swept_level'],
                            text="🔴 SFP",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1.2,
                            arrowwidth=2,
                            arrowcolor="#F44336",
                            font=dict(size=11, color="#F44336", family="Arial Black"),
                            bgcolor="#232323",
                            bordercolor="#F44336",
                            borderwidth=1
                        )
            st.plotly_chart(fig_rt, use_container_width=True, key=f"rt_chart_{symbol_rt}")
with tab_example:
    st.header("Visual Example: SMC Simplified by TJR Strategy (LONG and SHORT)")
    st.markdown("""
    Step-by-step examples of a LONG and SHORT signal according to the SMC Simplified by TJR methodology. Each chart shows: liquidity zone, sweep, FVG, Order Block, CHoCH, signal, SL, and TP.
    """)

    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta

    col_long, col_short = st.columns(2)

    # --- LONG Example ---
    with col_long:
        st.subheader("LONG Signal (Buy)")
        scenario_long = {
            'symbol': 'EXAMPLE/USDT',
            'timeframe': '15m',
            'structure': 'Bullish',
            'liquidity_zone': {'type': 'equal_lows', 'price': 1.0850},
            'sweep': {'low': 1.0835},
            'fvg': {'start': 1.0870, 'end': 1.0895},
            'order_block': {'low': 1.0840, 'high': 1.0860},
            'choch': {'confirmed_at': '2025-07-08 11:15'},
            'entry': 1.0865,
            'sl': 1.0830,
            'tp': 1.0930,
            'result': 'TP Hit ✅'
        }
        # Simular velas OHLC para el escenario
        n = 30
        base = 1.0850
        np.random.seed(1)
        prices = np.linspace(base, scenario_long['tp'], n)
        # Simular el desarrollo: zona de liquidez, sweep, fvg, ob, choch, entrada, sl, tp
        ohlc = []
        for i in range(n):
            if i < 5:
                open_ = close_ = base
                high = base + 0.0005
                low = base - 0.0005
            elif i == 5:
                open_ = base
                close_ = scenario_long['sweep']['low']
                high = open_ + 0.0005
                low = scenario_long['sweep']['low'] - 0.0005
            elif 6 <= i < 10:
                open_ = close_ = scenario_long['fvg']['start'] - 0.001
                high = open_ + 0.001
                low = open_ - 0.001
            elif 10 <= i < 13:
                open_ = close_ = scenario_long['order_block']['low']
                high = scenario_long['order_block']['high']
                low = scenario_long['order_block']['low'] - 0.0005
            elif i == 13:
                open_ = close_ = scenario_long['entry']
                high = open_ + 0.0007
                low = open_ - 0.0007
            elif 14 <= i < 20:
                open_ = close_ = scenario_long['entry'] + (i-13)*0.0007
                high = open_ + 0.0005
                low = open_ - 0.0005
            elif i == 20:
                open_ = close_ = scenario_long['tp']
                high = open_ + 0.0005
                low = open_ - 0.0005
            else:
                open_ = close_ = scenario_long['tp']
                high = open_ + 0.0002
                low = open_ - 0.0002
            ohlc.append([open_, high, low, close_])
        df_long = pd.DataFrame(ohlc, columns=['open','high','low','close'])
        df_long['timestamp'] = [datetime(2025,7,8,10,0) + timedelta(minutes=15*i) for i in range(n)]
        # Gráfico
        fig_long = go.Figure()
        fig_long.add_trace(go.Candlestick(
            x=df_long['timestamp'], open=df_long['open'], high=df_long['high'], low=df_long['low'], close=df_long['close'], name='Precio'))
        # Liquidity zone (equal lows)
        fig_long.add_shape(type="line", x0=df_long['timestamp'][0], x1=df_long['timestamp'][8], y0=scenario_long['liquidity_zone']['price'], y1=scenario_long['liquidity_zone']['price'], line=dict(color="#FFD700", width=2, dash="dot"))
        fig_long.add_annotation(x=df_long['timestamp'][2], y=scenario_long['liquidity_zone']['price']+0.0002, text="Equal Lows (Liquidity)", showarrow=False, font=dict(color="#FFD700"), bgcolor="#232323")
        # Sweep
        fig_long.add_shape(type="line", x0=df_long['timestamp'][5], x1=df_long['timestamp'][5], y0=scenario_long['liquidity_zone']['price'], y1=scenario_long['sweep']['low'], line=dict(color="#F44336", width=2, dash="dash"))
        fig_long.add_annotation(x=df_long['timestamp'][5], y=scenario_long['sweep']['low']-0.0002, text="Sweep", showarrow=True, arrowhead=2, font=dict(color="#F44336"), bgcolor="#232323")
        # FVG
        fig_long.add_shape(type="rect", x0=df_long['timestamp'][6], x1=df_long['timestamp'][9], y0=scenario_long['fvg']['start'], y1=scenario_long['fvg']['end'], fillcolor="#2962FF", opacity=0.2, line=dict(color="#2962FF", width=1, dash="dot"))
        fig_long.add_annotation(x=df_long['timestamp'][7], y=scenario_long['fvg']['end']+0.0002, text="FVG", showarrow=False, font=dict(color="#2962FF"), bgcolor="#232323")
        # Order Block
        fig_long.add_shape(type="rect", x0=df_long['timestamp'][10], x1=df_long['timestamp'][12], y0=scenario_long['order_block']['low'], y1=scenario_long['order_block']['high'], fillcolor="#4CAF50", opacity=0.2, line=dict(color="#4CAF50", width=1))
        fig_long.add_annotation(x=df_long['timestamp'][11], y=scenario_long['order_block']['high']+0.0002, text="Order Block", showarrow=False, font=dict(color="#4CAF50"), bgcolor="#232323")
        # CHoCH
        fig_long.add_shape(type="line", x0=df_long['timestamp'][13], x1=df_long['timestamp'][13], y0=scenario_long['order_block']['low'], y1=scenario_long['order_block']['high'], line=dict(color="#9C27B0", width=2, dash="dash"))
        fig_long.add_annotation(x=df_long['timestamp'][13], y=scenario_long['order_block']['high']+0.0005, text="CHoCH", showarrow=True, arrowhead=2, font=dict(color="#9C27B0"), bgcolor="#232323")
        # Entry, SL, TP
        fig_long.add_shape(type="line", x0=df_long['timestamp'][13], x1=df_long['timestamp'][13], y0=scenario_long['sl'], y1=scenario_long['entry'], line=dict(color="#26A69A", width=3, dash="dot"))
        fig_long.add_annotation(x=df_long['timestamp'][13], y=scenario_long['entry']+0.0003, text="LONG Entry", showarrow=True, arrowhead=2, font=dict(color="#26A69A"), bgcolor="#232323")
        fig_long.add_shape(type="line", x0=df_long['timestamp'][0], x1=df_long['timestamp'].iloc[-1], y0=scenario_long['sl'], y1=scenario_long['sl'], line=dict(color="#EF5350", width=2, dash="dash"))
        fig_long.add_annotation(x=df_long['timestamp'][2], y=scenario_long['sl']-0.0002, text="Stop Loss", showarrow=False, font=dict(color="#EF5350"), bgcolor="#232323")
        fig_long.add_shape(type="line", x0=df_long['timestamp'][0], x1=df_long['timestamp'].iloc[-1], y0=scenario_long['tp'], y1=scenario_long['tp'], line=dict(color="#FFD700", width=2, dash="dash"))
        fig_long.add_annotation(x=df_long['timestamp'][20], y=scenario_long['tp']+0.0002, text="Take Profit", showarrow=False, font=dict(color="#FFD700"), bgcolor="#232323")
        # Result
        fig_long.add_annotation(x=df_long['timestamp'][21], y=scenario_long['tp']+0.0005, text=scenario_long['result'], showarrow=False, font=dict(color="#26A69A", size=14, family="Arial Black"), bgcolor="#232323")
        fig_long.update_layout(title="LONG Example SMC-TJR", height=480, paper_bgcolor="#232323", plot_bgcolor="#232323", xaxis=dict(title="Time", color="#fff"), yaxis=dict(title="Price", color="#fff"))
        st.plotly_chart(fig_long, use_container_width=True)
        st.info(f"**Structure:** {scenario_long['structure']} | **Entry:** {scenario_long['entry']} | **SL:** {scenario_long['sl']} | **TP:** {scenario_long['tp']} | {scenario_long['result']}")

    # --- SHORT Example ---
    with col_short:
        st.subheader("SHORT Signal (Sell)")
        scenario_short = {
            'symbol': 'EXAMPLE/USDT',
            'timeframe': '15m',
            'structure': 'Bearish',
            'liquidity_zone': {'type': 'equal_highs', 'price': 1.1020},
            'sweep': {'high': 1.1035},
            'fvg': {'start': 1.0995, 'end': 1.0975},
            'order_block': {'low': 1.0980, 'high': 1.1000},
            'choch': {'confirmed_at': '2025-07-08 14:30'},
            'entry': 1.0990,
            'sl': 1.1040,
            'tp': 1.0925,
            'result': 'TP Hit ✅'
        }
        n = 30
        base = 1.1020
        np.random.seed(2)
        prices = np.linspace(base, scenario_short['tp'], n)
        ohlc = []
        for i in range(n):
            if i < 5:
                open_ = close_ = base
                high = base + 0.0005
                low = base - 0.0005
            elif i == 5:
                open_ = base
                close_ = scenario_short['sweep']['high']
                high = scenario_short['sweep']['high'] + 0.0005
                low = open_ - 0.0005
            elif 6 <= i < 10:
                open_ = close_ = scenario_short['fvg']['start'] + 0.001
                high = open_ + 0.001
                low = open_ - 0.001
            elif 10 <= i < 13:
                open_ = close_ = scenario_short['order_block']['high']
                high = scenario_short['order_block']['high'] + 0.0005
                low = scenario_short['order_block']['low']
            elif i == 13:
                open_ = close_ = scenario_short['entry']
                high = open_ + 0.0007
                low = open_ - 0.0007
            elif 14 <= i < 20:
                open_ = close_ = scenario_short['entry'] - (i-13)*0.0007
                high = open_ + 0.0005
                low = open_ - 0.0005
            elif i == 20:
                open_ = close_ = scenario_short['tp']
                high = open_ + 0.0005
                low = open_ - 0.0005
            else:
                open_ = close_ = scenario_short['tp']
                high = open_ + 0.0002
                low = open_ - 0.0002
            ohlc.append([open_, high, low, close_])
        df_short = pd.DataFrame(ohlc, columns=['open','high','low','close'])
        df_short['timestamp'] = [datetime(2025,7,8,13,0) + timedelta(minutes=15*i) for i in range(n)]
        fig_short = go.Figure()
        fig_short.add_trace(go.Candlestick(
            x=df_short['timestamp'], open=df_short['open'], high=df_short['high'], low=df_short['low'], close=df_short['close'], name='Precio'))
        # Liquidity zone (equal highs)
        fig_short.add_shape(type="line", x0=df_short['timestamp'][0], x1=df_short['timestamp'][8], y0=scenario_short['liquidity_zone']['price'], y1=scenario_short['liquidity_zone']['price'], line=dict(color="#FFD700", width=2, dash="dot"))
        fig_short.add_annotation(x=df_short['timestamp'][2], y=scenario_short['liquidity_zone']['price']+0.0002, text="Equal Highs (Liquidity)", showarrow=False, font=dict(color="#FFD700"), bgcolor="#232323")
        # Sweep
        fig_short.add_shape(type="line", x0=df_short['timestamp'][5], x1=df_short['timestamp'][5], y0=scenario_short['liquidity_zone']['price'], y1=scenario_short['sweep']['high'], line=dict(color="#F44336", width=2, dash="dash"))
        fig_short.add_annotation(x=df_short['timestamp'][5], y=scenario_short['sweep']['high']+0.0002, text="Sweep", showarrow=True, arrowhead=2, font=dict(color="#F44336"), bgcolor="#232323")
        # FVG
        fig_short.add_shape(type="rect", x0=df_short['timestamp'][6], x1=df_short['timestamp'][9], y0=scenario_short['fvg']['end'], y1=scenario_short['fvg']['start'], fillcolor="#FF6D00", opacity=0.2, line=dict(color="#FF6D00", width=1, dash="dot"))
        fig_short.add_annotation(x=df_short['timestamp'][7], y=scenario_short['fvg']['start']+0.0002, text="FVG", showarrow=False, font=dict(color="#FF6D00"), bgcolor="#232323")
        # Order Block
        fig_short.add_shape(type="rect", x0=df_short['timestamp'][10], x1=df_short['timestamp'][12], y0=scenario_short['order_block']['low'], y1=scenario_short['order_block']['high'], fillcolor="#F44336", opacity=0.2, line=dict(color="#F44336", width=1))
        fig_short.add_annotation(x=df_short['timestamp'][11], y=scenario_short['order_block']['high']+0.0002, text="Order Block", showarrow=False, font=dict(color="#F44336"), bgcolor="#232323")
        # CHoCH
        fig_short.add_shape(type="line", x0=df_short['timestamp'][13], x1=df_short['timestamp'][13], y0=scenario_short['order_block']['low'], y1=scenario_short['order_block']['high'], line=dict(color="#9C27B0", width=2, dash="dash"))
        fig_short.add_annotation(x=df_short['timestamp'][13], y=scenario_short['order_block']['high']+0.0005, text="CHoCH", showarrow=True, arrowhead=2, font=dict(color="#9C27B0"), bgcolor="#232323")
        # Entry, SL, TP
        fig_short.add_shape(type="line", x0=df_short['timestamp'][13], x1=df_short['timestamp'][13], y0=scenario_short['entry'], y1=scenario_short['sl'], line=dict(color="#F44336", width=3, dash="dot"))
        fig_short.add_annotation(x=df_short['timestamp'][13], y=scenario_short['entry']-0.0003, text="SHORT Entry", showarrow=True, arrowhead=2, font=dict(color="#F44336"), bgcolor="#232323")
        fig_short.add_shape(type="line", x0=df_short['timestamp'][0], x1=df_short['timestamp'].iloc[-1], y0=scenario_short['sl'], y1=scenario_short['sl'], line=dict(color="#EF5350", width=2, dash="dash"))
        fig_short.add_annotation(x=df_short['timestamp'][2], y=scenario_short['sl']+0.0002, text="Stop Loss", showarrow=False, font=dict(color="#EF5350"), bgcolor="#232323")
        fig_short.add_shape(type="line", x0=df_short['timestamp'][0], x1=df_short['timestamp'].iloc[-1], y0=scenario_short['tp'], y1=scenario_short['tp'], line=dict(color="#FFD700", width=2, dash="dash"))
        fig_short.add_annotation(x=df_short['timestamp'][20], y=scenario_short['tp']-0.0002, text="Take Profit", showarrow=False, font=dict(color="#FFD700"), bgcolor="#232323")
        # Result
        fig_short.add_annotation(x=df_short['timestamp'][21], y=scenario_short['tp']-0.0005, text=scenario_short['result'], showarrow=False, font=dict(color="#F44336", size=14, family="Arial Black"), bgcolor="#232323")
        fig_short.update_layout(title="SHORT Example SMC-TJR", height=480, paper_bgcolor="#232323", plot_bgcolor="#232323", xaxis=dict(title="Time", color="#fff"), yaxis=dict(title="Price", color="#fff"))
        st.plotly_chart(fig_short, use_container_width=True)
        st.info(f"**Structure:** {scenario_short['structure']} | **Entry:** {scenario_short['entry']} | **SL:** {scenario_short['sl']} | **TP:** {scenario_short['tp']} | {scenario_short['result']}")

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
            # Usar caché incremental para la carga principal
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=data_days)
            df = get_ohlcv_with_cache(symbol, timeframe, start_dt, end_dt)
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

        # --- CONTEXTO HTF Y LOGGING DETALLADO ---
        import logging
        logging.basicConfig(level=logging.INFO)
        trade_analysis = None
        htf_context = None
        if trade_engine_enabled and bot_analysis:
            try:
                with st.spinner("⚡ Ejecutando Motor de Trading TJR..."):
                    # Si HTF está activado, obtener contexto HTF (pero NO pasar a la función si no lo soporta)
                    if htf_enabled and htf_timeframe:
                        # Usar caché incremental para HTF
                        htf_end = datetime.utcnow()
                        htf_start = htf_end - timedelta(days=data_days)
                        htf_df = get_ohlcv_with_cache(symbol, htf_timeframe, htf_start, htf_end)
                        htf_signals = analyze(htf_df)
                        htf_context = {
                            'trend': htf_signals.get('trend', None),
                            'session': get_current_session(htf_df.iloc[-1]['timestamp']) if len(htf_df) > 0 else None
                        }
                        logging.info(f"[HTF] Contexto HTF ({htf_timeframe}): {htf_context}")
                    # Llamada sin htf_context (para compatibilidad)
                    trade_analysis = get_trade_engine_analysis(df, bot_analysis)
                    if trade_analysis['signal_count'] > 0:
                        show_temp_message('success', f"✅ Motor TJR: {trade_analysis['signal_count']} señales detectadas")
                        for sig in trade_analysis['signals']:
                            logging.info(f"[SIGNAL] {sig.signal_type.value} | Score: {getattr(sig, 'score', 'N/A')} | Confianza: {getattr(sig, 'confidence', 'N/A')}")
                    else:
                        st.info("ℹ️ Motor TJR: No hay señales en este momento")
            except Exception as e:
                logging.error(f"Error en Motor TJR: {e}")
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
    # Normalizar timestamp a tz-aware para overlays HTF si se usan
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)


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

    # --- Añadir overlays según toggles ---
    from utils_htf import get_htf_gaps_and_obs, monitor_fvg_alerts, monitor_ob_alerts, detect_sfp
    if 'alert_cache' not in st.session_state:
        st.session_state['alert_cache'] = {}
    alert_cache = st.session_state['alert_cache']
    htf_alerts = []
    with st.spinner("📊 Añadiendo overlays..."):
        # --- HTF overlays y alertas ---
        # Mostrar overlays HTF en cualquier timeframe <= 4h
        ltf_valid = ["1m", "5m", "15m", "1h", "4h"]
        new_htf_alerts = []
        # Ejemplo: Normalizar timestamp en df_htf si existe
        # if 'df_htf' in locals() and 'timestamp' in df_htf.columns:
        #     df_htf['timestamp'] = pd.to_datetime(df_htf['timestamp'], utc=True)
        # --- SFP Overlay (pestaña principal) ---
        market_structure_main = signals.get('market_structure', 'neutral')
        fvgs_main = []
        obs_main = []
        choch_main = []
        if 'fvg' in signals and hasattr(signals['fvg'], 'iterrows'):
            fvgs_main = [
                {'mid': (row['Top'] + row['Bottom']) / 2}
                for _, row in signals['fvg'].iterrows() if pd.notna(row.get('FVG', None))
            ]
        if 'orderblocks' in signals and hasattr(signals['orderblocks'], 'iterrows'):
            obs_main = [
                {'mid': (row['Top'] + row['Bottom']) / 2}
                for _, row in signals['orderblocks'].iterrows() if pd.notna(row.get('OB', None))
            ]
        if 'bos_choch' in signals and hasattr(signals['bos_choch'], 'iterrows'):
            choch_main = [
                {'timestamp': row['timestamp'] if 'timestamp' in row else df.iloc[i]['timestamp'], 'type': row.get('Signal', row.get('BOS', row.get('CHoCH', '')))}
                for i, row in signals['bos_choch'].iterrows() if pd.notna(row.get('Signal', row.get('BOS', row.get('CHoCH', None))))
            ]
        if show_sfp:
            sfps_main = detect_sfps(
                df,
                lookback=200,
                market_structure=market_structure_main,
                fvgs=fvgs_main,
                obs=obs_main,
                choch_list=choch_main,
                require_choch=require_choch_sfp
            )
            for sfp in sfps_main:
                ts = sfp['timestamp']
                if 'Bullish' in sfp['type']:
                    fig.add_annotation(
                        x=ts,
                        y=sfp['swept_level'],
                        text="🟢 SFP",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1.2,
                        arrowwidth=2,
                        arrowcolor="#26A69A",
                        font=dict(size=11, color="#26A69A", family="Arial Black"),
                        bgcolor="#232323",
                        bordercolor="#26A69A",
                        borderwidth=1
                    )
                elif 'Bearish' in sfp['type']:
                    fig.add_annotation(
                        x=ts,
                        y=sfp['swept_level'],
                        text="🔴 SFP",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1.2,
                        arrowwidth=2,
                        arrowcolor="#F44336",
                        font=dict(size=11, color="#F44336", family="Arial Black"),
                        bgcolor="#232323",
                        bordercolor="#F44336",
                        borderwidth=1
                    )
        if show_htf_zones and timeframe in ltf_valid:
            for htf in htf_timeframes:
                try:
                    fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs(symbol, htf=htf, ltf=timeframe)
                    # Dibujar FVGs HTF
                    for zone in fvg_zones:
                        fig.add_shape(
                            type="rect",
                            x0=df["timestamp"].iloc[0],
                            x1=df["timestamp"].iloc[-1],
                            y0=zone["bottom"],
                            y1=zone["top"],
                            fillcolor="#00BFFF" if htf=="1w" else "#FFD700",
                            opacity=0.10 if htf=="1w" else 0.07,
                            line=dict(color="#00BFFF" if htf=="1w" else "#FFD700", width=2, dash="dot")
                        )
                        fig.add_annotation(
                            x=df["timestamp"].iloc[-1],
                            y=zone["top"],
                            text=f"HTF FVG {htf.upper()}",
                            showarrow=False,
                            font=dict(size=10, color="#232323", family="Arial Black"),
                            bgcolor="#B3E5FC" if htf=="1w" else "#FFF9C4",
                            bordercolor="#00BFFF" if htf=="1w" else "#FFD700",
                            borderwidth=1
                        )
                    # Dibujar OBs HTF
                    for zone in ob_zones:
                        fig.add_shape(
                            type="rect",
                            x0=df["timestamp"].iloc[0],
                            x1=df["timestamp"].iloc[-1],
                            y0=zone["bottom"],
                            y1=zone["top"],
                            fillcolor="#4CAF50" if htf=="1w" else "#F44336",
                            opacity=0.10 if htf=="1w" else 0.07,
                            line=dict(color="#4CAF50" if htf=="1w" else "#F44336", width=2, dash="dot")
                        )
                        fig.add_annotation(
                            x=df["timestamp"].iloc[-1],
                            y=zone["top"],
                            text=f"HTF OB {htf.upper()}",
                            showarrow=False,
                            font=dict(size=10, color="#fff", family="Arial Black"),
                            bgcolor="#C8E6C9" if htf=="1w" else "#FFCDD2",
                            bordercolor="#4CAF50" if htf=="1w" else "#F44336",
                            borderwidth=1
                        )
                    # --- Alertas HTF ---
                    if enable_htf_alerts:
                        price = df['close'].iloc[-1]
                        # Solo alertas nuevas (no repetidas)
                        prev_alerts = set(st.session_state.get('last_htf_alerts', []))
                        new_fvg_alerts = [a for a in monitor_fvg_alerts(price, fvg_zones, alert_cache) if a not in prev_alerts]
                        new_ob_alerts = [a for a in monitor_ob_alerts(price, ob_zones, alert_cache) if a not in prev_alerts]
                        # SFPs en 4H
                        sfps = detect_sfp(df)
                        new_sfp_alerts = []
                        for sfp in sfps:
                            key = f"sfp_{sfp['timestamp']}_{sfp['type']}"
                            msg = f"{sfp['type']} detected at {sfp['level']}"
                            if not alert_cache.get(key) and msg not in prev_alerts:
                                new_sfp_alerts.append(msg)
                                alert_cache[key] = True
                        new_htf_alerts += new_fvg_alerts + new_ob_alerts + new_sfp_alerts
                except Exception as e:
                    st.warning(f"Error en overlays/alertas HTF ({htf}): {e}")
        # Mostrar solo las 10 alertas nuevas más recientes
        if enable_htf_alerts and new_htf_alerts:
            st.session_state['last_htf_alerts'] = new_htf_alerts[-10:]
            for a in new_htf_alerts[-10:]:
                st.warning(a)
        # FVG
        if show_fvg and "fvg" in signals:
            fvg_data = signals["fvg"]
            for i, row in fvg_data.iterrows():
                if pd.notna(row["FVG"]):
                    is_bullish = row["FVG"] == 1
                    color = '#2962FF' if is_bullish else '#FF6D00'
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
                    # Restore FVG annotation every 3rd FVG
                    if i % 3 == 0:
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
        # --- SESSION BACKGROUND COLOR ---
        # Add background color depending on which session is open (London, NY, Tokyo, etc.)
        session_colors = {
            "tokyo": "rgba(33, 150, 243, 0.07)",      # Blue
            "london": "rgba(76, 175, 80, 0.07)",      # Green
            "new_york": "rgba(244, 67, 54, 0.07)",    # Red
            "between_sessions": "rgba(158, 158, 158, 0.04)"  # Gray
        }
        # Assume df['timestamp'] is sorted
        if 'timestamp' in df.columns:
            session_col = df['timestamp'].apply(lambda ts: get_current_session(ts))
            prev_session = None
            session_start_idx = 0
            for idx, session in enumerate(session_col):
                if prev_session is None:
                    prev_session = session
                    session_start_idx = idx
                elif session != prev_session or idx == len(session_col)-1:
                    # Draw background for previous session
                    x0 = df.iloc[session_start_idx]["timestamp"]
                    x1 = df.iloc[idx]["timestamp"] if idx < len(df) else df.iloc[-1]["timestamp"]
                    color = session_colors.get(prev_session, "rgba(158,158,158,0.04)")
                    fig.add_vrect(
                        x0=x0,
                        x1=x1,
                        fillcolor=color,
                        opacity=1.0,
                        layer="below",
                        line_width=0
                    )
                    prev_session = session
                    session_start_idx = idx

        # --- SFP Overlay (Main Chart, filtered) ---
        # Get market structure, FVGs, OBs, CHoCH for main chart
        market_structure_main = 'neutral'
        fvgs_main = []
        obs_main = []
        choch_main = []
        if 'market_structure' in signals:
            market_structure_main = signals['market_structure']
        if 'fvg' in signals and hasattr(signals['fvg'], 'iterrows'):
            fvgs_main = [
                {'mid': (row['Top'] + row['Bottom']) / 2}
                for _, row in signals['fvg'].iterrows() if pd.notna(row.get('FVG', None))
            ]
        if 'orderblocks' in signals and hasattr(signals['orderblocks'], 'iterrows'):
            obs_main = [
                {'mid': (row['Top'] + row['Bottom']) / 2}
                for _, row in signals['orderblocks'].iterrows() if pd.notna(row.get('OB', None))
            ]
        if 'bos_choch' in signals and hasattr(signals['bos_choch'], 'iterrows'):
            choch_main = [
                {'timestamp': row['timestamp'] if 'timestamp' in row else df.iloc[i]['timestamp'], 'type': row.get('Signal', row.get('BOS', row.get('CHoCH', '')))}
                for i, row in signals['bos_choch'].iterrows() if pd.notna(row.get('Signal', row.get('BOS', row.get('CHoCH', None))))
            ]
        sfps = detect_sfps(
            df,
            lookback=200,
            market_structure=market_structure_main,
            fvgs=fvgs_main,
            obs=obs_main,
            choch_list=choch_main,
            require_choch=require_choch_sfp
        )
        for sfp in sfps:
            ts = sfp['timestamp']
            if 'Bullish' in sfp['type']:
                fig.add_annotation(
                    x=ts,
                    y=sfp['swept_level'],
                    text="🟢 SFP",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor="#26A69A",
                    font=dict(size=11, color="#26A69A", family="Arial Black"),
                    bgcolor="#232323",
                    bordercolor="#26A69A",
                    borderwidth=1
                )
            elif 'Bearish' in sfp['type']:
                fig.add_annotation(
                    x=ts,
                    y=sfp['swept_level'],
                    text="🔴 SFP",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor="#F44336",
                    font=dict(size=11, color="#F44336", family="Arial Black"),
                    bgcolor="#232323",
                    bordercolor="#F44336",
                    borderwidth=1
                )
        # Order Blocks
        if show_ob and "orderblocks" in signals:
            ob_data = signals["orderblocks"]
            for i, row in ob_data.iterrows():
                if pd.notna(row["OB"]):
                    is_bullish = row["OB"] == 1
                    color = '#4CAF50' if is_bullish else '#F44336'
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
        # BOS/CHoCH
        if show_bos and "bos_choch" in signals:
            bos_choch_data = signals["bos_choch"]
            for i, row in bos_choch_data.iterrows():
                val = row.get("Signal", row.get("BOS", row.get("CHoCH", None)))
                if pd.notna(val):
                    label = "BOS" if "BOS" in str(val) else "CHoCH"
                    fig.add_shape(
                        type="line",
                        x0=df.iloc[i]["timestamp"],
                        x1=df.iloc[i]["timestamp"],
                        y0=df.iloc[i]["low"] * 0.999,
                        y1=df.iloc[i]["high"] * 1.001,
                        line=dict(color="#9C27B0", width=3, dash="dash")
                    )
                    fig.add_annotation(
                        x=df.iloc[i]["timestamp"],
                        y=df.iloc[i]["high"] * 1.002,
                        text=label,
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
        if show_liq and "liquidity" in signals:
            liq_data = signals["liquidity"]
            if liq_data is not None:
                for i, row in liq_data.iterrows():
                    trigger = row.get("Sweep", row.get("Liquidity", None))
                    if pd.notna(trigger):
                        price = row.get("Price", row.get("Level", df.iloc[i]["high"]))
                        fig.add_shape(
                            type="line",
                            x0=df.iloc[max(0, i-5)]["timestamp"],
                            x1=df.iloc[min(i+5, len(df)-1)]["timestamp"],
                            y0=price,
                            y1=price,
                            line=dict(color="#FFD700", width=2, dash="solid")
                        )
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
        # Swings
        if show_swings and "swing_highs_lows" in signals:
            swing_data = signals.get("swing_highs_lows", None)
            if swing_data is not None and hasattr(swing_data, 'iterrows'):
                for i, row in swing_data.iterrows():
                    highlow = row.get("HighLow", None) if hasattr(row, 'get') else row["HighLow"] if "HighLow" in row else None
                    if pd.notna(highlow):
                        score = row["score"] if "score" in row else None
                        confidence = row["confidence"] if "confidence" in row else None
                        hovertext = f"Score: {score:.2f}<br>Confianza: {confidence:.2f}" if score is not None or confidence is not None else None
                        if highlow == 1:  # Swing High
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
                                hovertemplate=(hovertext or "Swing High<br>Price: %{y}<br>Time: %{x}<extra></extra>")
                            ))
                        elif highlow == -1:  # Swing Low
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
                                hovertemplate=(hovertext or "Swing Low<br>Price: %{y}<br>Time: %{x}<extra></extra>")
                            ))

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

    # ➕ Añadir Liquidity Sweeps usando la columna 'Level' (de detect_liquidity) si existe
    liq_data = signals["liquidity"]
    liq_count = 0
    if liq_data is not None:
        for i, row in liq_data.iterrows():
            # Usar 'Sweep' si existe, si no 'Liquidity' (compatibilidad)
            trigger = row.get("Sweep", row.get("Liquidity", None))
            if pd.notna(trigger):
                liq_count += 1
                # Usar 'Price' si existe, si no 'Level', si no el high de la vela
                price = row.get("Price", row.get("Level", df.iloc[i]["high"]))
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
    swing_data = signals.get("swing_highs_lows", None)
    swing_high_count = 0
    swing_low_count = 0
    if swing_data is not None and hasattr(swing_data, 'iterrows'):
        for i, row in swing_data.iterrows():
            highlow = row.get("HighLow", None) if hasattr(row, 'get') else row["HighLow"] if "HighLow" in row else None
            if pd.notna(highlow):
                # Añadir score/confianza como tooltip si existe
                score = row["score"] if "score" in row else None
                confidence = row["confidence"] if "confidence" in row else None
                hovertext = f"Score: {score:.2f}<br>Confianza: {confidence:.2f}" if score is not None or confidence is not None else None
                if highlow == 1:  # Swing High
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
                        hovertemplate=(hovertext or "Swing High<br>Price: %{y}<br>Time: %{x}<extra></extra>")
                    ))
                elif highlow == -1:  # Swing Low
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
                        hovertemplate=(hovertext or "Swing Low<br>Price: %{y}<br>Time: %{x}<extra></extra>")
                    ))

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
            title=dict(text='Tiempo', font=dict(color='#FFFFFF')),
            rangeslider=dict(visible=False),
            fixedrange=False,
            constrain='range',
            scaleratio=None,
            scaleanchor=None,
            autorange=True
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
            fixedrange=False,
            constrain='range',
            scaleratio=None,
            scaleanchor=None,
            autorange=True
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=650,
        hovermode='x unified',
        margin=dict(l=10, r=80, t=60, b=40),
        xaxis_showspikes=True,
        yaxis_showspikes=True,
        spikedistance=1000,
        hoverdistance=100,
        autosize=True,
        dragmode='zoom',  # Cambia a zoom para que el scroll y arrastre hagan zoom, no pan
    )

    # Configuración avanzada de interacción tipo TradingView
    fig.update_xaxes(fixedrange=False, rangeslider_visible=False, constrain='domain',
                     scaleratio=None, scaleanchor=None)
    fig.update_yaxes(fixedrange=False, constrain='domain', scaleratio=None, scaleanchor=None)

    # Configurar hover template personalizado para las velas
    fig.update_traces(
        hovertext=f"Precio: %{{y}}<br>Tiempo: %{{x}}",
        selector=dict(type="candlestick")
    )

    # Información de depuración antes del renderizado
    st.info(f"🎯 Rendering chart with {len(fig.data)} traces and {len(fig.layout.shapes)} shapes")


    # --- Export image button ---
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    export_btn = st.button("Download chart as image (PNG)")
    if export_btn:
        import io
        buf = io.BytesIO()
        fig.write_image(buf, format="png")
        st.download_button(
            label="Download image",
            data=buf.getvalue(),
            file_name="smc_chart.png",
            mime="image/png"
        )

    # --- Center on last relevant signal button ---
    center_btn = st.button("Center on last relevant signal")
    if center_btn:
        last_idx = None
        for overlay in ["fvg", "orderblocks", "bos_choch", "liquidity", "swing_highs_lows"]:
            if overlay in signals and hasattr(signals[overlay], 'last_valid_index'):
                idx = signals[overlay].last_valid_index()
                if idx is not None:
                    last_idx = max(last_idx or 0, idx)
        if last_idx is not None:
            ts = df.iloc[last_idx]["timestamp"]
            fig.update_xaxes(range=[ts - pd.Timedelta(minutes=60), ts + pd.Timedelta(minutes=60)])
            st.info(f"Centered on last relevant signal: {ts}")
        else:
            st.warning("No relevant signal found to center.")

    # Show main chart
    with st.spinner("🎨 Rendering chart..."):
        st.plotly_chart(fig, use_container_width=True, key="main_chart_display", config={
            'displayModeBar': True,
            'displaylogo': False,
            # Show all standard controls
            'scrollZoom': True,
            'doubleClick': 'reset',
        })
        show_temp_message('success', "✅ Chart rendered successfully")


# --- SETUPS & CONFLUENCIAS ---
with tab_setups:
    st.header("Setups & Confluencias")
    # Mostrar setups del snapshot histórico si está en modo histórico y snapshot seleccionado
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
            title=dict(text='Tiempo', font=dict(color='#FFFFFF')),
            rangeslider=dict(visible=False),
            fixedrange=False,
            constrain='range',
            scaleratio=None,
            scaleanchor=None,
            autorange=True
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
            fixedrange=False,
            constrain='range',
            scaleratio=None,
            scaleanchor=None,
            autorange=True
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=650,
        hovermode='x unified',
        margin=dict(l=10, r=80, t=60, b=40),
        xaxis_showspikes=True,
        yaxis_showspikes=True,
        spikedistance=1000,
        hoverdistance=100,
        autosize=True,
        dragmode='zoom',  # Forzar solo zoom, nunca pan
    )
    modo = st.radio(
        "Selecciona el modo:",
        ["Solo histórico", "Indicadores históricos", "Backtest"],
        index=0,
        help="Elige si solo quieres navegar el histórico, ver los indicadores que se habrían generado o simular el backtest de señales."
    )
    # Controles de periodo y timeframe
    st.markdown("#### Parámetros de histórico")
    symbol_hist = st.selectbox("Símbolo", ["BTC/USDT", "ETH/USDT", "EUR/USD", "GBP/USD", "XAU/USD", "SP500"], key="symbol_hist")
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
/* Métricas */
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

/* --- MOBILE OPTIMIZATION --- */
@media (max-width: 800px) {
    /* Reduce padding and margin for main container */
    .main .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-top: 0.5rem !important;
    }
    /* Make sidebar collapsible and overlay */
    section[data-testid="stSidebar"] {
        min-width: 0 !important;
        width: 60vw !important;
        max-width: 80vw !important;
        z-index: 1000;
        box-shadow: 2px 0 8px rgba(0,0,0,0.15);
    }
    /* Reduce font size for headers and text */
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.1em !important;
    }
    .stMarkdown, .stText, .stDataFrame, .stTable, .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
        font-size: 0.98em !important;
    }
    /* Responsive plotly charts */
    .js-plotly-plot, .stPlotlyChart {
        width: 100% !important;
        min-width: 0 !important;
        height: auto !important;
        max-height: 60vw !important;
    }
    /* Make tables scrollable horizontally */
    .stDataFrame, .stTable {
        overflow-x: auto !important;
        display: block !important;
        max-width: 100vw !important;
    }
    /* Reduce button and input size */
    button, .stButton>button, input, select, textarea {
        font-size: 1em !important;
        padding: 0.5em 0.7em !important;
    }
    /* Hide Streamlit footer */
    footer {display: none !important;}
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
    st.markdown("## 📈 Advanced Historical Analysis")

    # Create tabs for different charts
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Signal Evolution", "💰 Risk:Reward", "🎯 Confidence", "🏦 Market"])

    with tab1:
        st.markdown("### 📊 Signal Evolution Over Time")
        try:
            evolution_chart = st.session_state.historical_visualizer.create_historical_evolution_chart()
            if evolution_chart and evolution_chart.data:
                st.plotly_chart(evolution_chart, use_container_width=True, key="evolution_chart")
            else:
                st.info("📊 Not enough data to show signal evolution")
        except Exception as e:
            st.error(f"Error creating evolution chart: {e}")

    with tab2:
        st.markdown("### 💰 Risk:Reward Evolution")
        try:
            rr_chart = st.session_state.historical_visualizer.create_rr_evolution_chart()
            if rr_chart and rr_chart.data:
                st.plotly_chart(rr_chart, use_container_width=True, key="rr_chart")
            else:
                st.info("💰 Not enough data to show R:R evolution")
        except Exception as e:
            st.error(f"Error creating R:R chart: {e}")

    with tab3:
        st.markdown("### 🎯 Confidence Evolution")
        try:
            confidence_chart = st.session_state.historical_visualizer.create_confidence_evolution_chart()
            if confidence_chart and confidence_chart.data:
                st.plotly_chart(confidence_chart, use_container_width=True, key="confidence_chart")
            else:
                st.info("🎯 Not enough data to show confidence evolution")
        except Exception as e:
            st.error(f"Error creating confidence chart: {e}")

    with tab4:
        st.markdown("### 🏦 Market Conditions")
        try:
            market_chart = st.session_state.historical_visualizer.create_market_conditions_chart()
            if market_chart and market_chart.data:
                st.plotly_chart(market_chart, use_container_width=True, key="market_chart")
            else:
                st.info("🏦 Not enough data to show market conditions")
        except Exception as e:
            st.error(f"Error creating market chart: {e}")

    # Show detailed historical performance analysis
    if st.session_state.historical_manager.snapshots:
        st.markdown("### 📋 Detailed Historical Performance Analysis")

        # Get detailed statistics
        stats = st.session_state.historical_manager.get_signal_statistics()

        if stats:
            # Main metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("📊 Total Signals", stats['total_signals'])

            with col2:
                st.metric("🟢 BUY Signals", stats['buy_signals'])

            with col3:
                st.metric("🔴 SELL Signals", stats['sell_signals'])

            with col4:
                st.metric("💎 Avg R:R", f"{stats['avg_rr']:.2f}:1")

            with col5:
                st.metric("🎯 Avg Confidence", f"{stats['avg_confidence']:.1%}")

            # Additional info in tabs
            tab1, tab2, tab3 = st.tabs(["📈 Statistics", "⏰ Period", "🔍 Details"])

            with tab1:
                col1, col2 = st.columns(2)

                with col1:
                    st.info(f"""
                    **🎯 Signal Quality:**
                    - Total snapshots: {stats['snapshots_count']}
                    - Signals per snapshot: {stats['total_signals']/max(stats['snapshots_count'], 1):.1f}
                    - BUY/SELL Ratio: {stats['buy_signals']/max(stats['sell_signals'], 1):.2f}
                    """)

                with col2:
                    st.info(f"""
                    **💰 Risk Metrics:**
                    - Avg R:R: {stats['avg_rr']:.2f}:1
                    - Avg Confidence: {stats['avg_confidence']:.1%}
                    - BUY Signals: {stats['buy_signals']/max(stats['total_signals'], 1):.1%}
                    """)

            with tab2:
                duration = stats['timespan']['duration']
                hours = duration.total_seconds() / 3600

                st.info(f"""
                **⏱️ Analyzed Period:**
                - Start: {stats['timespan']['start'].strftime('%Y-%m-%d %H:%M:%S')}
                - End: {stats['timespan']['end'].strftime('%Y-%m-%d %H:%M:%S')}
                - Duration: {str(duration).split('.')[0]}
                - Total hours: {hours:.1f}h
                """)

            with tab3:
                st.info(f"""
                **🔍 Detailed Analysis:**
                - Symbol: {symbol}
                - Timeframe: {timeframe}
                - Historical period: {historical_period[0]}
                - Snapshots generated: {stats['snapshots_count']}
                - Data per snapshot: ~{100} candles
                """)

            # Progress of historical analysis
            if len(st.session_state.historical_manager.snapshots) > 0:
                current_pos = st.session_state.historical_visualizer.current_snapshot_index
                total_pos = len(st.session_state.historical_manager.snapshots)
                progress = (current_pos + 1) / total_pos

                st.progress(progress, text=f"Historical navigation: {current_pos + 1}/{total_pos}")
        else:
            st.warning("⚠️ No historical statistics available")

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
