#!/usr/bin/env python3
"""
Debug específico para HTF Indicators
Investiga por qué los FVGs y Order Blocks tienen valores NaN
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

def debug_htf_indicators():
    """Debug completo de HTF indicators"""
    print("🔍 DEBUG: HTF Indicators (FVGs y Order Blocks)")
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
    print(f"   Precio actual: {htf_data['close'].iloc[-1]:.2f}")
    
    # Verificar datos
    print(f"\n🔍 Verificación de datos:")
    print(f"   Columnas: {list(htf_data.columns)}")
    print(f"   Tipos de datos:")
    for col in htf_data.columns:
        print(f"     {col}: {htf_data[col].dtype}")
    
    # Verificar valores nulos
    print(f"\n🔍 Valores nulos:")
    for col in ['open', 'high', 'low', 'close', 'volume']:
        null_count = htf_data[col].isnull().sum()
        print(f"   {col}: {null_count} valores nulos")
    
    # Verificar rangos de precios
    print(f"\n🔍 Rangos de precios:")
    for col in ['open', 'high', 'low', 'close']:
        min_val = htf_data[col].min()
        max_val = htf_data[col].max()
        print(f"   {col}: {min_val:.2f} - {max_val:.2f}")
    
    # Verificar que no hay valores infinitos
    print(f"\n🔍 Valores infinitos:")
    for col in ['open', 'high', 'low', 'close']:
        inf_count = np.isinf(htf_data[col]).sum()
        print(f"   {col}: {inf_count} valores infinitos")
    
    # Detectar FVGs
    print(f"\n🔍 Detección de FVGs:")
    fvgs = smc.fvg(htf_data)
    print(f"   FVGs detectados: {len(fvgs)}")
    print(f"   Columnas FVG: {list(fvgs.columns)}")
    
    # Verificar FVGs con valores válidos
    if 'FVG' in fvgs.columns:
        valid_fvgs = fvgs[fvgs['FVG'] != 0]
        print(f"   FVGs válidos (no cero): {len(valid_fvgs)}")
        
        # Verificar FVGs con Top y Bottom válidos
        valid_fvgs_with_coords = valid_fvgs[
            valid_fvgs['Top'].notna() & 
            valid_fvgs['Bottom'].notna() &
            (valid_fvgs['Top'] != valid_fvgs['Bottom'])
        ]
        print(f"   FVGs con coordenadas válidas: {len(valid_fvgs_with_coords)}")
        
        if len(valid_fvgs_with_coords) > 0:
            print("   Ejemplos de FVGs válidos:")
            for i, (idx, row) in enumerate(valid_fvgs_with_coords.head(3).iterrows()):
                fvg_type = "Bullish" if row['FVG'] == 1 else "Bearish"
                print(f"     {i+1}. {fvg_type} FVG: {row['Top']:.2f} - {row['Bottom']:.2f}")
        else:
            print("   ⚠️ No hay FVGs con coordenadas válidas")
    
    # Detectar Order Blocks
    print(f"\n🔍 Detección de Order Blocks:")
    swing_highs_lows = smc.swing_highs_lows(htf_data)
    orderblocks = smc.ob(htf_data, swing_highs_lows)
    print(f"   Order Blocks detectados: {len(orderblocks)}")
    print(f"   Columnas Order Blocks: {list(orderblocks.columns)}")
    
    # Verificar Order Blocks con valores válidos
    if 'OB' in orderblocks.columns:
        valid_obs = orderblocks[orderblocks['OB'] != 0]
        print(f"   Order Blocks válidos (no cero): {len(valid_obs)}")
        
        # Verificar Order Blocks con Top y Bottom válidos
        valid_obs_with_coords = valid_obs[
            valid_obs['Top'].notna() & 
            valid_obs['Bottom'].notna() &
            (valid_obs['Top'] != valid_obs['Bottom'])
        ]
        print(f"   Order Blocks con coordenadas válidas: {len(valid_obs_with_coords)}")
        
        if len(valid_obs_with_coords) > 0:
            print("   Ejemplos de Order Blocks válidos:")
            for i, (idx, row) in enumerate(valid_obs_with_coords.head(3).iterrows()):
                ob_type = "Bullish" if row['OB'] == 1 else "Bearish"
                print(f"     {i+1}. {ob_type} OB: {row['Top']:.2f} - {row['Bottom']:.2f}")
        else:
            print("   ⚠️ No hay Order Blocks con coordenadas válidas")
    
    # Verificar swing highs/lows
    print(f"\n🔍 Swing Highs/Lows:")
    print(f"   Swing Highs/Lows detectados: {len(swing_highs_lows)}")
    if not swing_highs_lows.empty:
        print(f"   Columnas Swing: {list(swing_highs_lows.columns)}")
        
        # Verificar swing highs/lows válidos
        valid_swings = swing_highs_lows[
            swing_highs_lows['Level'].notna()
        ]
        print(f"   Swing Highs/Lows válidos: {len(valid_swings)}")
    
    # Comparar con timeframe más pequeño
    print(f"\n🔍 Comparación con timeframe 15m:")
    ltf_data = get_ohlcv_with_cache(
        symbol="BTC/USDT",
        timeframe="15m",
        start=end_date - timedelta(days=7),  # Solo 7 días para 15m
        end=end_date,
        provider_hint="yahoo"
    )
    
    if not ltf_data.empty:
        ltf_fvgs = smc.fvg(ltf_data)
        ltf_swing_highs_lows = smc.swing_highs_lows(ltf_data)
        ltf_obs = smc.ob(ltf_data, ltf_swing_highs_lows)
        
        print(f"   15m - FVGs: {len(ltf_fvgs)}")
        print(f"   15m - Order Blocks: {len(ltf_obs)}")
        print(f"   15m - Swing Highs/Lows: {len(ltf_swing_highs_lows)}")
        
        # Verificar FVGs válidos en 15m
        if 'FVG' in ltf_fvgs.columns:
            valid_ltf_fvgs = ltf_fvgs[ltf_fvgs['FVG'] != 0]
            valid_ltf_fvgs_with_coords = valid_ltf_fvgs[
                valid_ltf_fvgs['Top'].notna() & 
                valid_ltf_fvgs['Bottom'].notna() &
                (valid_ltf_fvgs['Top'] != valid_ltf_fvgs['Bottom'])
            ]
            print(f"   15m - FVGs válidos: {len(valid_ltf_fvgs_with_coords)}")
    
    print(f"\n🎯 CONCLUSIÓN:")
    print(f"   El problema parece ser que los datos HTF (1w) tienen muy pocos puntos")
    print(f"   para detectar FVGs y Order Blocks válidos.")
    print(f"   Los timeframes más pequeños (15m, 1h) deberían funcionar mejor.")

if __name__ == "__main__":
    debug_htf_indicators()
