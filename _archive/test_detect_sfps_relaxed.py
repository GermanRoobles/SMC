# test_detect_sfps_relaxed.py
"""
Test script to detect SFPs on BTC/USDT 15m (last 6 months) with relaxed filters (no market structure, no OB/FVG proximity, no strong rejection, no CHoCH required).
"""
import pandas as pd
from datetime import datetime, timedelta
from fetch_data import get_ohlcv_with_cache
from utils_htf import detect_sfp

symbol = "BTC/USDT"
timeframe = "15m"
end = pd.Timestamp.utcnow().replace(tzinfo=None)
start = end - timedelta(days=180)

print(f"Loading {symbol} {timeframe} data from {start} to {end}...")
df = get_ohlcv_with_cache(symbol, timeframe, start, end)
print(f"Loaded {len(df)} rows.")

print("Detecting SFPs with basic logic (no filters)...")
sfps = detect_sfp(df)
print(f"Detected {len(sfps)} SFPs.")

if len(sfps) > 0:
    print("Sample SFPs:")
    for sfp in sfps[:10]:
        print(sfp)
else:
    print("No SFPs detected.")
