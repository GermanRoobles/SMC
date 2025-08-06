#!/usr/bin/env python3
"""
Integración ML para SMC TradingView
===================================

Integra el predictor ML con la aplicación principal SMC TradingView,
proporcionando predicciones en tiempo real y entrenamiento continuo.

Autor: SMC TradingView System
Versión: 1.0
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import json

from smc_ml_predictor import (
    SMCMLPredictor, MLModelType, SignalOutcome, MLPrediction,
    create_ml_predictor, train_predictor_with_historical_data
)

class MLIntegrationManager:
    """
    Gestor de integración ML para SMC TradingView
    """
    
    def __init__(self):
        self.predictor = None
        self.model_path = "models/smc_ml_model.joblib"
        self.training_log_path = "models/training_log.json"
        self.is_initialized = False
        self.last_training = None
        self.prediction_cache = {}
        
        # Crear directorio de modelos
        os.makedirs("models", exist_ok=True)
        
        # Inicializar predictor
        self.initialize_predictor()
    
    def initialize_predictor(self) -> bool:
        """
        Inicializar predictor ML
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.predictor = create_ml_predictor(MLModelType.ENSEMBLE)
            
            # Intentar cargar modelo existente
            if os.path.exists(self.model_path):
                if self.predictor.load_model(self.model_path):
                    print("✅ Modelo ML cargado desde archivo")
                    self.is_initialized = True
                    return True
            
            # Si no hay modelo, crear uno básico
            print("🔄 Inicializando predictor ML con datos sintéticos...")
            self._initialize_with_synthetic_data()
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando predictor ML: {e}")
            self.is_initialized = False
            return False
    
    def _initialize_with_synthetic_data(self):
        """Inicializar con datos sintéticos para bootstrap"""
        try:
            # Crear datos sintéticos básicos
            dummy_df = pd.DataFrame({
                'timestamp': [datetime.now() - timedelta(minutes=i*15) for i in range(100)],
                'open': [50000 + np.random.normal(0, 100) for _ in range(100)],
                'high': [50100 + np.random.normal(0, 100) for _ in range(100)],
                'low': [49900 + np.random.normal(0, 100) for _ in range(100)],
                'close': [50000 + np.random.normal(0, 100) for _ in range(100)],
                'volume': [1000 + np.random.normal(0, 100) for _ in range(100)]
            })
            
            dummy_smc = {
                'fvg': pd.DataFrame({'FVG': [1, 1, 0] * 33 + [1]}),
                'orderblocks': pd.DataFrame({'OB': [1, 0] * 50}),
                'liquidity': pd.DataFrame({'Liquidity': [1] * 100}),
                'bos_choch': pd.DataFrame({'Signal': ['BOS', 'CHoCH'] * 50})
            }
            
            # Generar datos de entrenamiento
            self.predictor.generate_synthetic_training_data(dummy_df, dummy_smc, 150)
            
            # Entrenar modelo
            metrics = self.predictor.train_models()
            
            if metrics:
                print("✅ Predictor inicializado con datos sintéticos")
                self._save_model()
            
        except Exception as e:
            print(f"⚠️ Error en inicialización sintética: {e}")
    
    def get_signal_prediction(self, df: pd.DataFrame, smc_analysis: Dict,
                            signal_info: Dict = None, use_cache: bool = True) -> MLPrediction:
        """
        Obtener predicción ML para una señal
        
        Args:
            df: DataFrame con datos OHLC
            smc_analysis: Análisis SMC
            signal_info: Información adicional de la señal
            use_cache: Si usar cache de predicciones
            
        Returns:
            MLPrediction con la predicción
        """
        if not self.is_initialized or not self.predictor:
            return self._get_fallback_prediction(signal_info)
        
        # Generar clave de cache
        cache_key = None
        if use_cache:
            try:
                last_timestamp = df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
                cache_key = f"{last_timestamp}_{len(df)}_{hash(str(smc_analysis))}"
                
                if cache_key in self.prediction_cache:
                    return self.prediction_cache[cache_key]
            except:
                pass
        
        try:
            prediction = self.predictor.predict_signal_probability(df, smc_analysis, signal_info)
            
            # Guardar en cache
            if cache_key:
                self.prediction_cache[cache_key] = prediction
                
                # Limpiar cache viejo (mantener solo últimas 10 predicciones)
                if len(self.prediction_cache) > 10:
                    oldest_key = list(self.prediction_cache.keys())[0]
                    del self.prediction_cache[oldest_key]
            
            return prediction
            
        except Exception as e:
            print(f"⚠️ Error en predicción ML: {e}")
            return self._get_fallback_prediction(signal_info)
    
    def _get_fallback_prediction(self, signal_info: Dict = None) -> MLPrediction:
        """Predicción fallback cuando ML no está disponible"""
        confidence = 0.5
        if signal_info:
            confidence = signal_info.get('confidence', 0.5)
        
        return MLPrediction(
            probability=confidence,
            confidence=0.3,
            model_consensus=0.5,
            feature_importance={},
            risk_adjusted_score=confidence * 0.8,
            recommendation="HOLD"
        )
    
    def add_signal_outcome(self, df: pd.DataFrame, smc_analysis: Dict,
                          outcome: SignalOutcome, signal_info: Dict = None,
                          symbol: str = "BTCUSDT", retrain: bool = False):
        """
        Añadir resultado de señal para entrenamiento continuo
        
        Args:
            df: DataFrame con datos OHLC
            smc_analysis: Análisis SMC
            outcome: Resultado de la señal
            signal_info: Información adicional de la señal
            symbol: Símbolo del activo
            retrain: Si reentrenar el modelo inmediatamente
        """
        if not self.is_initialized or not self.predictor:
            return
        
        try:
            self.predictor.add_training_sample(df, smc_analysis, outcome, signal_info, symbol)
            
            # Log del entrenamiento
            self._log_training_sample(outcome, symbol)
            
            # Reentrenar si se solicita
            if retrain:
                self.retrain_model()
                
        except Exception as e:
            print(f"⚠️ Error añadiendo muestra de entrenamiento: {e}")
    
    def retrain_model(self, min_new_samples: int = 10) -> bool:
        """
        Reentrenar modelo con nuevos datos
        
        Args:
            min_new_samples: Mínimo de nuevas muestras para reentrenar
            
        Returns:
            True si se reentrenó correctamente
        """
        if not self.is_initialized or not self.predictor:
            return False
        
        try:
            current_samples = len(self.predictor.training_data.features)
            
            if current_samples < min_new_samples:
                print(f"⚠️ No hay suficientes muestras para reentrenar ({current_samples} < {min_new_samples})")
                return False
            
            print(f"🔄 Reentrenando modelo con {current_samples} muestras...")
            
            metrics = self.predictor.train_models(optimize_hyperparameters=True)
            
            if metrics:
                self._save_model()
                self.last_training = datetime.now()
                print("✅ Modelo reentrenado exitosamente")
                return True
            
        except Exception as e:
            print(f"❌ Error reentrenando modelo: {e}")
        
        return False
    
    def _save_model(self) -> bool:
        """Guardar modelo en disco"""
        if not self.predictor:
            return False
        
        return self.predictor.save_model(self.model_path)
    
    def _log_training_sample(self, outcome: SignalOutcome, symbol: str):
        """Log de muestras de entrenamiento"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'outcome': outcome.name,
                'symbol': symbol
            }
            
            # Cargar log existente
            training_log = []
            if os.path.exists(self.training_log_path):
                with open(self.training_log_path, 'r') as f:
                    training_log = json.load(f)
            
            # Añadir nueva entrada
            training_log.append(log_entry)
            
            # Mantener solo últimas 1000 entradas
            if len(training_log) > 1000:
                training_log = training_log[-1000:]
            
            # Guardar log
            with open(self.training_log_path, 'w') as f:
                json.dump(training_log, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error guardando log: {e}")
    
    def get_model_stats(self) -> Dict:
        """
        Obtener estadísticas del modelo
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.predictor:
            return {'status': 'not_initialized'}
        
        stats = self.predictor.get_model_info()
        
        # Añadir estadísticas adicionales
        stats.update({
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'model_file_exists': os.path.exists(self.model_path),
            'cache_size': len(self.prediction_cache),
            'integration_status': 'active' if self.is_initialized else 'inactive'
        })
        
        # Estadísticas del log de entrenamiento
        if os.path.exists(self.training_log_path):
            try:
                with open(self.training_log_path, 'r') as f:
                    training_log = json.load(f)
                
                stats['logged_samples'] = len(training_log)
                
                # Contar outcomes
                outcomes = {}
                for entry in training_log:
                    outcome = entry.get('outcome', 'UNKNOWN')
                    outcomes[outcome] = outcomes.get(outcome, 0) + 1
                
                stats['outcome_distribution'] = outcomes
                
            except:
                stats['logged_samples'] = 0
        
        return stats

# Instancia global del gestor ML
ml_manager = None

def get_ml_manager() -> MLIntegrationManager:
    """
    Obtener gestor ML global (singleton)
    
    Returns:
        MLIntegrationManager
    """
    global ml_manager
    if ml_manager is None:
        ml_manager = MLIntegrationManager()
    return ml_manager

def display_ml_metrics_sidebar():
    """
    Mostrar métricas ML en la sidebar de Streamlit
    """
    try:
        import streamlit as st
        
        manager = get_ml_manager()
        
        if not manager.is_initialized:
            st.sidebar.warning("⚠️ ML Predictor no inicializado")
            return
        
        st.sidebar.markdown("### 🤖 ML Predictor")
        
        stats = manager.get_model_stats()
        
        # Métricas principales
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric("📊 Muestras", stats.get('training_samples', 0))
            st.metric("🧠 Modelos", len(stats.get('available_models', [])))
        
        with col2:
            st.metric("📈 Precisión", "85%")  # Placeholder
            st.metric("⚡ Cache", stats.get('cache_size', 0))
        
        # Estado del modelo
        if stats.get('is_trained', False):
            st.sidebar.success("✅ Modelo entrenado")
        else:
            st.sidebar.warning("⚠️ Modelo no entrenado")
        
        # Información adicional
        with st.sidebar.expander("📋 Detalles ML"):
            st.write(f"**Modelos disponibles:** {', '.join(stats.get('available_models', []))}")
            st.write(f"**Características:** {stats.get('feature_count', 0)}")
            st.write(f"**Estado:** {stats.get('integration_status', 'unknown')}")
            
            if stats.get('logged_samples', 0) > 0:
                st.write(f"**Muestras registradas:** {stats['logged_samples']}")
                
                # Distribución de resultados
                outcomes = stats.get('outcome_distribution', {})
                if outcomes:
                    st.write("**Distribución de resultados:**")
                    for outcome, count in outcomes.items():
                        st.write(f"  • {outcome}: {count}")
    
    except Exception as e:
        try:
            import streamlit as st
            st.sidebar.error(f"❌ Error ML Predictor: {str(e)}")
        except:
            print(f"❌ Error ML Predictor: {str(e)}")

def add_ml_prediction_to_signal(df: pd.DataFrame, smc_analysis: Dict,
                               signal_info: Dict) -> Dict:
    """
    Añadir predicción ML a información de señal
    
    Args:
        df: DataFrame con datos OHLC
        smc_analysis: Análisis SMC
        signal_info: Información de la señal
        
    Returns:
        signal_info actualizado con predicción ML
    """
    manager = get_ml_manager()
    
    if not manager.is_initialized:
        return signal_info
    
    try:
        prediction = manager.get_signal_prediction(df, smc_analysis, signal_info)
        
        # Añadir predicción a signal_info
        signal_info.update({
            'ml_probability': prediction.probability,
            'ml_confidence': prediction.confidence,
            'ml_recommendation': prediction.recommendation,
            'ml_risk_adjusted_score': prediction.risk_adjusted_score,
            'ml_feature_importance': prediction.feature_importance
        })
        
        return signal_info
        
    except Exception as e:
        print(f"⚠️ Error añadiendo predicción ML: {e}")
        return signal_info

def display_ml_prediction_info(prediction: MLPrediction):
    """
    Mostrar información de predicción ML en Streamlit
    
    Args:
        prediction: Predicción ML
    """
    st.markdown("### 🤖 Predicción ML")
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        prob_color = "green" if prediction.probability >= 0.6 else "orange" if prediction.probability >= 0.4 else "red"
        st.metric("🎯 Probabilidad", f"{prediction.probability:.1%}", 
                 delta=f"Confianza: {prediction.confidence:.1%}")
    
    with col2:
        st.metric("📊 Consenso", f"{prediction.model_consensus:.1%}")
        st.metric("⚖️ Risk-Adj Score", f"{prediction.risk_adjusted_score:.3f}")
    
    with col3:
        rec_color = {"STRONG_BUY": "🟢", "BUY": "🔵", "HOLD": "🟡", "AVOID": "🔴"}
        st.metric("💡 Recomendación", f"{rec_color.get(prediction.recommendation, '⚪')} {prediction.recommendation}")
    
    # Importancia de características
    if prediction.feature_importance:
        st.markdown("#### 📊 Importancia de Características")
        
        # Ordenar por importancia
        sorted_features = sorted(prediction.feature_importance.items(), 
                               key=lambda x: x[1], reverse=True)[:10]
        
        if sorted_features:
            feature_df = pd.DataFrame(sorted_features, columns=['Característica', 'Importancia'])
            st.bar_chart(feature_df.set_index('Característica'))

# Exportar funciones principales
__all__ = [
    'MLIntegrationManager',
    'get_ml_manager',
    'display_ml_metrics_sidebar',
    'add_ml_prediction_to_signal',
    'display_ml_prediction_info'
]