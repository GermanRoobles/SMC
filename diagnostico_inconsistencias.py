#!/usr/bin/env python3
"""
Diagnóstico de Inconsistencias SMC
=================================

Script para analizar las inconsistencias detectadas en el dashboard SMC.
"""

import pandas as pd
import numpy as np
from fetch_data import get_ohlcv_extended
from smc_integration import get_smc_bot_analysis
from app_streamlit import consolidate_smc_metrics

def analyze_smc_data_consistency():
    """Analizar consistencia de datos SMC"""
    print("🔍 === DIAGNÓSTICO DE INCONSISTENCIAS SMC ===")
    print()

    # 1. Obtener datos reales
    print("📊 1. Obteniendo datos BTC/USDT 15m...")
    try:
        df = get_ohlcv_extended("BTC/USDT", "15m", days=5)
        print(f"   ✅ Datos obtenidos: {len(df)} velas")
        print(f"   📅 Desde: {df.index[0]} hasta: {df.index[-1]}")
    except Exception as e:
        print(f"   ❌ Error obteniendo datos: {e}")
        return

    # 2. Obtener análisis SMC
    print("\n🔍 2. Ejecutando análisis SMC...")
    try:
        bot_analysis = get_smc_bot_analysis(df)
        print(f"   ✅ Análisis SMC completado")
    except Exception as e:
        print(f"   ❌ Error en análisis SMC: {e}")
        return

    # 3. Analizar componentes individuales
    print("\n📊 3. Analizando componentes SMC detalladamente...")

    # Analizar FVG
    if 'fvg' in bot_analysis:
        fvg_data = bot_analysis['fvg']
        print(f"\n🔹 FVG Analysis:")
        print(f"   • DataFrame shape: {fvg_data.shape}")
        print(f"   • Columns: {list(fvg_data.columns)}")
        if 'FVG' in fvg_data.columns:
            fvg_count = fvg_data['FVG'].notna().sum()
            fvg_total = len(fvg_data)
            fvg_percentage = (fvg_count / fvg_total) * 100
            print(f"   • Valid FVGs: {fvg_count} de {fvg_total} ({fvg_percentage:.1f}%)")
            print(f"   • Valores únicos: {fvg_data['FVG'].dropna().unique()[:10]}")
        else:
            print(f"   ⚠️ No hay columna 'FVG'")

    # Analizar Order Blocks
    if 'orderblocks' in bot_analysis:
        ob_data = bot_analysis['orderblocks']
        print(f"\n🔸 Order Blocks Analysis:")
        print(f"   • DataFrame shape: {ob_data.shape}")
        print(f"   • Columns: {list(ob_data.columns)}")
        if hasattr(ob_data, 'OB'):
            ob_count = ob_data['OB'].notna().sum()
            print(f"   • Valid OBs: {ob_count}")
            print(f"   • Valores únicos: {ob_data['OB'].dropna().unique()}")
        else:
            print(f"   ⚠️ No hay columna 'OB'")

    # Analizar BOS/CHoCH
    if 'bos_choch' in bot_analysis:
        bos_data = bot_analysis['bos_choch']
        print(f"\n🔹 BOS/CHoCH Analysis:")
        print(f"   • DataFrame shape: {bos_data.shape}")
        print(f"   • Columns: {list(bos_data.columns)}")

        bos_count = 0
        choch_count = 0

        if 'BOS' in bos_data.columns:
            bos_count = bos_data['BOS'].notna().sum()
            print(f"   • Valid BOS: {bos_count}")
            if bos_count > 0:
                print(f"   • BOS valores: {bos_data['BOS'].dropna().unique()}")

        if 'CHOCH' in bos_data.columns:
            choch_count = bos_data['CHOCH'].notna().sum()
            print(f"   • Valid CHOCH: {choch_count}")
            if choch_count > 0:
                print(f"   • CHOCH valores: {bos_data['CHOCH'].dropna().unique()}")

        total_bos_choch = bos_count + choch_count
        print(f"   • Total BOS + CHOCH: {total_bos_choch}")

    # Analizar Liquidity
    if 'liquidity' in bot_analysis:
        liq_data = bot_analysis['liquidity']
        print(f"\n🔸 Liquidity Analysis:")
        print(f"   • DataFrame shape: {liq_data.shape}")
        print(f"   • Columns: {list(liq_data.columns)}")
        if hasattr(liq_data, 'Liquidity'):
            liq_count = liq_data['Liquidity'].notna().sum()
            print(f"   • Valid Liquidity: {liq_count}")
            if liq_count > 0:
                print(f"   • Liquidity valores: {liq_data['Liquidity'].dropna().unique()}")
        else:
            print(f"   ⚠️ No hay columna 'Liquidity'")

    # 4. Comparar métodos de conteo
    print("\n⚖️ 4. Comparando métodos de conteo...")

    # Usar consolidate_smc_metrics (método usado en dashboard principal)
    mock_signals = bot_analysis  # Usar bot_analysis como signals
    consolidated = consolidate_smc_metrics(mock_signals, bot_analysis)

    print(f"\n📊 Métricas Consolidadas (Dashboard Principal):")
    for key, value in consolidated.items():
        print(f"   • {key}: {value}")

    # Simular display_bot_metrics (método usado en bot sidebar)
    print(f"\n🤖 Métricas Bot Sidebar (simuladas):")

    # FVG count
    fvg_count_sidebar = 0
    if 'fvg' in bot_analysis:
        fvg_data = bot_analysis['fvg']
        if fvg_data is not None and not fvg_data.empty and 'FVG' in fvg_data.columns:
            fvg_count_sidebar = fvg_data['FVG'].notna().sum()
    print(f"   • FVGs: {fvg_count_sidebar}")

    # BOS/CHoCH count (método sidebar)
    choch_count_sidebar = 0
    if 'bos_choch' in bot_analysis:
        choch_data = bot_analysis['bos_choch']
        if choch_data is not None and not choch_data.empty:
            bos_count = 0
            choch_count = 0
            if 'BOS' in choch_data.columns:
                bos_count = choch_data['BOS'].notna().sum()
            if 'CHOCH' in choch_data.columns:
                choch_count = choch_data['CHOCH'].notna().sum()
            choch_count_sidebar = bos_count + choch_count
    print(f"   • BOS/CHoCH: {choch_count_sidebar}")

    # 5. Identificar discrepancias
    print("\n🔍 5. Análisis de Discrepancias:")

    fvg_diff = abs(consolidated.get('total_fvg', 0) - fvg_count_sidebar)
    bos_diff = abs(consolidated.get('bos_choch_count', 0) - choch_count_sidebar)

    if fvg_diff > 0:
        print(f"   ⚠️ FVG Discrepancia: {fvg_diff} ({consolidated.get('total_fvg', 0)} vs {fvg_count_sidebar})")
    else:
        print(f"   ✅ FVG Consistente: {fvg_count_sidebar}")

    if bos_diff > 0:
        print(f"   ⚠️ BOS/CHoCH Discrepancia: {bos_diff} ({consolidated.get('bos_choch_count', 0)} vs {choch_count_sidebar})")
    else:
        print(f"   ✅ BOS/CHoCH Consistente: {choch_count_sidebar}")

    # 6. Análisis de razonabilidad de números
    print("\n📈 6. Análisis de Razonabilidad:")

    total_candles = len(df)
    fvg_ratio = (fvg_count_sidebar / total_candles) * 100

    print(f"   • Total velas: {total_candles}")
    print(f"   • FVGs: {fvg_count_sidebar} ({fvg_ratio:.1f}% de las velas)")

    if fvg_ratio > 25:
        print(f"   ⚠️ FVG ratio muy alto (>{fvg_ratio:.1f}%) - posible over-detection")
    elif fvg_ratio < 5:
        print(f"   ⚠️ FVG ratio muy bajo (<{fvg_ratio:.1f}%) - posible under-detection")
    else:
        print(f"   ✅ FVG ratio razonable ({fvg_ratio:.1f}%)")

    ob_ratio = (consolidated.get('order_blocks_count', 0) / total_candles) * 100
    print(f"   • Order Blocks: {consolidated.get('order_blocks_count', 0)} ({ob_ratio:.1f}% de las velas)")

    if ob_ratio < 1:
        print(f"   ⚠️ Order Block ratio muy bajo (<{ob_ratio:.1f}%) - posible under-detection")
    else:
        print(f"   ✅ Order Block ratio razonable ({ob_ratio:.1f}%)")

if __name__ == "__main__":
    try:
        analyze_smc_data_consistency()
        print("\n🎯 Diagnóstico completado!")

    except Exception as e:
        print(f"\n❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
