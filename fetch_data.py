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
