#!/usr/bin/env python3
"""
TEST DE SEÑALES SMC PARA BACKTESTING
====================================

Test específico para verificar que se generan señales SMC tradicionales
correctamente para backtesting.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Importar módulos del proyecto
try:
    from fetch_data import get_ohlcv
    from smc_analysis import analyze
    from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
    print("✅ Todos los módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def generate_smc_signals_for_backtesting(df: pd.DataFrame, smc_analysis: Dict) -> List[TradeSignal]:
    """
    Generar señales SMC tradicionales para backtesting
    
    Args:
        df: DataFrame con datos OHLC
        smc_analysis: Análisis SMC
    
    Returns:
        Lista de TradeSignal para backtesting
    """
    signals = []
    
    try:
        # Generar señales basadas en FVG
        if 'fvg' in smc_analysis and not smc_analysis['fvg'].empty:
            fvg_data = smc_analysis['fvg']
            print(f"📊 FVG detectados: {len(fvg_data)}")
            
            for i, row in fvg_data.iterrows():
                if pd.notna(row['FVG']) and i < len(df) - 10:
                    # Crear señal basada en FVG
                    entry_price = df.iloc[i]['close']
                    if row['FVG'] == 1:  # Bullish FVG
                        signal_type = SignalType.LONG
                        stop_loss = entry_price * 0.98
                        take_profit = entry_price * 1.04
                    else:  # Bearish FVG
                        signal_type = SignalType.SHORT
                        stop_loss = entry_price * 1.02
                        take_profit = entry_price * 0.96
                    
                    trade_signal = TradeSignal(
                        timestamp=df.iloc[i]['timestamp'],
                        symbol="BTCUSDT",
                        timeframe="15m",
                        signal_type=signal_type,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=2.0,
                        confidence=0.7,
                        setup_components={'fvg_generated': True},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    signals.append(trade_signal)
                    print(f"   ✅ FVG {i}: {signal_type.value} @ ${entry_price:.2f}")
        
        # Generar señales basadas en Order Blocks
        if 'orderblocks' in smc_analysis and not smc_analysis['orderblocks'].empty:
            ob_data = smc_analysis['orderblocks']
            print(f"📊 Order Blocks detectados: {len(ob_data)}")
            
            for i, row in ob_data.iterrows():
                if i < len(df) - 10:
                    entry_price = df.iloc[i]['close']
                    # Determinar dirección basada en el contexto
                    if i > 0 and df.iloc[i]['close'] > df.iloc[i-1]['close']:
                        signal_type = SignalType.LONG
                        stop_loss = entry_price * 0.97
                        take_profit = entry_price * 1.06
                    else:
                        signal_type = SignalType.SHORT
                        stop_loss = entry_price * 1.03
                        take_profit = entry_price * 0.94
                    
                    trade_signal = TradeSignal(
                        timestamp=df.iloc[i]['timestamp'],
                        symbol="BTCUSDT",
                        timeframe="15m",
                        signal_type=signal_type,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=2.0,
                        confidence=0.6,
                        setup_components={'ob_generated': True},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    signals.append(trade_signal)
                    print(f"   ✅ OB {i}: {signal_type.value} @ ${entry_price:.2f}")
        
        # Generar señales basadas en swings
        if 'swing_highs_lows' in smc_analysis and not smc_analysis['swing_highs_lows'].empty:
            swing_data = smc_analysis['swing_highs_lows']
            print(f"📊 Swings detectados: {len(swing_data)}")
            
            for i, row in swing_data.iterrows():
                if i < len(df) - 10:
                    entry_price = df.iloc[i]['close']
                    # Señales basadas en swings
                    if row.get('swing_high', False):
                        signal_type = SignalType.SHORT
                        stop_loss = entry_price * 1.02
                        take_profit = entry_price * 0.96
                    elif row.get('swing_low', False):
                        signal_type = SignalType.LONG
                        stop_loss = entry_price * 0.98
                        take_profit = entry_price * 1.04
                    else:
                        continue
                    
                    trade_signal = TradeSignal(
                        timestamp=df.iloc[i]['timestamp'],
                        symbol="BTCUSDT",
                        timeframe="15m",
                        signal_type=signal_type,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=2.0,
                        confidence=0.5,
                        setup_components={'swing_generated': True},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    signals.append(trade_signal)
                    print(f"   ✅ Swing {i}: {signal_type.value} @ ${entry_price:.2f}")
        
        # Generar señales adicionales basadas en patrones de precio
        print("📊 Generando señales adicionales basadas en patrones...")
        for i in range(20, len(df) - 20, 10):  # Cada 10 velas
            current_price = df.iloc[i]['close']
            prev_price = df.iloc[i-1]['close']
            
            # Patrón simple: reversión después de movimiento fuerte
            if abs(current_price - prev_price) / prev_price > 0.01:  # Movimiento > 1%
                if current_price > prev_price:
                    signal_type = SignalType.LONG
                    stop_loss = current_price * 0.99
                    take_profit = current_price * 1.03
                else:
                    signal_type = SignalType.SHORT
                    stop_loss = current_price * 1.01
                    take_profit = current_price * 0.97
                
                trade_signal = TradeSignal(
                    timestamp=df.iloc[i]['timestamp'],
                    symbol="BTCUSDT",
                    timeframe="15m",
                    signal_type=signal_type,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward=1.5,
                    confidence=0.4,
                    setup_components={'pattern_generated': True},
                    confirmation_type=ConfirmationType.ENGULFING
                )
                signals.append(trade_signal)
                print(f"   ✅ Pattern {i}: {signal_type.value} @ ${current_price:.2f}")
        
        return signals
        
    except Exception as e:
        print(f"❌ Error generando señales SMC: {e}")
        return []

def test_smc_backtesting():
    """Test completo de backtesting con señales SMC"""
    print("🚀 TEST DE BACKTESTING CON SEÑALES SMC")
    print("=" * 60)
    
    try:
        # 1. Obtener datos
        print("\n📊 1. Obteniendo datos...")
        df = get_ohlcv("BTCUSDT", "15m", limit=300)
        
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
        
        # 3. Generar señales SMC
        print("\n⚡ 3. Generando señales SMC...")
        signals = generate_smc_signals_for_backtesting(df, smc_analysis)
        
        print(f"✅ {len(signals)} señales SMC generadas")
        
        if not signals:
            print("⚠️ No se generaron señales SMC")
            return False
        
        # 4. Test de backtesting
        print("\n📈 4. Ejecutando backtesting...")
        from smc_backtester import run_backtest_analysis
        
        backtest_results = run_backtest_analysis(
            df, signals, 10000, 1.0
        )
        
        if backtest_results['success']:
            results = backtest_results['results']
            print(f"✅ Backtesting completado:")
            print(f"   - Total trades: {results.total_trades}")
            print(f"   - Win rate: {results.win_rate:.1f}%")
            print(f"   - Profit factor: {results.profit_factor:.2f}")
            print(f"   - Total PnL: ${results.total_pnl:.2f}")
            print(f"   - Max drawdown: {results.max_drawdown_percent:.1f}%")
            
            # Mostrar detalles de trades
            if results.trades:
                print(f"\n📋 Detalles de trades:")
                for i, trade in enumerate(results.trades[:5]):  # Mostrar primeros 5
                    print(f"   {i+1}. {trade.signal_type} @ ${trade.entry_price:.2f} -> {trade.result.value if trade.result else 'Pendiente'}")
        else:
            print("❌ Error en backtesting")
            return False
        
        print("\n🎉 TEST DE BACKTESTING SMC COMPLETADO EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smc_backtesting()
    sys.exit(0 if success else 1)
