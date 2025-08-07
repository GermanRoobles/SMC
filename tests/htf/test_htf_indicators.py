#!/usr/bin/env python3
"""
Test específico para HTF Indicators (FVGs y Order Blocks)
Verifica que los indicadores de High Timeframes se muestren correctamente
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_data import get_ohlcv_with_cache
from smc_analysis import analyze


def test_htf_indicators():
    """Test completo de HTF indicators"""
    print("🧪 TEST: HTF Indicators (FVGs y Order Blocks)")
    print("=" * 60)
    
    # Test 1: Obtener datos HTF
    print("\n1️⃣ Obteniendo datos HTF (1w) para BTC/USDT...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Más datos para mejor análisis
        
        htf_data = get_ohlcv_with_cache(
            symbol="BTC/USDT",
            timeframe="1w",
            start=start_date,
            end=end_date,
            provider_hint="yahoo"
        )
        
        print(f"✅ Datos HTF obtenidos: {len(htf_data)} filas")
        print(f"   Rango: {htf_data['timestamp'].min()} a {htf_data['timestamp'].max()}")
        print(f"   Precio actual: {htf_data['close'].iloc[-1]:.2f}")
        
        # Verificar estructura de datos
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in htf_data.columns]
        if missing_cols:
            print(f"❌ Columnas faltantes: {missing_cols}")
            return False
        else:
            print("✅ Estructura de datos correcta")
        
        # Verificar duplicados
        duplicates = htf_data.duplicated(subset=['timestamp']).sum()
        if duplicates > 0:
            print(f"❌ Duplicados encontrados: {duplicates}")
            return False
        else:
            print("✅ Sin duplicados")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos HTF: {e}")
        return False
    
    # Test 2: Análisis SMC en HTF
    print("\n2️⃣ Ejecutando análisis SMC en HTF...")
    try:
        smc_result = analyze(htf_data, timeframe="1w")
        
        print(f"✅ Análisis SMC completado")
        print(f"   FVGs detectados: {len(smc_result.get('fvg', []))}")
        print(f"   Order Blocks detectados: {len(smc_result.get('orderblocks', []))}")
        print(f"   Liquidity detectada: {len(smc_result.get('liquidity', []))}")
        
        # Verificar estructura del resultado
        expected_keys = ['fvg', 'orderblocks', 'liquidity', 'swing_highs_lows', 'bos_choch']
        missing_keys = [key for key in expected_keys if key not in smc_result]
        if missing_keys:
            print(f"⚠️ Claves faltantes en resultado SMC: {missing_keys}")
        else:
            print("✅ Estructura de resultado SMC correcta")
            
    except Exception as e:
        print(f"❌ Error en análisis SMC: {e}")
        return False
    
    # Test 3: Verificar FVGs específicamente
    print("\n3️⃣ Verificando FVGs en HTF...")
    try:
        from smartmoneyconcepts import smc
        
        # Detectar FVGs
        fvgs = smc.fvg(htf_data)
        
        print(f"✅ FVGs detectados: {len(fvgs)}")
        if not fvgs.empty:
            print(f"   Columnas FVG: {list(fvgs.columns)}")
            
            # Verificar que no hay FVGs duplicados
            if 'FVG' in fvgs.columns:
                unique_fvgs = fvgs[fvgs['FVG'] != 0]
                print(f"   FVGs únicos: {len(unique_fvgs)}")
                
                # Mostrar algunos FVGs de ejemplo
                if len(unique_fvgs) > 0:
                    print("   Ejemplos de FVGs:")
                    for i, (idx, row) in enumerate(unique_fvgs.head(3).iterrows()):
                        fvg_type = "Bullish" if row['FVG'] == 1 else "Bearish"
                        print(f"     {i+1}. {fvg_type} FVG: {row['Top']:.2f} - {row['Bottom']:.2f}")
        else:
            print("⚠️ No se detectaron FVGs")
            
    except Exception as e:
        print(f"❌ Error verificando FVGs: {e}")
        return False
    
    # Test 4: Verificar Order Blocks específicamente
    print("\n4️⃣ Verificando Order Blocks en HTF...")
    try:
        from smartmoneyconcepts import smc
        
        # Detectar Order Blocks usando la función correcta
        swing_highs_lows = smc.swing_highs_lows(htf_data)
        orderblocks = smc.ob(htf_data, swing_highs_lows)
        
        print(f"✅ Order Blocks detectados: {len(orderblocks)}")
        if not orderblocks.empty:
            print(f"   Columnas Order Blocks: {list(orderblocks.columns)}")
            
            # Verificar que no hay Order Blocks duplicados
            if 'OB' in orderblocks.columns:
                unique_obs = orderblocks[orderblocks['OB'] != 0]
                print(f"   Order Blocks únicos: {len(unique_obs)}")
                
                # Mostrar algunos Order Blocks de ejemplo
                if len(unique_obs) > 0:
                    print("   Ejemplos de Order Blocks:")
                    for i, (idx, row) in enumerate(unique_obs.head(3).iterrows()):
                        ob_type = "Bullish" if row['OB'] == 1 else "Bearish"
                        print(f"     {i+1}. {ob_type} OB: {row['Top']:.2f} - {row['Bottom']:.2f}")
        else:
            print("⚠️ No se detectaron Order Blocks")
            
    except Exception as e:
        print(f"❌ Error verificando Order Blocks: {e}")
        return False
    
    # Test 5: Comparar con diferentes timeframes
    print("\n5️⃣ Comparando indicadores en diferentes timeframes...")
    try:
        timeframes = ["15m", "1h", "1d", "1w"]
        results = {}
        
        for tf in timeframes:
            data = get_ohlcv_with_cache(
                symbol="BTC/USDT",
                timeframe=tf,
                start=start_date,
                end=end_date,
                provider_hint="yahoo"
            )
            
            if not data.empty:
                fvgs_tf = smc.fvg(data)
                swing_highs_lows_tf = smc.swing_highs_lows(data)
                obs_tf = smc.ob(data, swing_highs_lows_tf)
                results[tf] = {
                    'fvgs': len(fvgs_tf),
                    'obs': len(obs_tf),
                    'rows': len(data)
                }
                print(f"   {tf}: {len(fvgs_tf)} FVGs, {len(obs_tf)} OBs, {len(data)} filas")
            else:
                print(f"   {tf}: Sin datos")
                
        print("✅ Comparación de timeframes completada")
        
    except Exception as e:
        print(f"❌ Error en comparación: {e}")
        return False
    
    print("\n🎉 TEST COMPLETADO EXITOSAMENTE")
    return True

def test_htf_data_quality():
    """Test de calidad de datos HTF"""
    print("\n🧪 TEST: HTF Data Quality")
    print("=" * 60)
    
    try:
        # Obtener datos de diferentes fuentes
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Yahoo Finance
        yahoo_data = get_ohlcv_with_cache(
            symbol="BTC/USDT",
            timeframe="1w",
            start=start_date,
            end=end_date,
            provider_hint="yahoo"
        )
        
        print(f"Yahoo Finance: {len(yahoo_data)} filas")
        if not yahoo_data.empty:
            print(f"   Rango: {yahoo_data['timestamp'].min()} a {yahoo_data['timestamp'].max()}")
            print(f"   Precio actual: {yahoo_data['close'].iloc[-1]:.2f}")
            
            # Verificar calidad de datos
            price_range = yahoo_data['high'].max() - yahoo_data['low'].min()
            avg_price = yahoo_data['close'].mean()
            price_volatility = yahoo_data['close'].std()
            
            print(f"   Rango de precios: {price_range:.2f}")
            print(f"   Precio promedio: {avg_price:.2f}")
            print(f"   Volatilidad: {price_volatility:.2f}")
            
            # Verificar que no hay gaps grandes en los datos
            time_diffs = yahoo_data['timestamp'].diff().dropna()
            max_gap = time_diffs.max()
            print(f"   Gap máximo entre datos: {max_gap}")
            
            if price_range > 0 and avg_price > 0:
                print("✅ Datos de precio razonables")
            else:
                print("❌ Datos de precio sospechosos")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error en test de calidad: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando tests de HTF Indicators...")
    
    # Ejecutar tests
    test1_passed = test_htf_indicators()
    test2_passed = test_htf_data_quality()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DE TESTS:")
    print(f"   Test HTF Indicators: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   Test HTF Data Quality: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 TODOS LOS TESTS PASARON")
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON")
        sys.exit(1)
