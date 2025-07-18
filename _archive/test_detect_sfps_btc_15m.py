import pandas as pd
from datetime import datetime, timedelta
from fetch_data import get_ohlcv_with_cache
from app_streamlit import detect_sfps

if __name__ == "__main__":
    # Parameters
    symbol = "BTC/USDT"
    timeframe = "15m"
    days = 180  # 6 months
    print(f"Fetching {days} days of {symbol} ({timeframe})...")
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)
    df = get_ohlcv_with_cache(symbol, timeframe, start_dt, end_dt)
    print(f"Loaded {len(df)} rows from {df['timestamp'].min()} to {df['timestamp'].max()}")
    if df.empty:
        print("No data loaded!")
        exit(1)

    # Dummy context for SFP detection (no advanced filters)
    sfps = detect_sfps(df, lookback=len(df), market_structure='neutral', fvgs=[], obs=[], choch_list=[], require_choch=False)
    print(f"\nDetected {len(sfps)} SFPs in {days} days of {symbol} ({timeframe}):")
    for i, sfp in enumerate(sfps):
        print(f"{i+1:3d}. {sfp['timestamp']} | {sfp['type']} | swept: {sfp['swept_level']:.2f} | close: {sfp['close']:.2f}")
    if not sfps:
        print("No SFPs detected. Consider adjusting filters or reviewing detection logic.")
