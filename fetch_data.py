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
    # Detect provider: use Yahoo by default for better cloud compatibility
    binance_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "XRP/USDT", "FARTCOIN/USDT", "SUI/USDT"]
    if provider_hint:
        provider = provider_hint
    else:
        provider = 'yahoo'  # Cambiado a Yahoo por defecto

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
            interval_map = {
                "1m": "1m", 
                "5m": "5m", 
                "15m": "15m", 
                "30m": "30m",
                "1h": "60m", 
                "4h": "4h", 
                "1d": "1d",
                "1w": "1wk"
            }
            ymap = {
                "EUR/USD": "EURUSD=X", 
                "GBP/USD": "GBPUSD=X", 
                "XAU/USD": "XAUUSD=X", 
                "SP500": "^GSPC",
                "BTC/USDT": "BTC-USD",
                "ETH/USDT": "ETH-USD",
                "SOL/USDT": "SOL-USD",
                "XRP/USDT": "XRP-USD"
            }
            yf_symbol = ymap.get(symbol, symbol)
            yf_interval = interval_map.get(timeframe, "15m")
            df = yf.download(yf_symbol, start=rng_start, end=rng_end + timedelta(days=1), interval=yf_interval, progress=False)
            if not df.empty:
                df = df.reset_index()
                # Handle MultiIndex columns from Yahoo Finance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
                df.columns = [str(col).lower() for col in df.columns]
                
                # Extract timestamp correctly
                if 'datetime' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['datetime'])
                elif 'date' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['date'])
                elif 'index' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['index'])
                else:
                    df['timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
                
                # Ensure timestamp is UTC
                if df['timestamp'].dt.tz is None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
                else:
                    df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
                
                # Map price columns correctly - Yahoo Finance uses different column names
                price_mapping = {
                    'open': ['open', 'open_', 'Open', 'open_btc-usd', 'open_eth-usd', 'open_sol-usd', 'open_xrp-usd'],
                    'high': ['high', 'high_', 'High', 'high_btc-usd', 'high_eth-usd', 'high_sol-usd', 'high_xrp-usd'],
                    'low': ['low', 'low_', 'Low', 'low_btc-usd', 'low_eth-usd', 'low_sol-usd', 'low_xrp-usd'],
                    'close': ['close', 'close_', 'Close', 'close_btc-usd', 'close_eth-usd', 'close_sol-usd', 'close_xrp-usd']
                }
                
                for target_col, possible_cols in price_mapping.items():
                    if target_col not in df.columns:
                        for col in possible_cols:
                            if col in df.columns:
                                df[target_col] = df[col]
                                break
                

                
                # Handle volume
                if 'volume' not in df.columns:
                    volume_candidates = [c for c in df.columns if 'volume' in c.lower()]
                    if volume_candidates:
                        df['volume'] = df[volume_candidates[0]]
                    else:
                        df['volume'] = 0.0
                
                # Validate required columns
                required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                missing = [col for col in ['open', 'high', 'low', 'close'] if col not in df.columns]
                if missing:
                    print(f"❌ Missing required price columns from Yahoo Finance for {symbol}: {missing}")
                    continue
                
                # Select only required columns and ensure proper order
                df = df[required_cols]
                
                # Remove duplicates based on timestamp
                df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        if not df.empty:
            new_data.append(df)

    # Merge all and clean duplicates
    all_data = pd.concat([cache_df] + new_data, ignore_index=True)
    if not all_data.empty:
        # Remove duplicates and ensure proper sorting
        all_data = all_data.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        # Additional validation for Yahoo Finance data
        if provider == 'yahoo':
            # Remove any rows with invalid timestamps
            all_data = all_data[all_data['timestamp'].notna()]
            # Ensure all price columns are numeric
            for col in ['open', 'high', 'low', 'close']:
                all_data[col] = pd.to_numeric(all_data[col], errors='coerce')
            all_data = all_data.dropna(subset=['open', 'high', 'low', 'close'])
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
    Obtener datos OHLCV básicos usando Yahoo Finance

    Args:
        symbol: Par de trading
        timeframe: Marco temporal
        limit: Número de velas

    Returns:
        DataFrame con datos OHLC
    """
    import yfinance as yf
    
    # Mapear símbolos para Yahoo Finance
    ymap = {
        "EUR/USD": "EURUSD=X", 
        "GBP/USD": "GBPUSD=X", 
        "XAU/USD": "XAUUSD=X", 
        "BTC/USDT": "BTC-USD",
        "ETH/USDT": "ETH-USD",
        "SOL/USDT": "SOL-USD",
        "XRP/USDT": "XRP-USD",
        "FARTCOIN/USDT": "FARTCOIN-USD"
    }
    
    # Mapear timeframes para Yahoo Finance
    interval_map = {
        "1m": "1m", 
        "5m": "5m", 
        "15m": "15m", 
        "30m": "30m",
        "1h": "60m", 
        "4h": "4h", 
        "1d": "1d",
        "1w": "1wk"
    }
    
    yahoo_symbol = ymap.get(symbol, symbol.replace("/", "-"))
    yahoo_interval = interval_map.get(timeframe, timeframe)
    
    try:
        ticker = yf.Ticker(yahoo_symbol)
        
        # Calcular el número correcto de velas según timeframe
        candles_per_day = {
            "1m": 1440,    # 24h * 60min
            "5m": 288,     # 24h * 12
            "15m": 96,     # 24h * 4
            "30m": 48,     # 24h * 2
            "1h": 24,      # 24h
            "4h": 6,       # 24h / 4
            "1d": 1,       # 1 día
            "1w": 1        # 1 semana
        }
        
        max_candles = candles_per_day.get(timeframe, 24) * limit
        
        # Limitar a un máximo razonable
        max_candles = min(max_candles, 1000)
        
        df = ticker.history(period=f"{limit}d", interval=yahoo_interval)
        
        # Limitar el número de filas si es necesario
        if len(df) > max_candles:
            df = df.tail(max_candles)
        
        if not df.empty:
            df = df.reset_index()
            # Handle MultiIndex columns from Yahoo Finance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
            df.columns = [str(col).lower() for col in df.columns]
            
            # Extract timestamp correctly
            if 'datetime' in df.columns:
                df['timestamp'] = pd.to_datetime(df['datetime'])
            elif 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
            elif 'index' in df.columns:
                df['timestamp'] = pd.to_datetime(df['index'])
            else:
                df['timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            
            # Ensure timestamp is UTC
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Map price columns correctly
            price_mapping = {
                'open': ['open', 'open_'],
                'high': ['high', 'high_'],
                'low': ['low', 'low_'],
                'close': ['close', 'close_']
            }
            
            for target_col, possible_cols in price_mapping.items():
                if target_col not in df.columns:
                    for col in possible_cols:
                        if col in df.columns:
                            df[target_col] = df[col]
                            break
            
            # Handle volume
            if 'volume' not in df.columns:
                volume_candidates = [c for c in df.columns if 'volume' in c.lower()]
                if volume_candidates:
                    df['volume'] = df[volume_candidates[0]]
                else:
                    df['volume'] = 0.0
            
            # Select only required columns and ensure proper order
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            
            # Remove duplicates based on timestamp
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
            
            return df
        else:
            print(f"❌ No se pudieron obtener datos para {symbol}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error obteniendo datos de Yahoo Finance para {symbol}: {e}")
        return pd.DataFrame()

def get_ohlcv_extended(symbol="BTC/USDT", timeframe="1m", days=5):
    """
    Obtener datos OHLCV extendidos para múltiples días usando Yahoo Finance

    Args:
        symbol: Par de trading
        timeframe: Marco temporal
        days: Número de días de datos

    Returns:
        DataFrame con datos OHLC extendidos
    """
    import yfinance as yf
    
    # Mapear símbolos para Yahoo Finance
    ymap = {
        "EUR/USD": "EURUSD=X", 
        "GBP/USD": "GBPUSD=X", 
        "XAU/USD": "XAUUSD=X", 
        "BTC/USDT": "BTC-USD",
        "ETH/USDT": "ETH-USD",
        "SOL/USDT": "SOL-USD",
        "XRP/USDT": "XRP-USD",
        "FARTCOIN/USDT": "FARTCOIN-USD"
    }
    
    # Mapear timeframes para Yahoo Finance
    interval_map = {
        "1m": "1m", 
        "5m": "5m", 
        "15m": "15m", 
        "30m": "30m",
        "1h": "60m", 
        "4h": "4h", 
        "1d": "1d",
        "1w": "1wk"
    }
    
    yahoo_symbol = ymap.get(symbol, symbol.replace("/", "-"))
    yahoo_interval = interval_map.get(timeframe, timeframe)
    
    try:
        ticker = yf.Ticker(yahoo_symbol)
        
        # Calcular el número correcto de velas según timeframe y días
        candles_per_day = {
            "1m": 1440,    # 24h * 60min
            "5m": 288,     # 24h * 12
            "15m": 96,     # 24h * 4
            "30m": 48,     # 24h * 2
            "1h": 24,      # 24h
            "4h": 6,       # 24h / 4
            "1d": 1,       # 1 día
            "1w": 1        # 1 semana
        }
        
        max_candles = candles_per_day.get(timeframe, 24) * days
        
        # Limitar a un máximo razonable para evitar sobrecarga
        max_candles = min(max_candles, 1000)
        
        df = ticker.history(period=f"{days}d", interval=yahoo_interval)
        
        # Limitar el número de filas si es necesario
        if len(df) > max_candles:
            df = df.tail(max_candles)
        
        if not df.empty:
            df = df.reset_index()
            # Handle MultiIndex columns from Yahoo Finance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
            df.columns = [str(col).lower() for col in df.columns]
            
            # Extract timestamp correctly
            if 'datetime' in df.columns:
                df['timestamp'] = pd.to_datetime(df['datetime'])
            elif 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
            elif 'index' in df.columns:
                df['timestamp'] = pd.to_datetime(df['index'])
            else:
                df['timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            
            # Ensure timestamp is UTC
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Map price columns correctly
            price_mapping = {
                'open': ['open', 'open_'],
                'high': ['high', 'high_'],
                'low': ['low', 'low_'],
                'close': ['close', 'close_']
            }
            
            for target_col, possible_cols in price_mapping.items():
                if target_col not in df.columns:
                    for col in possible_cols:
                        if col in df.columns:
                            df[target_col] = df[col]
                            break
            
            # Handle volume
            if 'volume' not in df.columns:
                volume_candidates = [c for c in df.columns if 'volume' in c.lower()]
                if volume_candidates:
                    df['volume'] = df[volume_candidates[0]]
                else:
                    df['volume'] = 0.0
            
            # Select only required columns and ensure proper order
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            
            # Remove duplicates based on timestamp
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
            
            print(f"📊 Obtenidos {len(df)} puntos de datos desde {df['timestamp'].min()} hasta {df['timestamp'].max()}")
            return df
        else:
            print(f"❌ No se pudieron obtener datos para {symbol}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error obteniendo datos de Yahoo Finance para {symbol}: {e}")
        return pd.DataFrame()

def get_ohlcv_full(symbol="BTC/USDT", timeframe="1m", since=None, until=None, max_limit=1000, sleep_sec=0.2):
    """
    Descargar todas las velas necesarias para cubrir el rango [since, until] usando Yahoo Finance.

    Args:
        symbol: Par de trading
        timeframe: Marco temporal
        since: datetime o timestamp inicial
        until: datetime o timestamp final
        max_limit: máximo de velas por llamada (no aplicable para Yahoo)
        sleep_sec: segundos a esperar entre llamadas (no aplicable para Yahoo)

    Returns:
        DataFrame con todas las velas en el rango
    """
    import yfinance as yf
    import time
    
    # Mapear símbolos para Yahoo Finance
    ymap = {
        "EUR/USD": "EURUSD=X", 
        "GBP/USD": "GBPUSD=X", 
        "XAU/USD": "XAUUSD=X", 
        "BTC/USDT": "BTC-USD",
        "ETH/USDT": "ETH-USD",
        "SOL/USDT": "SOL-USD",
        "XRP/USDT": "XRP-USD",
        "FARTCOIN/USDT": "FARTCOIN-USD"
    }
    
    # Mapear timeframes para Yahoo Finance
    interval_map = {
        "1m": "1m", 
        "5m": "5m", 
        "15m": "15m", 
        "30m": "30m",
        "1h": "60m", 
        "4h": "4h", 
        "1d": "1d",
        "1w": "1wk"
    }
    
    yahoo_symbol = ymap.get(symbol, symbol.replace("/", "-"))
    yahoo_interval = interval_map.get(timeframe, timeframe)
    
    try:
        ticker = yf.Ticker(yahoo_symbol)
        
        # Calcular el período basado en since y until
        if since and until:
            start_date = pd.to_datetime(since)
            end_date = pd.to_datetime(until)
            period = None
        else:
            # Si no se especifican fechas, usar un período por defecto
            start_date = None
            end_date = None
            period = "1y"  # 1 año por defecto
        
        df = ticker.history(
            start=start_date,
            end=end_date,
            period=period,
            interval=yahoo_interval
        )
        
        if not df.empty:
            df = df.reset_index()
            # Handle MultiIndex columns from Yahoo Finance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
            df.columns = [str(col).lower() for col in df.columns]
            
            # Extract timestamp correctly
            if 'datetime' in df.columns:
                df['timestamp'] = pd.to_datetime(df['datetime'])
            elif 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
            elif 'index' in df.columns:
                df['timestamp'] = pd.to_datetime(df['index'])
            else:
                df['timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            
            # Ensure timestamp is UTC
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Map price columns correctly
            price_mapping = {
                'open': ['open', 'open_'],
                'high': ['high', 'high_'],
                'low': ['low', 'low_'],
                'close': ['close', 'close_']
            }
            
            for target_col, possible_cols in price_mapping.items():
                if target_col not in df.columns:
                    for col in possible_cols:
                        if col in df.columns:
                            df[target_col] = df[col]
                            break
            
            # Handle volume
            if 'volume' not in df.columns:
                volume_candidates = [c for c in df.columns if 'volume' in c.lower()]
                if volume_candidates:
                    df['volume'] = df[volume_candidates[0]]
                else:
                    df['volume'] = 0.0
            
            # Select only required columns and ensure proper order
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            
            # Remove duplicates based on timestamp
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
            
            # Filtrar usando timestamps UTC tz-aware
            if since:
                since_dt = pd.to_datetime(since, utc=True)
                df = df[df["timestamp"] >= since_dt]
            if until:
                until_dt = pd.to_datetime(until, utc=True)
                df = df[df["timestamp"] <= until_dt]
            
            return df
        else:
            print(f"❌ No se pudieron obtener datos para {symbol}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error obteniendo datos de Yahoo Finance para {symbol}: {e}")
        return pd.DataFrame()
