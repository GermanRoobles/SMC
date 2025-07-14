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
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{symbol.replace('/', '_')}_{timeframe}.parquet")
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    # Detectar proveedor
    if provider_hint:
        provider = provider_hint
    elif symbol in ["BTC/USDT", "ETH/USDT"]:
        provider = 'binance'
    else:
        provider = 'yahoo'
    # Cargar caché si existe
    if os.path.exists(cache_path):
        cache_df = pd.read_parquet(cache_path)
        cache_df['timestamp'] = pd.to_datetime(cache_df['timestamp'])
    else:
        cache_df = pd.DataFrame()
    # Determinar qué rangos faltan
    if not cache_df.empty:
        min_cached = cache_df['timestamp'].min()
        max_cached = cache_df['timestamp'].max()
    else:
        min_cached = max_cached = None
    missing_ranges = []
    if min_cached is None or start_dt < min_cached:
        missing_ranges.append((start_dt, min_cached or end_dt))
    if max_cached is None or end_dt > max_cached:
        missing_ranges.append((max_cached or start_dt, end_dt))
    # Descargar y unir los bloques faltantes
    new_data = []
    for rng_start, rng_end in missing_ranges:
        if rng_start is None or rng_end is None or rng_start >= rng_end:
            continue
        print(f"Descargando {symbol} {timeframe} desde {rng_start} hasta {rng_end}")
        if provider == 'binance':
            # Usa get_ohlcv_full para Binance
            df = get_ohlcv_full(symbol, timeframe, since=rng_start, until=rng_end)
        else:
            # Yahoo Finance: descarga bloque único (yfinance no permite paginación, pero sí varios periodos)
            import yfinance as yf
            interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "240m", "1d": "1d"}
            yf_symbol = symbol
            ymap = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "XAU/USD": "XAUUSD=X", "SP500": "^GSPC"}
            yf_symbol = ymap.get(symbol, symbol)
            yf_interval = interval_map.get(timeframe, "15m")
            df = yf.download(yf_symbol, start=rng_start, end=rng_end + timedelta(days=1), interval=yf_interval, progress=False)
            if not df.empty:
                df = df.reset_index()
                # Normalizar columnas
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
                # Remap columns if needed
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
                    print(f"❌ Faltan columnas requeridas de precios en Yahoo Finance para {symbol}: {missing}")
                    continue
                df = df[required_cols]
        if not df.empty:
            new_data.append(df)
    # Unir todo y limpiar duplicados
    all_data = pd.concat([cache_df] + new_data, ignore_index=True)
    if not all_data.empty:
        all_data = all_data.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        # Filtrar solo el rango solicitado
        mask = (all_data['timestamp'] >= start_dt) & (all_data['timestamp'] <= end_dt)
        result = all_data.loc[mask].copy()
        # Actualizar caché
        all_data.to_parquet(cache_path, index=False)
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
    # Detectar si es símbolo de Binance o de Yahoo Finance
    if symbol in ["BTC/USDT", "ETH/USDT"]:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    else:
        # Mapear símbolo a ticker de Yahoo Finance
        ymap = {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "XAU/USD": "XAUUSD=X",
            "SP500": "^GSPC"
        }
        yf_symbol = ymap.get(symbol, symbol)
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "240m", "1d": "1d"}
        yf_interval = interval_map.get(timeframe, "15m")
        # Yahoo limita la cantidad de datos en intervalos pequeños
        data = yf.download(yf_symbol, period="7d", interval=yf_interval, progress=False)
        if data.empty:
            print(f"⚠️ Yahoo Finance no devolvió datos para {symbol} en {timeframe}")
            return pd.DataFrame()
        data = data.tail(limit)
        # --- Robust normalization for yfinance DataFrame ---
        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join([str(i) for i in col if i]) for col in data.columns.values]
        # Lowercase and standardize column names
        data.columns = [str(col).lower() for col in data.columns]
        # Reset index to access timestamp
        data = data.reset_index()
        # Find the timestamp column (Datetime, Date, or index)
        if 'datetime' in data.columns:
            data['timestamp'] = pd.to_datetime(data['datetime'])
        elif 'date' in data.columns:
            data['timestamp'] = pd.to_datetime(data['date'])
        elif 'index' in data.columns:
            data['timestamp'] = pd.to_datetime(data['index'])
        else:
            # fallback: use the first column as timestamp if it looks like a date
            data['timestamp'] = pd.to_datetime(data.iloc[:, 0], errors='coerce')

        # Try to remap columns like open_x, open_close, etc. to open, high, low, close
        for col in ['open', 'high', 'low', 'close']:
            if col not in data.columns:
                # Find any column that starts with the required name
                candidates = [c for c in data.columns if c.startswith(col)]
                if candidates:
                    data[col] = data[candidates[0]]

        # If volume is missing, fill with zeros
        if 'volume' not in data.columns:
            data['volume'] = 0.0

        # Ensure required columns exist
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in ['open', 'high', 'low', 'close'] if col not in data.columns]
        if missing:
            print(f"❌ Faltan columnas requeridas de precios en Yahoo Finance para {symbol}: {missing}")
            print(f"[DEBUG] Columnas disponibles: {list(data.columns)}")
            return pd.DataFrame()
        # Reorder and return only required columns
        return data[required_cols]

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
    # Detectar si es símbolo de Binance o de Yahoo Finance
    if symbol in ["BTC/USDT", "ETH/USDT"]:
        # Calcular límite basado en días y timeframe
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
        # Limitar a máximo razonable para evitar problemas de API
        total_limit = min(total_limit, 1000)
        print(f"📊 Obteniendo {total_limit} velas para {days} días en {timeframe}")
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=total_limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        print(f"   ✅ Obtenidos {len(df)} puntos de datos desde {df['timestamp'].min()} hasta {df['timestamp'].max()}")
        return df
    else:
        # Yahoo Finance
        ymap = {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "XAU/USD": "XAUUSD=X",
            "SP500": "^GSPC"
        }
        yf_symbol = ymap.get(symbol, symbol)
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "240m", "1d": "1d"}
        yf_interval = interval_map.get(timeframe, "15m")
        period_map = {1: "1d", 3: "3d", 5: "5d", 7: "7d", 14: "14d", 30: "1mo"}
        period = period_map.get(days, "7d")
        data = yf.download(yf_symbol, period=period, interval=yf_interval, progress=False)
        if data.empty:
            print(f"⚠️ Yahoo Finance no devolvió datos para {symbol} en {timeframe}")
            return pd.DataFrame()
        # --- Robust normalization for yfinance DataFrame ---
        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join([str(i) for i in col if i]) for col in data.columns.values]
        # Lowercase and standardize column names
        data.columns = [str(col).lower() for col in data.columns]
        # Reset index to access timestamp
        data = data.reset_index()
        # Find the timestamp column (Datetime, Date, or index)
        if 'datetime' in data.columns:
            data['timestamp'] = pd.to_datetime(data['datetime'])
        elif 'date' in data.columns:
            data['timestamp'] = pd.to_datetime(data['date'])
        elif 'index' in data.columns:
            data['timestamp'] = pd.to_datetime(data['index'])
        else:
            # fallback: use the first column as timestamp if it looks like a date
            data['timestamp'] = pd.to_datetime(data.iloc[:, 0], errors='coerce')

        # Try to remap columns like open_x, open_close, etc. to open, high, low, close
        for col in ['open', 'high', 'low', 'close']:
            if col not in data.columns:
                candidates = [c for c in data.columns if c.startswith(col)]
                if candidates:
                    data[col] = data[candidates[0]]

        # If volume is missing, fill with zeros
        if 'volume' not in data.columns:
            data['volume'] = 0.0

        # Ensure required columns exist
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in ['open', 'high', 'low', 'close'] if col not in data.columns]
        if missing:
            print(f"❌ Faltan columnas requeridas de precios en Yahoo Finance para {symbol}: {missing}")
            print(f"[DEBUG] Columnas disponibles: {list(data.columns)}")
            return pd.DataFrame()
        # Limitar a la cantidad de velas equivalente a Binance
        timeframe_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
        minutes_per_day = 1440
        minutes_in_timeframe = timeframe_minutes.get(timeframe, 1)
        candles_per_day = minutes_per_day // minutes_in_timeframe
        total_limit = candles_per_day * days
        data = data.tail(total_limit)
        # Reorder and return only required columns
        return data[required_cols]

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
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    if since:
        df = df[df["timestamp"] >= pd.to_datetime(since)]
    if until:
        df = df[df["timestamp"] <= pd.to_datetime(until)]
    df = df.reset_index(drop=True)
    return df
