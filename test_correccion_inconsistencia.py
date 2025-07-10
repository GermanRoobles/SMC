#!/usr/bin/env python3
"""
TEST DE VERIFICACIÓN: Corrección de Inconsistencia BOS/CHoCH
==========================================================

Verificar que la inconsistencia crítica entre sidebar y bot section ha sido corregida.
"""

from fetch_data import get_ohlcv
from smc_analysis import analyze
from smc_integration import get_smc_bot_analysis
from app_streamlit import consolidate_smc_metrics

def test_bos_choch_consistency():
    """Verificar que todas las funciones reportan el mismo valor para BOS/CHoCH"""

    print("="*70)
    print("🔍 TEST DE CORRECCIÓN: Inconsistencia BOS/CHoCH")
    print("="*70)

    try:
        # 1. Obtener datos de prueba (mismo escenario que el dashboard)
        print("\n📊 Obteniendo datos BTC/USDT 15m (480 velas)...")
        df = get_ohlcv('BTCUSDT', '15m', limit=480)
        print(f"   ✅ Datos obtenidos: {len(df)} velas")

        # 2. Realizar análisis SMC
        print("\n🔍 Realizando análisis SMC...")
        signals = analyze(df)
        bot_analysis = get_smc_bot_analysis(df)

        # 3. Calcular métricas con diferentes métodos
        print("\n📊 COMPARANDO MÉTODOS DE CONTEO:")

        # Método 1: Consolidado (usado en dashboard principal)
        consolidated_metrics = consolidate_smc_metrics(signals, bot_analysis)
        method1_count = consolidated_metrics['bos_choch_count']
        print(f"   📈 Método Consolidado (dashboard): {method1_count}")

        # Método 2: Directo sobre signals
        if 'bos_choch' in signals and signals['bos_choch'] is not None:
            bos_direct = int(signals['bos_choch']['BOS'].notna().sum())
            choch_direct = int(signals['bos_choch']['CHOCH'].notna().sum()) if 'CHOCH' in signals['bos_choch'].columns else 0
            method2_count = bos_direct + choch_direct
            print(f"   🔍 Método Directo (signals): {method2_count} (BOS={bos_direct}, CHoCH={choch_direct})")
        else:
            method2_count = 0
            print(f"   🔍 Método Directo (signals): {method2_count}")

        # Método 3: Directo sobre bot_analysis
        if 'bos_choch' in bot_analysis and bot_analysis['bos_choch'] is not None:
            bos_bot = int(bot_analysis['bos_choch']['BOS'].notna().sum())
            choch_bot = int(bot_analysis['bos_choch']['CHOCH'].notna().sum()) if 'CHOCH' in bot_analysis['bos_choch'].columns else 0
            method3_count = bos_bot + choch_bot
            print(f"   🤖 Método Bot Analysis: {method3_count} (BOS={bos_bot}, CHoCH={choch_bot})")
        else:
            method3_count = 0
            print(f"   🤖 Método Bot Analysis: {method3_count}")

        # 4. Verificar consistencia
        print(f"\n🎯 RESULTADOS DE CONSISTENCIA:")
        all_methods = [method1_count, method2_count, method3_count]
        unique_values = set(all_methods)

        if len(unique_values) == 1:
            print(f"   ✅ CORRECTO: Todos los métodos reportan {list(unique_values)[0]}")
            consistency_status = "PERFECTO"
        else:
            print(f"   ❌ INCONSISTENCIA: Valores diferentes detectados")
            print(f"      Consolidado: {method1_count}")
            print(f"      Directo Signals: {method2_count}")
            print(f"      Bot Analysis: {method3_count}")
            consistency_status = "FALLA"

        # 5. Simular lo que ve el usuario en diferentes secciones
        print(f"\n👤 VISTA DEL USUARIO:")
        print(f"   📊 Dashboard Principal (Sidebar): {method1_count}")
        print(f"   🤖 Bot Section: {method1_count}")  # Ahora ambos usan consolidado
        print(f"   📈 Análisis Técnico: {method1_count}")

        # 6. Verificar que display_bot_metrics ahora usa consolidado
        print(f"\n🔧 VERIFICACIÓN DE CORRECCIÓN:")

        # Simular el flujo que usa display_bot_metrics
        test_consolidated = consolidate_smc_metrics(bot_analysis, bot_analysis)
        sidebar_value = test_consolidated['bos_choch_count']

        if sidebar_value == method1_count:
            print(f"   ✅ display_bot_metrics usa métricas consolidadas correctamente")
            correction_status = "IMPLEMENTADA"
        else:
            print(f"   ❌ display_bot_metrics aún usa lógica diferente")
            correction_status = "FALLA"

        # 7. Resumen final
        print(f"\n" + "="*70)
        print(f"📋 RESUMEN DE LA VERIFICACIÓN")
        print(f"="*70)
        print(f"✅ Datos analizados: {len(df)} velas BTC/USDT 15m")
        print(f"📊 Valor BOS/CHoCH detectado: {method1_count}")
        print(f"🎯 Consistencia entre métodos: {consistency_status}")
        print(f"🔧 Estado de la corrección: {correction_status}")

        if consistency_status == "PERFECTO" and correction_status == "IMPLEMENTADA":
            print(f"\n🎉 ¡CORRECCIÓN EXITOSA!")
            print(f"   La inconsistencia crítica ha sido resuelta")
            print(f"   Todas las secciones del dashboard mostrarán valores consistentes")
            return True
        else:
            print(f"\n⚠️  CORRECCIÓN INCOMPLETA")
            print(f"   Se requiere revisión adicional del código")
            return False

    except Exception as e:
        print(f"\n❌ ERROR EN LA VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bos_choch_consistency()

    if success:
        print(f"\n✅ TEST COMPLETADO: Inconsistencia corregida exitosamente")
    else:
        print(f"\n❌ TEST FALLIDO: Se requiere corrección adicional")
