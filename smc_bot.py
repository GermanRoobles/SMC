#!/usr/bin/env python3
"""
Smart Money Concepts Simplified by TJR - Trading Bot
====================================================

Bot de trading algorítmico que implementa la estrategia SMC Simplified by TJR
para detectar señales de entrada basadas en:
- Estructura de mercado (HH, HL, LL, LH)
- Liquidez y barridos
- Order Blocks y Fair Value Gaps
- Confirmaciones de velas

Autor: Desarrollado para análisis SMC
Versión: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURACIÓN ====================

@dataclass
class SMCConfig:
    """Configuración para la estrategia SMC Simplified by TJR"""
    # Configuración de swings (5 velas recomendado)
    swing_length: int = 5

    # Tolerancia para equal highs/lows (0.05% a 0.1%)
    equal_tolerance: float = 0.075  # 0.075% balanceado

    # Risk-Reward mínimo (configurable, por defecto 2:1)
    min_rr: float = 2.0

    # Riesgo por operación (% del balance)
    risk_per_trade: float = 1.0

    # Configuración de confirmación
    min_confirmation_body: float = 0.6  # % del cuerpo de la vela

    # Configuración FVG
    fvg_min_size: float = 0.05  # % mínimo del tamaño del FVG

    # Configuración Multi-Timeframe
    htf_timeframe: str = "4h"  # Higher Time Frame para estructura
    ltf_timeframe: str = "15m"  # Lower Time Frame para entrada

    # Configuración SL/TP método TJR
    use_tjr_method: bool = True  # Usar método TJR (True) o ATR (False)
    sl_buffer: float = 0.001  # Buffer para SL (0.1% por defecto)

    # Configuración de confirmación de velas
    enable_engulfing: bool = True
    enable_pinbar: bool = True
    enable_rejection_wick: bool = True
    min_wick_ratio: float = 2.0  # Ratio mínimo mecha/cuerpo para pinbar

class TrendDirection(Enum):
    """Direcciones de tendencia"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"

class StructureType(Enum):
    """Tipos de estructura"""
    HH = "higher_high"
    HL = "higher_low"
    LL = "lower_low"
    LH = "lower_high"

class SignalType(Enum):
    """Tipos de señales"""
    BUY = "buy"
    SELL = "sell"

@dataclass
class TradingSignal:
    """Estructura para señales de trading"""
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float
    reason: str
    timestamp: pd.Timestamp

# ==================== CLASE PRINCIPAL ====================

class SMCBot:
    """
    Bot de trading basado en Smart Money Concepts Simplified by TJR
    """

    def __init__(self, config: SMCConfig = None):
        """
        Inicializar el bot SMC

        Args:
            config: Configuración del bot
        """
        self.config = config or SMCConfig()
        self.df = None
        self.swings = None
        self.structure = None
        self.trend = TrendDirection.SIDEWAYS

        # Almacenamiento de detecciones
        self.liquidity_zones = []
        self.order_blocks = []
        self.fvg_zones = []
        self.signals = []

        print("🤖 SMC Bot inicializado con configuración:")
        print(f"   📊 Swing Length: {self.config.swing_length}")
        print(f"   📏 Equal Tolerance: {self.config.equal_tolerance}%")
        print(f"   💰 Min R:R: {self.config.min_rr}:1")
        print(f"   ⚠️ Risk per Trade: {self.config.risk_per_trade}%")

    def analyze_market(self, df: pd.DataFrame) -> Dict:
        """
        Análisis completo del mercado

        Args:
            df: DataFrame con datos OHLC

        Returns:
            Diccionario con análisis completo
        """
        print("\n🔍 Iniciando análisis de mercado...")

        self.df = df.copy()

        # 1. Detectar estructura
        self.swings = self.detect_swings()
        self.structure = self.detect_structure()
        self.trend = self.determine_trend()

        # 2. Detectar liquidez
        self.liquidity_zones = self.detect_liquidity_zones()
        sweeps = self.detect_sweeps()

        # 3. Detectar CHoCH y BOS
        choch_bos = self.detect_choch_bos()

        # 4. Detectar Order Blocks
        self.order_blocks = self.detect_order_blocks()

        # 5. Detectar FVG
        self.fvg_zones = self.detect_fvg()

        # 6. Buscar confirmaciones y generar señales
        self.signals = self.generate_signals()

        return {
            'trend': self.trend.value,
            'swings': len(self.swings),
            'liquidity_zones': len(self.liquidity_zones),
            'sweeps': len(sweeps),
            'choch_bos': len(choch_bos),
            'order_blocks': len(self.order_blocks),
            'fvg_zones': len(self.fvg_zones),
            'signals': len(self.signals)
        }

    # ==================== DETECCIÓN DE ESTRUCTURA ====================

    def detect_swings(self) -> pd.DataFrame:
        """
        Detectar swing highs y swing lows usando 5 velas (2 izq + 2 der)

        Returns:
            DataFrame con swings detectados
        """
        print("📈 Detectando swings highs/lows...")

        df = self.df.copy()
        swings = pd.DataFrame(index=df.index)
        swings['swing_high'] = False
        swings['swing_low'] = False
        swings['swing_high_price'] = np.nan
        swings['swing_low_price'] = np.nan

        # Usar 5 velas: 2 izquierda + 1 central + 2 derecha
        left_bars = 2
        right_bars = 2

        for i in range(left_bars, len(df) - right_bars):
            current_high = df.iloc[i]['high']
            current_low = df.iloc[i]['low']

            # Verificar Swing High
            is_swing_high = True
            for j in range(1, left_bars + 1):
                if current_high <= df.iloc[i - j]['high']:
                    is_swing_high = False
                    break

            if is_swing_high:
                for j in range(1, right_bars + 1):
                    if current_high <= df.iloc[i + j]['high']:
                        is_swing_high = False
                        break

            if is_swing_high:
                swings.iloc[i, swings.columns.get_loc('swing_high')] = True
                swings.iloc[i, swings.columns.get_loc('swing_high_price')] = current_high

            # Verificar Swing Low
            is_swing_low = True
            for j in range(1, left_bars + 1):
                if current_low >= df.iloc[i - j]['low']:
                    is_swing_low = False
                    break

            if is_swing_low:
                for j in range(1, right_bars + 1):
                    if current_low >= df.iloc[i + j]['low']:
                        is_swing_low = False
                        break

            if is_swing_low:
                swings.iloc[i, swings.columns.get_loc('swing_low')] = True
                swings.iloc[i, swings.columns.get_loc('swing_low_price')] = current_low

        # Filtrar solo swings válidos
        swing_highs = swings[swings['swing_high']].copy()
        swing_lows = swings[swings['swing_low']].copy()

        print(f"   ✅ Detectados {len(swing_highs)} swing highs y {len(swing_lows)} swing lows")

        return swings

    def detect_structure(self) -> List[Dict]:
        """
        Detectar estructura del mercado (HH, HL, LL, LH)

        Returns:
            Lista con puntos de estructura
        """
        print("🏗️ Analizando estructura del mercado...")

        structure_points = []

        # Obtener swing highs y lows
        swing_highs = self.swings[self.swings['swing_high']].copy()
        swing_lows = self.swings[self.swings['swing_low']].copy()

        # Analizar swing highs
        for i in range(1, len(swing_highs)):
            prev_high = swing_highs.iloc[i-1]['swing_high_price']
            curr_high = swing_highs.iloc[i]['swing_high_price']

            if curr_high > prev_high:
                structure_type = StructureType.HH
            else:
                structure_type = StructureType.LH

            structure_points.append({
                'type': structure_type,
                'price': curr_high,
                'timestamp': swing_highs.index[i],
                'category': 'high'
            })

        # Analizar swing lows
        for i in range(1, len(swing_lows)):
            prev_low = swing_lows.iloc[i-1]['swing_low_price']
            curr_low = swing_lows.iloc[i]['swing_low_price']

            if curr_low > prev_low:
                structure_type = StructureType.HL
            else:
                structure_type = StructureType.LL

            structure_points.append({
                'type': structure_type,
                'price': curr_low,
                'timestamp': swing_lows.index[i],
                'category': 'low'
            })

        # Ordenar por timestamp
        structure_points.sort(key=lambda x: x['timestamp'])

        print(f"   ✅ Detectados {len(structure_points)} puntos de estructura")

        return structure_points

    def determine_trend(self) -> TrendDirection:
        """
        Determinar la tendencia actual del mercado

        Returns:
            Dirección de la tendencia
        """
        print("📊 Determinando tendencia del mercado...")

        if not self.structure or len(self.structure) < 4:
            return TrendDirection.SIDEWAYS

        # Analizar últimos 4 puntos de estructura
        recent_structure = self.structure[-4:]

        hh_count = sum(1 for s in recent_structure if s['type'] == StructureType.HH)
        hl_count = sum(1 for s in recent_structure if s['type'] == StructureType.HL)
        ll_count = sum(1 for s in recent_structure if s['type'] == StructureType.LL)
        lh_count = sum(1 for s in recent_structure if s['type'] == StructureType.LH)

        bullish_signals = hh_count + hl_count
        bearish_signals = ll_count + lh_count

        if bullish_signals > bearish_signals:
            trend = TrendDirection.BULLISH
        elif bearish_signals > bullish_signals:
            trend = TrendDirection.BEARISH
        else:
            trend = TrendDirection.SIDEWAYS

        print(f"   ✅ Tendencia detectada: {trend.value.upper()}")

        return trend

    # ==================== DETECCIÓN DE LIQUIDEZ ====================

    def detect_liquidity_zones(self) -> List[Dict]:
        """
        Detectar zonas de liquidez (equal highs/lows) con tolerancia mejorada

        Returns:
            Lista con zonas de liquidez
        """
        print("💧 Detectando zonas de liquidez...")

        liquidity_zones = []
        tolerance = self.config.equal_tolerance / 100  # Convertir a decimal

        # Obtener swing highs y lows
        swing_highs = self.swings[self.swings['swing_high']].copy()
        swing_lows = self.swings[self.swings['swing_low']].copy()

        print(f"[DEBUG] Swings detectados: {len(self.swings)} swing_highs, {len(self.swings)} swing_lows")
        print(f"[DEBUG] Tolerancia para equal highs/lows: {tolerance}")

        # Función helper para verificar si dos precios son "iguales"
        def is_equal_level(price1, price2, tolerance_pct):
            return abs(price1 - price2) / ((price1 + price2) / 2) <= tolerance_pct

        # Detectar equal highs
        processed_highs = set()
        for i in range(len(swing_highs)):
            if i in processed_highs:
                continue

            base_price = swing_highs.iloc[i]['swing_high_price']
            base_timestamp = swing_highs.index[i]
            equal_highs = [(base_timestamp, base_price)]

            for j in range(i + 1, len(swing_highs)):
                if j in processed_highs:
                    continue

                compare_price = swing_highs.iloc[j]['swing_high_price']
                compare_timestamp = swing_highs.index[j]

                if is_equal_level(base_price, compare_price, tolerance):
                    equal_highs.append((compare_timestamp, compare_price))
                    processed_highs.add(j)

            if len(equal_highs) >= 2:  # Al menos 2 highs iguales
                avg_price = sum(price for _, price in equal_highs) / len(equal_highs)
                liquidity_zones.append({
                    'type': 'equal_highs',
                    'price': avg_price,
                    'count': len(equal_highs),
                    'timestamps': [ts for ts, _ in equal_highs],
                    'swept': False,
                    'strength': 'high' if len(equal_highs) >= 3 else 'medium'
                })

        # Detectar equal lows
        processed_lows = set()
        for i in range(len(swing_lows)):
            if i in processed_lows:
                continue

            base_price = swing_lows.iloc[i]['swing_low_price']
            base_timestamp = swing_lows.index[i]
            equal_lows = [(base_timestamp, base_price)]

            for j in range(i + 1, len(swing_lows)):
                if j in processed_lows:
                    continue

                compare_price = swing_lows.iloc[j]['swing_low_price']
                compare_timestamp = swing_lows.index[j]

                if is_equal_level(base_price, compare_price, tolerance):
                    equal_lows.append((compare_timestamp, compare_price))
                    processed_lows.add(j)

            if len(equal_lows) >= 2:  # Al menos 2 lows iguales
                avg_price = sum(price for _, price in equal_lows) / len(equal_lows)
                liquidity_zones.append({
                    'type': 'equal_lows',
                    'price': avg_price,
                    'count': len(equal_lows),
                    'timestamps': [ts for ts, _ in equal_lows],
                    'swept': False,
                    'strength': 'high' if len(equal_lows) >= 3 else 'medium'
                })

        print(f"   ✅ Detectadas {len(liquidity_zones)} zonas de liquidez")

        return liquidity_zones

    def detect_sweeps(self) -> List[Dict]:
        """
        Detectar barridos de liquidez

        Returns:
            Lista con barridos detectados
        """
        print("🌊 Detectando barridos de liquidez...")

        sweeps = []

        for zone in self.liquidity_zones:
            zone_price = zone['price']
            zone_type = zone['type']

            # Buscar barridos después de la última aparición de la zona
            last_timestamp = max(zone['timestamps'])
            future_data = self.df[self.df.index > last_timestamp].copy()

            if len(future_data) == 0:
                continue

            for idx, row in future_data.iterrows():
                if zone_type == 'equal_highs':
                    # Barrido alcista: precio rompe por encima y cierra por debajo
                    if row['high'] > zone_price and row['close'] < zone_price:
                        sweeps.append({
                            'type': 'bullish_sweep',
                            'zone_price': zone_price,
                            'sweep_high': row['high'],
                            'close_price': row['close'],
                            'timestamp': idx,
                            'zone': zone
                        })
                        zone['swept'] = True
                        break

                elif zone_type == 'equal_lows':
                    # Barrido bajista: precio rompe por debajo y cierra por encima
                    if row['low'] < zone_price and row['close'] > zone_price:
                        sweeps.append({
                            'type': 'bearish_sweep',
                            'zone_price': zone_price,
                            'sweep_low': row['low'],
                            'close_price': row['close'],
                            'timestamp': idx,
                            'zone': zone
                        })
                        zone['swept'] = True
                        break

        print(f"   ✅ Detectados {len(sweeps)} barridos de liquidez")

        return sweeps

    # ==================== PLACEHOLDERS PARA FUNCIONES ADICIONALES ====================

    def detect_choch_bos(self) -> List[Dict]:
        """
        Detectar cambios de estructura (CHoCH) y rupturas de estructura (BOS)

        Returns:
            Lista con CHoCH y BOS detectados
        """
        print("🔄 Detectando CHoCH y BOS...")

        # Importar función avanzada
        from smc_advanced import detect_choch_bos_advanced

        try:
            choch_bos = detect_choch_bos_advanced(self.df, self.swings, self.structure)
            print(f"   ✅ Detectados {len(choch_bos)} cambios de estructura")
            return choch_bos
        except Exception as e:
            print(f"   ⚠️ Error en detección CHoCH/BOS: {e}")
            return []

    def detect_order_blocks(self) -> List[Dict]:
        """
        Detectar Order Blocks

        Returns:
            Lista con Order Blocks detectados
        """
        print("📦 Detectando Order Blocks...")

        # Importar función avanzada
        from smc_advanced import detect_order_blocks_advanced

        try:
            # Primero necesitamos CHoCH/BOS
            choch_bos = self.detect_choch_bos()
            order_blocks = detect_order_blocks_advanced(self.df, self.swings, choch_bos)
            print(f"   ✅ Detectados {len(order_blocks)} Order Blocks")
            return order_blocks
        except Exception as e:
            print(f"   ⚠️ Error en detección Order Blocks: {e}")
            return []

    def detect_fvg(self) -> List[Dict]:
        """
        Detectar Fair Value Gaps

        Returns:
            Lista con FVG detectados
        """
        print("⚡ Detectando Fair Value Gaps...")

        # Importar función avanzada
        from smc_advanced import detect_fvg_advanced

        try:
            fvg_zones = detect_fvg_advanced(self.df, self.config.fvg_min_size)
            print(f"   ✅ Detectados {len(fvg_zones)} Fair Value Gaps")
            return fvg_zones
        except Exception as e:
            print(f"   ⚠️ Error en detección FVG: {e}")
            return []

    def detect_confirmation(self, index: int) -> Dict:
        """
        Detectar velas de confirmación

        Args:
            index: Índice de la vela a analizar

        Returns:
            Diccionario con información de confirmación
        """
        from smc_advanced import detect_confirmation_patterns

        try:
            confirmation = detect_confirmation_patterns(self.df, index, self.config.min_confirmation_body)
            return confirmation
        except Exception as e:
            print(f"   ⚠️ Error en detección confirmación: {e}")
            return {'confirmed': False, 'type': None, 'strength': 0}

    def generate_signals(self) -> List[TradingSignal]:
        """
        Generar señales de trading basadas en la estrategia SMC

        Returns:
            Lista con señales de trading
        """
        print("🎯 Generando señales de trading...")

        try:
            from smc_advanced import calculate_atr
            from smc_integration import generate_trading_signals

            # Calcular ATR
            atr = calculate_atr(self.df)
            current_atr = atr.iloc[-1] if not atr.empty else self.df['close'].iloc[-1] * 0.01

            # Obtener todos los componentes necesarios
            choch_bos = self.detect_choch_bos()
            order_blocks = self.detect_order_blocks()
            fvg_zones = self.detect_fvg()
            sweeps = self.detect_sweeps()

            # Generar señales
            signals = generate_trading_signals(
                self.df, self.liquidity_zones, sweeps, choch_bos,
                order_blocks, fvg_zones, current_atr, self.config
            )

            print(f"   ✅ Generadas {len(signals)} señales de trading")
            return signals

        except Exception as e:
            print(f"   ⚠️ Error en generación de señales: {e}")
            return []

    def calculate_sl_tp(self, entry_price: float, signal_type: SignalType) -> Tuple[float, float]:
        """
        Calcular Stop Loss y Take Profit

        Args:
            entry_price: Precio de entrada
            signal_type: Tipo de señal (BUY/SELL)

        Returns:
            Tupla con (stop_loss, take_profit)
        """
        try:
            from smc_advanced import calculate_sl_tp_advanced, calculate_atr

            # Calcular ATR
            atr = calculate_atr(self.df)
            current_atr = atr.iloc[-1] if not atr.empty else entry_price * 0.01

            # Calcular SL/TP
            sl, tp, _ = calculate_sl_tp_advanced(
                entry_price,
                signal_type.value,
                current_atr,
                self.config.min_rr
            )

            return (sl, tp)

        except Exception as e:
            print(f"   ⚠️ Error en cálculo SL/TP: {e}")
            # Valores por defecto
            if signal_type == SignalType.BUY:
                return (entry_price * 0.98, entry_price * 1.04)  # -2% SL, +4% TP
            else:
                return (entry_price * 1.02, entry_price * 0.96)  # +2% SL, -4% TP

    def place_trade(self, signal: TradingSignal):
        """
        Simular colocación de operación

        Args:
            signal: Señal de trading
        """
        print(f"\n📢 SEÑAL DE {signal.signal_type.value.upper()}:")
        print(f"   💰 Entrada: ${signal.entry_price:.2f}")
        print(f"   🛑 Stop Loss: ${signal.stop_loss:.2f}")
        print(f"   🎯 Take Profit: ${signal.take_profit:.2f}")
        print(f"   📊 R:R: {signal.risk_reward:.2f}")
        print(f"   🔒 Confianza: {signal.confidence:.1%}")
        print(f"   📝 Razón: {signal.reason}")
        print(f"   ⏰ Tiempo: {signal.timestamp}")

def detect_potential_setups(df, fvg_data, ob_data, structure_data):
    """
    Detecta posibles setups incompletos: FVG u OB mitigado pero sin CHoCH todavía.
    """
    potential_setups = []
    # Ejemplo de lógica: buscar FVG/OB tocados pero sin CHoCH
    for i, row in fvg_data.iterrows():
        if row.get('mitigated', False) and not structure_data.get('choch', []):
            potential_setups.append({
                'type': 'FVG',
                'index': i,
                'timestamp': row.get('timestamp', None),
                'mitigated': True,
                'confirmed': False
            })
    for i, row in ob_data.iterrows():
        if row.get('mitigated', False) and not structure_data.get('choch', []):
            potential_setups.append({
                'type': 'OB',
                'index': i,
                'timestamp': row.get('timestamp', None),
                'mitigated': True,
                'confirmed': False
            })
    return potential_setups

def score_confluences(setup):
    """
    Evalúa un setup según cuántas condiciones clave están alineadas.
    Retorna score (0-5) y detalle de confluencias.
    """
    score = 0
    reasons = []
    keys = [
        ('liquidity_sweep', 'Barrido de liquidez'),
        ('choch', 'CHoCH'),
        ('fvg_mitigated', 'FVG mitigado'),
        ('order_block_touched', 'Order Block tocado'),
        ('confirmation_candle', 'Vela de confirmación')
    ]
    for k, label in keys:
        if setup.get(k, False):
            score += 1
            reasons.append(f"✅ {label}")
        else:
            reasons.append(f"❌ {label}")
    confidence = score / 5
    return {'score': score, 'confidence': confidence, 'reasons': reasons}

# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    """
    Función principal para probar el bot
    """
    print("🚀 Iniciando Smart Money Concepts Bot")
    print("=" * 50)

    # Crear configuración personalizada
    config = SMCConfig(
        swing_length=10,
        equal_tolerance=0.1,
        min_rr=2.0,
        risk_per_trade=1.0
    )

    # Inicializar bot
    bot = SMCBot(config)

    # Datos de ejemplo (reemplazar con datos reales)
    print("\n📊 Cargando datos de ejemplo...")

    # TODO: Cargar datos reales aquí
    # df = pd.read_csv('datos.csv')
    # o desde una API

    print("⚠️ Para usar el bot, proporciona datos OHLC en el siguiente formato:")
    print("   df = pd.DataFrame con columnas: ['open', 'high', 'low', 'close', 'volume']")
    print("   Luego ejecuta: bot.analyze_market(df)")

if __name__ == "__main__":
    main()
