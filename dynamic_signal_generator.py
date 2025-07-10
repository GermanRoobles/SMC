#!/usr/bin/env python3
"""
Generador de señales SMC con niveles dinámicos
==============================================

Sistema para generar señales SMC con niveles adaptativos basados en ATR
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from smc_trade_engine import TradeSignal, SignalType, ConfirmationType
from smc_backtester import calculate_adaptive_levels, validate_sl_tp_levels, LevelValidationResult

class DynamicSignalGenerator:
    """Generador de señales con niveles dinámicos"""

    def __init__(self, atr_period: int = 14, conservative_mode: bool = False):
        """
        Args:
            atr_period: Período para calcular ATR
            conservative_mode: Si True, usa niveles más conservadores
        """
        self.atr_period = atr_period
        self.risk_multiplier = 0.7 if conservative_mode else 1.0

    def generate_signal_with_adaptive_levels(self,
                                           df: pd.DataFrame,
                                           entry_idx: int,
                                           signal_type: SignalType,
                                           symbol: str = "BTCUSDT",
                                           timeframe: str = "1h",
                                           confidence: float = 0.8,
                                           max_retries: int = 5) -> Optional[TradeSignal]:
        """
        Generar señal con niveles adaptativos basados en ATR, validando niveles antes de crear la señal.
        Reintenta con diferentes índices o multiplicadores si los niveles son inválidos.
        """
        for attempt in range(max_retries):
            try:
                # Ajustar entry_idx en cada intento si es necesario
                idx = entry_idx + attempt if (entry_idx + attempt) < len(df) else entry_idx - attempt
                if idx < 0 or idx >= len(df):
                    break
                entry_price = df['close'].iloc[idx]
                timestamp = df['timestamp'].iloc[idx]

                # Calcular niveles adaptativos
                stop_loss, take_profit = calculate_adaptive_levels(
                    df, entry_price, signal_type.value, self.risk_multiplier
                )

                # Validar niveles
                validation = validate_sl_tp_levels(
                    df, entry_price, stop_loss, take_profit, signal_type.value
                )

                if validation.result == LevelValidationResult.VALID:
                    # Calcular Risk/Reward ratio
                    sl_pct = abs((stop_loss - entry_price) / entry_price) * 100
                    tp_pct = abs((take_profit - entry_price) / entry_price) * 100
                    risk_reward = tp_pct / sl_pct if sl_pct > 0 else 2.0

                    signal = TradeSignal(
                        timestamp=timestamp,
                        symbol=symbol,
                        timeframe=timeframe,
                        signal_type=signal_type,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=risk_reward,
                        confidence=confidence,
                        setup_components={'atr_adaptive': True},
                        confirmation_type=ConfirmationType.ENGULFING
                    )
                    return signal
                else:
                    print(f"⚠️ Intento {attempt+1}: Niveles inválidos en {timestamp}: {validation.message}")
                    for suggestion in validation.suggestions:
                        print(f"   💡 {suggestion}")
                    # Opcional: ajustar risk_multiplier en reintentos
                    self.risk_multiplier *= 0.95  # Hacerlo más conservador en cada intento
            except Exception as e:
                print(f"Error generando señal adaptativa (intento {attempt+1}): {e}")
                continue
        print(f"❌ No se pudo generar señal válida en idx {entry_idx} tras {max_retries} intentos.")
        return None

    def generate_multiple_signals(self,
                                 df: pd.DataFrame,
                                 signal_count: int = 3,
                                 spacing: int = 20) -> List[TradeSignal]:
        """
        Generar múltiples señales con niveles adaptativos, solo si los niveles son válidos.
        """
        signals = []

        print(f"🔄 Generando {signal_count} señales con niveles adaptativos...")

        # Analizar volatilidad general
        price_range = df['high'].max() - df['low'].min()
        volatility = (price_range / df['close'].mean()) * 100

        print(f"   📊 Volatilidad del mercado: {volatility:.2f}%")
        print(f"   🎯 Modo: {'Conservador' if self.risk_multiplier < 1.0 else 'Normal'}")

        signal_types = [SignalType.LONG, SignalType.SHORT, SignalType.LONG]
        attempts = 0
        i = 0
        idx = 20
        while len(signals) < signal_count and idx < len(df) - 10 and attempts < signal_count * 3:
            signal_type = signal_types[i % len(signal_types)]
            confidence = 0.8 + (i * 0.05)
            signal = self.generate_signal_with_adaptive_levels(
                df, idx, signal_type, confidence=confidence
            )
            if signal:
                signals.append(signal)
                sl_pct = abs((signal.stop_loss - signal.entry_price) / signal.entry_price) * 100
                tp_pct = abs((signal.take_profit - signal.entry_price) / signal.entry_price) * 100
                print(f"   {len(signals)}. {signal.signal_type.value} en ${signal.entry_price:.2f}")
                print(f"      SL: ${signal.stop_loss:.2f} ({sl_pct:.1f}%)")
                print(f"      TP: ${signal.take_profit:.2f} ({tp_pct:.1f}%)")
                print(f"      RR: {signal.risk_reward:.1f}")
            else:
                print(f"   ⏭️  Saltando idx {idx} por niveles inválidos.")
            i += 1
            idx += spacing
            attempts += 1
        return signals

    def analyze_market_conditions(self, df: pd.DataFrame) -> dict:
        """
        Analizar condiciones del mercado para ajustar niveles

        Args:
            df: DataFrame con datos OHLC

        Returns:
            dict con análisis de condiciones
        """
        try:
            # Calcular ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=self.atr_period).mean()
            current_atr = atr.iloc[-1]
            atr_pct = (current_atr / df['close'].iloc[-1]) * 100

            # Calcular volatilidad
            price_range = df['high'].max() - df['low'].min()
            volatility = (price_range / df['close'].mean()) * 100

            # Tendencia
            sma_short = df['close'].rolling(window=10).mean()
            sma_long = df['close'].rolling(window=20).mean()
            trend = "BULLISH" if sma_short.iloc[-1] > sma_long.iloc[-1] else "BEARISH"

            # Clasificar condiciones
            if volatility < 2.0:
                market_condition = "LOW_VOLATILITY"
                recommended_multiplier = 0.8
            elif volatility > 5.0:
                market_condition = "HIGH_VOLATILITY"
                recommended_multiplier = 1.2
            else:
                market_condition = "NORMAL_VOLATILITY"
                recommended_multiplier = 1.0

            return {
                'atr': current_atr,
                'atr_pct': atr_pct,
                'volatility': volatility,
                'trend': trend,
                'market_condition': market_condition,
                'recommended_multiplier': recommended_multiplier,
                'price_range': price_range,
                'current_price': df['close'].iloc[-1]
            }

        except Exception as e:
            print(f"Error analizando condiciones: {e}")
            return {
                'atr': 0,
                'atr_pct': 1.0,
                'volatility': 2.0,
                'trend': "NEUTRAL",
                'market_condition': "NORMAL_VOLATILITY",
                'recommended_multiplier': 1.0,
                'price_range': 1000,
                'current_price': 100000
            }

def create_dynamic_test_signals(df: pd.DataFrame,
                               symbol: str = "BTCUSDT",
                               timeframe: str = "1h",
                               conservative: bool = False) -> List[TradeSignal]:
    """
    Crear señales de prueba con niveles dinámicos

    Args:
        df: DataFrame con datos OHLC
        symbol: Símbolo del activo
        timeframe: Timeframe
        conservative: Si True, usa niveles más conservadores

    Returns:
        Lista de señales con niveles adaptativos
    """
    generator = DynamicSignalGenerator(conservative_mode=conservative)

    # Analizar condiciones del mercado
    conditions = generator.analyze_market_conditions(df)

    print(f"📈 ANÁLISIS DE CONDICIONES DEL MERCADO:")
    print(f"   • ATR: {conditions['atr']:.2f} ({conditions['atr_pct']:.2f}%)")
    print(f"   • Volatilidad: {conditions['volatility']:.2f}%")
    print(f"   • Tendencia: {conditions['trend']}")
    print(f"   • Condición: {conditions['market_condition']}")
    print(f"   • Multiplicador recomendado: {conditions['recommended_multiplier']:.1f}")

    # Ajustar multiplicador según condiciones
    generator.risk_multiplier = conditions['recommended_multiplier']

    # Generar señales
    signals = generator.generate_multiple_signals(df, signal_count=3, spacing=20)

    return signals

if __name__ == "__main__":
    # Test rápido del generador
    from fetch_data import get_ohlcv

    df = get_ohlcv("BTCUSDT", "1h", limit=100)
    signals = create_dynamic_test_signals(df, conservative=False)

    print(f"\n✅ Generadas {len(signals)} señales dinámicas")
    for i, signal in enumerate(signals):
        print(f"   {i+1}. {signal.signal_type.value} - RR: {signal.risk_reward:.1f}")
