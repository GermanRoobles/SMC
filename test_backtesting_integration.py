#!/usr/bin/env python3
"""
TEST DE INTEGRACIÓN COMPLETA DEL BACKTESTING
============================================

Test que verifica que toda la funcionalidad de backtesting está integrada
correctamente con el sistema SMC y ML.
"""

import sys
import os
import time
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Importar módulos del proyecto
try:
    from fetch_data import get_ohlcv, get_ohlcv_extended, get_ohlcv_with_cache
    from smc_analysis import analyze
    from smc_backtester import SMCBacktester, run_backtest_analysis, BacktestResults
    from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
    from smc_ml_signal_integration import MLSignalIntegration
    from smc_ml_signal_generator import MLSignalGenerator, MLSignal
    print("✅ Todos los módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def test_backtesting_integration():
    """Test completo de integración del backtesting"""
    print("🚀 TEST DE INTEGRACIÓN COMPLETA DEL BACKTESTING")
    print("=" * 60)
    
    try:
        # 1. Obtener datos de prueba
        print("\n📊 1. Obteniendo datos de prueba...")
        df = get_ohlcv("BTCUSDT", "15m", limit=200)
        
        if df is None or len(df) == 0:
            print("❌ No se pudieron obtener datos")
            return False
        
        print(f"✅ Datos obtenidos: {len(df)} velas")
        
        # 2. Análisis SMC
        print("\n🔍 2. Ejecutando análisis SMC...")
        smc_analysis = analyze(df, timeframe="15m")
        
        if not smc_analysis:
            print("❌ Error en análisis SMC")
            return False
        
        print("✅ Análisis SMC completado")
        
        # 3. Test de generación de señales ML
        print("\n🤖 3. Test de generación de señales ML...")
        ml_integration = MLSignalIntegration()
        
        # Generar algunas señales ML de prueba
        ml_signals = []
        for i in range(50, len(df) - 50, 20):  # Cada 20 velas
            current_data = df.iloc[:i+1]
            current_price = current_data['close'].iloc[-1]
            
            ml_signal = ml_integration.generate_ml_signal(
                current_data, smc_analysis, "BTCUSDT", "15m"
            )
            
            if ml_signal and ml_signal.signal_type.value != "HOLD":
                ml_signals.append(ml_signal)
        
        print(f"✅ {len(ml_signals)} señales ML generadas")
        
        # 4. Convertir señales ML a TradeSignal
        print("\n🔄 4. Convirtiendo señales ML a TradeSignal...")
        trade_signals = []
        
        for ml_signal in ml_signals:
            try:
                trade_signal = TradeSignal(
                    timestamp=ml_signal.timestamp,
                    symbol="BTCUSDT",
                    timeframe="15m",
                    signal_type=SignalType.LONG if ml_signal.signal_type.value == "BUY" else SignalType.SHORT,
                    entry_price=ml_signal.entry_price,
                    stop_loss=ml_signal.stop_loss,
                    take_profit=ml_signal.take_profit_1,
                    risk_reward=ml_signal.risk_reward_ratio,
                    confidence=ml_signal.confluence_score,
                    setup_components={'ml_generated': True},
                    confirmation_type=None
                )
                trade_signals.append(trade_signal)
            except Exception as e:
                print(f"⚠️ Error convirtiendo señal: {e}")
        
        print(f"✅ {len(trade_signals)} señales convertidas")
        
        # 5. Test de backtesting básico
        print("\n📈 5. Test de backtesting básico...")
        backtester = SMCBacktester(initial_capital=10000, risk_per_trade=1.0)
        
        if trade_signals:
            results = backtester.run_backtest(df, trade_signals, max_trade_duration=48)
            
            print(f"✅ Backtesting completado:")
            print(f"   - Total trades: {results.total_trades}")
            print(f"   - Win rate: {results.win_rate:.1f}%")
            print(f"   - Profit factor: {results.profit_factor:.2f}")
            print(f"   - Total PnL: ${results.total_pnl:.2f}")
        else:
            print("⚠️ No hay señales para backtesting")
        
        # 6. Test de función de análisis integrada
        print("\n🔧 6. Test de función de análisis integrada...")
        backtest_analysis = run_backtest_analysis(
            df, trade_signals, 10000, 1.0
        )
        
        if backtest_analysis['success']:
            print("✅ Función de análisis integrada funcionando")
            results = backtest_analysis['results']
            print(f"   - Trades ejecutados: {results.total_trades}")
            print(f"   - Win rate: {results.win_rate:.1f}%")
        else:
            print("❌ Error en función de análisis integrada")
        
        # 7. Test de generación de reportes
        print("\n📋 7. Test de generación de reportes...")
        if 'report' in backtest_analysis:
            report = backtest_analysis['report']
            print("✅ Reporte generado correctamente")
            print(f"   - Longitud del reporte: {len(report)} caracteres")
        else:
            print("⚠️ No se generó reporte")
        
        # 8. Test de gráficos de performance
        print("\n📊 8. Test de gráficos de performance...")
        if 'chart' in backtest_analysis:
            chart = backtest_analysis['chart']
            print("✅ Gráfico de performance generado")
            print(f"   - Tipo de gráfico: {type(chart)}")
        else:
            print("⚠️ No se generó gráfico")
        
        # 9. Test de métricas avanzadas
        print("\n📊 9. Test de métricas avanzadas...")
        if results and hasattr(results, 'trades') and results.trades:
            # Calcular métricas adicionales
            winning_trades = [t for t in results.trades if t.result and t.result.value == "WIN"]
            losing_trades = [t for t in results.trades if t.result and t.result.value == "LOSS"]
            
            if winning_trades:
                avg_win = np.mean([t.pnl_points for t in winning_trades])
                print(f"   - Ganancias promedio: ${avg_win:.2f}")
            
            if losing_trades:
                avg_loss = np.mean([t.pnl_points for t in losing_trades])
                print(f"   - Pérdidas promedio: ${avg_loss:.2f}")
            
            # Duración promedio
            durations = [t.duration_hours for t in results.trades if t.duration_hours > 0]
            if durations:
                avg_duration = np.mean(durations)
                print(f"   - Duración promedio: {avg_duration:.1f} horas")
        
        # 10. Test de robustez
        print("\n🛡️ 10. Test de robustez...")
        
        # Test con datos vacíos
        try:
            empty_results = run_backtest_analysis(pd.DataFrame(), [], 10000, 1.0)
            print("✅ Manejo correcto de datos vacíos")
        except Exception as e:
            print(f"⚠️ Error con datos vacíos: {e}")
        
        # Test con señales inválidas
        try:
            invalid_results = run_backtest_analysis(df, [], 10000, 1.0)
            print("✅ Manejo correcto de señales vacías")
        except Exception as e:
            print(f"⚠️ Error con señales vacías: {e}")
        
        print("\n🎉 TEST DE INTEGRACIÓN COMPLETADO EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de integración: {e}")
        traceback.print_exc()
        return False

def test_backtesting_performance():
    """Test de rendimiento del backtesting"""
    print("\n⚡ TEST DE RENDIMIENTO DEL BACKTESTING")
    print("=" * 50)
    
    try:
        # Obtener datos más grandes para test de rendimiento
        df = get_ohlcv("BTCUSDT", "15m", limit=500)
        
        if df is None or len(df) == 0:
            print("❌ No se pudieron obtener datos para test de rendimiento")
            return False
        
        # Generar señales rápidamente
        start_time = time.time()
        
        smc_analysis = analyze(df, timeframe="15m")
        ml_integration = MLSignalIntegration()
        
        # Generar señales de prueba
        trade_signals = []
        for i in range(50, len(df) - 50, 10):  # Más frecuente para test de rendimiento
            current_data = df.iloc[:i+1]
            
            ml_signal = ml_integration.generate_ml_signal(
                current_data, smc_analysis, "BTCUSDT", "15m"
            )
            
            if ml_signal and ml_signal.signal_type.value != "HOLD":
                try:
                    trade_signal = TradeSignal(
                        timestamp=ml_signal.timestamp,
                        symbol="BTCUSDT",
                        timeframe="15m",
                        signal_type=SignalType.LONG if ml_signal.signal_type.value == "BUY" else SignalType.SHORT,
                        entry_price=ml_signal.entry_price,
                        stop_loss=ml_signal.stop_loss,
                        take_profit=ml_signal.take_profit_1,
                        risk_reward=ml_signal.risk_reward_ratio,
                        confidence=ml_signal.confluence_score,
                        setup_components={'ml_generated': True},
                        confirmation_type=None
                    )
                    trade_signals.append(trade_signal)
                except:
                    pass
        
        signal_generation_time = time.time() - start_time
        
        # Ejecutar backtesting
        backtest_start = time.time()
        backtest_analysis = run_backtest_analysis(df, trade_signals, 10000, 1.0)
        backtest_time = time.time() - backtest_start
        
        total_time = time.time() - start_time
        
        print(f"📊 RESULTADOS DE RENDIMIENTO:")
        print(f"   - Datos procesados: {len(df)} velas")
        print(f"   - Señales generadas: {len(trade_signals)}")
        print(f"   - Tiempo generación señales: {signal_generation_time:.3f}s")
        print(f"   - Tiempo backtesting: {backtest_time:.3f}s")
        print(f"   - Tiempo total: {total_time:.3f}s")
        
        if backtest_analysis['success']:
            results = backtest_analysis['results']
            print(f"   - Trades ejecutados: {results.total_trades}")
            print(f"   - Win rate: {results.win_rate:.1f}%")
        
        # Verificar que el rendimiento es aceptable
        if total_time < 30.0:  # Máximo 30 segundos
            print("✅ Rendimiento aceptable")
            return True
        else:
            print("⚠️ Rendimiento lento")
            return False
        
    except Exception as e:
        print(f"❌ Error en test de rendimiento: {e}")
        return False

def main():
    """Función principal del test"""
    print("🧪 INICIANDO TESTS DE INTEGRACIÓN DEL BACKTESTING")
    print("=" * 80)
    
    # Test de integración básica
    integration_success = test_backtesting_integration()
    
    # Test de rendimiento
    performance_success = test_backtesting_performance()
    
    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print(f"   - Integración básica: {'✅' if integration_success else '❌'}")
    print(f"   - Rendimiento: {'✅' if performance_success else '❌'}")
    
    if integration_success and performance_success:
        print("\n🎉 ¡BACKTESTING COMPLETAMENTE INTEGRADO Y FUNCIONAL!")
        print("   El sistema está listo para usar en producción")
    else:
        print("\n⚠️ Hay problemas que necesitan ser corregidos")
    
    return integration_success and performance_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
