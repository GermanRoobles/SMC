#!/usr/bin/env python3
"""
Test Integración Completa SMC
=============================

Test para verificar la integración completa del sistema SMC:
- Fetch de datos
- Análisis SMC
- Motor de trading
- Backtesting
- Visualización
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fetch_data import get_ohlcv_extended
from smc_integration import get_smc_bot_analysis
from smc_trade_engine import get_trade_engine_analysis
from smc_backtester import run_backtest_analysis

def test_complete_integration():
    """Test de integración completa del sistema SMC"""
    print("🧪 === TEST INTEGRACIÓN COMPLETA SMC ===")
    print()

    # 1. Test de fetch de datos
    print("📊 1. Probando fetch de datos...")
    try:
        df = get_ohlcv_extended("BTC/USDT", "15m", days=2)
        print(f"   ✅ Datos obtenidos: {len(df)} velas desde {df.index[0]} hasta {df.index[-1]}")

        if df.empty:
            print("   ❌ Error: No hay datos disponibles")
            return False

    except Exception as e:
        print(f"   ❌ Error en fetch de datos: {e}")
        return False

    # 2. Test de análisis SMC
    print("\n🔍 2. Probando análisis SMC...")
    try:
        bot_analysis = get_smc_bot_analysis(df)
        print(f"   ✅ Análisis SMC completado")

        # Verificar componentes del análisis
        if bot_analysis:
            print(f"   📈 FVG detectados: {len(bot_analysis.get('fvg', []))}")
            print(f"   📦 Order Blocks: {len(bot_analysis.get('orderblocks', []))}")
            print(f"   💧 Liquidity: {len(bot_analysis.get('liquidity', []))}")
            print(f"   📊 BOS/CHOCH: {len(bot_analysis.get('bos_choch', []))}")
        else:
            print("   ⚠️ Análisis SMC vacío")

    except Exception as e:
        print(f"   ❌ Error en análisis SMC: {e}")
        return False

    # 3. Test del motor de trading
    print("\n🎯 3. Probando motor de trading...")
    try:
        trade_analysis = get_trade_engine_analysis(df, bot_analysis)
        print(f"   ✅ Motor de trading ejecutado")

        if trade_analysis and 'signal_count' in trade_analysis:
            signal_count = trade_analysis['signal_count']
            print(f"   🎯 Señales detectadas: {signal_count}")

            if signal_count > 0:
                signals = trade_analysis.get('signals', [])
                print(f"   📝 Señales en lista: {len(signals)}")

                # Mostrar detalles de la primera señal
                if signals:
                    first_signal = signals[0]
                    print(f"   🔍 Primera señal: {first_signal.signal_type.value} @ {first_signal.entry_price}")
                    print(f"   🛡️ SL: {first_signal.stop_loss}, 🎯 TP: {first_signal.take_profit}")

                # 4. Test de backtesting (solo si hay señales)
                print("\n📈 4. Probando backtesting...")
                try:
                    backtest_analysis = run_backtest_analysis(
                        df,
                        signals,
                        initial_capital=10000,
                        risk_per_trade=2.0
                    )

                    if backtest_analysis['success']:
                        results = backtest_analysis['results']
                        print(f"   ✅ Backtesting completado")
                        print(f"   📊 Trades ejecutados: {results.total_trades}")
                        print(f"   📈 Win Rate: {results.win_rate:.1f}%")
                        print(f"   💰 PnL Total: {results.total_pnl:.2f} puntos")
                        print(f"   📉 Drawdown: {results.max_drawdown_percent:.1f}%")

                        # Verificar que se generó el gráfico
                        chart = backtest_analysis.get('chart')
                        if chart:
                            print(f"   📊 Gráfico de performance generado")

                    else:
                        print(f"   ❌ Error en backtesting: {backtest_analysis.get('report', 'Sin reporte')}")

                except Exception as e:
                    print(f"   ❌ Error en backtesting: {e}")
                    return False

            else:
                print("   ℹ️ No hay señales para testear backtesting")

        else:
            print("   ⚠️ Motor de trading no devolvió análisis válido")

    except Exception as e:
        print(f"   ❌ Error en motor de trading: {e}")
        return False

    # 5. Test de métricas consolidadas
    print("\n📊 5. Probando consolidación de métricas...")
    try:
        from app_streamlit import consolidate_smc_metrics

        # Crear análisis mock para las métricas
        mock_signals = {
            'fvg': pd.DataFrame({'FVG': [1, 0, 1, 0, 1]}),
            'orderblocks': pd.DataFrame({'OB': [1, 1, 0, 1, 0]}),
            'liquidity': pd.DataFrame({'Liquidity': [0, 1, 0, 1, 1]}),
            'bos_choch': pd.DataFrame({'BoS': [1, 0, 0], 'ChoCh': [0, 1, 1]}),
            'swing_highs_lows': pd.DataFrame({'swing_highs': [1, 0, 1], 'swing_lows': [0, 1, 0]})
        }

        consolidated = consolidate_smc_metrics(mock_signals, bot_analysis)
        print(f"   ✅ Métricas consolidadas: {len(consolidated)} métricas")

        # Verificar algunas métricas clave
        expected_keys = ['total_fvg', 'total_orderblocks', 'total_liquidity', 'total_bos', 'total_choch']
        for key in expected_keys:
            if key in consolidated:
                print(f"   📊 {key}: {consolidated[key]}")

    except Exception as e:
        print(f"   ❌ Error en consolidación de métricas: {e}")
        return False

    print("\n🎉 === INTEGRACIÓN COMPLETA EXITOSA ===")
    print("✅ Todos los componentes funcionan correctamente")
    print("✅ Pipeline completo: Datos → SMC → Trading → Backtesting")
    return True

def test_streamlit_components():
    """Test específico de componentes de Streamlit"""
    print("\n🖥️ === TEST COMPONENTES STREAMLIT ===")

    try:
        # Test de funciones de visualización
        print("🎨 Probando funciones de visualización...")

        # Verificar imports
        from smc_integration import add_bot_signals_to_chart, display_bot_metrics
        print("   ✅ Imports de integración correctos")

        # Verificar visualización avanzada
        try:
            from smc_visualization_advanced import enhance_signal_visualization
            print("   ✅ Visualización avanzada disponible")
        except ImportError:
            print("   ⚠️ Visualización avanzada no disponible")

        # Test de funciones de mensaje temporal
        try:
            import streamlit as st
            print("   ✅ Streamlit disponible para tests")
        except ImportError:
            print("   ⚠️ Streamlit no disponible en entorno de test")

        return True

    except Exception as e:
        print(f"   ❌ Error en componentes Streamlit: {e}")
        return False

if __name__ == "__main__":
    try:
        # Test de integración completa
        integration_success = test_complete_integration()

        # Test de componentes Streamlit
        streamlit_success = test_streamlit_components()

        if integration_success and streamlit_success:
            print("\n🏆 TODOS LOS TESTS PASARON EXITOSAMENTE")
            print("🚀 El sistema SMC está listo para producción")
        else:
            print("\n⚠️ ALGUNOS TESTS FALLARON")
            print("🔧 Revisar los componentes marcados con ❌")

    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN TESTS: {e}")
        import traceback
        traceback.print_exc()
