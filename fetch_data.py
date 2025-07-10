import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

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
