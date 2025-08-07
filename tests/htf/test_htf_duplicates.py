#!/usr/bin/env python3
"""
Test específico para verificar duplicados en HTF FVGs y Order Blocks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_data import get_ohlcv_with_cache
from smartmoneyconcepts import smc

def test_htf_duplicates():
    """Test para verificar duplicados en HTF indicators"""
    print("🧪 TEST: HTF Duplicates Detection")
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
    
    # Detectar FVGs
    print(f"\n🔍 Detección de FVGs:")
    fvgs = smc.fvg(htf_data)
    print(f"   FVGs totales detectados: {len(fvgs)}")
    
    # Verificar FVGs válidos
    if 'FVG' in fvgs.columns:
        valid_fvgs = fvgs[fvgs['FVG'] != 0]
        valid_fvgs_with_coords = valid_fvgs[
            valid_fvgs['Top'].notna() & 
            valid_fvgs['Bottom'].notna() &
            (valid_fvgs['Top'] != valid_fvgs['Bottom'])
        ]
        print(f"   FVGs válidos con coordenadas: {len(valid_fvgs_with_coords)}")
        
        # Verificar duplicados por coordenadas
        fvg_coords = valid_fvgs_with_coords[['Top', 'Bottom']].drop_duplicates()
        print(f"   FVGs únicos por coordenadas: {len(fvg_coords)}")
        
        # Verificar duplicados por timestamp
        if 'timestamp' in valid_fvgs_with_coords.columns:
            fvg_timestamps = valid_fvgs_with_coords['timestamp'].drop_duplicates()
            print(f"   FVGs únicos por timestamp: {len(fvg_timestamps)}")
        
        # Mostrar algunos FVGs para verificar
        if len(valid_fvgs_with_coords) > 0:
            print("   Ejemplos de FVGs válidos:")
            for i, (idx, row) in enumerate(valid_fvgs_with_coords.head(5).iterrows()):
                fvg_type = "Bullish" if row['FVG'] == 1 else "Bearish"
                print(f"     {i+1}. {fvg_type} FVG: {row['Top']:.2f} - {row['Bottom']:.2f}")
    
    # Detectar Order Blocks
    print(f"\n🔍 Detección de Order Blocks:")
    swing_highs_lows = smc.swing_highs_lows(htf_data)
    orderblocks = smc.ob(htf_data, swing_highs_lows)
    print(f"   Order Blocks totales detectados: {len(orderblocks)}")
    
    # Verificar Order Blocks válidos
    if 'OB' in orderblocks.columns:
        valid_obs = orderblocks[orderblocks['OB'] != 0]
        valid_obs_with_coords = valid_obs[
            valid_obs['Top'].notna() & 
            valid_obs['Bottom'].notna() &
            (valid_obs['Top'] != valid_obs['Bottom'])
        ]
        print(f"   Order Blocks válidos con coordenadas: {len(valid_obs_with_coords)}")
        
        # Verificar duplicados por coordenadas
        ob_coords = valid_obs_with_coords[['Top', 'Bottom']].drop_duplicates()
        print(f"   Order Blocks únicos por coordenadas: {len(ob_coords)}")
        
        # Verificar duplicados por timestamp
        if 'timestamp' in valid_obs_with_coords.columns:
            ob_timestamps = valid_obs_with_coords['timestamp'].drop_duplicates()
            print(f"   Order Blocks únicos por timestamp: {len(ob_timestamps)}")
        
        # Mostrar algunos Order Blocks para verificar
        if len(valid_obs_with_coords) > 0:
            print("   Ejemplos de Order Blocks válidos:")
            for i, (idx, row) in enumerate(valid_obs_with_coords.head(5).iterrows()):
                ob_type = "Bullish" if row['OB'] == 1 else "Bearish"
                print(f"     {i+1}. {ob_type} OB: {row['Top']:.2f} - {row['Bottom']:.2f}")
    
    # Verificar si hay demasiados indicadores para el timeframe
    print(f"\n🔍 Análisis de densidad:")
    total_weeks = len(htf_data)
    print(f"   Total de semanas en datos: {total_weeks}")
    
    if len(valid_fvgs_with_coords) > 0:
        fvg_density = len(valid_fvgs_with_coords) / total_weeks
        print(f"   Densidad de FVGs: {fvg_density:.2f} FVGs por semana")
        if fvg_density > 2:
            print(f"   ⚠️ ALTA DENSIDAD: {fvg_density:.2f} FVGs por semana es sospechoso")
    
    if len(valid_obs_with_coords) > 0:
        ob_density = len(valid_obs_with_coords) / total_weeks
        print(f"   Densidad de Order Blocks: {ob_density:.2f} OBs por semana")
        if ob_density > 2:
            print(f"   ⚠️ ALTA DENSIDAD: {ob_density:.2f} OBs por semana es sospechoso")
    
    # Comparar con timeframe más pequeño
    print(f"\n🔍 Comparación con timeframe 15m:")
    ltf_data = get_ohlcv_with_cache(
        symbol="BTC/USDT",
        timeframe="15m",
        start=end_date - timedelta(days=7),
        end=end_date,
        provider_hint="yahoo"
    )
    
    if not ltf_data.empty:
        ltf_fvgs = smc.fvg(ltf_data)
        ltf_swing_highs_lows = smc.swing_highs_lows(ltf_data)
        ltf_obs = smc.ob(ltf_data, ltf_swing_highs_lows)
        
        # Verificar FVGs válidos en 15m
        if 'FVG' in ltf_fvgs.columns:
            valid_ltf_fvgs = ltf_fvgs[ltf_fvgs['FVG'] != 0]
            valid_ltf_fvgs_with_coords = valid_ltf_fvgs[
                valid_ltf_fvgs['Top'].notna() & 
                valid_ltf_fvgs['Bottom'].notna() &
                (valid_ltf_fvgs['Top'] != valid_ltf_fvgs['Bottom'])
            ]
            print(f"   15m - FVGs válidos: {len(valid_ltf_fvgs_with_coords)}")
            
            # Calcular densidad para 15m
            total_15m_periods = len(ltf_data)
            ltf_fvg_density = len(valid_ltf_fvgs_with_coords) / total_15m_periods
            print(f"   15m - Densidad de FVGs: {ltf_fvg_density:.4f} FVGs por período 15m")
    
    print(f"\n🎯 CONCLUSIÓN:")
    print(f"   Si hay más de 2-3 FVGs/OBs por semana en HTF, es sospechoso.")
    print(f"   Los HTF indicators deberían ser más selectivos que los LTF.")

if __name__ == "__main__":
    test_htf_duplicates()
