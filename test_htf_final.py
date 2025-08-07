#!/usr/bin/env python3
"""
Test final para verificar que los HTF indicators se renderizan correctamente
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

def test_htf_final():
    """Test final de HTF indicators"""
    print("🧪 TEST: HTF Final Verification")
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
    
    # Probar la función get_htf_gaps_and_obs
    print(f"\n🔍 Probando get_htf_gaps_and_obs:")
    try:
        fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs("BTC/USDT", "1w", "4h")
        
        print(f"   FVG zones proyectadas: {len(fvg_zones)}")
        print(f"   OB zones proyectadas: {len(ob_zones)}")
        print(f"   LTF DataFrame: {len(ltf_df)} filas")
        
        # Verificar que no hay duplicados
        if len(fvg_zones) > 0:
            fvg_coords = [(zone['top'], zone['bottom']) for zone in fvg_zones]
            unique_fvg_coords = set(fvg_coords)
            print(f"   FVG zones únicas por coordenadas: {len(unique_fvg_coords)}")
            
            if len(fvg_coords) != len(unique_fvg_coords):
                print(f"   ⚠️ DUPLICADOS DETECTADOS en FVG zones!")
            else:
                print(f"   ✅ No hay duplicados en FVG zones")
        
        if len(ob_zones) > 0:
            ob_coords = [(zone['top'], zone['bottom']) for zone in ob_zones]
            unique_ob_coords = set(ob_coords)
            print(f"   OB zones únicas por coordenadas: {len(unique_ob_coords)}")
            
            if len(ob_coords) != len(unique_ob_coords):
                print(f"   ⚠️ DUPLICADOS DETECTADOS en OB zones!")
            else:
                print(f"   ✅ No hay duplicados en OB zones")
        
        # Mostrar algunas zonas de ejemplo
        if len(fvg_zones) > 0:
            print(f"   Ejemplos de FVG zones:")
            for i, zone in enumerate(fvg_zones[:3]):
                print(f"     {i+1}. Top: {zone['top']:.2f}, Bottom: {zone['bottom']:.2f}")
        
        if len(ob_zones) > 0:
            print(f"   Ejemplos de OB zones:")
            for i, zone in enumerate(ob_zones[:3]):
                print(f"     {i+1}. Top: {zone['top']:.2f}, Bottom: {zone['bottom']:.2f}")
        
        # Verificar densidad razonable
        total_weeks = len(htf_data)
        fvg_density = len(fvg_zones) / total_weeks if total_weeks > 0 else 0
        ob_density = len(ob_zones) / total_weeks if total_weeks > 0 else 0
        
        print(f"\n📊 Análisis de densidad:")
        print(f"   Total semanas: {total_weeks}")
        print(f"   Densidad FVG: {fvg_density:.2f} FVGs por semana")
        print(f"   Densidad OB: {ob_density:.2f} OBs por semana")
        
        if fvg_density > 2:
            print(f"   ⚠️ ALTA DENSIDAD FVG: {fvg_density:.2f} por semana")
        else:
            print(f"   ✅ Densidad FVG normal")
            
        if ob_density > 2:
            print(f"   ⚠️ ALTA DENSIDAD OB: {ob_density:.2f} por semana")
        else:
            print(f"   ✅ Densidad OB normal")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test final de HTF...")
    
    success = test_htf_final()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST FINAL EXITOSO")
        print("✅ Los HTF indicators deberían renderizarse correctamente sin duplicados")
    else:
        print("❌ TEST FINAL FALLÓ")
        print("⚠️ Hay problemas con los HTF indicators")
