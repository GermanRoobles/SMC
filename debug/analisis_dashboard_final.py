#!/usr/bin/env python3
"""
ANÁLISIS FINAL DE INCONSISTENCIAS Y ERRORES DEL DASHBOARD SMC
============================================================

Este script realiza un diagnóstico exhaustivo del dashboard SMC para identificar
inconsistencias, errores y proporcionar recomendaciones de optimización.
"""

from fetch_data import get_ohlcv
from smc_analysis import analyze
from smc_integration import get_smc_bot_analysis
from app_streamlit import consolidate_smc_metrics

def diagnose_dashboard_consistency():
    """Diagnosticar consistencia completa del dashboard"""

    print("="*80)
    print("🔍 ANÁLISIS FINAL DE CONSISTENCIA DEL DASHBOARD SMC")
    print("="*80)

    # 1. Obtener datos de muestra (usando diferentes timeframes para probar robustez)
    print("\n📊 OBTENIENDO DATOS DE PRUEBA...")

    # Simular datos como los del dashboard mostrado (15m, 5 días = 480 velas)
    timeframes = [
        ('15m', 480, '5 días en 15m'),
        ('1h', 120, '5 días en 1h'),
        ('4h', 30, '5 días en 4h')
    ]

    results = []

    for timeframe, limit, description in timeframes:
        print(f"\n🔄 Analizando {description}...")

        try:
            # Obtener datos
            df = get_ohlcv('BTCUSDT', timeframe, limit=limit)
            print(f"   ✅ Datos obtenidos: {len(df)} velas")

            # Realizar análisis SMC
            signals = analyze(df)
            bot_analysis = get_smc_bot_analysis(df)

            # Obtener métricas consolidadas
            consolidated_metrics = consolidate_smc_metrics(signals, bot_analysis)

            # Verificación directa vs consolidada
            verification = {}

            # FVG
            if 'fvg' in signals and signals['fvg'] is not None:
                fvg_direct = int(signals['fvg']['FVG'].notna().sum())
                fvg_consolidated = consolidated_metrics['fvg_count']
                fvg_percentage = (fvg_direct / len(signals['fvg']) * 100) if len(signals['fvg']) > 0 else 0
                verification['fvg'] = {
                    'direct': fvg_direct,
                    'consolidated': fvg_consolidated,
                    'match': fvg_direct == fvg_consolidated,
                    'percentage': fvg_percentage,
                    'quality': 'HIGH' if fvg_percentage > 15 else 'NORMAL' if fvg_percentage > 5 else 'LOW'
                }

            # Order Blocks
            if 'orderblocks' in signals and signals['orderblocks'] is not None:
                ob_direct = int(signals['orderblocks']['OB'].notna().sum())
                ob_consolidated = consolidated_metrics['order_blocks_count']
                ob_percentage = (ob_direct / len(signals['orderblocks']) * 100) if len(signals['orderblocks']) > 0 else 0
                verification['orderblocks'] = {
                    'direct': ob_direct,
                    'consolidated': ob_consolidated,
                    'match': ob_direct == ob_consolidated,
                    'percentage': ob_percentage,
                    'quality': 'LOW' if ob_percentage < 2 else 'NORMAL' if ob_percentage < 8 else 'HIGH'
                }

            # BOS/CHoCH
            if 'bos_choch' in signals and signals['bos_choch'] is not None:
                bos_direct = int(signals['bos_choch']['BOS'].notna().sum())
                choch_direct = int(signals['bos_choch']['CHOCH'].notna().sum()) if 'CHOCH' in signals['bos_choch'].columns else 0
                total_direct = bos_direct + choch_direct
                bos_consolidated = consolidated_metrics['bos_choch_count']
                bos_percentage = (total_direct / len(signals['bos_choch']) * 100) if len(signals['bos_choch']) > 0 else 0
                verification['bos_choch'] = {
                    'direct': total_direct,
                    'consolidated': bos_consolidated,
                    'match': total_direct == bos_consolidated,
                    'percentage': bos_percentage,
                    'bos_count': bos_direct,
                    'choch_count': choch_direct,
                    'balance': 'GOOD' if 0.3 <= (bos_direct/choch_direct if choch_direct > 0 else 1) <= 3 else 'IMBALANCED'
                }

            # Liquidity
            if 'liquidity' in signals and signals['liquidity'] is not None:
                liq_direct = int(signals['liquidity']['Liquidity'].notna().sum())
                liq_consolidated = consolidated_metrics['liquidity_count']
                liq_percentage = (liq_direct / len(signals['liquidity']) * 100) if len(signals['liquidity']) > 0 else 0
                verification['liquidity'] = {
                    'direct': liq_direct,
                    'consolidated': liq_consolidated,
                    'match': liq_direct == liq_consolidated,
                    'percentage': liq_percentage
                }

            # Swings
            if 'swing_highs_lows' in signals and signals['swing_highs_lows'] is not None:
                swing_direct = int(signals['swing_highs_lows']['HighLow'].notna().sum())
                swing_consolidated = consolidated_metrics['total_swings']
                swing_percentage = (swing_direct / len(signals['swing_highs_lows']) * 100) if len(signals['swing_highs_lows']) > 0 else 0
                verification['swings'] = {
                    'direct': swing_direct,
                    'consolidated': swing_consolidated,
                    'match': swing_direct == swing_consolidated,
                    'percentage': swing_percentage
                }

            results.append({
                'timeframe': timeframe,
                'description': description,
                'data_points': len(df),
                'verification': verification,
                'all_consistent': all(v.get('match', True) for v in verification.values())
            })

        except Exception as e:
            print(f"   ❌ Error en {description}: {e}")
            results.append({
                'timeframe': timeframe,
                'description': description,
                'error': str(e)
            })

    # 2. Mostrar resultados del análisis
    print("\n" + "="*80)
    print("📋 RESULTADOS DEL ANÁLISIS")
    print("="*80)

    for result in results:
        if 'error' in result:
            print(f"\n❌ {result['description']}: ERROR - {result['error']}")
            continue

        print(f"\n✅ {result['description']} ({result['data_points']} velas)")
        print(f"   Consistencia general: {'✅ CORRECTO' if result['all_consistent'] else '❌ INCONSISTENTE'}")

        for indicator, data in result['verification'].items():
            status = "✅" if data['match'] else "❌"
            print(f"   {indicator.upper()}: {status} Directo={data['direct']} vs Consolidado={data['consolidated']} ({data['percentage']:.1f}%)")

    # 3. Análisis específico del dashboard mostrado
    print("\n" + "="*80)
    print("🎯 ANÁLISIS DEL DASHBOARD MOSTRADO (BTC/USDT 15m, 5 días)")
    print("="*80)

    dashboard_data = {
        'FVG': 143,
        'Order Blocks': 2,
        'BOS/CHoCH': {'sidebar': 5, 'bot_section': 7},  # Inconsistencia encontrada
        'Liquidity': 3,
        'Swing Highs': 13,
        'Swing Lows': 13,
        'Total Swings': 26
    }

    # Buscar el resultado de 15m para comparar
    dashboard_result = next((r for r in results if r['timeframe'] == '15m'), None)

    if dashboard_result and 'verification' in dashboard_result:
        print("\n🔍 COMPARACIÓN CON DATOS REALES:")

        verification = dashboard_result['verification']

        if 'fvg' in verification:
            real_fvg = verification['fvg']['direct']
            print(f"   FVG: Dashboard={dashboard_data['FVG']} vs Real={real_fvg}")
            if abs(dashboard_data['FVG'] - real_fvg) > real_fvg * 0.1:  # >10% diferencia
                print(f"      ⚠️  DISCREPANCIA SIGNIFICATIVA en FVG")

        if 'orderblocks' in verification:
            real_ob = verification['orderblocks']['direct']
            print(f"   Order Blocks: Dashboard={dashboard_data['Order Blocks']} vs Real={real_ob}")
            if dashboard_data['Order Blocks'] != real_ob:
                print(f"      ⚠️  DISCREPANCIA en Order Blocks")

        if 'bos_choch' in verification:
            real_bos = verification['bos_choch']['direct']
            print(f"   BOS/CHoCH: Dashboard Sidebar={dashboard_data['BOS/CHoCH']['sidebar']} vs Bot Section={dashboard_data['BOS/CHoCH']['bot_section']} vs Real={real_bos}")
            if dashboard_data['BOS/CHoCH']['sidebar'] != dashboard_data['BOS/CHoCH']['bot_section']:
                print(f"      ❌ INCONSISTENCIA INTERNA: Sidebar ≠ Bot Section")
            if real_bos not in [dashboard_data['BOS/CHoCH']['sidebar'], dashboard_data['BOS/CHoCH']['bot_section']]:
                print(f"      ⚠️  DISCREPANCIA con datos reales")

    # 4. Recomendaciones de optimización
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES DE OPTIMIZACIÓN")
    print("="*80)

    recommendations = []

    # Analizar cada timeframe para patrones
    for result in results:
        if 'verification' not in result:
            continue

        verification = result['verification']

        # FVG over-detection
        if 'fvg' in verification and verification['fvg']['quality'] == 'HIGH':
            recommendations.append(f"📈 FVG en {result['timeframe']}: Detección muy alta ({verification['fvg']['percentage']:.1f}%) - implementar filtros más estrictos")

        # Order Blocks under-detection
        if 'orderblocks' in verification and verification['orderblocks']['quality'] == 'LOW':
            recommendations.append(f"🏗️ Order Blocks en {result['timeframe']}: Detección muy baja ({verification['orderblocks']['percentage']:.1f}%) - relajar criterios de detección")

        # BOS/CHoCH imbalance
        if 'bos_choch' in verification and verification['bos_choch']['balance'] == 'IMBALANCED':
            bos = verification['bos_choch']['bos_count']
            choch = verification['bos_choch']['choch_count']
            recommendations.append(f"⚡ BOS/CHoCH en {result['timeframe']}: Desbalance (BOS={bos}, CHoCH={choch}) - revisar lógica de clasificación")

    # Recomendaciones específicas del dashboard
    recommendations.extend([
        "🔧 OPTIMIZACIONES TÉCNICAS:",
        "   • Implementar filtros ATR para FVG (reducir noise)",
        "   • Añadir validación por volumen para Order Blocks",
        "   • Unificar configuración de riesgo entre Trade Engine y Backtester",
        "   • Implementar detección multi-timeframe para confirmación",
        "",
        "🎨 MEJORAS DE UX:",
        "   • Consolidar todas las métricas en una sola función",
        "   • Añadir tooltips explicativos para cada indicador",
        "   • Implementar alertas cuando la detección esté fuera de rangos óptimos",
        "   • Mostrar porcentajes de detección junto a números absolutos"
    ])

    for rec in recommendations:
        print(rec)

    # 5. Resumen ejecutivo
    print("\n" + "="*80)
    print("📊 RESUMEN EJECUTIVO")
    print("="*80)

    all_consistent = all(r.get('all_consistent', False) for r in results if 'all_consistent' in r)
    successful_tests = len([r for r in results if 'verification' in r])

    print(f"✅ Tests ejecutados: {successful_tests}/{len(timeframes)}")
    print(f"📊 Consistencia interna: {'✅ PERFECTA' if all_consistent else '⚠️ REQUIERE ATENCIÓN'}")
    print(f"🎯 Estado del dashboard: {'✅ ESTABLE' if successful_tests == len(timeframes) else '⚠️ INESTABLE'}")

    if dashboard_data['BOS/CHoCH']['sidebar'] != dashboard_data['BOS/CHoCH']['bot_section']:
        print("❌ PROBLEMA CRÍTICO: Inconsistencia en BOS/CHoCH entre secciones del dashboard")
    else:
        print("✅ No se detectaron inconsistencias críticas")

    print("\n🏁 Análisis completado. Revisar recomendaciones para optimización.")

if __name__ == "__main__":
    diagnose_dashboard_consistency()
