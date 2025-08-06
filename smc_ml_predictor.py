#!/usr/bin/env python3
"""
SMC ML Predictor - Machine Learning para Smart Money Concepts
============================================================

Sistema de machine learning avanzado que predice la probabilidad de éxito
de señales SMC basándose en patrones históricos y características del mercado.

Características:
- Predicción de probabilidad de señales
- Optimización automática de parámetros
- Aprendizaje continuo
- Múltiples algoritmos ML
- Feature engineering avanzado
- Backtesting con ML

Autor: SMC TradingView System
Versión: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# ML imports
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.feature_selection import SelectKBest, f_classif
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ Scikit-learn no disponible. Instalando automáticamente...")

# Instalar dependencias ML si no están disponibles
if not ML_AVAILABLE:
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn", "joblib"])
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import SVC
        from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        from sklearn.feature_selection import SelectKBest, f_classif
        import joblib
        ML_AVAILABLE = True
        print("✅ Scikit-learn instalado correctamente")
    except Exception as e:
        print(f"❌ Error instalando scikit-learn: {e}")
        ML_AVAILABLE = False

class MLModelType(Enum):
    """Tipos de modelos ML disponibles"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LOGISTIC_REGRESSION = "logistic_regression"
    SVM = "svm"
    ENSEMBLE = "ensemble"

class SignalOutcome(Enum):
    """Resultados posibles de una señal"""
    WIN = 1
    LOSS = 0
    PENDING = -1

@dataclass
class MLFeatures:
    """Características extraídas para ML"""
    # Características SMC
    fvg_count: float = 0.0
    ob_count: float = 0.0
    liquidity_zones: float = 0.0
    choch_count: float = 0.0
    bos_count: float = 0.0
    swing_strength: float = 0.0
    
    # Características técnicas
    rsi: float = 50.0
    macd_signal: float = 0.0
    bollinger_position: float = 0.5
    atr_normalized: float = 0.0
    volume_ratio: float = 1.0
    
    # Características de mercado
    volatility: float = 0.0
    trend_strength: float = 0.0
    session_type: int = 0  # 0=asian, 1=london, 2=ny
    time_of_day: float = 0.0
    day_of_week: int = 0
    
    # Características de señal
    signal_confidence: float = 0.0
    risk_reward: float = 0.0
    entry_quality: float = 0.0
    confluence_score: float = 0.0
    
    def to_array(self) -> np.ndarray:
        """Convertir a array numpy para ML"""
        return np.array([
            self.fvg_count, self.ob_count, self.liquidity_zones,
            self.choch_count, self.bos_count, self.swing_strength,
            self.rsi, self.macd_signal, self.bollinger_position,
            self.atr_normalized, self.volume_ratio, self.volatility,
            self.trend_strength, self.session_type, self.time_of_day,
            self.day_of_week, self.signal_confidence, self.risk_reward,
            self.entry_quality, self.confluence_score
        ])
    
    def get_feature_names(self) -> List[str]:
        """Obtener nombres de características"""
        return [
            'fvg_count', 'ob_count', 'liquidity_zones',
            'choch_count', 'bos_count', 'swing_strength',
            'rsi', 'macd_signal', 'bollinger_position',
            'atr_normalized', 'volume_ratio', 'volatility',
            'trend_strength', 'session_type', 'time_of_day',
            'day_of_week', 'signal_confidence', 'risk_reward',
            'entry_quality', 'confluence_score'
        ]

@dataclass
class MLPrediction:
    """Predicción ML para una señal"""
    probability: float
    confidence: float
    model_consensus: float
    feature_importance: Dict[str, float]
    risk_adjusted_score: float
    recommendation: str  # "STRONG_BUY", "BUY", "HOLD", "AVOID"

@dataclass
class MLTrainingData:
    """Datos de entrenamiento para ML"""
    features: List[MLFeatures] = field(default_factory=list)
    outcomes: List[SignalOutcome] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    
    def add_sample(self, features: MLFeatures, outcome: SignalOutcome, 
                   timestamp: datetime, symbol: str):
        """Añadir muestra de entrenamiento"""
        self.features.append(features)
        self.outcomes.append(outcome)
        self.timestamps.append(timestamp)
        self.symbols.append(symbol)
    
    def to_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """Convertir a arrays numpy"""
        X = np.array([f.to_array() for f in self.features])
        y = np.array([o.value for o in self.outcomes])
        return X, y

class SMCMLPredictor:
    """
    Predictor ML para señales SMC
    """
    
    def __init__(self, model_type: MLModelType = MLModelType.ENSEMBLE):
        self.model_type = model_type
        self.models = {}
        self.scalers = {}
        self.feature_selector = None
        self.is_trained = False
        self.training_data = MLTrainingData()
        self.feature_names = MLFeatures().get_feature_names()
        
        # Configuración de modelos
        self.model_configs = {
            MLModelType.RANDOM_FOREST: {
                'model': RandomForestClassifier,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'random_state': 42
                }
            },
            MLModelType.GRADIENT_BOOSTING: {
                'model': GradientBoostingClassifier,
                'params': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 6,
                    'random_state': 42
                }
            },
            MLModelType.LOGISTIC_REGRESSION: {
                'model': LogisticRegression,
                'params': {
                    'random_state': 42,
                    'max_iter': 1000
                }
            },
            MLModelType.SVM: {
                'model': SVC,
                'params': {
                    'kernel': 'rbf',
                    'probability': True,
                    'random_state': 42
                }
            }
        }
    
    def extract_features(self, df: pd.DataFrame, smc_analysis: Dict, 
                        signal_info: Dict = None) -> MLFeatures:
        """
        Extraer características para ML desde datos OHLC y análisis SMC
        
        Args:
            df: DataFrame con datos OHLC
            smc_analysis: Análisis SMC
            signal_info: Información adicional de la señal
            
        Returns:
            MLFeatures con características extraídas
        """
        features = MLFeatures()
        
        try:
            # Características SMC
            features.fvg_count = len(smc_analysis.get('fvg', [])) if 'fvg' in smc_analysis else 0
            features.ob_count = len(smc_analysis.get('orderblocks', [])) if 'orderblocks' in smc_analysis else 0
            features.liquidity_zones = len(smc_analysis.get('liquidity', [])) if 'liquidity' in smc_analysis else 0
            
            # Contar CHoCH y BOS
            bos_choch_data = smc_analysis.get('bos_choch', pd.DataFrame())
            if not bos_choch_data.empty and hasattr(bos_choch_data, '__len__'):
                features.choch_count = len(bos_choch_data) * 0.6  # Aproximación CHoCH
                features.bos_count = len(bos_choch_data) * 0.4    # Aproximación BOS
            
            # Características técnicas
            if len(df) >= 14:
                # RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                features.rsi = rsi.iloc[-1] if not rsi.empty else 50.0
                
                # ATR normalizado
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(window=14).mean()
                features.atr_normalized = (atr.iloc[-1] / df['close'].iloc[-1]) if not atr.empty else 0.0
                
                # Volatilidad
                returns = df['close'].pct_change()
                features.volatility = returns.rolling(window=20).std().iloc[-1] if len(returns) >= 20 else 0.0
                
                # Tendencia
                sma_short = df['close'].rolling(window=10).mean()
                sma_long = df['close'].rolling(window=20).mean()
                if not sma_short.empty and not sma_long.empty:
                    features.trend_strength = (sma_short.iloc[-1] - sma_long.iloc[-1]) / sma_long.iloc[-1]
            
            # Características de tiempo
            if len(df) > 0:
                last_time = df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
                if isinstance(last_time, str):
                    last_time = pd.to_datetime(last_time)
                
                features.time_of_day = last_time.hour + last_time.minute / 60.0
                features.day_of_week = last_time.weekday()
                
                # Sesión de trading
                hour = last_time.hour
                if 0 <= hour < 8:
                    features.session_type = 0  # Asian
                elif 8 <= hour < 16:
                    features.session_type = 1  # London
                else:
                    features.session_type = 2  # NY
            
            # Características de volumen
            if len(df) >= 20 and 'volume' in df.columns:
                avg_volume = df['volume'].rolling(window=20).mean()
                current_volume = df['volume'].iloc[-1]
                features.volume_ratio = current_volume / avg_volume.iloc[-1] if not avg_volume.empty else 1.0
            
            # Características de señal (si están disponibles)
            if signal_info:
                features.signal_confidence = signal_info.get('confidence', 0.0)
                features.risk_reward = signal_info.get('risk_reward', 0.0)
                features.entry_quality = signal_info.get('entry_quality', 0.0)
                features.confluence_score = signal_info.get('confluence_score', 0.0)
            
            # Swing strength (basado en volatilidad y estructura)
            features.swing_strength = min(features.volatility * 10, 1.0)
            
        except Exception as e:
            print(f"⚠️ Error extrayendo características: {e}")
        
        return features
    
    def add_training_sample(self, df: pd.DataFrame, smc_analysis: Dict,
                          outcome: SignalOutcome, signal_info: Dict = None,
                          symbol: str = "BTCUSDT"):
        """
        Añadir muestra de entrenamiento
        
        Args:
            df: DataFrame con datos OHLC
            smc_analysis: Análisis SMC
            outcome: Resultado de la señal
            signal_info: Información adicional de la señal
            symbol: Símbolo del activo
        """
        features = self.extract_features(df, smc_analysis, signal_info)
        timestamp = datetime.now()
        if len(df) > 0 and 'timestamp' in df.columns:
            timestamp = df['timestamp'].iloc[-1]
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
        
        self.training_data.add_sample(features, outcome, timestamp, symbol)
        print(f"📊 Muestra de entrenamiento añadida: {outcome.name} para {symbol}")
    
    def generate_synthetic_training_data(self, df: pd.DataFrame, smc_analysis: Dict,
                                       num_samples: int = 100) -> None:
        """
        Generar datos de entrenamiento sintéticos basados en patrones SMC
        
        Args:
            df: DataFrame con datos OHLC
            smc_analysis: Análisis SMC
            num_samples: Número de muestras a generar
        """
        print(f"🔄 Generando {num_samples} muestras de entrenamiento sintéticas...")
        
        base_features = self.extract_features(df, smc_analysis)
        
        for i in range(num_samples):
            # Crear variaciones de las características base
            features = MLFeatures()
            
            # Añadir ruido controlado a las características
            noise_factor = 0.1
            features.fvg_count = max(0, base_features.fvg_count + np.random.normal(0, noise_factor))
            features.ob_count = max(0, base_features.ob_count + np.random.normal(0, noise_factor))
            features.liquidity_zones = max(0, base_features.liquidity_zones + np.random.normal(0, noise_factor))
            features.choch_count = max(0, base_features.choch_count + np.random.normal(0, noise_factor))
            features.bos_count = max(0, base_features.bos_count + np.random.normal(0, noise_factor))
            
            # Características técnicas con ruido
            features.rsi = np.clip(base_features.rsi + np.random.normal(0, 5), 0, 100)
            features.atr_normalized = max(0, base_features.atr_normalized + np.random.normal(0, noise_factor * 0.1))
            features.volatility = max(0, base_features.volatility + np.random.normal(0, noise_factor * 0.01))
            features.trend_strength = base_features.trend_strength + np.random.normal(0, noise_factor * 0.1)
            features.volume_ratio = max(0.1, base_features.volume_ratio + np.random.normal(0, noise_factor))
            
            # Características de tiempo aleatorias
            features.session_type = np.random.randint(0, 3)
            features.time_of_day = np.random.uniform(0, 24)
            features.day_of_week = np.random.randint(0, 7)
            
            # Características de señal simuladas
            features.signal_confidence = np.random.uniform(0.3, 0.9)
            features.risk_reward = np.random.uniform(1.0, 4.0)
            features.entry_quality = np.random.uniform(0.4, 1.0)
            features.confluence_score = np.random.uniform(0.2, 1.0)
            features.swing_strength = np.random.uniform(0.0, 1.0)
            
            # Determinar outcome basado en características (lógica heurística)
            win_probability = self._calculate_synthetic_win_probability(features)
            outcome = SignalOutcome.WIN if np.random.random() < win_probability else SignalOutcome.LOSS
            
            # Añadir muestra
            self.training_data.add_sample(
                features, outcome, 
                datetime.now() - timedelta(days=np.random.randint(1, 365)),
                "BTCUSDT"
            )
        
        print(f"✅ {num_samples} muestras sintéticas generadas")
    
    def _calculate_synthetic_win_probability(self, features: MLFeatures) -> float:
        """
        Calcular probabilidad de éxito sintética basada en características
        
        Args:
            features: Características de la señal
            
        Returns:
            Probabilidad de éxito (0-1)
        """
        # Lógica heurística para determinar probabilidad de éxito
        score = 0.5  # Base
        
        # Factores positivos
        if features.fvg_count > 2:
            score += 0.1
        if features.ob_count > 1:
            score += 0.1
        if features.liquidity_zones > 3:
            score += 0.1
        if features.signal_confidence > 0.7:
            score += 0.15
        if features.risk_reward > 2.0:
            score += 0.1
        if features.confluence_score > 0.6:
            score += 0.1
        if 30 < features.rsi < 70:  # RSI neutral
            score += 0.05
        
        # Factores negativos
        if features.volatility > 0.05:  # Alta volatilidad
            score -= 0.1
        if features.volume_ratio < 0.5:  # Bajo volumen
            score -= 0.05
        if features.signal_confidence < 0.4:
            score -= 0.15
        
        return np.clip(score, 0.1, 0.9)
    
    def train_models(self, test_size: float = 0.2, optimize_hyperparameters: bool = True) -> Dict:
        """
        Entrenar modelos ML
        
        Args:
            test_size: Porcentaje de datos para testing
            optimize_hyperparameters: Si optimizar hiperparámetros
            
        Returns:
            Métricas de entrenamiento
        """
        if not ML_AVAILABLE:
            print("❌ Scikit-learn no disponible. No se puede entrenar.")
            return {}
        
        if len(self.training_data.features) < 10:
            print("⚠️ Datos de entrenamiento insuficientes. Generando datos sintéticos...")
            # Generar datos sintéticos básicos
            dummy_df = pd.DataFrame({
                'timestamp': [datetime.now()],
                'open': [50000], 'high': [51000], 'low': [49000], 'close': [50500], 'volume': [1000]
            })
            dummy_smc = {'fvg': [], 'orderblocks': [], 'liquidity': [], 'bos_choch': pd.DataFrame()}
            self.generate_synthetic_training_data(dummy_df, dummy_smc, 200)
        
        print(f"🤖 Entrenando modelos ML con {len(self.training_data.features)} muestras...")
        
        # Preparar datos
        X, y = self.training_data.to_arrays()
        
        # Filtrar solo muestras con resultados conocidos (no PENDING)
        valid_mask = y != SignalOutcome.PENDING.value
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(X) < 5:
            print("❌ No hay suficientes muestras válidas para entrenar")
            return {}
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Escalado de características
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['main'] = scaler
        
        # Selección de características
        if optimize_hyperparameters:
            self.feature_selector = SelectKBest(f_classif, k=min(15, X.shape[1]))
            X_train_selected = self.feature_selector.fit_transform(X_train_scaled, y_train)
            X_test_selected = self.feature_selector.transform(X_test_scaled)
        else:
            X_train_selected = X_train_scaled
            X_test_selected = X_test_scaled
        
        metrics = {}
        
        # Entrenar modelos individuales
        models_to_train = [MLModelType.RANDOM_FOREST, MLModelType.GRADIENT_BOOSTING, 
                          MLModelType.LOGISTIC_REGRESSION]
        
        for model_type in models_to_train:
            try:
                print(f"  📊 Entrenando {model_type.value}...")
                
                config = self.model_configs[model_type]
                model = config['model'](**config['params'])
                
                # Optimización de hiperparámetros
                if optimize_hyperparameters and model_type == MLModelType.RANDOM_FOREST:
                    param_grid = {
                        'n_estimators': [50, 100, 200],
                        'max_depth': [5, 10, 15],
                        'min_samples_split': [2, 5, 10]
                    }
                    grid_search = GridSearchCV(model, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
                    grid_search.fit(X_train_selected, y_train)
                    model = grid_search.best_estimator_
                    print(f"    🎯 Mejores parámetros: {grid_search.best_params_}")
                
                # Entrenar modelo
                model.fit(X_train_selected, y_train)
                
                # Predicciones
                y_pred = model.predict(X_test_selected)
                y_pred_proba = model.predict_proba(X_test_selected)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                
                # Métricas
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                try:
                    auc = roc_auc_score(y_test, y_pred_proba)
                except:
                    auc = 0.5
                
                model_metrics = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'auc_roc': auc
                }
                
                metrics[model_type.value] = model_metrics
                self.models[model_type.value] = model
                
                print(f"    ✅ {model_type.value}: Accuracy={accuracy:.3f}, AUC={auc:.3f}")
                
            except Exception as e:
                print(f"    ❌ Error entrenando {model_type.value}: {e}")
        
        self.is_trained = len(self.models) > 0
        
        if self.is_trained:
            print(f"🎉 Entrenamiento completado. {len(self.models)} modelos entrenados.")
        
        return metrics
    
    def predict_signal_probability(self, df: pd.DataFrame, smc_analysis: Dict,
                                 signal_info: Dict = None) -> MLPrediction:
        """
        Predecir probabilidad de éxito de una señal
        
        Args:
            df: DataFrame con datos OHLC
            smc_analysis: Análisis SMC
            signal_info: Información adicional de la señal
            
        Returns:
            MLPrediction con la predicción
        """
        if not self.is_trained or not ML_AVAILABLE:
            # Predicción fallback sin ML
            return MLPrediction(
                probability=0.6,
                confidence=0.3,
                model_consensus=0.6,
                feature_importance={},
                risk_adjusted_score=0.5,
                recommendation="HOLD"
            )
        
        # Extraer características
        features = self.extract_features(df, smc_analysis, signal_info)
        X = features.to_array().reshape(1, -1)
        
        # Escalar características
        if 'main' in self.scalers:
            X_scaled = self.scalers['main'].transform(X)
        else:
            X_scaled = X
        
        # Selección de características
        if self.feature_selector:
            X_selected = self.feature_selector.transform(X_scaled)
        else:
            X_selected = X_scaled
        
        # Predicciones de todos los modelos
        predictions = []
        probabilities = []
        
        for model_name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X_selected)[0, 1]
                else:
                    pred = model.predict(X_selected)[0]
                    proba = pred if pred > 0 else 0.3
                
                predictions.append(proba)
                probabilities.append(proba)
                
            except Exception as e:
                print(f"⚠️ Error en predicción con {model_name}: {e}")
        
        if not predictions:
            return MLPrediction(
                probability=0.5,
                confidence=0.2,
                model_consensus=0.5,
                feature_importance={},
                risk_adjusted_score=0.4,
                recommendation="HOLD"
            )
        
        # Consenso de modelos
        avg_probability = np.mean(predictions)
        model_consensus = 1.0 - np.std(predictions)  # Menor desviación = mayor consenso
        
        # Importancia de características (usando Random Forest si está disponible)
        feature_importance = {}
        if 'random_forest' in self.models:
            try:
                rf_model = self.models['random_forest']
                if hasattr(rf_model, 'feature_importances_'):
                    importances = rf_model.feature_importances_
                    feature_names = self.feature_names
                    if self.feature_selector:
                        # Mapear características seleccionadas
                        selected_features = self.feature_selector.get_support()
                        feature_names = [name for i, name in enumerate(feature_names) if selected_features[i]]
                    
                    for name, importance in zip(feature_names, importances):
                        feature_importance[name] = float(importance)
            except Exception as e:
                print(f"⚠️ Error calculando importancia: {e}")
        
        # Score ajustado por riesgo
        risk_reward = signal_info.get('risk_reward', 2.0) if signal_info else 2.0
        risk_adjusted_score = avg_probability * min(risk_reward / 2.0, 1.5)
        
        # Recomendación
        if avg_probability >= 0.75 and model_consensus >= 0.8:
            recommendation = "STRONG_BUY"
        elif avg_probability >= 0.6 and model_consensus >= 0.6:
            recommendation = "BUY"
        elif avg_probability >= 0.45:
            recommendation = "HOLD"
        else:
            recommendation = "AVOID"
        
        return MLPrediction(
            probability=avg_probability,
            confidence=model_consensus,
            model_consensus=model_consensus,
            feature_importance=feature_importance,
            risk_adjusted_score=risk_adjusted_score,
            recommendation=recommendation
        )
    
    def save_model(self, filepath: str) -> bool:
        """
        Guardar modelo entrenado
        
        Args:
            filepath: Ruta donde guardar el modelo
            
        Returns:
            True si se guardó correctamente
        """
        if not self.is_trained or not ML_AVAILABLE:
            print("❌ No hay modelo entrenado para guardar")
            return False
        
        try:
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'feature_selector': self.feature_selector,
                'feature_names': self.feature_names,
                'model_type': self.model_type,
                'training_samples': len(self.training_data.features)
            }
            
            joblib.dump(model_data, filepath)
            print(f"💾 Modelo guardado en: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando modelo: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        Cargar modelo guardado
        
        Args:
            filepath: Ruta del modelo guardado
            
        Returns:
            True si se cargó correctamente
        """
        if not ML_AVAILABLE:
            print("❌ Scikit-learn no disponible")
            return False
        
        try:
            model_data = joblib.load(filepath)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.feature_selector = model_data['feature_selector']
            self.feature_names = model_data['feature_names']
            self.model_type = model_data['model_type']
            self.is_trained = True
            
            print(f"📂 Modelo cargado desde: {filepath}")
            print(f"   📊 Muestras de entrenamiento: {model_data.get('training_samples', 'N/A')}")
            print(f"   🤖 Modelos disponibles: {list(self.models.keys())}")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """
        Obtener información del modelo
        
        Returns:
            Diccionario con información del modelo
        """
        return {
            'is_trained': self.is_trained,
            'model_type': self.model_type.value if self.model_type else None,
            'available_models': list(self.models.keys()),
            'training_samples': len(self.training_data.features),
            'feature_count': len(self.feature_names),
            'ml_available': ML_AVAILABLE
        }

# Funciones de utilidad
def create_ml_predictor(model_type: MLModelType = MLModelType.ENSEMBLE) -> SMCMLPredictor:
    """
    Crear predictor ML para SMC
    
    Args:
        model_type: Tipo de modelo ML a usar
        
    Returns:
        SMCMLPredictor inicializado
    """
    return SMCMLPredictor(model_type)

def train_predictor_with_historical_data(predictor: SMCMLPredictor, 
                                       historical_data: List[Dict]) -> Dict:
    """
    Entrenar predictor con datos históricos
    
    Args:
        predictor: Predictor ML
        historical_data: Lista de datos históricos con resultados
        
    Returns:
        Métricas de entrenamiento
    """
    print(f"📚 Entrenando predictor con {len(historical_data)} muestras históricas...")
    
    for data in historical_data:
        df = data.get('df')
        smc_analysis = data.get('smc_analysis')
        outcome = data.get('outcome', SignalOutcome.LOSS)
        signal_info = data.get('signal_info')
        symbol = data.get('symbol', 'BTCUSDT')
        
        if df is not None and smc_analysis is not None:
            predictor.add_training_sample(df, smc_analysis, outcome, signal_info, symbol)
    
    return predictor.train_models()

# Exportar clases y funciones principales
__all__ = [
    'SMCMLPredictor',
    'MLFeatures',
    'MLPrediction',
    'MLModelType',
    'SignalOutcome',
    'create_ml_predictor',
    'train_predictor_with_historical_data'
]