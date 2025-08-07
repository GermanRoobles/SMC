#!/usr/bin/env python3
"""
Test específico para FVG en High Timeframes (HTF)
Verifica que los datos de Yahoo Finance se procesen correctamente para HTF
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

def test_htf_fvg_processing():
    """Test completo del procesamiento de FVG en HTF"""
    print("🧪 TEST: HTF FVG Processing")
    print("=" * 50)
    
    # Test 1: Obtener datos HTF
    print("\n1️⃣ Obteniendo datos HTF (1w) para BTC/USDT...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        htf_data = get_ohlcv_with_cache(
            symbol="BTC/USDT",
            timeframe="1w",
            start=start_date,
            end=end_date,
            provider_hint="yahoo"
        )
        
        print(f"✅ Datos HTF obtenidos: {len(htf_data)} filas")
        print(f"   Rango: {htf_data['timestamp'].min()} a {htf_data['timestamp'].max()}")
        print(f"   Columnas: {list(htf_data.columns)}")
        
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
        
        # Verificar datos numéricos
        for col in ['open', 'high', 'low', 'close']:
            if not pd.api.types.is_numeric_dtype(htf_data[col]):
                print(f"❌ Columna {col} no es numérica")
                return False
        print("✅ Datos numéricos correctos")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos HTF: {e}")
        return False
    
    # Test 2: Análisis SMC en HTF
    print("\n2️⃣ Ejecutando análisis SMC en HTF...")
    try:
        smc_result = analyze(htf_data, timeframe="1w")
        
        print(f"✅ Análisis SMC completado")
        print(f"   FVGs detectados: {len(smc_result.get('fvgs', []))}")
        print(f"   Order Blocks detectados: {len(smc_result.get('orderblocks', []))}")
        
        # Verificar estructura del resultado
        expected_keys = ['fvgs', 'orderblocks', 'liquidity', 'swing_highs', 'swing_lows']
        missing_keys = [key for key in expected_keys if key not in smc_result]
        if missing_keys:
            print(f"⚠️ Claves faltantes en resultado SMC: {missing_keys}")
        else:
            print("✅ Estructura de resultado SMC correcta")
            
    except Exception as e:
        print(f"❌ Error en análisis SMC: {e}")
        return False
    
    # Test 3: Verificar FVG específicamente
    print("\n3️⃣ Verificando FVGs en HTF...")
    try:
        from smartmoneyconcepts import smc
        
        # Obtener swing highs/lows
        swing_highs_lows = smc.swing_highs_lows(htf_data)
        
        # Detectar FVGs
        fvgs = smc.fvg(htf_data)
        
        print(f"✅ FVGs detectados: {len(fvgs)}")
        if not fvgs.empty:
            print(f"   Columnas FVG: {list(fvgs.columns)}")
            print(f"   Primeros FVGs:")
            print(fvgs.head())
            
            # Verificar que no hay FVGs duplicados
            if 'FVG' in fvgs.columns:
                unique_fvgs = fvgs[fvgs['FVG'] != 0]
                print(f"   FVGs únicos: {len(unique_fvgs)}")
        else:
            print("⚠️ No se detectaron FVGs")
            
    except Exception as e:
        print(f"❌ Error verificando FVGs: {e}")
        return False
    
    # Test 4: Comparar con datos de diferentes timeframes
    print("\n4️⃣ Comparando con diferentes timeframes...")
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
                results[tf] = len(fvgs_tf)
                print(f"   {tf}: {len(fvgs_tf)} FVGs, {len(data)} filas")
            else:
                print(f"   {tf}: Sin datos")
                
        print("✅ Comparación de timeframes completada")
        
    except Exception as e:
        print(f"❌ Error en comparación: {e}")
        return False
    
    print("\n🎉 TEST COMPLETADO EXITOSAMENTE")
    return True

def test_htf_data_consistency():
    """Test de consistencia de datos HTF"""
    print("\n🧪 TEST: HTF Data Consistency")
    print("=" * 50)
    
    try:
        # Obtener datos de diferentes fuentes
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
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
        
        # Verificar que los datos son razonables
        if not yahoo_data.empty:
            price_range = yahoo_data['high'].max() - yahoo_data['low'].min()
            avg_price = yahoo_data['close'].mean()
            
            if price_range > 0 and avg_price > 0:
                print(f"✅ Rango de precios razonable: {price_range:.2f}")
                print(f"✅ Precio promedio razonable: {avg_price:.2f}")
            else:
                print("❌ Datos de precio sospechosos")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error en test de consistencia: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando tests de HTF FVG...")
    
    # Ejecutar tests
    test1_passed = test_htf_fvg_processing()
    test2_passed = test_htf_data_consistency()
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DE TESTS:")
    print(f"   Test HTF FVG Processing: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   Test HTF Data Consistency: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 TODOS LOS TESTS PASARON")
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON")
        sys.exit(1)
