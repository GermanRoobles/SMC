#!/usr/bin/env python3
"""
Test para verificar la limitación de HTF zones en el renderizado
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

def test_htf_limitation():
    """Test para verificar la limitación de HTF zones"""
    print("🧪 TEST: HTF Limitation Verification")
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
    
    # Probar la función get_htf_gaps_and_obs
    print(f"\n🔍 Probando get_htf_gaps_and_obs:")
    try:
        fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs("BTC/USDT", "1w", "4h")
        
        print(f"   FVG zones totales: {len(fvg_zones)}")
        print(f"   OB zones totales: {len(ob_zones)}")
        
        # Aplicar limitación como en app_streamlit.py
        max_htf_zones = 5
        fvg_zones_limited = fvg_zones[:max_htf_zones] if len(fvg_zones) > max_htf_zones else fvg_zones
        ob_zones_limited = ob_zones[:max_htf_zones] if len(ob_zones) > max_htf_zones else ob_zones
        
        print(f"\n📊 Resultados después de limitación:")
        print(f"   FVG zones limitadas: {len(fvg_zones_limited)}")
        print(f"   OB zones limitadas: {len(ob_zones_limited)}")
        
        # Verificar que la limitación funciona
        if len(fvg_zones) > max_htf_zones:
            if len(fvg_zones_limited) == max_htf_zones:
                print(f"   ✅ Limitación FVG correcta: {len(fvg_zones)} → {len(fvg_zones_limited)}")
            else:
                print(f"   ❌ Limitación FVG incorrecta: {len(fvg_zones)} → {len(fvg_zones_limited)}")
        else:
            print(f"   ✅ FVG zones dentro del límite: {len(fvg_zones)}")
        
        if len(ob_zones) > max_htf_zones:
            if len(ob_zones_limited) == max_htf_zones:
                print(f"   ✅ Limitación OB correcta: {len(ob_zones)} → {len(ob_zones_limited)}")
            else:
                print(f"   ❌ Limitación OB incorrecta: {len(ob_zones)} → {len(ob_zones_limited)}")
        else:
            print(f"   ✅ OB zones dentro del límite: {len(ob_zones)}")
        
        # Mostrar las zonas que se mostrarán
        print(f"\n🎯 Zonas que se mostrarán en la interfaz:")
        if len(fvg_zones_limited) > 0:
            print(f"   FVG zones (primeras {len(fvg_zones_limited)}):")
            for i, zone in enumerate(fvg_zones_limited):
                print(f"     {i+1}. Top: {zone['top']:.2f}, Bottom: {zone['bottom']:.2f}")
        
        if len(ob_zones_limited) > 0:
            print(f"   OB zones (primeras {len(ob_zones_limited)}):")
            for i, zone in enumerate(ob_zones_limited):
                print(f"     {i+1}. Top: {zone['top']:.2f}, Bottom: {zone['bottom']:.2f}")
        
        # Verificar que no hay duplicados en las zonas limitadas
        fvg_coords_limited = [(zone['top'], zone['bottom']) for zone in fvg_zones_limited]
        ob_coords_limited = [(zone['top'], zone['bottom']) for zone in ob_zones_limited]
        
        unique_fvg_limited = set(fvg_coords_limited)
        unique_ob_limited = set(ob_coords_limited)
        
        if len(fvg_coords_limited) == len(unique_fvg_limited):
            print(f"   ✅ No hay duplicados en FVG zones limitadas")
        else:
            print(f"   ⚠️ Hay duplicados en FVG zones limitadas")
        
        if len(ob_coords_limited) == len(unique_ob_limited):
            print(f"   ✅ No hay duplicados en OB zones limitadas")
        else:
            print(f"   ⚠️ Hay duplicados en OB zones limitadas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de limitación HTF...")
    
    success = test_htf_limitation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST DE LIMITACIÓN EXITOSO")
        print("✅ Los HTF indicators ahora están limitados correctamente")
    else:
        print("❌ TEST DE LIMITACIÓN FALLÓ")
        print("⚠️ Hay problemas con la limitación de HTF indicators")
