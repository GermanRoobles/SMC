#!/usr/bin/env python3
"""
SMC ML Signal Generator
======================

Generador de señales completas basado en Machine Learning que produce:
- Puntos de entrada específicos
- Take Profit levels (TP1, TP2, TP3)
- Stop Loss inteligente
- Timing y validez de señal
- Risk/Reward ratio optimizado

Integra con el ML Predictor para generar señales de alta calidad.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Tipos de señales ML"""
    BUY = "BUY"
    SELL = "SELL"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"
    HOLD = "HOLD"
    AVOID = "AVOID"

class SignalStrength(Enum):
    """Fuerza de la señal"""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"

@dataclass
class MLSignal:
    """Estructura de señal ML completa"""
    # Información básica
    timestamp: datetime
    symbol: str
    timeframe: str
    signal_type: SignalType
    strength: SignalStrength
    
    # ML Predictor info
    ml_probability: float
    ml_confidence: float
    ml_recommendation: str
    
    # Niveles de precio
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    
    # Risk Management
    risk_reward_1: float
    risk_reward_2: float
    risk_reward_3: float
    position_size_percent: float
    max_risk_percent: float
    
    # Timing
    signal_validity_hours: int
    expiry_time: datetime
    session_type: str
    
    # Contexto técnico
    current_price: float
    atr_value: float
    volatility: float
    trend_direction: str
    market_structure: str
    
    # Características SMC
    fvg_count: int
    ob_count: int
    liquidity_zones: int
    bos_choch_strength: float
    
    # Métricas adicionales
    volume_profile: str
    momentum_score: float
    confluence_score: float
    signal_id: str

class MLSignalGenerator:
    """
    Generador de señales ML completas
    
    Combina ML Predictor con análisis técnico avanzado para generar
    señales completas con entrada, TP/SL y gestión de riesgo.
    """
    
    def __init__(self):
        """Inicializar el generador de señales ML"""
        self.signals_cache = {}
        self.active_signals = []
        self.signal_history = []
        self.config = self._load_default_config()
        
        logger.info("🚀 ML Signal Generator inicializado")
    
    def _load_default_config(self) -> Dict:
        """Cargar configuración por defecto"""
        return {
            # Risk Management
            'max_risk_per_trade': 2.0,  # 2% máximo por trade
            'default_position_size': 1.0,  # 1% del capital
            'min_risk_reward': 1.5,  # RR mínimo 1.5:1
            
            # Signal Timing
            'default_validity_hours': 4,  # 4 horas de validez
            'max_validity_hours': 24,  # máximo 24 horas
            
            # ML Thresholds
            'min_ml_probability': 0.40,  # 40% mínimo (ajustado para demostración)
            'min_ml_confidence': 0.50,   # 50% confianza mínima (ajustado para demostración)
            'strong_signal_threshold': 0.85,  # 85% para señales fuertes
            
            # Technical Filters
            'min_atr_multiplier': 1.5,   # SL mínimo 1.5x ATR
            'max_atr_multiplier': 3.0,   # SL máximo 3x ATR
            'tp_multipliers': [2.0, 3.5, 5.0],  # TP1, TP2, TP3
            
            # Confluence
            'min_confluence_score': 0.5,  # Score mínimo de confluencia (ajustado para demostración)
        }
    
    def generate_signal(self, data: pd.DataFrame, ml_prediction: Dict, 
                       smc_analysis: Dict, current_price: float) -> Optional[MLSignal]:
        """Generar señal ML completa"""
        logger.info(f"🚀 Iniciando generación de señal ML")
        logger.info(f"📊 Datos: {data.shape}, ML: {ml_prediction}")
        """
        Generar señal ML completa
        
        Args:
            data: DataFrame con datos OHLCV
            ml_prediction: Predicción del ML Predictor
            smc_analysis: Análisis SMC completo
            current_price: Precio actual
            
        Returns:
            MLSignal completa o None si no cumple criterios
        """
        try:
            # Validar entrada
            if not self._validate_inputs(data, ml_prediction, current_price):
                return None
            
            # Evaluar si generar señal
            if not self._should_generate_signal(ml_prediction):
                logger.info(f"❌ Señal rechazada: ML probability {ml_prediction.get('probability', 0):.2f}")
                return None
            
            # Determinar tipo y fuerza de señal
            signal_type = self._determine_signal_type(ml_prediction)
            signal_strength = self._determine_signal_strength(ml_prediction)
            
            # Calcular ATR y volatilidad
            atr_value = self._calculate_atr(data)
            volatility = self._calculate_volatility(data)
            
            # Calcular niveles de precio
            entry_price = self._calculate_entry_price(current_price, signal_type, atr_value)
            stop_loss = self._calculate_stop_loss(entry_price, signal_type, atr_value)
            tp_levels = self._calculate_take_profits(entry_price, stop_loss, signal_type)
            
            # Calcular Risk/Reward ratios
            rr_ratios = self._calculate_risk_rewards(entry_price, stop_loss, tp_levels)
            
            # Validar RR mínimo
            if rr_ratios[0] < self.config['min_risk_reward']:
                logger.info(f"❌ Señal rechazada: RR {rr_ratios[0]:.2f} < {self.config['min_risk_reward']}")
                return None
            
            # Calcular gestión de riesgo
            position_size = self._calculate_position_size(signal_strength, rr_ratios[0])
            max_risk = min(position_size * 2, self.config['max_risk_per_trade'])
            
            # Determinar timing
            validity_hours = self._calculate_signal_validity(signal_strength, volatility)
            expiry_time = datetime.now() + timedelta(hours=validity_hours)
            
            # Análizar contexto técnico
            trend_direction = self._analyze_trend(data)
            market_structure = smc_analysis.get('market_structure', 'neutral')
            session_type = self._determine_session_type()
            
            # Calcular confluence score
            confluence_score = self._calculate_confluence_score(
                ml_prediction, smc_analysis, trend_direction, market_structure
            )
            
            # Validar confluence mínima
            if confluence_score < self.config['min_confluence_score']:
                logger.info(f"❌ Señal rechazada: Confluence {confluence_score:.2f} < {self.config['min_confluence_score']}")
                return None
            
            # Crear señal completa
            # Obtener símbolo de attrs o usar Unknown como fallback
            symbol_value = data.attrs.get('symbol', 'Unknown') if hasattr(data, 'attrs') else 'Unknown'
            timeframe_value = data.attrs.get('timeframe', '15m') if hasattr(data, 'attrs') else '15m'
            
            signal = MLSignal(
                # Información básica
                timestamp=datetime.now(),
                symbol=symbol_value,
                timeframe=timeframe_value,
                signal_type=signal_type,
                strength=signal_strength,
                
                # ML Predictor info
                ml_probability=ml_prediction.get('probability', 0.0),
                ml_confidence=ml_prediction.get('confidence', 0.0),
                ml_recommendation=ml_prediction.get('recommendation', 'HOLD'),
                
                # Niveles de precio
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=tp_levels[0],
                take_profit_2=tp_levels[1],
                take_profit_3=tp_levels[2],
                
                # Risk Management
                risk_reward_1=rr_ratios[0],
                risk_reward_2=rr_ratios[1],
                risk_reward_3=rr_ratios[2],
                position_size_percent=position_size,
                max_risk_percent=max_risk,
                
                # Timing
                signal_validity_hours=validity_hours,
                expiry_time=expiry_time,
                session_type=session_type,
                
                # Contexto técnico
                current_price=current_price,
                atr_value=atr_value,
                volatility=volatility,
                trend_direction=trend_direction,
                market_structure=market_structure,
                
                # Características SMC
                fvg_count=len(smc_analysis.get('fvg', [])),
                ob_count=len(smc_analysis.get('ob', [])),
                liquidity_zones=len(smc_analysis.get('liquidity', [])),
                bos_choch_strength=smc_analysis.get('bos_choch_strength', 0.0),
                
                # Métricas adicionales
                volume_profile=self._analyze_volume_profile(data),
                momentum_score=self._calculate_momentum_score(data),
                confluence_score=confluence_score,
                signal_id=self._generate_signal_id()
            )
            
            # Guardar señal
            self.active_signals.append(signal)
            self.signal_history.append(signal)
            
            logger.info(f"✅ Señal ML generada: {signal.signal_type.value} {signal.symbol} @ {signal.entry_price:.2f}")
            logger.info(f"   🎯 TP1: {signal.take_profit_1:.2f} (RR: {signal.risk_reward_1:.2f})")
            logger.info(f"   🛡️ SL: {signal.stop_loss:.2f}")
            logger.info(f"   ⏰ Válida por: {signal.signal_validity_hours}h")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error generando señal ML: {str(e)}")
            return None
    
    def _validate_inputs(self, data: pd.DataFrame, ml_prediction: Dict, current_price: float) -> bool:
        """Validar inputs de entrada"""
        if data.empty:
            logger.warning("❌ DataFrame vacío")
            return False
        
        if not ml_prediction or 'probability' not in ml_prediction:
            logger.warning("❌ ML prediction inválida")
            return False
        
        if current_price <= 0:
            logger.warning("❌ Precio actual inválido")
            return False
        
        return True
    
    def _should_generate_signal(self, ml_prediction: Dict) -> bool:
        """Determinar si generar señal basado en ML"""
        probability = ml_prediction.get('probability', 0.0)
        confidence = ml_prediction.get('confidence', 0.0)
        
        # Debug logging
        logger.info(f"🔍 ML Signal Check: prob={probability:.3f}, conf={confidence:.3f}")
        logger.info(f"🔍 Thresholds: min_prob={self.config['min_ml_probability']:.3f}, min_conf={self.config['min_ml_confidence']:.3f}")
        
        result = (probability >= self.config['min_ml_probability'] and 
                 confidence >= self.config['min_ml_confidence'])
        
        logger.info(f"🔍 Signal generation: {'✅ PASS' if result else '❌ FAIL'}")
        
        return result
    
    def _determine_signal_type(self, ml_prediction: Dict) -> SignalType:
        """Determinar tipo de señal"""
        recommendation = ml_prediction.get('recommendation', 'HOLD')
        probability = ml_prediction.get('probability', 0.0)
        
        if recommendation in ['STRONG_BUY'] or probability >= 0.9:
            return SignalType.STRONG_BUY
        elif recommendation in ['BUY'] or probability >= 0.8:
            return SignalType.BUY
        elif recommendation in ['STRONG_SELL'] or probability <= 0.1:
            return SignalType.STRONG_SELL
        elif recommendation in ['SELL'] or probability <= 0.2:
            return SignalType.SELL
        else:
            return SignalType.HOLD
    
    def _determine_signal_strength(self, ml_prediction: Dict) -> SignalStrength:
        """Determinar fuerza de la señal"""
        probability = ml_prediction.get('probability', 0.0)
        confidence = ml_prediction.get('confidence', 0.0)
        
        combined_score = (probability + confidence) / 2
        
        if combined_score >= 0.9:
            return SignalStrength.VERY_STRONG
        elif combined_score >= 0.8:
            return SignalStrength.STRONG
        elif combined_score >= 0.7:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calcular Average True Range"""
        try:
            if len(data) < period:
                return data['high'].iloc[-1] - data['low'].iloc[-1]
            
            high = data['high'].iloc[-period:]
            low = data['low'].iloc[-period:]
            close = data['close'].iloc[-period:]
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return true_range.mean()
            
        except Exception:
            return data['high'].iloc[-1] - data['low'].iloc[-1]
    
    def _calculate_volatility(self, data: pd.DataFrame, period: int = 20) -> float:
        """Calcular volatilidad"""
        try:
            if len(data) < period:
                period = len(data)
            
            returns = data['close'].pct_change().iloc[-period:]
            return returns.std() * np.sqrt(period)
            
        except Exception:
            return 0.02  # 2% por defecto
    
    def _calculate_entry_price(self, current_price: float, signal_type: SignalType, atr: float) -> float:
        """Calcular precio de entrada optimizado"""
        # Para señales BUY: entrada ligeramente por encima del precio actual
        # Para señales SELL: entrada ligeramente por debajo del precio actual
        
        adjustment_factor = 0.1  # 10% del ATR
        
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            return current_price + (atr * adjustment_factor)
        elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            return current_price - (atr * adjustment_factor)
        else:
            return current_price
    
    def _calculate_stop_loss(self, entry_price: float, signal_type: SignalType, atr: float) -> float:
        """Calcular Stop Loss inteligente"""
        # SL basado en ATR con multiplicadores adaptativos
        
        if signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
            multiplier = self.config['min_atr_multiplier']  # SL más ajustado para señales fuertes
        else:
            multiplier = (self.config['min_atr_multiplier'] + self.config['max_atr_multiplier']) / 2
        
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)
    
    def _calculate_take_profits(self, entry_price: float, stop_loss: float, signal_type: SignalType) -> List[float]:
        """Calcular niveles de Take Profit"""
        risk = abs(entry_price - stop_loss)
        
        tp_multipliers = self.config['tp_multipliers']
        take_profits = []
        
        for multiplier in tp_multipliers:
            if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                tp = entry_price + (risk * multiplier)
            else:
                tp = entry_price - (risk * multiplier)
            
            take_profits.append(tp)
        
        return take_profits
    
    def _calculate_risk_rewards(self, entry_price: float, stop_loss: float, tp_levels: List[float]) -> List[float]:
        """Calcular Risk/Reward ratios"""
        risk = abs(entry_price - stop_loss)
        rr_ratios = []
        
        for tp in tp_levels:
            reward = abs(tp - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            rr_ratios.append(rr_ratio)
        
        return rr_ratios
    
    def _calculate_position_size(self, strength: SignalStrength, rr_ratio: float) -> float:
        """Calcular tamaño de posición basado en fuerza y RR"""
        base_size = self.config['default_position_size']
        
        # Ajustar por fuerza de señal
        strength_multiplier = {
            SignalStrength.WEAK: 0.5,
            SignalStrength.MODERATE: 0.75,
            SignalStrength.STRONG: 1.0,
            SignalStrength.VERY_STRONG: 1.25
        }.get(strength, 0.75)
        
        # Ajustar por RR ratio
        rr_multiplier = min(1.5, max(0.5, rr_ratio / 2))
        
        position_size = base_size * strength_multiplier * rr_multiplier
        
        # Limitar al máximo configurado
        return min(position_size, self.config['max_risk_per_trade'])
    
    def _calculate_signal_validity(self, strength: SignalStrength, volatility: float) -> int:
        """Calcular validez de la señal en horas"""
        base_hours = self.config['default_validity_hours']
        
        # Señales más fuertes duran más tiempo
        strength_multiplier = {
            SignalStrength.WEAK: 0.5,
            SignalStrength.MODERATE: 0.75,
            SignalStrength.STRONG: 1.0,
            SignalStrength.VERY_STRONG: 1.5
        }.get(strength, 1.0)
        
        # Mayor volatilidad = menor validez
        volatility_adjustment = max(0.5, 1 - (volatility * 10))
        
        validity_hours = int(base_hours * strength_multiplier * volatility_adjustment)
        
        return max(1, min(validity_hours, self.config['max_validity_hours']))
    
    def _analyze_trend(self, data: pd.DataFrame, period: int = 20) -> str:
        """Analizar dirección de tendencia"""
        try:
            if len(data) < period:
                period = len(data)
            
            prices = data['close'].iloc[-period:]
            sma = prices.rolling(period).mean().iloc[-1]
            current_price = prices.iloc[-1]
            
            if current_price > sma * 1.02:
                return "bullish"
            elif current_price < sma * 0.98:
                return "bearish"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    def _determine_session_type(self) -> str:
        """Determinar tipo de sesión de trading"""
        current_hour = datetime.now().hour
        
        if 8 <= current_hour < 16:
            return "london"
        elif 13 <= current_hour < 21:
            return "new_york"
        elif 21 <= current_hour or current_hour < 8:
            return "asian"
        else:
            return "overlap"
    
    def _calculate_confluence_score(self, ml_prediction: Dict, smc_analysis: Dict, 
                                  trend: str, market_structure: str) -> float:
        """Calcular score de confluencia"""
        score = 0.0
        
        # ML Predictor weight (40%)
        ml_score = (ml_prediction.get('probability', 0) + ml_prediction.get('confidence', 0)) / 2
        score += ml_score * 0.4
        
        # Trend alignment (20%)
        signal_direction = ml_prediction.get('recommendation', 'HOLD')
        if (signal_direction in ['BUY', 'STRONG_BUY'] and trend == 'bullish') or \
           (signal_direction in ['SELL', 'STRONG_SELL'] and trend == 'bearish'):
            score += 0.2
        
        # SMC indicators (25%)
        fvg_count = len(smc_analysis.get('fvg', []))
        ob_count = len(smc_analysis.get('ob', []))
        liquidity_count = len(smc_analysis.get('liquidity', []))
        
        smc_score = min(1.0, (fvg_count + ob_count + liquidity_count) / 10)
        score += smc_score * 0.25
        
        # Market structure (15%)
        if market_structure in ['bullish', 'bearish']:
            score += 0.15
        elif market_structure == 'neutral':
            score += 0.075
        
        return min(1.0, score)
    
    def _analyze_volume_profile(self, data: pd.DataFrame) -> str:
        """Analizar perfil de volumen"""
        try:
            recent_volume = data['volume'].iloc[-10:].mean()
            avg_volume = data['volume'].mean()
            
            if recent_volume > avg_volume * 1.5:
                return "high"
            elif recent_volume < avg_volume * 0.5:
                return "low"
            else:
                return "normal"
                
        except Exception:
            return "normal"
    
    def _calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """Calcular score de momentum"""
        try:
            if len(data) < 10:
                return 0.5
            
            # RSI simple
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            # Normalizar RSI a 0-1
            if current_rsi > 70:
                return 0.8 + (current_rsi - 70) / 30 * 0.2
            elif current_rsi < 30:
                return 0.2 - (30 - current_rsi) / 30 * 0.2
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    def _generate_signal_id(self) -> str:
        """Generar ID único para la señal"""
        import uuid
        return f"ML_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def get_active_signals(self) -> List[MLSignal]:
        """Obtener señales activas (no expiradas)"""
        current_time = datetime.now()
        active = [signal for signal in self.active_signals 
                 if signal.expiry_time > current_time]
        
        # Actualizar lista
        self.active_signals = active
        return active
    
    def get_signal_stats(self) -> Dict:
        """Obtener estadísticas de señales"""
        active_signals = self.get_active_signals()
        
        return {
            'total_signals_generated': len(self.signal_history),
            'active_signals': len(active_signals),
            'expired_signals': len(self.signal_history) - len(active_signals),
            'signal_types': {
                signal_type.value: len([s for s in self.signal_history 
                                      if s.signal_type == signal_type])
                for signal_type in SignalType
            },
            'avg_confidence': np.mean([s.ml_confidence for s in self.signal_history]) if self.signal_history else 0,
            'avg_probability': np.mean([s.ml_probability for s in self.signal_history]) if self.signal_history else 0,
            'avg_risk_reward': np.mean([s.risk_reward_1 for s in self.signal_history]) if self.signal_history else 0,
        }
    
    def format_signal_for_display(self, signal: MLSignal) -> Dict:
        """Formatear señal para mostrar en UI"""
        return {
            'id': signal.signal_id,
            'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': signal.symbol,
            'type': signal.signal_type.value,
            'strength': signal.strength.value,
            'entry': f"${signal.entry_price:.2f}",
            'sl': f"${signal.stop_loss:.2f}",
            'tp1': f"${signal.take_profit_1:.2f}",
            'tp2': f"${signal.take_profit_2:.2f}",
            'tp3': f"${signal.take_profit_3:.2f}",
            'rr1': f"{signal.risk_reward_1:.2f}:1",
            'rr2': f"{signal.risk_reward_2:.2f}:1",
            'rr3': f"{signal.risk_reward_3:.2f}:1",
            'ml_prob': f"{signal.ml_probability:.1%}",
            'ml_conf': f"{signal.ml_confidence:.1%}",
            'position_size': f"{signal.position_size_percent:.1f}%",
            'validity': f"{signal.signal_validity_hours}h",
            'expires': signal.expiry_time.strftime('%H:%M'),
            'confluence': f"{signal.confluence_score:.1%}",
        }

# Instancia global del generador
_ml_signal_generator = None

def get_ml_signal_generator() -> MLSignalGenerator:
    """Obtener instancia singleton del ML Signal Generator"""
    global _ml_signal_generator
    if _ml_signal_generator is None:
        _ml_signal_generator = MLSignalGenerator()
    return _ml_signal_generator

if __name__ == "__main__":
    # Test básico del generador
    generator = get_ml_signal_generator()
    
    # Crear datos de prueba
    test_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='15T'),
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Predicción ML de prueba
    test_ml_prediction = {
        'probability': 0.87,
        'confidence': 0.92,
        'recommendation': 'STRONG_BUY'
    }
    
    # Análisis SMC de prueba
    test_smc_analysis = {
        'fvg': [1, 2, 3],
        'ob': [1, 2],
        'liquidity': [1],
        'market_structure': 'bullish',
        'bos_choch_strength': 0.8
    }
    
    # Generar señal de prueba
    signal = generator.generate_signal(
        test_data, 
        test_ml_prediction, 
        test_smc_analysis, 
        100.0
    )
    
    if signal:
        print("✅ Señal ML generada exitosamente:")
        formatted = generator.format_signal_for_display(signal)
        for key, value in formatted.items():
            print(f"  {key}: {value}")
    else:
        print("❌ No se pudo generar señal")
    
    # Mostrar estadísticas
    stats = generator.get_signal_stats()
    print(f"\n📊 Estadísticas: {stats}")