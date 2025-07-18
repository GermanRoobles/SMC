#!/usr/bin/env python3
"""
Test para verificar estructura de datos SMC
"""

import pandas as pd
from fetch_data import get_ohlcv_extended
import smc_analysis
from smartmoneyconcepts import smc

def test_smc_data_structure():
    """Verificar estructura de datos SMC"""
    print("🔍 Obteniendo datos de prueba...")
    df = get_ohlcv_extended("BTCUSDT", "15m", days=1)

    if df is None or df.empty:
        print("❌ No se pudieron obtener datos")
        return

    print(f"📊 Dataset: {len(df)} velas")
    print(f"📅 Rango: {df.index[0]} a {df.index[-1]}")

    # Analizar cada componente
    print("\n🔍 Analizando componentes SMC...")

    # Swing highs/lows primero
    swing_highs_lows = smc.swing_highs_lows(df, swing_length=10)
    print(f"\n📊 Swing Highs/Lows:")
    print(f"  - Tipo: {type(swing_highs_lows)}")
    print(f"  - Shape: {swing_highs_lows.shape if hasattr(swing_highs_lows, 'shape') else 'N/A'}")
    print(f"  - Columnas: {list(swing_highs_lows.columns) if hasattr(swing_highs_lows, 'columns') else 'N/A'}")

    if hasattr(swing_highs_lows, 'columns') and 'HighLow' in swing_highs_lows.columns:
        valid_swings = swing_highs_lows['HighLow'].notna().sum()
        print(f"  - Swings válidos: {valid_swings}")
        print(f"  - Primeros 5 valores:")
        print(f"    {swing_highs_lows['HighLow'].dropna().head()}")

    # FVG
    fvg_data = smc.fvg(df)
    print(f"\n📊 FVG (Fair Value Gaps):")
    print(f"  - Tipo: {type(fvg_data)}")
    print(f"  - Shape: {fvg_data.shape if hasattr(fvg_data, 'shape') else 'N/A'}")
    print(f"  - Columnas: {list(fvg_data.columns) if hasattr(fvg_data, 'columns') else 'N/A'}")

    if hasattr(fvg_data, 'columns'):
        # Buscar columnas relevantes para FVG
        fvg_columns = [col for col in fvg_data.columns if 'FVG' in col.upper()]
        print(f"  - Columnas FVG: {fvg_columns}")

        if fvg_columns:
            for col in fvg_columns:
                valid_fvgs = fvg_data[col].notna().sum()
                print(f"    - {col}: {valid_fvgs} válidos")

    # Order Blocks
    ob_data = smc.ob(df, swing_highs_lows)
    print(f"\n📊 Order Blocks:")
    print(f"  - Tipo: {type(ob_data)}")
    print(f"  - Shape: {ob_data.shape if hasattr(ob_data, 'shape') else 'N/A'}")
    print(f"  - Columnas: {list(ob_data.columns) if hasattr(ob_data, 'columns') else 'N/A'}")

    if hasattr(ob_data, 'columns'):
        ob_columns = [col for col in ob_data.columns if 'OB' in col.upper()]
        print(f"  - Columnas OB: {ob_columns}")

        if ob_columns:
            for col in ob_columns:
                valid_obs = ob_data[col].notna().sum()
                print(f"    - {col}: {valid_obs} válidos")

    # BOS/CHoCH
    bos_choch_data = smc.bos_choch(df, swing_highs_lows)
    print(f"\n📊 BOS/CHoCH:")
    print(f"  - Tipo: {type(bos_choch_data)}")
    print(f"  - Shape: {bos_choch_data.shape if hasattr(bos_choch_data, 'shape') else 'N/A'}")
    print(f"  - Columnas: {list(bos_choch_data.columns) if hasattr(bos_choch_data, 'columns') else 'N/A'}")

    if hasattr(bos_choch_data, 'columns'):
        bos_columns = [col for col in bos_choch_data.columns if any(x in col.upper() for x in ['BOS', 'CHOCH'])]
        print(f"  - Columnas BOS/CHoCH: {bos_columns}")

        if bos_columns:
            for col in bos_columns:
                valid_bos = bos_choch_data[col].notna().sum()
                print(f"    - {col}: {valid_bos} válidos")

    # Liquidity
    liquidity_data = smc.liquidity(df, swing_highs_lows)
    print(f"\n📊 Liquidity:")
    print(f"  - Tipo: {type(liquidity_data)}")
    print(f"  - Shape: {liquidity_data.shape if hasattr(liquidity_data, 'shape') else 'N/A'}")
    print(f"  - Columnas: {list(liquidity_data.columns) if hasattr(liquidity_data, 'columns') else 'N/A'}")

    if hasattr(liquidity_data, 'columns'):
        liq_columns = [col for col in liquidity_data.columns if 'LIQ' in col.upper()]
        print(f"  - Columnas Liquidity: {liq_columns}")

        if liq_columns:
            for col in liq_columns:
                valid_liq = liquidity_data[col].notna().sum()
                print(f"    - {col}: {valid_liq} válidos")

if __name__ == "__main__":
    test_smc_data_structure()
