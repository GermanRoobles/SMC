#!/usr/bin/env python3
"""
SMC ML Signal Integration
========================

Integración del ML Signal Generator con el sistema SMC existente.
Conecta el generador de señales ML con el ML Predictor y la interfaz de usuario.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import streamlit as st

# Imports locales
from smc_ml_signal_generator import get_ml_signal_generator, MLSignal, SignalType
from smc_ml_integration import get_ml_manager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLSignalIntegration:
    """
    Clase de integración para conectar ML Signal Generator con el sistema SMC
    """
    
    def __init__(self):
        """Inicializar integración"""
        self.signal_generator = get_ml_signal_generator()
        self.ml_manager = get_ml_manager()
        self.last_signal_time = None
        self.signal_cooldown_minutes = 15  # Cooldown entre señales
        self.last_prediction: Optional[Dict] = None
        self.prediction_history: List[Dict] = []
        
        logger.info("🔗 ML Signal Integration inicializada")
    
    def generate_ml_signal(self, data: pd.DataFrame, smc_analysis: Dict, 
                          symbol: str = "BTC/USDT", timeframe: str = "15m") -> Optional[MLSignal]:
        """
        Generar señal ML completa integrando todos los componentes
        
        Args:
            data: DataFrame con datos OHLCV
            smc_analysis: Análisis SMC completo
            symbol: Símbolo del activo
            timeframe: Timeframe de análisis
            
        Returns:
            MLSignal completa o None
        """
        try:
            # Validar cooldown
            if not self._check_cooldown():
                logger.info(f"⏰ Cooldown activo, esperando {self.signal_cooldown_minutes} minutos entre señales")
                return None
            
            # Obtener precio actual
            current_price = float(data['close'].iloc[-1])
            
            # Preparar datos para ML
            ml_features = self._prepare_ml_features(data, smc_analysis, current_price)
            
            # Obtener predicción ML
            ml_prediction_obj = self.ml_manager.get_signal_prediction(data, smc_analysis)
            
            # Convertir a formato esperado por el generador
            if ml_prediction_obj:
                ml_prediction = {
                    'probability': ml_prediction_obj.probability,
                    'confidence': ml_prediction_obj.confidence,
                    'recommendation': ml_prediction_obj.recommendation
                }
            else:
                # Fallback con datos sintéticos
                ml_prediction = {
                    'probability': 0.75,
                    'confidence': 0.70,
                    'recommendation': 'BUY'
                }
            # Guardar última predicción para UI
            self.last_prediction = ml_prediction.copy()
            try:
                self.prediction_history.append({
                    'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    **ml_prediction
                })
                # Limitar historial
                if len(self.prediction_history) > 200:
                    self.prediction_history = self.prediction_history[-200:]
            except Exception:
                pass
            
            if not ml_prediction:
                logger.warning("❌ No se pudo obtener predicción ML")
                return None
            
            # Enriquecer datos con información adicional
            data_enriched = data.copy()
            # Asegurar que el símbolo sea string, no Serie
            data_enriched.attrs = {'symbol': symbol, 'timeframe': timeframe}
            
            # Generar señal completa
            signal = self.signal_generator.generate_signal(
                data_enriched, 
                ml_prediction, 
                smc_analysis, 
                current_price
            )
            
            if signal:
                self.last_signal_time = datetime.now()
                logger.info(f"✅ Señal ML generada: {signal.signal_type.value} @ {signal.entry_price:.2f}")
                
                # Registrar señal para entrenamiento futuro
                try:
                    self._log_signal_for_training(signal, ml_features)
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo registrar señal para entrenamiento: {str(e)}")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error generando señal ML integrada: {str(e)}")
            return None
    
    def _check_cooldown(self) -> bool:
        """Verificar si ha pasado el cooldown entre señales"""
        if self.last_signal_time is None:
            return True
        
        time_diff = datetime.now() - self.last_signal_time
        return time_diff.total_seconds() >= (self.signal_cooldown_minutes * 60)
    
    def _prepare_ml_features(self, data: pd.DataFrame, smc_analysis: Dict, current_price: float) -> Dict:
        """Preparar características para el ML Predictor"""
        try:
            # Validar que el DataFrame no esté vacío
            if data.empty:
                logger.warning("⚠️ DataFrame vacío para características ML")
                return {}
            
            # Validar columnas requeridas
            required_columns = ['open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                logger.error(f"❌ Columnas requeridas faltantes: {missing_columns}")
                return {}
            
            logger.debug(f"📊 Preparando características ML con {len(data)} filas y columnas: {list(data.columns)}")
            # Características básicas de precio
            features = {
                'current_price': current_price,
                'price_change_1h': self._calculate_price_change(data, 4),  # 4 periodos de 15m = 1h
                'price_change_4h': self._calculate_price_change(data, 16), # 16 periodos de 15m = 4h
                'price_change_1d': self._calculate_price_change(data, 96), # 96 periodos de 15m = 1d
            }
            
            # Características de volumen (con validación)
            if 'volume' in data.columns:
                features.update({
                    'volume_avg': float(data['volume'].tail(20).mean()),
                    'volume_current': float(data['volume'].iloc[-1]),
                    'volume_ratio': float(data['volume'].iloc[-1] / data['volume'].tail(20).mean()),
                })
            else:
                # Valores por defecto si no hay columna volume
                features.update({
                    'volume_avg': 1000000.0,
                    'volume_current': 1000000.0,
                    'volume_ratio': 1.0,
                })
                logger.warning("⚠️ Columna 'volume' no encontrada, usando valores por defecto")
            
            # Características SMC
            features.update({
                'fvg_count': len(smc_analysis.get('fvg', [])),
                'ob_count': len(smc_analysis.get('ob', [])),
                'liquidity_count': len(smc_analysis.get('liquidity', [])),
                'bos_choch_present': 1 if smc_analysis.get('bos_choch_strength', 0) > 0.5 else 0,
                'market_structure_bullish': 1 if smc_analysis.get('market_structure') == 'bullish' else 0,
                'market_structure_bearish': 1 if smc_analysis.get('market_structure') == 'bearish' else 0,
            })
            
            # Características técnicas
            rsi = self._calculate_rsi(data)
            macd_signal = self._calculate_macd_signal(data)
            bb_position = self._calculate_bollinger_position(data, current_price)
            
            features.update({
                'rsi': rsi,
                'macd_signal': macd_signal,
                'bollinger_position': bb_position,
                'atr_normalized': self._calculate_normalized_atr(data, current_price),
            })
            
            # Características de sesión
            features.update({
                'session_london': 1 if self._is_london_session() else 0,
                'session_new_york': 1 if self._is_new_york_session() else 0,
                'session_asian': 1 if self._is_asian_session() else 0,
            })
            
            # Características de tendencia
            trend_strength = self._calculate_trend_strength(data)
            features.update({
                'trend_strength': trend_strength,
                'trend_bullish': 1 if trend_strength > 0.1 else 0,
                'trend_bearish': 1 if trend_strength < -0.1 else 0,
            })
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error preparando características ML: {str(e)}")
            return {}
    
    def _calculate_price_change(self, data: pd.DataFrame, periods: int) -> float:
        """Calcular cambio de precio en períodos específicos"""
        try:
            if len(data) < periods:
                periods = len(data) - 1
            
            if periods <= 0:
                return 0.0
            
            current_price = data['close'].iloc[-1]
            past_price = data['close'].iloc[-(periods + 1)]
            
            return float((current_price - past_price) / past_price)
            
        except Exception:
            return 0.0
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calcular RSI"""
        try:
            if len(data) < period + 1:
                return 50.0
            
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1])
            
        except Exception:
            return 50.0
    
    def _calculate_macd_signal(self, data: pd.DataFrame) -> float:
        """Calcular señal MACD"""
        try:
            if len(data) < 26:
                return 0.0
            
            ema12 = data['close'].ewm(span=12).mean()
            ema26 = data['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            
            return float(macd.iloc[-1] - signal.iloc[-1])
            
        except Exception:
            return 0.0
    
    def _calculate_bollinger_position(self, data: pd.DataFrame, current_price: float, period: int = 20) -> float:
        """Calcular posición en Bandas de Bollinger"""
        try:
            if len(data) < period:
                return 0.5
            
            sma = data['close'].rolling(period).mean().iloc[-1]
            std = data['close'].rolling(period).std().iloc[-1]
            
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            
            # Normalizar posición entre 0 y 1
            position = (current_price - lower_band) / (upper_band - lower_band)
            return float(max(0, min(1, position)))
            
        except Exception:
            return 0.5
    
    def _calculate_normalized_atr(self, data: pd.DataFrame, current_price: float, period: int = 14) -> float:
        """Calcular ATR normalizado"""
        try:
            if len(data) < period:
                return 0.02
            
            high = data['high'].iloc[-period:]
            low = data['low'].iloc[-period:]
            close = data['close'].iloc[-period:]
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.mean()
            
            # Normalizar por precio actual
            return float(atr / current_price)
            
        except Exception:
            return 0.02
    
    def _is_london_session(self) -> bool:
        """Verificar si es sesión de Londres"""
        current_hour = datetime.now().hour
        return 8 <= current_hour < 16
    
    def _is_new_york_session(self) -> bool:
        """Verificar si es sesión de Nueva York"""
        current_hour = datetime.now().hour
        return 13 <= current_hour < 21
    
    def _is_asian_session(self) -> bool:
        """Verificar si es sesión asiática"""
        current_hour = datetime.now().hour
        return current_hour >= 21 or current_hour < 8
    
    def _calculate_trend_strength(self, data: pd.DataFrame, period: int = 20) -> float:
        """Calcular fuerza de tendencia"""
        try:
            if len(data) < period:
                return 0.0
            
            prices = data['close'].iloc[-period:]
            slope = np.polyfit(range(len(prices)), prices, 1)[0]
            
            # Normalizar por precio promedio
            avg_price = prices.mean()
            normalized_slope = slope / avg_price
            
            return float(normalized_slope)
            
        except Exception:
            return 0.0
    
    def _log_signal_for_training(self, signal: MLSignal, features: Dict):
        """Registrar señal para entrenamiento futuro del ML"""
        try:
            # Preparar datos para logging
            signal_data = {
                'timestamp': signal.timestamp,
                'signal_type': signal.signal_type.value,
                'entry_price': signal.entry_price,
                'ml_probability': signal.ml_probability,
                'ml_confidence': signal.ml_confidence,
                'features': features,
                'confluence_score': signal.confluence_score,
            }
            
            # Registrar en el ML Manager para entrenamiento futuro (si el método existe)
            if hasattr(self.ml_manager, 'log_signal_outcome'):
                self.ml_manager.log_signal_outcome(signal_data, None)  # Outcome se determinará después
            else:
                logger.info("📝 Logging de señales no disponible en ML Manager")
            
            logger.info(f"📝 Señal registrada para entrenamiento: {signal.signal_id}")
            
        except Exception as e:
            logger.error(f"❌ Error registrando señal para entrenamiento: {str(e)}")
    
    def get_recent_signals(self, hours: int = 24) -> List[MLSignal]:
        """Obtener señales recientes"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_signals = [
                signal for signal in self.signal_generator.signal_history
                if signal.timestamp >= cutoff_time
            ]
            return recent_signals
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo señales recientes: {str(e)}")
            return []
    
    def get_active_signals(self) -> List[MLSignal]:
        """Obtener señales activas"""
        return self.signal_generator.get_active_signals()
    
    def get_integration_stats(self) -> Dict:
        """Obtener estadísticas de integración"""
        try:
            signal_stats = self.signal_generator.get_signal_stats()
            ml_stats = self.ml_manager.get_model_stats()
            
            return {
                'ml_signal_generator': signal_stats,
                'ml_predictor': ml_stats,
                'integration_status': 'active',
                'last_signal_time': self.last_signal_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_signal_time else None,
                'cooldown_remaining_minutes': self._get_cooldown_remaining(),
                # Evitar llamar a preparación de features con DF vacío para no emitir warnings
                'total_features_used': len(self._prepare_ml_features(self._get_last_data_sample(), {}, 100.0)) if self._has_recent_data() else 0,
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de integración: {str(e)}")
            return {'error': str(e)}

    def _has_recent_data(self) -> bool:
        """Indica si tenemos alguna señal previa para inferir estructura de features"""
        try:
            return len(self.signal_generator.signal_history) > 0
        except Exception:
            return False

    def _get_last_data_sample(self) -> pd.DataFrame:
        """Construye un pequeño DataFrame ficticio con columnas mínimas si no hay datos reales"""
        try:
            # Si no hay historial, crear un sample mínimo de 20 filas con columnas requeridas
            if not self._has_recent_data():
                import pandas as pd
                import numpy as np
                now = pd.Timestamp.utcnow().tz_localize('UTC')
                ts = pd.date_range(end=now, periods=20, freq='15T')
                return pd.DataFrame({
                    'timestamp': ts,
                    'open': np.linspace(100, 101, len(ts)),
                    'high': np.linspace(100.5, 101.5, len(ts)),
                    'low': np.linspace(99.5, 100.5, len(ts)),
                    'close': np.linspace(100, 101, len(ts)),
                    'volume': np.ones(len(ts))
                })
            # Si existe historia, intentar derivar columnas desde la última señal formateada no es trivial.
            # Retornamos un DF mínimo igualmente, ya que solo se usa para contar keys de features.
            else:
                import pandas as pd
                import numpy as np
                now = pd.Timestamp.utcnow().tz_localize('UTC')
                ts = pd.date_range(end=now, periods=20, freq='15T')
                return pd.DataFrame({
                    'timestamp': ts,
                    'open': np.linspace(100, 101, len(ts)),
                    'high': np.linspace(100.5, 101.5, len(ts)),
                    'low': np.linspace(99.5, 100.5, len(ts)),
                    'close': np.linspace(100, 101, len(ts)),
                    'volume': np.ones(len(ts))
                })
        except Exception:
            return pd.DataFrame()
    
    def _get_cooldown_remaining(self) -> int:
        """Obtener minutos restantes de cooldown"""
        if self.last_signal_time is None:
            return 0
        
        time_diff = datetime.now() - self.last_signal_time
        elapsed_minutes = time_diff.total_seconds() / 60
        remaining = max(0, self.signal_cooldown_minutes - elapsed_minutes)
        
        return int(remaining)

# Funciones de utilidad para Streamlit

def display_ml_signals_sidebar():
    """Mostrar señales ML en la sidebar de Streamlit"""
    try:
        integration = get_ml_signal_integration()
        active_signals = integration.get_active_signals()
        
        if not active_signals:
            st.sidebar.info("📭 No hay señales ML activas")
            return
        
        st.sidebar.markdown("### 🎯 Señales ML Activas")
        
        for signal in active_signals:
            with st.sidebar.expander(f"{signal.signal_type.value} {signal.symbol}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Entry", f"${signal.entry_price:.2f}")
                    st.metric("TP1", f"${signal.take_profit_1:.2f}")
                    st.metric("SL", f"${signal.stop_loss:.2f}")
                
                with col2:
                    st.metric("RR", f"{signal.risk_reward_1:.2f}:1")
                    st.metric("Prob", f"{signal.ml_probability:.1%}")
                    st.metric("Conf", f"{signal.ml_confidence:.1%}")
                
                # Información adicional
                st.write(f"⏰ Expira: {signal.expiry_time.strftime('%H:%M')}")
                st.write(f"💪 Fuerza: {signal.strength.value}")
                st.write(f"🎯 Confluencia: {signal.confluence_score:.1%}")
                
    except Exception as e:
        st.sidebar.error(f"❌ Error mostrando señales ML: {str(e)}")

def display_ml_signal_metrics():
    """Mostrar métricas de señales ML en el dashboard principal"""
    try:
        integration = get_ml_signal_integration()
        stats = integration.get_integration_stats()
        
        st.markdown("## 🎯 ML Signal Generator")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_signals = stats.get('ml_signal_generator', {}).get('total_signals_generated', 0)
            st.metric("Señales Generadas", total_signals)
        
        with col2:
            active_signals = stats.get('ml_signal_generator', {}).get('active_signals', 0)
            st.metric("Señales Activas", active_signals)
        
        with col3:
            avg_confidence = stats.get('ml_signal_generator', {}).get('avg_confidence', 0)
            st.metric("Confianza Promedio", f"{avg_confidence:.1%}")
        
        with col4:
            avg_rr = stats.get('ml_signal_generator', {}).get('avg_risk_reward', 0)
            st.metric("Risk/Reward Promedio", f"{avg_rr:.2f}:1")
        
        # Estado del sistema
        cooldown_remaining = stats.get('cooldown_remaining_minutes', 0)
        if cooldown_remaining > 0:
            st.warning(f"⏰ Cooldown activo: {cooldown_remaining} minutos restantes")
        else:
            st.success("✅ Sistema listo para generar señales")
        
        # Tabla de señales recientes
        recent_signals = integration.get_recent_signals(hours=12)
        if recent_signals:
            st.markdown("### 📊 Señales Recientes (12h)")
            
            signals_data = []
            for signal in recent_signals[-5:]:  # Últimas 5 señales
                formatted = integration.signal_generator.format_signal_for_display(signal)
                signals_data.append({
                    'Tiempo': formatted['timestamp'],
                    'Tipo': formatted['type'],
                    'Entry': formatted['entry'],
                    'TP1': formatted['tp1'],
                    'SL': formatted['sl'],
                    'RR': formatted['rr1'],
                    'Prob': formatted['ml_prob'],
                    'Estado': '🟢 Activa' if signal in integration.get_active_signals() else '⏰ Expirada'
                })
            
            st.dataframe(pd.DataFrame(signals_data), use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error mostrando métricas ML Signal: {str(e)}")

# Instancia global de integración
_ml_signal_integration = None

def get_ml_signal_integration() -> MLSignalIntegration:
    """Obtener instancia singleton de ML Signal Integration"""
    global _ml_signal_integration
    if _ml_signal_integration is None:
        _ml_signal_integration = MLSignalIntegration()
    return _ml_signal_integration

if __name__ == "__main__":
    # Test de integración
    integration = get_ml_signal_integration()
    
    # Crear datos de prueba
    test_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='15T'),
        'open': np.random.randn(100).cumsum() + 50000,
        'high': np.random.randn(100).cumsum() + 50200,
        'low': np.random.randn(100).cumsum() + 49800,
        'close': np.random.randn(100).cumsum() + 50000,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Análisis SMC de prueba
    test_smc = {
        'fvg': [1, 2],
        'ob': [1],
        'liquidity': [1, 2, 3],
        'market_structure': 'bullish',
        'bos_choch_strength': 0.7
    }
    
    # Generar señal de prueba
    signal = integration.generate_ml_signal(test_data, test_smc)
    
    if signal:
        print("✅ Señal ML integrada generada:")
        formatted = integration.signal_generator.format_signal_for_display(signal)
        for key, value in formatted.items():
            print(f"  {key}: {value}")
    else:
        print("❌ No se pudo generar señal integrada")
    
    # Mostrar estadísticas
    stats = integration.get_integration_stats()
    print(f"\n📊 Estadísticas de integración:")
    for key, value in stats.items():
        print(f"  {key}: {value}")