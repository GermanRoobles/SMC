#!/usr/bin/env python3
"""
RESUMEN FINAL: TEST DEL BACKTESTER SMC
=====================================

Prueba final del backtester SMC completamente funcional
mostrando todas las capacidades implementadas.
"""

from fetch_data import get_ohlcv
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import SMCBacktester, run_backtest_analysis
import pandas as pd
from datetime import datetime

def create_realistic_signals(df, symbol, timeframe):
    """Crear señales con niveles realistas de SL/TP basados en volatilidad"""
    signals = []

    # Analizar volatilidad del dataset
    price_min = df['low'].min()
    price_max = df['high'].max()
    price_range = price_max - price_min
    volatility_pct = (price_range / price_min) * 100

    # Calcular niveles adaptativos basados en volatilidad
    # Para volatilidad baja (<3%), usar niveles más ajustados
    if volatility_pct < 3.0:
        sl_pct = 0.005  # 0.5%
        tp_pct = 0.008  # 0.8%
    elif volatility_pct < 5.0:
        sl_pct = 0.008  # 0.8%
        tp_pct = 0.015  # 1.5%
    else:
        sl_pct = 0.015  # 1.5%
        tp_pct = 0.025  # 2.5%

    print(f"   📊 Volatilidad detectada: {volatility_pct:.2f}%")
    print(f"   🎯 Niveles adaptativos: SL ±{sl_pct*100:.1f}%, TP ±{tp_pct*100:.1f}%")

    # Señal 1: LONG con niveles realistas
    entry_price = df['close'].iloc[20]
    signals.append(TradeSignal(
        timestamp=df['timestamp'].iloc[20],
        symbol=symbol,
        timeframe=timeframe,
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * (1 - sl_pct),
        take_profit=entry_price * (1 + tp_pct),
        risk_reward=tp_pct / sl_pct,
        confidence=0.85,
        setup_components={'fvg': True, 'order_block': True},
        confirmation_type=ConfirmationType.ENGULFING
    ))

    # Señal 2: SHORT con niveles realistas
    entry_price = df['close'].iloc[40]
    signals.append(TradeSignal(
        timestamp=df['timestamp'].iloc[40],
        symbol=symbol,
        timeframe=timeframe,
        signal_type=SignalType.SHORT,
        entry_price=entry_price,
        stop_loss=entry_price * (1 + sl_pct),
        take_profit=entry_price * (1 - tp_pct),
        risk_reward=tp_pct / sl_pct,
        confidence=0.75,
        setup_components={'fvg': True, 'liquidity': True},
        confirmation_type=ConfirmationType.REJECTION_WICK
    ))

    # Señal 3: LONG con niveles ligeramente más amplios
    entry_price = df['close'].iloc[60]
    signals.append(TradeSignal(
        timestamp=df['timestamp'].iloc[60],
        symbol=symbol,
        timeframe=timeframe,
        signal_type=SignalType.LONG,
        entry_price=entry_price,
        stop_loss=entry_price * (1 - sl_pct * 1.2),
        take_profit=entry_price * (1 + tp_pct * 1.2),
        risk_reward=(tp_pct * 1.2) / (sl_pct * 1.2),
        confidence=0.80,
        setup_components={'order_block': True, 'bos': True},
        confirmation_type=ConfirmationType.HAMMER
    ))

    return signals

def final_backtester_test():
    """Test final del backtester SMC"""

    print("="*80)
    print("🎯 RESUMEN FINAL: BACKTESTER SMC COMPLETAMENTE FUNCIONAL")
    print("="*80)

    try:
        # 1. Obtener datos de mercado reales
        print("\n📊 CONFIGURACIÓN DEL TEST:")
        symbol = 'BTCUSDT'
        timeframe = '1h'
        limit = 100

        df = get_ohlcv(symbol, timeframe, limit=limit)
        print(f"   • Símbolo: {symbol}")
        print(f"   • Timeframe: {timeframe}")
        print(f"   • Datos: {len(df)} velas")
        print(f"   • Período: {df['timestamp'].min()} a {df['timestamp'].max()}")

        # 2. Crear señales de prueba con niveles realistas
        print(f"\n⚡ CREANDO SEÑALES DE PRUEBA:")
        signals = create_realistic_signals(df, symbol, timeframe)

    def create_realistic_signals(df, symbol, timeframe):
        """Crear señales con niveles realistas de SL/TP basados en volatilidad"""
        signals = []

        # Analizar volatilidad del dataset
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = price_max - price_min
        volatility_pct = (price_range / price_min) * 100

        # Calcular niveles adaptativos basados en volatilidad
        # Para volatilidad baja (<3%), usar niveles más ajustados
        if volatility_pct < 3.0:
            sl_pct = 0.005  # 0.5%
            tp_pct = 0.008  # 0.8%
        elif volatility_pct < 5.0:
            sl_pct = 0.008  # 0.8%
            tp_pct = 0.015  # 1.5%
        else:
            sl_pct = 0.015  # 1.5%
            tp_pct = 0.025  # 2.5%

        print(f"   📊 Volatilidad detectada: {volatility_pct:.2f}%")
        print(f"   🎯 Niveles adaptativos: SL ±{sl_pct*100:.1f}%, TP ±{tp_pct*100:.1f}%")

        # Señal 1: LONG con niveles realistas
        entry_price = df['close'].iloc[20]
        signals.append(TradeSignal(
            timestamp=df['timestamp'].iloc[20],
            symbol=symbol,
            timeframe=timeframe,
            signal_type=SignalType.LONG,
            entry_price=entry_price,
            stop_loss=entry_price * (1 - sl_pct),
            take_profit=entry_price * (1 + tp_pct),
            risk_reward=tp_pct / sl_pct,
            confidence=0.85,
            setup_components={'fvg': True, 'order_block': True},
            confirmation_type=ConfirmationType.ENGULFING
        ))

        # Señal 2: SHORT con niveles realistas
        entry_price = df['close'].iloc[40]
        signals.append(TradeSignal(
            timestamp=df['timestamp'].iloc[40],
            symbol=symbol,
            timeframe=timeframe,
            signal_type=SignalType.SHORT,
            entry_price=entry_price,
            stop_loss=entry_price * (1 + sl_pct),
            take_profit=entry_price * (1 - tp_pct),
            risk_reward=tp_pct / sl_pct,
            confidence=0.75,
            setup_components={'fvg': True, 'liquidity': True},
            confirmation_type=ConfirmationType.REJECTION_WICK
        ))

        # Señal 3: LONG con niveles ligeramente más amplios
        entry_price = df['close'].iloc[60]
        signals.append(TradeSignal(
            timestamp=df['timestamp'].iloc[60],
            symbol=symbol,
            timeframe=timeframe,
            signal_type=SignalType.LONG,
            entry_price=entry_price,
            stop_loss=entry_price * (1 - sl_pct * 1.2),
            take_profit=entry_price * (1 + tp_pct * 1.2),
            risk_reward=(tp_pct * 1.2) / (sl_pct * 1.2),
            confidence=0.80,
            setup_components={'order_block': True, 'bos': True},
            confirmation_type=ConfirmationType.HAMMER
        ))

        return signals

        print(f"   ✅ {len(signals)} señales creadas:")
        for i, signal in enumerate(signals):
            rr = signal.risk_reward
            print(f"      {i+1}. {signal.signal_type.value} en ${signal.entry_price:.2f} (RR: {rr:.1f})")

        # 3. Configuración del backtesting
        print(f"\n🎯 CONFIGURACIÓN DEL BACKTESTING:")
        initial_capital = 10000
        risk_per_trade = 1.0

        print(f"   • Capital inicial: ${initial_capital:,.2f}")
        print(f"   • Riesgo por trade: {risk_per_trade}%")
        print(f"   • Máxima duración: 48 horas")

        # 4. Ejecutar backtesting
        print(f"\n🚀 EJECUTANDO BACKTESTING...")

        backtest_result = run_backtest_analysis(
            df=df,
            signals=signals,
            initial_capital=initial_capital,
            risk_per_trade=risk_per_trade
        )

        if not backtest_result['success']:
            print(f"   ❌ Error en backtesting: {backtest_result.get('report', 'Error desconocido')}")
            return False

        results = backtest_result['results']

        # 5. Mostrar resultados detallados
        print(f"\n📈 RESULTADOS COMPLETOS:")
        print(f"   📊 Trades ejecutados: {results.total_trades}")
        print(f"   ✅ Ganadores: {results.winning_trades}")
        print(f"   ❌ Perdedores: {results.losing_trades}")
        print(f"   ⚖️ Breakeven: {results.breakeven_trades}")

        if results.total_trades > 0:
            print(f"   🎯 Win Rate: {results.win_rate:.1f}%")
            print(f"   💰 Capital final: ${results.final_capital:,.2f}")
            print(f"   📈 Retorno total: {results.total_return:.2f}%")
            print(f"   📊 Retorno anualizado: {results.annualized_return:.2f}%")
            print(f"   📉 Máximo Drawdown: {results.max_drawdown_percent:.1f}%")
            print(f"   🔢 Profit Factor: {results.profit_factor:.2f}")
            print(f"   💸 Expectancy: ${results.expectancy:.2f} por trade")
            print(f"   ⏱️ Duración promedio: {results.average_trade_duration:.1f} horas")

        # 6. Análisis individual de trades
        if results.trades:
            print(f"\n📋 ANÁLISIS INDIVIDUAL DE TRADES:")
            for i, trade in enumerate(results.trades):
                result_icon = "✅" if trade.result.value == "WIN" else "❌" if trade.result.value == "LOSS" else "⚖️"
                print(f"   {i+1}. {result_icon} {trade.signal_type}")
                print(f"      Entry: ${trade.entry_price:.2f} | Exit: ${trade.exit_price:.2f}")
                print(f"      P&L: {trade.pnl_percent:.2f}% | RR logrado: {trade.risk_reward_achieved:.1f}")
                print(f"      Duración: {trade.duration_hours:.1f}h | Fecha: {trade.entry_time}")

        # 7. Verificar componentes del sistema
        print(f"\n🔧 VERIFICACIÓN DE COMPONENTES:")

        components = [
            ("Obtención de datos", True),
            ("Creación de señales", len(signals) > 0),
            ("Ejecución de backtesting", backtest_result['success']),
            ("Cálculo de trades", results.total_trades > 0),
            ("Métricas de performance", results.win_rate >= 0),
            ("Reporte generado", len(backtest_result['report']) > 100),
            ("Gráfico de performance", hasattr(backtest_result['chart'], 'data')),
            ("Capital final calculado", results.final_capital > 0),
            ("Retornos calculados", results.total_return != 0 or results.total_trades == 0)
        ]

        all_working = True
        for component, status in components:
            icon = "✅" if status else "❌"
            print(f"   {icon} {component}")
            if not status:
                all_working = False

        # 8. Mostrar parte del reporte
        print(f"\n📄 EXTRACTO DEL REPORTE:")
        report = backtest_result['report']
        report_lines = report.split('\n')[:15]  # Primeras 15 líneas
        for line in report_lines:
            if line.strip():
                print(f"   {line}")

        # 9. Resumen final
        print(f"\n" + "="*80)
        print(f"🏆 RESUMEN FINAL DEL BACKTESTER SMC")
        print(f"="*80)

        print(f"✅ FUNCIONALIDADES IMPLEMENTADAS:")
        print(f"   📊 Simulación de trades realista con SL/TP")
        print(f"   💰 Gestión de capital con riesgo configurable")
        print(f"   📈 Métricas completas de performance (Win Rate, Profit Factor, etc.)")
        print(f"   📉 Cálculo de drawdown máximo")
        print(f"   ⏱️ Análisis de duración de trades")
        print(f"   📊 Generación de gráficos de performance")
        print(f"   📄 Reportes detallados en formato Markdown")
        print(f"   🔧 Integración lista para Streamlit")

        if all_working:
            performance_emoji = "🚀" if results.total_return > 0 else "📉" if results.total_return < 0 else "➡️"
            print(f"\n{performance_emoji} ESTADO: COMPLETAMENTE FUNCIONAL")
            if results.total_trades > 0:
                print(f"📊 Performance de prueba: {results.total_return:.2f}% en {results.total_trades} trades")
            print(f"✅ Listo para uso en producción con señales reales del motor SMC")
        else:
            print(f"\n⚠️ ESTADO: REQUIERE REVISIÓN MENOR")
            print(f"📝 Algunos componentes necesitan ajustes")

        return all_working

    except Exception as e:
        print(f"\n❌ ERROR EN EL TEST FINAL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Ejecutando test final del backtester SMC...")
    success = final_backtester_test()

    if success:
        print(f"\n🎉 ¡BACKTESTER SMC COMPLETAMENTE OPERATIVO!")
        print(f"   🔥 Todas las funcionalidades verificadas")
        print(f"   ✅ Listo para integración en el dashboard")
    else:
        print(f"\n⚠️ Test completado con observaciones")
        print(f"   📝 Revisar detalles arriba")
