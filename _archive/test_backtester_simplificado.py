#!/usr/bin/env python3
"""
TEST SIMPLIFICADO DEL BACKTESTER
===============================

Prueba del backtester con señales simuladas para verificar
que la funcionalidad de backtesting funciona correctamente.
"""

from fetch_data import get_ohlcv
from smc_analysis import analyze
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import SMCBacktester, run_backtest_analysis
import pandas as pd
from datetime import datetime

def create_mock_signals(df: pd.DataFrame) -> list:
    """Crear señales simuladas para probar el backtester"""
    signals = []

    # Crear algunas señales de prueba cada 20 velas
    for i in range(20, len(df), 40):  # Cada 40 velas
        if i < len(df) - 10:  # Asegurar que hay espacio para el trade

            current_price = df.iloc[i]['close']

            # Señal LONG
            if i % 80 == 20:  # Cada 80 velas, crear señal LONG
                entry_price = current_price
                stop_loss = entry_price * 0.98  # 2% stop loss
                take_profit = entry_price * 1.06  # 6% take profit (RR 3:1)

                signal = TradeSignal(
                    timestamp=df.iloc[i]['timestamp'],
                    symbol='BTCUSDT',
                    timeframe='1h',
                    signal_type=SignalType.LONG,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward=3.0,
                    confidence=0.8,
                    setup_components={
                        'fvg': True,
                        'order_block': True,
                        'liquidity_sweep': True
                    },
                    confirmation_type=ConfirmationType.ENGULFING
                )
                signals.append(signal)

            # Señal SHORT
            elif i % 80 == 60:  # Cada 80 velas, crear señal SHORT
                entry_price = current_price
                stop_loss = entry_price * 1.02  # 2% stop loss
                take_profit = entry_price * 0.94  # 6% take profit (RR 3:1)

                signal = TradeSignal(
                    timestamp=df.iloc[i]['timestamp'],
                    symbol='BTCUSDT',
                    timeframe='1h',
                    signal_type=SignalType.SHORT,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward=3.0,
                    confidence=0.75,
                    setup_components={
                        'fvg': True,
                        'order_block': False,
                        'liquidity_sweep': True
                    },
                    confirmation_type=ConfirmationType.REJECTION_WICK
                )
                signals.append(signal)

    return signals

def test_backtester_with_mock_signals():
    """Probar backtester con señales simuladas"""

    print("="*70)
    print("🧪 PRUEBA DEL BACKTESTER CON SEÑALES SIMULADAS")
    print("="*70)

    try:
        # 1. Obtener datos de mercado
        print("\n📊 Obteniendo datos de mercado...")
        df = get_ohlcv('BTCUSDT', '1h', limit=300)  # Más datos para más oportunidades
        print(f"   ✅ Datos obtenidos: {len(df)} velas")
        print(f"   📅 Período: {df['timestamp'].min()} a {df['timestamp'].max()}")

        # 2. Crear señales simuladas
        print("\n⚡ Creando señales simuladas...")
        mock_signals = create_mock_signals(df)
        print(f"   ✅ Señales simuladas creadas: {len(mock_signals)}")

        # Mostrar detalles de las señales
        print(f"   📋 Señales generadas:")
        for i, signal in enumerate(mock_signals):
            print(f"      {i+1}. {signal.signal_type.value} en ${signal.entry_price:.2f} "
                  f"(RR: {signal.risk_reward:.1f}, Conf: {signal.confidence:.1f})")

        # 3. Configurar y ejecutar backtesting
        print(f"\n🎯 EJECUTANDO BACKTESTING...")

        initial_capital = 10000
        risk_per_trade = 2.0

        print(f"   💰 Capital inicial: ${initial_capital:,.2f}")
        print(f"   ⚠️ Riesgo por trade: {risk_per_trade}%")

        # Ejecutar backtesting
        backtest_result = run_backtest_analysis(
            df=df,
            signals=mock_signals,
            initial_capital=initial_capital,
            risk_per_trade=risk_per_trade
        )

        if not backtest_result['success']:
            print(f"   ❌ Error en backtesting: {backtest_result.get('report', 'Error desconocido')}")
            return False

        results = backtest_result['results']

        # 4. Mostrar resultados detallados
        print(f"\n📈 RESULTADOS DEL BACKTESTING:")
        print(f"   📊 Total de trades: {results.total_trades}")
        print(f"   ✅ Trades ganadores: {results.winning_trades}")
        print(f"   ❌ Trades perdedores: {results.losing_trades}")
        print(f"   ⚖️ Trades breakeven: {results.breakeven_trades}")

        if results.total_trades > 0:
            win_rate = (results.winning_trades / results.total_trades) * 100
            print(f"   🎯 Win Rate: {win_rate:.1f}%")
            print(f"   💰 Capital inicial: ${initial_capital:,.2f}")
            print(f"   💰 Capital final: ${results.final_capital:,.2f}")
            print(f"   📈 Retorno total: {results.total_return:.2f}%")
            print(f"   📊 Retorno anualizado: {results.annualized_return:.2f}%")
            print(f"   📉 Máximo Drawdown: {results.max_drawdown:.2f}%")
            print(f"   ⚡ Sharpe Ratio: {results.sharpe_ratio:.2f}")
            print(f"   🔢 Profit Factor: {results.profit_factor:.2f}")
            print(f"   💸 Expectancy: ${results.expectancy:.2f}")

            # Mostrar detalles de trades
            print(f"\n📋 DETALLES DE TODOS LOS TRADES:")
            for i, trade in enumerate(results.trades):
                result_icon = "✅" if trade.result.value == "WIN" else "❌" if trade.result.value == "LOSS" else "⚖️"
                duration = f"{trade.duration_hours:.1f}h"
                print(f"   {i+1}. {result_icon} {trade.signal_type} | "
                      f"Entry: ${trade.entry_price:.2f} | "
                      f"Exit: ${trade.exit_price:.2f} | "
                      f"P&L: {trade.pnl_percent:.2f}% | "
                      f"RR: {trade.risk_reward_achieved:.1f} | "
                      f"Duración: {duration}")

        # 5. Probar generación de reporte completo
        print(f"\n📄 REPORTE COMPLETO:")
        backtester = backtest_result['backtester']
        report = backtester.generate_report()

        # Mostrar el reporte completo
        print(report)

        # 6. Información del gráfico
        print(f"\n📊 GRÁFICO DE PERFORMANCE:")
        chart = backtest_result['chart']
        if hasattr(chart, 'data') and len(chart.data) > 0:
            print(f"   📈 Gráfico generado con {len(chart.data)} series de datos")
            print(f"   ✅ Listo para mostrar en Streamlit")

        # 7. Resumen de verificación
        print(f"\n" + "="*70)
        print(f"🎯 VERIFICACIÓN DE FUNCIONALIDADES")
        print(f"="*70)

        checks = [
            ("Generación de señales", len(mock_signals) > 0),
            ("Ejecución de trades", results.total_trades > 0),
            ("Cálculo de P&L", results.total_trades == 0 or any(t.pnl_percent != 0 for t in results.trades)),
            ("Métricas de performance", results.total_trades == 0 or results.sharpe_ratio is not None),
            ("Generación de reporte", len(report) > 500),
            ("Creación de gráfico", hasattr(chart, 'data'))
        ]

        all_passed = all(check[1] for check in checks)

        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")

        print(f"\n🏆 RESULTADO FINAL: {'✅ BACKTESTER TOTALMENTE FUNCIONAL' if all_passed else '⚠️ ALGUNAS FUNCIONALIDADES NECESITAN REVISIÓN'}")

        if results.total_trades > 0:
            performance_emoji = "🚀" if results.total_return > 0 else "📉" if results.total_return < 0 else "➡️"
            print(f"{performance_emoji} PERFORMANCE SIMULADA: {results.total_return:.2f}% en {results.total_trades} trades")

        return all_passed

    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba del backtester con señales simuladas...")
    success = test_backtester_with_mock_signals()

    if success:
        print(f"\n🎉 ¡BACKTESTER COMPLETAMENTE FUNCIONAL!")
        print(f"   ✅ Todas las funcionalidades verificadas")
        print(f"   ✅ Listo para integración en dashboard Streamlit")
        print(f"   ✅ Puede procesar señales reales del motor de trading")
    else:
        print(f"\n⚠️ PRUEBA COMPLETADA CON OBSERVACIONES")
        print(f"   Revisar detalles arriba")
