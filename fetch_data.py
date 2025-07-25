import os
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data_cache')

def get_ohlcv_with_cache(symbol, timeframe, start, end, provider_hint=None):
    """
    Devuelve un DataFrame OHLCV para el rango solicitado, usando caché local y descargas incrementales si faltan datos.
    Guarda y actualiza la caché automáticamente.
    - symbol: str (ej: 'BTC/USDT' o 'EUR/USD')
    - timeframe: str (ej: '15m', '1h')
    - start, end: str o datetime
    - provider_hint: 'binance' o 'yahoo' (opcional, para forzar proveedor)
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    import streamlit as st
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{symbol.replace('/', '_')}_{timeframe}.parquet")
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    # Ensure tz-awareness for all datetime objects (force UTC)
    if getattr(start_dt, 'tzinfo', None) is None:
        start_dt = pd.Timestamp(start_dt).tz_localize('UTC')
    else:
        start_dt = pd.Timestamp(start_dt).tz_convert('UTC')
    if getattr(end_dt, 'tzinfo', None) is None:
        end_dt = pd.Timestamp(end_dt).tz_localize('UTC')
    else:
        end_dt = pd.Timestamp(end_dt).tz_convert('UTC')
    # Detect provider: all crypto symbols use Binance by default
    binance_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "XRP/USDT", "FARTCOIN/USDT", "SUI/USDT"]
    if provider_hint:
        provider = provider_hint
    else:
        provider = 'binance'

    # --- In-memory session cache for fast incremental updates ---
    session_key = f"ohlcv_{symbol.replace('/', '_')}_{timeframe}"
    cache_loaded_from = None
    if hasattr(st, 'session_state') and session_key in st.session_state:
        cache_df = st.session_state[session_key]
        cache_loaded_from = 'memory'
        print(f"[CACHE] Cache hit in memory for {session_key} ({len(cache_df)} rows)")
    elif os.path.exists(cache_path):
        cache_df = pd.read_parquet(cache_path)
        cache_df['timestamp'] = pd.to_datetime(cache_df['timestamp'])
        if hasattr(st, 'session_state'):
            st.session_state[session_key] = cache_df.copy()
        cache_loaded_from = 'disk'
        print(f"[CACHE] Cache hit on disk for {session_key} ({len(cache_df)} rows)")
    else:
        cache_df = pd.DataFrame()
        cache_loaded_from = 'none'
        print(f"[CACHE] No cache found for {session_key}")

    # Determine missing ranges
    if not cache_df.empty:
        cache_df['timestamp'] = pd.to_datetime(cache_df['timestamp'])
        # Force all cache timestamps to UTC tz-aware
        if getattr(cache_df['timestamp'].dt, 'tz', None) is None:
            cache_df['timestamp'] = cache_df['timestamp'].dt.tz_localize('UTC')
        else:
            cache_df['timestamp'] = cache_df['timestamp'].dt.tz_convert('UTC')
        min_cached = cache_df['timestamp'].min()
        max_cached = cache_df['timestamp'].max()
    else:
        min_cached = max_cached = None
    missing_ranges = []
    if min_cached is None or start_dt < min_cached:
        missing_ranges.append((start_dt, min_cached or end_dt))
    if max_cached is None or end_dt > max_cached:
        missing_ranges.append((max_cached or start_dt, end_dt))

    # Download and join only missing blocks
    new_data = []
    downloaded_any = False
    for rng_start, rng_end in missing_ranges:
        if rng_start is None or rng_end is None or rng_start >= rng_end:
            continue
        print(f"[DOWNLOAD] Downloading {symbol} {timeframe} from {rng_start} to {rng_end}")
        downloaded_any = True
        if provider == 'binance':
            df = get_ohlcv_full(symbol, timeframe, since=rng_start, until=rng_end)
        else:
            import yfinance as yf
            interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "240m", "1d": "1d"}
            ymap = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "XAU/USD": "XAUUSD=X", "SP500": "^GSPC"}
            yf_symbol = ymap.get(symbol, symbol)
            yf_interval = interval_map.get(timeframe, "15m")
            df = yf.download(yf_symbol, start=rng_start, end=rng_end + timedelta(days=1), interval=yf_interval, progress=False)
            if not df.empty:
                df = df.reset_index()
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
                df.columns = [str(col).lower() for col in df.columns]
                if 'datetime' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['datetime'])
                elif 'date' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['date'])
                elif 'index' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['index'])
                else:
                    df['timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
                for col in ['open', 'high', 'low', 'close']:
                    if col not in df.columns:
                        candidates = [c for c in df.columns if c.startswith(col)]
                        if candidates:
                            df[col] = df[candidates[0]]
                if 'volume' not in df.columns:
                    df['volume'] = 0.0
                required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                missing = [col for col in ['open', 'high', 'low', 'close'] if col not in df.columns]
                if missing:
                    print(f"❌ Missing required price columns from Yahoo Finance for {symbol}: {missing}")
                    continue
                df = df[required_cols]
        if not df.empty:
            new_data.append(df)

    # Merge all and clean duplicates
    all_data = pd.concat([cache_df] + new_data, ignore_index=True)
    if not all_data.empty:
        all_data = all_data.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        # Ensure tz-awareness matches for filtering
        if hasattr(all_data['timestamp'], 'dt') and all_data['timestamp'].dt.tz is not None:
            # If timestamps are tz-aware, localize/convert start_dt and end_dt to UTC
            import pandas as pd
            if getattr(start_dt, 'tzinfo', None) is None:
                start_dt = pd.Timestamp(start_dt).tz_localize('UTC')
            else:
                start_dt = pd.Timestamp(start_dt).tz_convert('UTC')
            if getattr(end_dt, 'tzinfo', None) is None:
                end_dt = pd.Timestamp(end_dt).tz_localize('UTC')
            else:
                end_dt = pd.Timestamp(end_dt).tz_convert('UTC')
        # Filter only requested range
        mask = (all_data['timestamp'] >= start_dt) & (all_data['timestamp'] <= end_dt)
        result = all_data.loc[mask].copy()
        # Update both disk and session cache
        all_data.to_parquet(cache_path, index=False)
        if hasattr(st, 'session_state'):
            st.session_state[session_key] = all_data.copy()
        # UI indicator for cache/download source
        if hasattr(st, 'info'):
            if downloaded_any:
                st.info(f"Data for {symbol} {timeframe} was downloaded and cached. Rows: {len(result)}")
            elif cache_loaded_from == 'memory':
                st.info(f"Data for {symbol} {timeframe} loaded from memory cache. Rows: {len(result)}")
            elif cache_loaded_from == 'disk':
                st.info(f"Data for {symbol} {timeframe} loaded from disk cache. Rows: {len(result)}")
            else:
                st.info(f"Data for {symbol} {timeframe} loaded. Rows: {len(result)}")
        return result
    return pd.DataFrame()
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import yfinance as yf

def get_ohlcv(symbol="BTC/USDT", timeframe="1m", limit=100):
    """
    Obtener datos OHLCV básicos

    Args:
        symbol: Par de trading
        timeframe: Marco temporal
        limit: Número de velas

    Returns:
        DataFrame con datos OHLC
    """
    # Todos los símbolos usan Binance por defecto
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def get_ohlcv_extended(symbol="BTC/USDT", timeframe="1m", days=5):
    """
    Obtener datos OHLCV extendidos para múltiples días

    Args:
        symbol: Par de trading
        timeframe: Marco temporal
        days: Número de días de datos

    Returns:
        DataFrame con datos OHLC extendidos
    """
    # Todos los símbolos usan Binance por defecto
    timeframe_minutes = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440
    }
    minutes_per_day = 1440  # 24 * 60
    minutes_in_timeframe = timeframe_minutes.get(timeframe, 1)
    candles_per_day = minutes_per_day // minutes_in_timeframe
    total_limit = candles_per_day * days
    total_limit = min(total_limit, 1000)
    print(f"📊 Obteniendo {total_limit} velas para {days} días en {timeframe}")
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=total_limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    print(f"   ✅ Obtenidos {len(df)} puntos de datos desde {df['timestamp'].min()} hasta {df['timestamp'].max()}")
    return df

def get_ohlcv_full(symbol="BTC/USDT", timeframe="1m", since=None, until=None, max_limit=1000, sleep_sec=0.2):
    """
    Descargar todas las velas necesarias para cubrir el rango [since, until] (inclusive), paginando si es necesario.

    Args:
        symbol: Par de trading
        timeframe: Marco temporal
        since: datetime o timestamp inicial (ms)
        until: datetime o timestamp final (ms)
        max_limit: máximo de velas por llamada (por defecto 1000 para Binance)
        sleep_sec: segundos a esperar entre llamadas para evitar rate limit

    Returns:
        DataFrame con todas las velas en el rango
    """
    try:
        exchange = ccxt.binance()
        all_ohlcv = []
        since_ms = int(since.timestamp() * 1000) if isinstance(since, datetime) else since
        until_ms = int(until.timestamp() * 1000) if isinstance(until, datetime) else until
        fetch_since = since_ms
        while True:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=fetch_since, limit=max_limit)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            last_ts = ohlcv[-1][0]
            if until_ms and last_ts >= until_ms:
                break
            if len(ohlcv) < max_limit:
                break
            fetch_since = last_ts + 1
            time.sleep(sleep_sec)
        df = pd.DataFrame(all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        # Filtrar usando timestamps UTC tz-aware
        if since:
            since_dt = pd.to_datetime(since, utc=True)
            df = df[df["timestamp"] >= since_dt]
        if until:
            until_dt = pd.to_datetime(until, utc=True)
            df = df[df["timestamp"] <= until_dt]
        df = df.reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Binance no disponible ({e}), símbolo no soportado: {symbol}. Solo se aceptan pares XXX/USDT.")
        return pd.DataFrame()
