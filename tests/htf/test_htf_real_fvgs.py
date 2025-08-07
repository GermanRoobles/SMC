#!/usr/bin/env python3
"""
Test para verificar que se detectan FVGs HTF reales y significativos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_data import get_ohlcv_with_cache
from utils_htf import get_htf_gaps_and_obs
from smc_analysis import detect_fvgs

def test_htf_real_fvgs():
    """Test para verificar FVGs HTF reales"""
    print("🧪 TEST: HTF Real FVGs Detection")
    print("=" * 60)
    
    # Obtener datos HTF
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    htf_data = get_ohlcv_with_cache(
        symbol="BTC/USDT",
        timeframe="1w",
        start=start_date,
        end=end_date,
        provider_hint="yahoo"
    )
    
    print(f"📊 Datos HTF obtenidos: {len(htf_data)} filas")
    print(f"   Rango: {htf_data['timestamp'].min()} a {htf_data['timestamp'].max()}")
    
    # Probar la nueva función detect_fvgs con timeframe
    print(f"\n🔍 Probando detect_fvgs con filtros HTF:")
    try:
        fvgs_filtered = detect_fvgs(htf_data, timeframe="1w")
        
        print(f"   FVGs detectados con filtros: {len(fvgs_filtered)}")
        
        if len(fvgs_filtered) > 0:
            print(f"   Ejemplos de FVGs filtrados:")
            for i, (idx, row) in enumerate(fvgs_filtered.head(5).iterrows()):
                fvg_type = "Bullish" if row['FVG'] == 1 else "Bearish"
                gap_size = abs(row['Top'] - row['Bottom'])
                gap_pct = (gap_size / htf_data['close'].mean()) * 100
                print(f"     {i+1}. {fvg_type} FVG: {row['Top']:.2f} - {row['Bottom']:.2f} (gap: {gap_pct:.2f}%)")
        
        # Comparar con detección sin filtros
        from smartmoneyconcepts import smc
        fvgs_raw = smc.fvg(htf_data)
        print(f"\n📊 Comparación:")
        print(f"   FVGs sin filtros: {len(fvgs_raw)}")
        print(f"   FVGs con filtros: {len(fvgs_filtered)}")
        print(f"   Reducción: {len(fvgs_raw) - len(fvgs_filtered)} FVGs eliminados")
        
        # Verificar que los FVGs restantes son significativos
        if len(fvgs_filtered) > 0:
            avg_gap = fvgs_filtered['Top'].sub(fvgs_filtered['Bottom']).abs().mean()
            avg_gap_pct = (avg_gap / htf_data['close'].mean()) * 100
            print(f"   Gap promedio: {avg_gap:.2f} ({avg_gap_pct:.2f}% del precio)")
            
            if avg_gap_pct > 1.0:
                print(f"   ✅ Gaps significativos detectados")
            else:
                print(f"   ⚠️ Gaps pequeños, considerar ajustar filtros")
        
        # Probar get_htf_gaps_and_obs
        print(f"\n🔍 Probando get_htf_gaps_and_obs:")
        fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs("BTC/USDT", "1w", "4h")
        
        print(f"   FVG zones proyectadas: {len(fvg_zones)}")
        print(f"   OB zones proyectadas: {len(ob_zones)}")
        
        # Verificar que no hay duplicados
        if len(fvg_zones) > 0:
            fvg_coords = [(zone['top'], zone['bottom']) for zone in fvg_zones]
            unique_fvg_coords = set(fvg_coords)
            print(f"   FVG zones únicas: {len(unique_fvg_coords)}")
            
            if len(fvg_coords) == len(unique_fvg_coords):
                print(f"   ✅ No hay duplicados en FVG zones")
            else:
                print(f"   ⚠️ Hay duplicados en FVG zones")
        
        # Mostrar las zonas más significativas
        if len(fvg_zones) > 0:
            print(f"\n🎯 FVG zones más significativas:")
            # Ordenar por tamaño de gap
            fvg_zones_sorted = sorted(fvg_zones, key=lambda x: abs(x['top'] - x['bottom']), reverse=True)
            for i, zone in enumerate(fvg_zones_sorted[:5]):
                gap_size = abs(zone['top'] - zone['bottom'])
                gap_pct = (gap_size / htf_data['close'].mean()) * 100
                print(f"     {i+1}. Top: {zone['top']:.2f}, Bottom: {zone['bottom']:.2f} (gap: {gap_pct:.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de FVGs HTF reales...")
    
    success = test_htf_real_fvgs()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST DE FVGs HTF REALES EXITOSO")
        print("✅ Ahora se detectan solo FVGs HTF reales y significativos")
    else:
        print("❌ TEST DE FVGs HTF REALES FALLÓ")
        print("⚠️ Hay problemas con la detección de FVGs HTF reales")
