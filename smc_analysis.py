from smartmoneyconcepts import smc
import pandas as pd
import numpy as np

# Umbrales globales de volatilidad
LOW_VOL_THRESHOLD = 0.5  # %
HIGH_VOL_THRESHOLD = 5.0  # %

# --- Ajuste de liquidez para timeframes bajos ---
def detect_liquidity(df, swing_highs_lows, timeframe="15m"):
    """
    Detección adaptativa de liquidez según timeframe y volatilidad
    """
    base_threshold = {
        "1m": 0.0005,
        "5m": 0.001,
        "15m": 0.002,
        "1h": 0.005
    }
    # Calcular factor de volatilidad relativo
    volatility_factor = df['high'].std() / df['close'].mean() if df['close'].mean() > 0 else 1
    threshold = base_threshold.get(timeframe, 0.002) * max(volatility_factor, 0.5)
    # Logging para monitoreo
    print(f"[LIQUIDITY] Timeframe: {timeframe}, Threshold: {threshold:.6f}, VolFactor: {volatility_factor:.4f}")
    try:
        liquidity = smc.liquidity(df, swing_highs_lows)
        # Filtrar por threshold adaptativo si existe columna 'Level'
        if hasattr(liquidity, 'Level'):
            mask = liquidity['Level'].notna() & (liquidity['Level'].abs() > threshold)
            filtered = liquidity[mask]
            if not filtered.empty:
                return filtered
            # Si no hay zonas válidas, relajar el threshold a la mitad
            relaxed_threshold = threshold * 0.5
            mask_relaxed = liquidity['Level'].notna() & (liquidity['Level'].abs() > relaxed_threshold)
            filtered_relaxed = liquidity[mask_relaxed]
            if not filtered_relaxed.empty:
                print(f"[LIQUIDITY][INFO] Zonas detectadas con threshold relajado {relaxed_threshold:.6f}")
                return filtered_relaxed
            # Si sigue vacío, devolver todas las zonas con Level no nulo
            mask_any = liquidity['Level'].notna()
            filtered_any = liquidity[mask_any]
            if not filtered_any.empty:
                print(f"[LIQUIDITY][INFO] Zonas devueltas sin filtrar por magnitud")
                return filtered_any
            print(f"[LIQUIDITY][WARN] No se detectaron zonas válidas con threshold {threshold:.6f} ni relajado")
            return liquidity
        return liquidity
    except Exception as e:
        print(f"[LIQUIDITY][ERROR] {e}")
        return smc.liquidity(df, swing_highs_lows)

def detect_orderblocks(df, swing_highs_lows, timeframe="15m"):
    """
    Detección adaptativa de order blocks según timeframe y volatilidad
    """
    base_threshold = {
        "1m": 0.0005,
        "5m": 0.001,
        "15m": 0.002,
        "1h": 0.005
    }
    volatility_factor = df['high'].std() / df['close'].mean() if df['close'].mean() > 0 else 1
    threshold = base_threshold.get(timeframe, 0.002) * max(volatility_factor, 0.5)
    print(f"[ORDERBLOCKS] Timeframe: {timeframe}, Threshold: {threshold:.6f}, VolFactor: {volatility_factor:.4f}")
    try:
        ob = smc.ob(df, swing_highs_lows)
        if hasattr(ob, 'Top') and hasattr(ob, 'Bottom'):
            mask = ob['Top'].notna() & ob['Bottom'].notna() & ((ob['Top'] - ob['Bottom']).abs() > threshold)
            filtered = ob[mask]
            if filtered.empty:
                print(f"[ORDERBLOCKS][WARN] No se detectaron OB válidos con threshold {threshold:.6f}")
            return filtered
        return ob
    except Exception as e:
        print(f"[ORDERBLOCKS][ERROR] {e}")
        return smc.ob(df, swing_highs_lows)

# --- Manejo de gaps extremos antes de señales ---
def has_extreme_gap(df, window=14):
    if len(df) < window:
        return False
    high = df['high'].iloc[-1]
    low = df['low'].iloc[-1]
    high_low_gap = high - low
    # ATR móvil
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=window).mean().iloc[-1]
    gap_threshold = atr * 3
    return high_low_gap > gap_threshold

# --- Volatilidad móvil consistente ---
def calc_volatility(df, window=20):
    return df['close'].pct_change().rolling(window).std()

# --- Análisis principal con mejoras ---
def run_analysis(df, params=None, timeframe="15m"):
    if params is None:
        params = {}
    swing_highs_lows = smc.swing_highs_lows(df, swing_length=10)
    print(f"[DEBUG] Liquidity detection: {df['high'].max()}-{df['low'].min()}")
    # Calcular sesiones
    sessions_data = {}
    try:
        sessions_data["tokyo"] = smc.sessions(df, session="Tokyo", start_time="00:00", end_time="09:00")
    except:
        sessions_data["tokyo"] = pd.DataFrame()
    try:
        sessions_data["london"] = smc.sessions(df, session="London", start_time="08:00", end_time="17:00")
    except:
        sessions_data["london"] = pd.DataFrame()
    try:
        sessions_data["new_york"] = smc.sessions(df, session="New York", start_time="13:00", end_time="22:00")
    except:
        sessions_data["new_york"] = pd.DataFrame()
    # Volatilidad móvil
    volatility_series = calc_volatility(df)
    volatility_pct = volatility_series.iloc[-1] * 100 if not volatility_series.isna().all() else 0
    if volatility_pct < LOW_VOL_THRESHOLD:
        volatility_label = "LOW_VOLATILITY"
    elif volatility_pct > HIGH_VOL_THRESHOLD:
        volatility_label = "HIGH_VOLATILITY"
    else:
        volatility_label = "NORMAL_VOLATILITY"
    # --- Manejo de gaps extremos ---
    if has_extreme_gap(df):
        print("[GAP] Gap extremo detectado, omitiendo generación de señales.")
        signals = []
    else:
        signals = None  # Se generan normalmente en el motor de señales
    return {
        "fvg": smc.fvg(df),
        "orderblocks": detect_orderblocks(df, swing_highs_lows, timeframe),
        "bos_choch": smc.bos_choch(df, swing_highs_lows),
        "liquidity": detect_liquidity(df, swing_highs_lows, timeframe),
        "sessions": sessions_data,
        "swing_highs_lows": swing_highs_lows,
        "volatility": volatility_label,
        "volatility_pct": volatility_pct,
        "signals": signals
    }

def analyze(df, params=None, timeframe="15m"):
    return run_analysis(df, params, timeframe)

def get_current_session(timestamp):
    """Determinar la sesión actual basada en la hora UTC"""
    hour = timestamp.hour

    # Sesiones en UTC
    if 23 <= hour or hour < 8:  # Tokyo: 23:00 - 08:00 UTC
        return "tokyo"
    elif 8 <= hour < 16:  # London: 08:00 - 16:00 UTC
        return "london"
    elif 13 <= hour < 22:  # New York: 13:00 - 22:00 UTC (overlap con London)
        return "new_york"
    else:
        return "between_sessions"

def get_session_color(session):
    """Obtener el color de fondo para cada sesión"""
    session_colors = {
        "tokyo": "rgba(255, 193, 7, 0.05)",      # Amarillo suave - Sesión Asiática
        "london": "rgba(76, 175, 80, 0.05)",     # Verde suave - Sesión Europea
        "new_york": "rgba(33, 150, 243, 0.05)",  # Azul suave - Sesión Americana
        "between_sessions": "rgba(158, 158, 158, 0.02)"  # Gris muy suave
    }
    return session_colors.get(session, "rgba(158, 158, 158, 0.02)")
