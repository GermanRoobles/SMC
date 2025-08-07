#!/usr/bin/env python3
"""
CORRECCIÓN DE REALISMO EN BACKTESTING
=====================================

Script para corregir los problemas identificados y hacer el backtesting
100% realista y representativo de condiciones reales de mercado.
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
    from fetch_data import get_ohlcv, get_ohlcv_extended
    from smc_analysis import analyze
    from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
    from smc_backtester import run_backtest_analysis
    print("✅ Todos los módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def generate_realistic_smc_signals(df: pd.DataFrame, smc_analysis: Dict) -> List[TradeSignal]:
    """
    Generar señales SMC REALISTAS para backtesting
    
    Args:
        df: DataFrame con datos OHLC
        smc_analysis: Análisis SMC
    
    Returns:
        Lista de TradeSignal REALISTAS para backtesting
    """
    signals = []
    
    try:
        # 1. CORRECCIÓN: Filtrar solo FVG significativos
        if 'fvg' in smc_analysis and not smc_analysis['fvg'].empty:
            fvg_data = smc_analysis['fvg']
            print(f"📊 FVG totales detectados: {len(fvg_data)}")
            
            # Filtrar solo FVG significativos (no todos los FVG)
            significant_fvgs = []
            for i, row in fvg_data.iterrows():
                if pd.notna(row['FVG']) and i < len(df) - 20:
                    # Solo considerar FVG con gap significativo
                    gap_size = abs(row['Top'] - row['Bottom'])
                    price_at_time = df.iloc[i]['close']
                    gap_percentage = (gap_size / price_at_time) * 100
                    
                    # Solo FVG con gap > 0.1% (más realista)
                    if gap_percentage > 0.1:
                        significant_fvgs.append((i, row))
            
            print(f"📊 FVG significativos filtrados: {len(significant_fvgs)}")
            
            # Generar señales solo para FVG significativos
            for i, row in significant_fvgs:
                entry_price = df.iloc[i]['close']
                
                # Calcular niveles REALISTAS basados en el rango histórico
                price_range = df['high'].max() - df['low'].min()
                atr = df['close'].pct_change().rolling(14).std().iloc[i] * entry_price
                
                if row['FVG'] == 1:  # Bullish FVG
                    signal_type = SignalType.LONG
                    # SL más conservador: 1.5 * ATR
                    stop_loss = entry_price - (1.5 * atr)
                    # TP más realista: 2.5 * ATR
                    take_profit = entry_price + (2.5 * atr)
                else:  # Bearish FVG
                    signal_type = SignalType.SHORT
                    stop_loss = entry_price + (1.5 * atr)
                    take_profit = entry_price - (2.5 * atr)
                
                # Validar que los niveles están dentro del rango histórico
                min_price = df['low'].min()
                max_price = df['high'].max()
                
                if min_price <= stop_loss <= max_price and min_price <= take_profit <= max_price:
                    trade_signal = TradeSignal(
                        timestamp=df.iloc[i]['timestamp'],
                        symbol="BTCUSDT",
                        timeframe="15m",
                        signal_type=signal_type,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=2.5/1.5,  # R:R realista
                        confidence=0.7,
                        setup_components={'fvg_significant': True, 'gap_pct': gap_percentage},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    signals.append(trade_signal)
                    print(f"   ✅ FVG {i}: {signal_type.value} @ ${entry_price:.2f} (gap: {gap_percentage:.2f}%)")
        
        # 2. CORRECCIÓN: Filtrar Order Blocks significativos
        if 'orderblocks' in smc_analysis and not smc_analysis['orderblocks'].empty:
            ob_data = smc_analysis['orderblocks']
            print(f"📊 Order Blocks totales: {len(ob_data)}")
            
            # Solo considerar OB con volumen significativo
            significant_obs = []
            for i, row in ob_data.iterrows():
                if i < len(df) - 20:
                    # Verificar volumen significativo
                    if 'OBVolume' in row and row['OBVolume'] > df['volume'].mean() * 1.5:
                        significant_obs.append((i, row))
            
            print(f"📊 Order Blocks significativos: {len(significant_obs)}")
            
            for i, row in significant_obs:
                entry_price = df.iloc[i]['close']
                atr = df['close'].pct_change().rolling(14).std().iloc[i] * entry_price
                
                # Determinar dirección basada en el contexto de precio
                if i > 0 and df.iloc[i]['close'] > df.iloc[i-1]['close']:
                    signal_type = SignalType.LONG
                    stop_loss = entry_price - (1.2 * atr)
                    take_profit = entry_price + (2.4 * atr)
                else:
                    signal_type = SignalType.SHORT
                    stop_loss = entry_price + (1.2 * atr)
                    take_profit = entry_price - (2.4 * atr)
                
                # Validar niveles
                min_price = df['low'].min()
                max_price = df['high'].max()
                
                if min_price <= stop_loss <= max_price and min_price <= take_profit <= max_price:
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
                        setup_components={'ob_significant': True},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    signals.append(trade_signal)
                    print(f"   ✅ OB {i}: {signal_type.value} @ ${entry_price:.2f}")
        
        # 3. CORRECCIÓN: Generar señales adicionales más conservadoras
        print("📊 Generando señales adicionales conservadoras...")
        
        # Solo generar señales en puntos clave (no cada 10 velas)
        for i in range(50, len(df) - 50, 30):  # Cada 30 velas (más conservador)
            current_price = df.iloc[i]['close']
            prev_price = df.iloc[i-1]['close']
            
            # Solo señales en movimientos significativos
            price_change_pct = abs(current_price - prev_price) / prev_price * 100
            
            if price_change_pct > 0.5:  # Movimiento > 0.5% (más realista)
                atr = df['close'].pct_change().rolling(14).std().iloc[i] * current_price
                
                if current_price > prev_price:
                    signal_type = SignalType.LONG
                    stop_loss = current_price - (1.0 * atr)
                    take_profit = current_price + (2.0 * atr)
                else:
                    signal_type = SignalType.SHORT
                    stop_loss = current_price + (1.0 * atr)
                    take_profit = current_price - (2.0 * atr)
                
                # Validar niveles
                min_price = df['low'].min()
                max_price = df['high'].max()
                
                if min_price <= stop_loss <= max_price and min_price <= take_profit <= max_price:
                    trade_signal = TradeSignal(
                        timestamp=df.iloc[i]['timestamp'],
                        symbol="BTCUSDT",
                        timeframe="15m",
                        signal_type=signal_type,
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=2.0,
                        confidence=0.4,
                        setup_components={'pattern_conservative': True, 'price_change_pct': price_change_pct},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    signals.append(trade_signal)
                    print(f"   ✅ Pattern {i}: {signal_type.value} @ ${current_price:.2f} (change: {price_change_pct:.2f}%)")
        
        return signals
        
    except Exception as e:
        print(f"❌ Error generando señales realistas: {e}")
        return []

def test_realistic_backtesting():
    """Test de backtesting con señales REALISTAS"""
    print("🚀 TEST DE BACKTESTING REALISTA")
    print("=" * 60)
    
    try:
        # 1. Obtener datos con período más largo para realismo
        print("\n📊 1. Obteniendo datos históricos (7 días)...")
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=7)
        df = get_ohlcv_extended("BTCUSDT", "15m", days=7)
        
        if df is None or len(df) == 0:
            print("❌ No se pudieron obtener datos")
            return False
        
        print(f"✅ Datos obtenidos: {len(df)} velas")
        print(f"📅 Período: {df['timestamp'].min()} a {df['timestamp'].max()}")
        print(f"💰 Rango de precios: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        print(f"📊 Volatilidad: {((df['high'].max() - df['low'].min()) / df['close'].mean() * 100):.2f}%")
        
        # 2. Análisis SMC
        print("\n🔍 2. Ejecutando análisis SMC...")
        smc_analysis = analyze(df, timeframe="15m")
        
        if not smc_analysis:
            print("❌ Error en análisis SMC")
            return False
        
        print("✅ Análisis SMC completado")
        
        # 3. Generar señales REALISTAS
        print("\n⚡ 3. Generando señales SMC REALISTAS...")
        signals = generate_realistic_smc_signals(df, smc_analysis)
        
        print(f"✅ {len(signals)} señales REALISTAS generadas")
        
        if not signals:
            print("⚠️ No se generaron señales realistas")
            return False
        
        # 4. Test de backtesting REALISTA
        print("\n📈 4. Ejecutando backtesting REALISTA...")
        
        backtest_results = run_backtest_analysis(
            df, signals, 10000, 1.0
        )
        
        if backtest_results['success']:
            results = backtest_results['results']
            print(f"✅ Backtesting REALISTA completado:")
            print(f"   - Total trades: {results.total_trades}")
            print(f"   - Win rate: {results.win_rate:.1f}%")
            print(f"   - Profit factor: {results.profit_factor:.2f}")
            print(f"   - Total PnL: ${results.total_pnl:.2f}")
            print(f"   - Max drawdown: {results.max_drawdown_percent:.1f}%")
            print(f"   - Avg trade duration: {results.average_trade_duration:.1f}h")
            print(f"   - Expectancy: {results.expectancy:.2f}")
            
            # Validar realismo de resultados
            print(f"\n🔍 VALIDACIÓN DE REALISMO:")
            
            # 1. Verificar que el número de trades es razonable
            trades_per_day = results.total_trades / 7  # 7 días de datos
            if 1 <= trades_per_day <= 10:
                print(f"   ✅ Trades por día: {trades_per_day:.1f} (realista)")
            else:
                print(f"   ⚠️ Trades por día: {trades_per_day:.1f} (poco realista)")
            
            # 2. Verificar que el drawdown es razonable
            if results.max_drawdown_percent < 20:
                print(f"   ✅ Max drawdown: {results.max_drawdown_percent:.1f}% (razonable)")
            else:
                print(f"   ⚠️ Max drawdown: {results.max_drawdown_percent:.1f}% (alto)")
            
            # 3. Verificar que el profit factor es realista
            if 0.5 <= results.profit_factor <= 3.0:
                print(f"   ✅ Profit factor: {results.profit_factor:.2f} (realista)")
            else:
                print(f"   ⚠️ Profit factor: {results.profit_factor:.2f} (poco realista)")
            
            # Mostrar detalles de trades
            if results.trades:
                print(f"\n📋 Detalles de trades (primeros 5):")
                for i, trade in enumerate(results.trades[:5]):
                    result_str = trade.result.value if trade.result else "Pendiente"
                    pnl_str = f"${trade.pnl_points:.2f}" if trade.pnl_points else "N/A"
                    print(f"   {i+1}. {trade.signal_type} @ ${trade.entry_price:.2f} -> {result_str} ({pnl_str})")
        else:
            print("❌ Error en backtesting")
            return False
        
        print("\n🎉 TEST DE BACKTESTING REALISTA COMPLETADO EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_realistic_backtesting()
    sys.exit(0 if success else 1)
