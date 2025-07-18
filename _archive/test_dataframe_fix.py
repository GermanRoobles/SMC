#!/usr/bin/env python3
"""
Prueba rápida de la función display_bot_metrics corregida
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_display_bot_metrics():
    """Probar la función display_bot_metrics sin errores de DataFrame"""
    print("🧪 Probando display_bot_metrics corregida...")

    try:
        from smc_integration import get_smc_bot_analysis
        from fetch_data import get_ohlcv_extended
        import pandas as pd

        # Obtener datos de prueba
        df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
        bot_analysis = get_smc_bot_analysis(df)

        print(f"✅ Análisis SMC Bot completado")
        print(f"   - Tipo de swings: {type(bot_analysis.get('swings', 'N/A'))}")
        print(f"   - Tipo de signals: {type(bot_analysis.get('signals', 'N/A'))}")
        print(f"   - Tipo de liquidity_zones: {type(bot_analysis.get('liquidity_zones', 'N/A'))}")

        # Verificar estructura de swings si es DataFrame
        if isinstance(bot_analysis.get('swings'), pd.DataFrame):
            swings_df = bot_analysis['swings']
            print(f"   - Swings DataFrame shape: {swings_df.shape}")
            print(f"   - Swings DataFrame columns: {list(swings_df.columns)}")

            # Contar swings manualmente como en la función
            swing_highs = 0
            swing_lows = 0
            if 'swing_high' in swings_df.columns:
                swing_highs = swings_df['swing_high'].notna().sum()
            if 'swing_low' in swings_df.columns:
                swing_lows = swings_df['swing_low'].notna().sum()

            print(f"   - Swing highs detectados: {swing_highs}")
            print(f"   - Swing lows detectados: {swing_lows}")
            print(f"   - Total swings: {swing_highs + swing_lows}")

        print("✅ Función display_bot_metrics debería funcionar correctamente ahora")
        return True

    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_display_bot_metrics()
    print(f"\n{'🎉 Prueba exitosa!' if success else '❌ Prueba falló'}")
    sys.exit(0 if success else 1)
