#!/usr/bin/env python3
"""
Test rápido para verificar el conteo correcto
"""

import pandas as pd
from fetch_data import get_ohlcv_extended
from smc_integration import get_smc_bot_analysis, display_bot_metrics
import streamlit as st

def test_counting():
    """Test del conteo correcto"""
    print("🔍 Probando conteo correcto...")

    # Obtener datos
    df = get_ohlcv_extended("BTCUSDT", "15m", days=1)
    if df is None or df.empty:
        print("❌ No se pudieron obtener datos")
        return

    print(f"📊 Dataset: {len(df)} velas")

    # Obtener análisis
    analysis = get_smc_bot_analysis(df)

    # Verificar conteos manuales
    print("\n🔍 Conteos correctos:")

    if 'fvg' in analysis and analysis['fvg'] is not None:
        fvg_data = analysis['fvg']
        if not fvg_data.empty and 'FVG' in fvg_data.columns:
            fvg_count = fvg_data['FVG'].notna().sum()
            print(f"  ✅ FVGs: {fvg_count} (era {len(fvg_data)} antes)")

    if 'orderblocks' in analysis and analysis['orderblocks'] is not None:
        ob_data = analysis['orderblocks']
        if not ob_data.empty and 'OB' in ob_data.columns:
            ob_count = ob_data['OB'].notna().sum()
            print(f"  ✅ Order Blocks: {ob_count} (era {len(ob_data)} antes)")

    if 'bos_choch' in analysis and analysis['bos_choch'] is not None:
        bos_data = analysis['bos_choch']
        if not bos_data.empty:
            bos_count = 0
            choch_count = 0
            if 'BOS' in bos_data.columns:
                bos_count = bos_data['BOS'].notna().sum()
            if 'CHOCH' in bos_data.columns:
                choch_count = bos_data['CHOCH'].notna().sum()
            total = bos_count + choch_count
            print(f"  ✅ BOS/CHoCH: {total} (BOS: {bos_count}, CHoCH: {choch_count}) (era {len(bos_data)} antes)")

    if 'liquidity' in analysis and analysis['liquidity'] is not None:
        liq_data = analysis['liquidity']
        if not liq_data.empty and 'Liquidity' in liq_data.columns:
            liq_count = liq_data['Liquidity'].notna().sum()
            print(f"  ✅ Liquidity: {liq_count} (era {len(liq_data)} antes)")

    if 'swing_highs_lows' in analysis and analysis['swing_highs_lows'] is not None:
        swing_data = analysis['swing_highs_lows']
        if not swing_data.empty and 'HighLow' in swing_data.columns:
            swing_count = swing_data['HighLow'].notna().sum()
            print(f"  ✅ Swings: {swing_count} (era {len(swing_data)} antes)")

if __name__ == "__main__":
    test_counting()
