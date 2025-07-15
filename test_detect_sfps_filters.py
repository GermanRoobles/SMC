# test_detect_sfps_filters.py
"""
Test SFP detection with all filter combinations for 1 month of BTC/USDT 15m data.
Shows how many SFPs are detected for each configuration.
"""
import pandas as pd
from datetime import datetime, timedelta
from fetch_data import get_ohlcv_with_cache
from app_streamlit import detect_sfps

symbol = "BTC/USDT"
timeframe = "15m"
end = pd.Timestamp.utcnow().replace(tzinfo=None)
start = end - timedelta(days=30)

print(f"Loading {symbol} {timeframe} data from {start} to {end}...")
df = get_ohlcv_with_cache(symbol, timeframe, start, end)
print(f"Loaded {len(df)} rows.")

# Dummy signals for filters (empty = disables filter)
market_structures = ["neutral", "bullish", "bearish"]
fvgs = []
obs = []
choch_list = []

configs = [
    {"desc": "No filters (neutral, no proximity, no body, no choch)", "market_structure": "neutral", "require_choch": False, "min_body_ratio": 0.0, "max_zone_distance_pct": 1.0},
    {"desc": "Only market structure (bullish)", "market_structure": "bullish", "require_choch": False, "min_body_ratio": 0.0, "max_zone_distance_pct": 1.0},
    {"desc": "Only market structure (bearish)", "market_structure": "bearish", "require_choch": False, "min_body_ratio": 0.0, "max_zone_distance_pct": 1.0},
    {"desc": "+ Proximity to OB/FVG", "market_structure": "neutral", "require_choch": False, "min_body_ratio": 0.0, "max_zone_distance_pct": 0.005},
    {"desc": "+ Strong body", "market_structure": "neutral", "require_choch": False, "min_body_ratio": 0.4, "max_zone_distance_pct": 1.0},
    {"desc": "+ CHoCH required", "market_structure": "neutral", "require_choch": True, "min_body_ratio": 0.0, "max_zone_distance_pct": 1.0},
    {"desc": "All filters (bullish, proximity, body, choch)", "market_structure": "bullish", "require_choch": True, "min_body_ratio": 0.4, "max_zone_distance_pct": 0.005},
    {"desc": "All filters (bearish, proximity, body, choch)", "market_structure": "bearish", "require_choch": True, "min_body_ratio": 0.4, "max_zone_distance_pct": 0.005},
]

for cfg in configs:
    print(f"\n--- {cfg['desc']} ---")
    sfps = detect_sfps(
        df,
        lookback=2000,
        market_structure=cfg["market_structure"],
        fvgs=fvgs,
        obs=obs,
        choch_list=choch_list,
        min_body_ratio=cfg["min_body_ratio"],
        max_zone_distance_pct=cfg["max_zone_distance_pct"],
        require_choch=cfg["require_choch"]
    )
    print(f"Detected {len(sfps)} SFPs.")
    if len(sfps) > 0:
        print("Sample SFPs:")
        for sfp in sfps[:5]:
            print(sfp)
    else:
        print("No SFPs detected.")
