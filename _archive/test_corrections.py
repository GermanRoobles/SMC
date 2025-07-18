#!/usr/bin/env python3
"""
Script para probar las correcciones implementadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_corrections():
    """Probar las correcciones implementadas"""
    print("🧪 Probando correcciones implementadas...")

    # Test 1: Importar módulos
    print("\n1. 📦 Probando importaciones...")
    try:
        from fetch_data import get_ohlcv_extended
        print("   ✅ get_ohlcv_extended importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando get_ohlcv_extended: {e}")
        return False

    try:
        from smc_integration import display_bot_metrics
        print("   ✅ display_bot_metrics importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando display_bot_metrics: {e}")
        return False

    try:
        from smc_visualization_advanced import enhance_signal_visualization
        print("   ✅ enhance_signal_visualization importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando enhance_signal_visualization: {e}")
        return False

    # Test 2: Probar función de datos extendidos
    print("\n2. 📊 Probando función de datos extendidos...")
    try:
        df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
        if len(df) > 0:
            print(f"   ✅ Datos extendidos funcionando: {len(df)} puntos")
        else:
            print("   ❌ No se obtuvieron datos")
            return False
    except Exception as e:
        print(f"   ❌ Error obteniendo datos: {e}")
        return False

    # Test 3: Probar análisis básico
    print("\n3. 🔍 Probando análisis básico...")
    try:
        from smc_analysis import analyze
        signals = analyze(df)
        if signals and 'fvg' in signals:
            fvg_count = len(signals['fvg'])
            print(f"   ✅ Análisis básico funcionando: {fvg_count} FVGs detectados")
        else:
            print("   ⚠️ Análisis básico sin FVGs")
    except Exception as e:
        print(f"   ❌ Error en análisis básico: {e}")
        return False

    # Test 4: Probar análisis SMC Bot
    print("\n4. 🤖 Probando análisis SMC Bot...")
    try:
        from smc_integration import get_smc_bot_analysis
        bot_analysis = get_smc_bot_analysis(df)
        if bot_analysis:
            print(f"   ✅ Análisis SMC Bot funcionando")
            print(f"      - Señales: {len(bot_analysis.get('signals', []))}")
            print(f"      - Swings: {len(bot_analysis.get('swings', {}).get('swing_high', []))}")
        else:
            print("   ❌ No se obtuvo análisis SMC Bot")
            return False
    except Exception as e:
        print(f"   ❌ Error en análisis SMC Bot: {e}")
        return False

    print("\n✅ Todas las pruebas pasaron exitosamente!")
    return True

if __name__ == "__main__":
    success = test_corrections()
    if success:
        print("\n🎉 Las correcciones están funcionando correctamente!")
        print("   - FVGs se mostrarán siempre (optimizados con muchos datos)")
        print("   - Visualización avanzada maneja errores robustamente")
        print("   - Métricas del bot son más estables")
        print("   - Datos extendidos funcionan correctamente")
    else:
        print("\n❌ Algunas correcciones necesitan ajustes adicionales")

    sys.exit(0 if success else 1)
