#!/usr/bin/env python3
"""
Módulo de Histórico SMC Bot
==========================

Este módulo gestiona el histórico de datos y señales del SMC Bot,
permitiendo navegar hacia atrás en el tiempo y ver la evolución
de indicadores y señales.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import os
from dataclasses import dataclass
from enum import Enum

from fetch_data import get_ohlcv
from smc_integration import get_smc_bot_analysis
from smc_bot import TradingSignal, SignalType

class HistoricalPeriod(Enum):
    """Períodos históricos disponibles"""
    HOUR_1 = "1h"
    HOURS_4 = "4h"
    HOURS_12 = "12h"
    DAY_1 = "1d"
    DAYS_3 = "3d"
    WEEK_1 = "1w"
    WEEKS_2 = "2w"
    MONTH_1 = "1M"

@dataclass
class HistoricalSnapshot:
    """Snapshot histórico de datos y análisis"""
    timestamp: datetime
    df: pd.DataFrame
    bot_analysis: Dict
    signals: List[TradingSignal]
    market_conditions: Dict
    symbol: str
    timeframe: str

class SMCHistoricalManager:
    """
    Gestor de histórico para el SMC Bot
    """

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.cache_dir = "historical_cache"
        self.snapshots: List[HistoricalSnapshot] = []

        # Crear directorio de cache si no existe
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            # Crear subdirectorios para cada símbolo
            symbol_dir = os.path.join(self.cache_dir, symbol.replace('/', '_'))
            os.makedirs(symbol_dir, exist_ok=True)
            print(f"📁 Cache directory creado: {symbol_dir}")
        except Exception as e:
            print(f"⚠️ Error creando directorio cache: {e}")

        # Configuración de períodos históricos
        self.period_configs = {
            HistoricalPeriod.HOUR_1: {"delta": timedelta(hours=1), "limit": 100},
            HistoricalPeriod.HOURS_4: {"delta": timedelta(hours=4), "limit": 100},
            HistoricalPeriod.HOURS_12: {"delta": timedelta(hours=12), "limit": 100},
            HistoricalPeriod.DAY_1: {"delta": timedelta(days=1), "limit": 100},
            HistoricalPeriod.DAYS_3: {"delta": timedelta(days=3), "limit": 100},
            HistoricalPeriod.WEEK_1: {"delta": timedelta(weeks=1), "limit": 100},
            HistoricalPeriod.WEEKS_2: {"delta": timedelta(weeks=2), "limit": 100},
            HistoricalPeriod.MONTH_1: {"delta": timedelta(days=30), "limit": 100},
            # Claves string para compatibilidad con selectbox
            "1h": {"delta": timedelta(hours=1), "limit": 100},
            "4h": {"delta": timedelta(hours=4), "limit": 100},
            "12h": {"delta": timedelta(hours=12), "limit": 100},
            "1d": {"delta": timedelta(days=1), "limit": 100},
            "3d": {"delta": timedelta(days=3), "limit": 100},
            "1w": {"delta": timedelta(weeks=1), "limit": 100},
            "2w": {"delta": timedelta(weeks=2), "limit": 100},
            "1M": {"delta": timedelta(days=30), "limit": 100}
        }

    def get_historical_data(self, period: HistoricalPeriod,
                          end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtener datos históricos para un período específico

        Args:
            period: Período histórico
            end_time: Tiempo final (si no se especifica, usa tiempo actual)

        Returns:
            DataFrame con datos históricos
        """
        if end_time is None:
            end_time = datetime.now()

        config = self.period_configs[period]
        start_time = end_time - config["delta"]

        print(f"📊 Obteniendo datos históricos desde {start_time} hasta {end_time}")

        try:
            from fetch_data import get_ohlcv_full
            # Descargar todas las velas necesarias para el rango
            df = get_ohlcv_full(self.symbol, self.timeframe, since=start_time, until=end_time)
            print(f"   ✅ Obtenidos {len(df)} puntos de datos (full range)")
            return df
        except Exception as e:
            print(f"   ❌ Error obteniendo datos históricos: {e}")
            return pd.DataFrame()

    def create_historical_snapshot(self, target_time: datetime, period) -> Optional[HistoricalSnapshot]:
        """
        Crear un snapshot histórico para un momento específico y período

        Args:
            target_time: Momento objetivo
            period: Período histórico a usar para el snapshot

        Returns:
            Snapshot histórico o None si hay error
        """
        try:
            # Obtener datos hasta el momento objetivo usando el período correcto
            df = self.get_historical_data(period, target_time)

            min_required = 10  # Mínimo de velas para considerar válido el snapshot
            if df.empty or len(df) < min_required:
                print(f"❌ No hay suficientes datos para {target_time} (obtenidos: {len(df)})")
                # Intentar buscar el dato más cercano anterior si el rango está vacío
                if not df.empty:
                    # Buscar el último dato anterior al rango
                    last_row = df.iloc[[-1]]
                    print(f"   ⚠️ Usando último dato disponible anterior para snapshot: {last_row['timestamp'].values[0]}")
                    df = last_row
                else:
                    return None

            # Realizar análisis SMC para ese momento
            print(f"🤖 Analizando condiciones del mercado en {target_time}")
            bot_analysis = get_smc_bot_analysis(df)

            # Extraer señales
            signals = bot_analysis.get('signals', [])

            # Analizar condiciones del mercado
            market_conditions = self._analyze_market_conditions(df, bot_analysis)

            # Crear snapshot
            snapshot = HistoricalSnapshot(
                timestamp=target_time,
                df=df,
                bot_analysis=bot_analysis,
                signals=signals,
                market_conditions=market_conditions,
                symbol=self.symbol,
                timeframe=self.timeframe
            )

            print(f"   ✅ Snapshot creado con {len(signals)} señales")

            print("\nIndicadores generados en ese punto histórico:")
            # Mostrar resumen de indicadores clave
            for key in ["trend", "fvg", "orderblocks", "bos_choch", "liquidity", "sessions", "swing_highs_lows"]:
                if key in bot_analysis:
                    val = bot_analysis[key]
                    if hasattr(val, 'to_string'):
                        print(f'"{key}":\n' + val.to_string() + "\n")
                    elif isinstance(val, dict):
                        print(f'"{key}": {val}\n')
                    else:
                        print(f'"{key}": {val}\n')
            print("\n---\n")

            return snapshot

        except Exception as e:
            print(f"   ❌ Error creando snapshot: {e}")
            return None

    def _analyze_market_conditions(self, df: pd.DataFrame, bot_analysis: Dict) -> Dict:
        """
        Analizar condiciones del mercado

        Args:
            df: DataFrame con datos OHLC
            bot_analysis: Análisis del bot

        Returns:
            Diccionario con condiciones del mercado
        """
        if df.empty:
            return {}

        # Precio y movimiento
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
        price_change = ((current_price - prev_price) / prev_price) * 100

        # Volatilidad
        volatility = df['close'].pct_change().std() * 100

        # Rango del día
        daily_range = ((df['high'].max() - df['low'].min()) / current_price) * 100

        # Tendencia
        trend = bot_analysis.get('trend', 'UNKNOWN')

        # Análisis de volumen (si está disponible)
        volume_analysis = "N/A"
        if 'volume' in df.columns:
            avg_volume = df['volume'].mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio > 1.5:
                volume_analysis = "Alto"
            elif volume_ratio < 0.5:
                volume_analysis = "Bajo"
            else:
                volume_analysis = "Normal"

        return {
            'price': current_price,
            'price_change': price_change,
            'volatility': volatility,
            'daily_range': daily_range,
            'trend': trend.value if hasattr(trend, 'value') else str(trend),
            'volume_analysis': volume_analysis,
            'smc_elements': {
                'liquidity_zones': len(bot_analysis.get('liquidity_zones', [])),
                'order_blocks': len(bot_analysis.get('order_blocks', [])),
                'fvg_zones': len(bot_analysis.get('fvg_zones', [])),
                'sweeps': len(bot_analysis.get('sweeps', [])),
                'choch_bos': len(bot_analysis.get('choch_bos', []))
            }
        }

    def generate_historical_timeline(self, period: HistoricalPeriod,
                                   intervals: int = 10) -> List[HistoricalSnapshot]:
        """
        Generar timeline histórico con múltiples snapshots

        Args:
            period: Período histórico total
            intervals: Número de intervalos a generar

        Returns:
            Lista de snapshots históricos
        """
        snapshots = []

        # Calcular intervalos de tiempo
        total_delta = self.period_configs[period]["delta"]
        interval_delta = total_delta / intervals

        end_time = datetime.now()

        period_str = period.value if hasattr(period, 'value') else str(period)
        print(f"📅 Generando timeline histórico para {period_str} con {intervals} intervalos")

        for i in range(intervals):
            target_time = end_time - (interval_delta * i)

            print(f"   📊 Procesando intervalo {i+1}/{intervals} - {target_time}")

            snapshot = self.create_historical_snapshot(target_time, period)
            if snapshot:
                snapshots.append(snapshot)

        # Ordenar por timestamp
        snapshots.sort(key=lambda x: x.timestamp)

        self.snapshots = snapshots
        print(f"   ✅ Timeline generado con {len(snapshots)} snapshots")

        return snapshots

    def create_detailed_historical_timeline(self, period: HistoricalPeriod,
                                          intervals: int = 20) -> List[HistoricalSnapshot]:
        """
        Crear timeline histórico detallado con más puntos de datos

        Args:
            period: Período histórico
            intervals: Número de intervalos (puntos temporales)

        Returns:
            Lista de snapshots históricos
        """
        period_str = period.value if hasattr(period, 'value') else str(period)
        print(f"📅 Creando timeline histórico detallado para {period_str} con {intervals} intervalos")

        # Limpiar snapshots existentes
        self.snapshots = []

        # Configuración del período
        config = self.period_configs[period]
        end_time = datetime.now()
        start_time = end_time - config["delta"]

        # Calcular intervalos
        time_delta = config["delta"] / intervals

        # Crear timeline
        timeline = []

        for i in range(intervals + 1):
            target_time = start_time + (time_delta * i)

            print(f"   📊 Creando snapshot {i+1}/{intervals+1} para {target_time}")

            # Crear snapshot
            snapshot = self.create_historical_snapshot(target_time, period)

            if snapshot:
                timeline.append(snapshot)
                print(f"      ✅ Snapshot creado con {len(snapshot.signals)} señales")
            else:
                print(f"      ❌ Error creando snapshot")

        # Guardar timeline
        self.snapshots = timeline

        # Guardar en cache
        self.save_timeline_to_cache(period, timeline)

        print(f"✅ Timeline histórico creado con {len(timeline)} snapshots")
        return timeline

    def save_timeline_to_cache(self, period: HistoricalPeriod, timeline: List[HistoricalSnapshot]):
        """
        Guardar timeline en cache para uso posterior

        Args:
            period: Período histórico
            timeline: Lista de snapshots
        """
        try:
            # Crear directorio específico para el símbolo
            symbol_dir = os.path.join(self.cache_dir, self.symbol.replace('/', '_'))
            os.makedirs(symbol_dir, exist_ok=True)

            period_str = period.value if hasattr(period, 'value') else str(period)
            cache_file = os.path.join(
                symbol_dir,
                f"timeline_{self.timeframe}_{period_str}.pkl"
            )

            with open(cache_file, 'wb') as f:
                pickle.dump(timeline, f)

            print(f"💾 Timeline guardado en cache: {cache_file}")

        except Exception as e:
            print(f"❌ Error guardando timeline en cache: {e}")

    def load_timeline_from_cache(self, period: HistoricalPeriod) -> Optional[List[HistoricalSnapshot]]:
        """
        Cargar timeline desde cache

        Args:
            period: Período histórico

        Returns:
            Lista de snapshots o None si no existe
        """
        try:
            symbol_dir = os.path.join(self.cache_dir, self.symbol.replace('/', '_'))
            period_str = period.value if hasattr(period, 'value') else str(period)
            cache_file = os.path.join(
                symbol_dir,
                f"timeline_{self.timeframe}_{period_str}.pkl"
            )

            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    timeline = pickle.load(f)
                print(f"📂 Timeline cargado desde cache: {cache_file}")
                return timeline
            else:
                print(f"📂 No existe cache para {cache_file}")
                return None

        except Exception as e:
            print(f"❌ Error cargando timeline desde cache: {e}")
            return None

    def save_historical_data(self, filename: Optional[str] = None) -> str:
        """
        Guardar datos históricos en cache

        Args:
            filename: Nombre del archivo (opcional)

        Returns:
            Ruta del archivo guardado
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Crear nombre de archivo válido
            symbol_clean = self.symbol.replace("/", "_")
            filename = f"historical_{symbol_clean}_{self.timeframe}_{timestamp}.pkl"

        filepath = os.path.join(self.cache_dir, filename)

        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.snapshots, f)

            print(f"💾 Datos históricos guardados en {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Error guardando datos históricos: {e}")
            return ""

    def load_historical_data(self, filename: str) -> bool:
        """
        Cargar datos históricos desde cache

        Args:
            filename: Nombre del archivo

        Returns:
            True si se cargó correctamente
        """
        filepath = os.path.join(self.cache_dir, filename)

        try:
            with open(filepath, 'rb') as f:
                self.snapshots = pickle.load(f)

            print(f"📂 Datos históricos cargados desde {filepath}")
            print(f"   ✅ {len(self.snapshots)} snapshots cargados")
            return True

        except Exception as e:
            print(f"❌ Error cargando datos históricos: {e}")
            return False

    def get_available_cache_files(self) -> List[str]:
        """
        Obtener archivos de cache disponibles

        Returns:
            Lista de nombres de archivos
        """
        if not os.path.exists(self.cache_dir):
            return []

        files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        return sorted(files, reverse=True)  # Más recientes primero

    def get_snapshot_by_index(self, index: int) -> Optional[HistoricalSnapshot]:
        """
        Obtener snapshot por índice

        Args:
            index: Índice del snapshot

        Returns:
            Snapshot o None si no existe
        """
        if 0 <= index < len(self.snapshots):
            return self.snapshots[index]
        return None

    def get_snapshot_by_time(self, target_time: datetime) -> Optional[HistoricalSnapshot]:
        """
        Obtener snapshot más cercano a un tiempo específico

        Args:
            target_time: Tiempo objetivo

        Returns:
            Snapshot más cercano o None
        """
        if not self.snapshots:
            return None

        # Encontrar snapshot más cercano
        closest_snapshot = None
        min_diff = float('inf')

        for snapshot in self.snapshots:
            diff = abs((snapshot.timestamp - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_snapshot = snapshot

        return closest_snapshot

    def get_snapshots_in_range(self, start_time: datetime,
                              end_time: datetime) -> List[HistoricalSnapshot]:
        """
        Obtener snapshots en un rango de tiempo

        Args:
            start_time: Tiempo de inicio
            end_time: Tiempo de fin

        Returns:
            Lista de snapshots en el rango
        """
        if not self.snapshots:
            return []

        return [snapshot for snapshot in self.snapshots
                if start_time <= snapshot.timestamp <= end_time]

    def get_signals_evolution(self) -> Dict:
        """
        Obtener evolución de señales a lo largo del tiempo

        Returns:
            Diccionario con evolución de señales
        """
        if not self.snapshots:
            return {}

        evolution = {
            'timestamps': [],
            'total_signals': [],
            'buy_signals': [],
            'sell_signals': [],
            'avg_rr': [],
            'avg_confidence': [],
            'market_conditions': []
        }

        for snapshot in self.snapshots:
            evolution['timestamps'].append(snapshot.timestamp)
            evolution['total_signals'].append(len(snapshot.signals))

            buy_count = len([s for s in snapshot.signals if s.signal_type == SignalType.BUY])
            sell_count = len([s for s in snapshot.signals if s.signal_type == SignalType.SELL])

            evolution['buy_signals'].append(buy_count)
            evolution['sell_signals'].append(sell_count)

            if snapshot.signals:
                avg_rr = sum(s.risk_reward for s in snapshot.signals) / len(snapshot.signals)
                avg_conf = sum(s.confidence for s in snapshot.signals) / len(snapshot.signals)
                evolution['avg_rr'].append(avg_rr)
                evolution['avg_confidence'].append(avg_conf)
            else:
                evolution['avg_rr'].append(0)
                evolution['avg_confidence'].append(0)

            evolution['market_conditions'].append(snapshot.market_conditions)

        return evolution

    def get_signal_statistics(self) -> Dict:
        """
        Obtener estadísticas de señales históricas

        Returns:
            Diccionario con estadísticas
        """
        if not self.snapshots:
            return {}

        total_signals = 0
        buy_signals = 0
        sell_signals = 0
        total_rr = 0
        total_confidence = 0

        for snapshot in self.snapshots:
            total_signals += len(snapshot.signals)

            for signal in snapshot.signals:
                if signal.signal_type == SignalType.BUY:
                    buy_signals += 1
                elif signal.signal_type == SignalType.SELL:
                    sell_signals += 1

                total_rr += signal.risk_reward
                total_confidence += signal.confidence

        avg_rr = total_rr / max(total_signals, 1)
        avg_confidence = total_confidence / max(total_signals, 1)

        return {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'avg_rr': avg_rr,
            'avg_confidence': avg_confidence,
            'snapshots_count': len(self.snapshots),
            'timespan': {
                'start': self.snapshots[0].timestamp,
                'end': self.snapshots[-1].timestamp,
                'duration': self.snapshots[-1].timestamp - self.snapshots[0].timestamp
            }
        }

# Funciones de utilidad
def create_historical_manager(symbol: str, timeframe: str) -> SMCHistoricalManager:
    """
    Crear gestor histórico

    Args:
        symbol: Símbolo del par
        timeframe: Timeframe

    Returns:
        Gestor histórico
    """
    return SMCHistoricalManager(symbol, timeframe)

def analyze_historical_performance(snapshots: List[HistoricalSnapshot]) -> Dict:
    """
    Analizar rendimiento histórico de señales

    Args:
        snapshots: Lista de snapshots históricos

    Returns:
        Análisis de rendimiento
    """
    if not snapshots:
        return {}

    total_signals = 0
    total_buy = 0
    total_sell = 0
    rr_values = []
    confidence_values = []

    for snapshot in snapshots:
        total_signals += len(snapshot.signals)

        for signal in snapshot.signals:
            if signal.signal_type == SignalType.BUY:
                total_buy += 1
            else:
                total_sell += 1

            rr_values.append(signal.risk_reward)
            confidence_values.append(signal.confidence)

    analysis = {
        'total_signals': total_signals,
        'buy_signals': total_buy,
        'sell_signals': total_sell,
        'avg_rr': np.mean(rr_values) if rr_values else 0,
        'avg_confidence': np.mean(confidence_values) if confidence_values else 0,
        'best_rr': max(rr_values) if rr_values else 0,
        'worst_rr': min(rr_values) if rr_values else 0,
        'timespan': {
            'start': snapshots[0].timestamp,
            'end': snapshots[-1].timestamp,
            'duration': snapshots[-1].timestamp - snapshots[0].timestamp
        }
    }

    return analysis

# Ejemplo de uso
if __name__ == "__main__":
    print("📅 SMC Historical Manager - Ejemplo de uso")
    print("=" * 45)

    # Crear gestor histórico
    manager = create_historical_manager("BTC/USDT", "15m")

    # Generar timeline histórico
    timeline = manager.generate_historical_timeline(HistoricalPeriod.DAY_1, 5)

    # Analizar rendimiento
    performance = analyze_historical_performance(timeline)

    print("\n📊 Análisis de rendimiento histórico:")
    print(f"   Total señales: {performance.get('total_signals', 0)}")
    print(f"   Señales BUY: {performance.get('buy_signals', 0)}")
    print(f"   Señales SELL: {performance.get('sell_signals', 0)}")
    print(f"   R:R promedio: {performance.get('avg_rr', 0):.2f}")
    print(f"   Confianza promedio: {performance.get('avg_confidence', 0):.1%}")
