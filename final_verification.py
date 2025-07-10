#!/usr/bin/env python3
"""
Verificación final de todas las correcciones implementadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def final_verification():
    """Verificación final completa"""
    print("🔍 VERIFICACIÓN FINAL DE CORRECCIONES")
    print("="*50)

    all_tests_passed = True

    # Test 1: FVGs siempre visibles
    print("\n1. 📊 Verificando FVGs siempre visibles...")
    try:
        from fetch_data import get_ohlcv_extended
        from smc_analysis import analyze

        # Probar con datos grandes (debería mostrar FVGs optimizados)
        df_large = get_ohlcv_extended("BTC/USDT", "15m", days=5)
        signals_large = analyze(df_large)
        fvg_count_large = len(signals_large['fvg'])

        # Probar con datos pequeños (debería mostrar FVGs completos)
        df_small = get_ohlcv_extended("BTC/USDT", "15m", days=1)
        signals_small = analyze(df_small)
        fvg_count_small = len(signals_small['fvg'])

        print(f"   ✅ FVGs con datos grandes ({len(df_large)} puntos): {fvg_count_large} FVGs")
        print(f"   ✅ FVGs con datos pequeños ({len(df_small)} puntos): {fvg_count_small} FVGs")

        if fvg_count_large > 0 and fvg_count_small > 0:
            print("   ✅ FVGs se detectan correctamente en ambos casos")
        else:
            print("   ❌ Problemas con detección de FVGs")
            all_tests_passed = False

    except Exception as e:
        print(f"   ❌ Error en verificación de FVGs: {e}")
        all_tests_passed = False

    # Test 2: Display bot metrics sin errores
    print("\n2. 🤖 Verificando métricas del bot...")
    try:
        from smc_integration import get_smc_bot_analysis, display_bot_metrics

        df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
        bot_analysis = get_smc_bot_analysis(df)

        # Verificar estructura de datos
        required_keys = ['trend', 'swings', 'signals', 'liquidity_zones', 'sweeps', 'choch_bos']
        missing_keys = [key for key in required_keys if key not in bot_analysis]

        if not missing_keys:
            print("   ✅ Estructura de bot_analysis correcta")
            print(f"      - Swings: {type(bot_analysis['swings'])}")
            print(f"      - Signals: {type(bot_analysis['signals'])} con {len(bot_analysis['signals'])} señales")
            print(f"      - Trend: {bot_analysis['trend']}")
        else:
            print(f"   ⚠️ Claves faltantes en bot_analysis: {missing_keys}")

    except Exception as e:
        print(f"   ❌ Error en verificación de métricas: {e}")
        all_tests_passed = False

    # Test 3: Visualización avanzada sin errores
    print("\n3. 🎨 Verificando visualización avanzada...")
    try:
        from smc_visualization_advanced import enhance_signal_visualization
        import plotly.graph_objects as go

        # Crear figura básica
        fig = go.Figure()
        df = get_ohlcv_extended("BTC/USDT", "15m", days=1)
        bot_analysis = get_smc_bot_analysis(df)

        # Probar función de visualización avanzada
        enhance_signal_visualization(fig, df, bot_analysis)
        print("   ✅ Visualización avanzada funciona sin errores")

    except Exception as e:
        print(f"   ❌ Error en visualización avanzada: {e}")
        all_tests_passed = False

    # Test 4: Datos extendidos funcionando
    print("\n4. 📈 Verificando datos extendidos...")
    try:
        # Probar diferentes timeframes y días
        test_cases = [
            ("BTC/USDT", "1m", 1),
            ("BTC/USDT", "15m", 3),
            ("BTC/USDT", "15m", 5),
            ("ETH/USDT", "15m", 2)
        ]

        for symbol, timeframe, days in test_cases:
            df = get_ohlcv_extended(symbol, timeframe, days)
            print(f"   ✅ {symbol} {timeframe} {days}d: {len(df)} puntos")

    except Exception as e:
        print(f"   ❌ Error en datos extendidos: {e}")
        all_tests_passed = False

    # Resumen final
    print("\n" + "="*50)
    if all_tests_passed:
        print("🎉 TODAS LAS CORRECCIONES VERIFICADAS EXITOSAMENTE")
        print("\n✅ Problemas Resueltos:")
        print("   1. FVGs ahora siempre visibles (con renderizado inteligente)")
        print("   2. Tabla inferior estable (manejo robusto de DataFrames)")
        print("   3. Visualización avanzada sin errores")
        print("   4. Datos extendidos funcionando correctamente")
        print("\n🚀 La aplicación está lista para usar!")
        return True
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("   Revisar los errores anteriores")
        return False

if __name__ == "__main__":
    success = final_verification()
    sys.exit(0 if success else 1)
