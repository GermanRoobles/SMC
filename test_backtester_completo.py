#!/usr/bin/env python3
"""
TEST DEL BACKTESTER SMC
======================

Script para probar el sistema de backtesting SMC con datos reales
y verificar que todas las funcionalidades operan correctamente.
"""

from fetch_data import get_ohlcv
from smc_analysis import analyze
from smc_trade_engine import SMCTradeEngine
from smc_backtester import SMCBacktester, run_backtest_analysis
import pandas as pd
import plotly.graph_objects as go

def test_smc_backtester():
    """Probar el backtester SMC completo"""

    print("="*70)
    print("🔬 PRUEBA DEL BACKTESTER SMC")
    print("="*70)

    try:
        # 1. Obtener datos de mercado
        print("\n📊 Obteniendo datos de mercado...")
        symbol = 'BTCUSDT'
        timeframe = '1h'
        limit = 200  # 200 horas ≈ 8 días

        df = get_ohlcv(symbol, timeframe, limit=limit)
        print(f"   ✅ Datos obtenidos: {len(df)} velas {symbol} {timeframe}")
        print(f"   📅 Período: {df['timestamp'].min()} a {df['timestamp'].max()}")
        print(f"   💰 Rango de precios: ${df['low'].min():.2f} - ${df['high'].max():.2f}")

        # 2. Realizar análisis SMC
        print("\n🔍 Realizando análisis SMC...")
        smc_signals = analyze(df)
        print(f"   ✅ Análisis SMC completado")

        # Contar señales disponibles
        signal_counts = {}
        for signal_type, data in smc_signals.items():
            if data is not None and hasattr(data, '__len__'):
                if hasattr(data, 'notna'):
                    # Es un DataFrame con columnas de señales
                    if signal_type == 'fvg' and 'FVG' in data.columns:
                        signal_counts['FVG'] = int(data['FVG'].notna().sum())
                    elif signal_type == 'orderblocks' and 'OB' in data.columns:
                        signal_counts['Order Blocks'] = int(data['OB'].notna().sum())
                    elif signal_type == 'bos_choch':
                        bos_count = int(data['BOS'].notna().sum()) if 'BOS' in data.columns else 0
                        choch_count = int(data['CHOCH'].notna().sum()) if 'CHOCH' in data.columns else 0
                        signal_counts['BOS/CHoCH'] = bos_count + choch_count
                    elif signal_type == 'liquidity' and 'Liquidity' in data.columns:
                        signal_counts['Liquidity'] = int(data['Liquidity'].notna().sum())
                    elif signal_type == 'swing_highs_lows' and 'HighLow' in data.columns:
                        signal_counts['Swings'] = int(data['HighLow'].notna().sum())

        print(f"   📊 Señales detectadas:")
        for signal_type, count in signal_counts.items():
            print(f"      • {signal_type}: {count}")

        # 3. Generar señales de trading
        print("\n⚡ Generando señales de trading...")
        trade_engine = SMCTradeEngine(
            min_rr=2.0,
            max_risk_percent=2.0
        )

        trade_signals = trade_engine.analyze_for_entry(df, smc_signals)
        signal_count = len(trade_signals)
        print(f"   ✅ Señales de trading generadas: {signal_count}")

        if signal_count > 0:
            # Mostrar detalles de las primeras señales
            print(f"   📋 Primeras señales generadas:")
            for i, signal in enumerate(trade_signals[:3]):
                print(f"      {i+1}. {signal.signal_type} en ${signal.entry_price:.2f} "
                      f"(RR: {signal.risk_reward_ratio:.1f})")

        # 4. Ejecutar backtesting usando la función de utilidad
        print("\n🎯 EJECUTANDO BACKTESTING...")

        # Configuración del backtest
        initial_capital = 10000
        risk_per_trade = 1.5  # 1.5% por trade

        print(f"   💰 Capital inicial: ${initial_capital:,.2f}")
        print(f"   ⚠️ Riesgo por trade: {risk_per_trade}%")

        # Ejecutar backtest usando la función de integración
        backtest_result = run_backtest_analysis(
            df=df,
            signals=trade_signals,  # Directamente la lista
            initial_capital=initial_capital,
            risk_per_trade=risk_per_trade
        )

        if not backtest_result['success']:
            print(f"   ❌ Error en backtesting: {backtest_result.get('report', 'Error desconocido')}")
            return False

        results = backtest_result['results']

        # 5. Mostrar resultados del backtesting
        print(f"\n📈 RESULTADOS DEL BACKTESTING:")
        print(f"   📊 Total de trades: {results.total_trades}")
        print(f"   ✅ Trades ganadores: {results.winning_trades}")
        print(f"   ❌ Trades perdedores: {results.losing_trades}")
        print(f"   ⚖️ Trades breakeven: {results.breakeven_trades}")

        if results.total_trades > 0:
            win_rate = (results.winning_trades / results.total_trades) * 100
            print(f"   🎯 Win Rate: {win_rate:.1f}%")
            print(f"   💰 Capital final: ${results.final_capital:,.2f}")
            print(f"   📈 Retorno total: {results.total_return:.2f}%")
            print(f"   📊 Máximo Drawdown: {results.max_drawdown:.2f}%")
            print(f"   ⚡ Sharpe Ratio: {results.sharpe_ratio:.2f}")
            print(f"   🔢 Profit Factor: {results.profit_factor:.2f}")

            # Mostrar detalles de algunos trades
            if len(results.trades) > 0:
                print(f"\n📋 DETALLES DE TRADES (primeros 5):")
                for i, trade in enumerate(results.trades[:5]):
                    result_icon = "✅" if trade.result.value == "WIN" else "❌" if trade.result.value == "LOSS" else "⚖️"
                    print(f"   {i+1}. {result_icon} {trade.signal_type} | "
                          f"Entry: ${trade.entry_price:.2f} | "
                          f"Exit: ${trade.exit_price:.2f} | "
                          f"P&L: {trade.pnl_percent:.2f}% | "
                          f"RR: {trade.risk_reward_achieved:.1f}")

        # 6. Probar generación de reporte
        print(f"\n📄 GENERANDO REPORTE...")

        backtester = backtest_result['backtester']
        report = backtester.generate_report()

        # Mostrar una parte del reporte
        report_lines = report.split('\n')
        print(f"   📋 Reporte generado ({len(report_lines)} líneas)")
        print(f"   📄 Primeras líneas del reporte:")
        for line in report_lines[:10]:
            if line.strip():
                print(f"      {line}")

        # 7. Verificar gráfico de performance
        print(f"\n📊 GENERANDO GRÁFICO DE PERFORMANCE...")

        chart = backtest_result['chart']
        print(f"   📈 Gráfico generado: {type(chart).__name__}")

        if hasattr(chart, 'data') and len(chart.data) > 0:
            print(f"   📊 Trazas en el gráfico: {len(chart.data)}")
            print(f"   ✅ Gráfico de performance listo para mostrar")
        else:
            print(f"   ⚠️ Gráfico generado pero puede estar vacío")

        # 8. Resumen final
        print(f"\n" + "="*70)
        print(f"📋 RESUMEN DE LA PRUEBA")
        print(f"="*70)

        success_indicators = [
            ("Datos de mercado", True),
            ("Análisis SMC", True),
            ("Señales de trading", signal_count > 0),
            ("Backtesting", backtest_result['success']),
            ("Resultados", results.total_trades >= 0),
            ("Reporte", len(report) > 100),
            ("Gráfico", hasattr(chart, 'data'))
        ]

        all_success = all(indicator[1] for indicator in success_indicators)

        print(f"✅ Estado de componentes:")
        for component, success in success_indicators:
            status = "✅" if success else "❌"
            print(f"   {status} {component}")

        print(f"\n🎯 RESULTADO FINAL: {'✅ ÉXITO COMPLETO' if all_success else '⚠️ PARCIALMENTE EXITOSO'}")

        if results.total_trades > 0:
            print(f"🔥 RENDIMIENTO: {results.total_return:.2f}% en {results.total_trades} trades")
        else:
            print(f"ℹ️ No se generaron trades (normal en períodos cortos)")

        return all_success

    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba del backtester SMC...")
    success = test_smc_backtester()

    if success:
        print(f"\n🎉 ¡PRUEBA COMPLETADA CON ÉXITO!")
        print(f"   El backtester SMC está funcionando correctamente")
        print(f"   Listo para uso en el dashboard Streamlit")
    else:
        print(f"\n⚠️ PRUEBA COMPLETADA CON PROBLEMAS")
        print(f"   Revisar errores arriba para debugging")
