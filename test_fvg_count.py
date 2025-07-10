#!/usr/bin/env python3
"""
Test rápido de conteo FVG
========================
"""

from fetch_data import get_ohlcv_extended
from smc_integration import get_smc_bot_analysis
from app_streamlit import consolidate_smc_metrics

def test_fvg_counting():
    # Obtener datos
    df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
    print(f"Datos: {len(df)} velas")

    # Análisis
    bot_analysis = get_smc_bot_analysis(df)
    print(f"Bot analysis keys: {bot_analysis.keys()}")

    # Revisar FVG directamente
    if 'fvg' in bot_analysis:
        fvg_data = bot_analysis['fvg']
        print(f"FVG data type: {type(fvg_data)}")
        print(f"FVG shape: {fvg_data.shape}")
        print(f"FVG columns: {fvg_data.columns.tolist()}")

        if 'FVG' in fvg_data.columns:
            direct_count = fvg_data['FVG'].notna().sum()
            print(f"Direct FVG count: {direct_count}")

            # Test consolidation
            consolidated = consolidate_smc_metrics(bot_analysis, bot_analysis)
            print(f"Consolidated FVG count: {consolidated.get('fvg_count', 'KEY_MISSING')}")

if __name__ == "__main__":
    test_fvg_counting()
