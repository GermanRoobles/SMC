#!/usr/bin/env python3
"""
ML Avanzado para SMC TradingView
================================

Sistema de Machine Learning avanzado con características sofisticadas:
- Predicción de volatilidad
- Detección de anomalías
- Clasificación de patrones
- Predicción de dirección de tendencia
- Análisis de sentimiento
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import joblib
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class PatternType(Enum):
    """Tipos de patrones de mercado"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    CONSOLIDATION = "consolidation"
    NEUTRAL = "neutral"

class TrendDirection(Enum):
    """Direcciones de tendencia"""
    STRONG_UP = "strong_up"
    WEAK_UP = "weak_up"
    NEUTRAL = "neutral"
    WEAK_DOWN = "weak_down"
    STRONG_DOWN = "strong_down"

@dataclass
class VolatilityPrediction:
    """Predicción de volatilidad"""
    current_volatility: float
    predicted_volatility: float
    confidence: float
    timeframe: str
    timestamp: datetime

@dataclass
class AnomalyDetection:
    """Detección de anomalías"""
    is_anomaly: bool
    anomaly_score: float
    anomaly_type: str
    confidence: float
    timestamp: datetime

@dataclass
class PatternClassification:
    """Clasificación de patrones"""
    pattern_type: PatternType
    confidence: float
    strength: float
    duration: int
    timestamp: datetime

@dataclass
class TrendPrediction:
    """Predicción de tendencia"""
    direction: TrendDirection
    confidence: float
    strength: float
    duration_hours: int
    timestamp: datetime

@dataclass
class SentimentAnalysis:
    """Análisis de sentimiento"""
    sentiment_score: float
    sentiment_label: str
    confidence: float
    factors: Dict[str, float]
    timestamp: datetime

class AdvancedMLSystem:
    """Sistema de ML avanzado para trading"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Modelos
        self.volatility_model = None
        self.anomaly_detector = None
        self.pattern_classifier = None
        self.trend_predictor = None
        self.sentiment_analyzer = None
        
        # Crear directorio de modelos si no existe
        os.makedirs(model_dir, exist_ok=True)
        
        # Cargar o inicializar modelos
        self._load_or_initialize_models()
    
    def _load_or_initialize_models(self):
        """Cargar modelos existentes o inicializar nuevos"""
        try:
            # Volatilidad
            volatility_path = os.path.join(self.model_dir, "volatility_model.joblib")
            if os.path.exists(volatility_path):
                self.volatility_model = joblib.load(volatility_path)
            else:
                self.volatility_model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Anomalías
            anomaly_path = os.path.join(self.model_dir, "anomaly_detector.joblib")
            if os.path.exists(anomaly_path):
                self.anomaly_detector = joblib.load(anomaly_path)
            else:
                self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            
            # Patrones
            pattern_path = os.path.join(self.model_dir, "pattern_classifier.joblib")
            if os.path.exists(pattern_path):
                self.pattern_classifier = joblib.load(pattern_path)
            else:
                self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Tendencia
            trend_path = os.path.join(self.model_dir, "trend_predictor.joblib")
            if os.path.exists(trend_path):
                self.trend_predictor = joblib.load(trend_path)
            else:
                self.trend_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Inicializar label encoders
            self.label_encoder = LabelEncoder()
            
            print("✅ Modelos ML avanzados cargados/inicializados")
            
        except Exception as e:
            print(f"⚠️ Error cargando modelos: {e}")
            self._initialize_default_models()
        
        # Verificar que todos los modelos estén inicializados correctamente
        if not hasattr(self.anomaly_detector, 'predict'):
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        if not hasattr(self.pattern_classifier, 'feature_importances_'):
            self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        if not hasattr(self.trend_predictor, 'feature_importances_'):
            self.trend_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Verificar que los label encoders estén inicializados
        if not hasattr(self.label_encoder, 'classes_'):
            # Crear un label encoder por defecto con clases básicas
            default_classes = ['neutral', 'bullish', 'bearish', 'sideways']
            self.label_encoder.fit(default_classes)
    
    def _initialize_default_models(self):
        """Inicializar modelos por defecto"""
        self.volatility_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.trend_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        print("✅ Modelos por defecto inicializados")
    
    def _extract_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extraer características avanzadas para ML"""
        features = df.copy()
        
        # Características de precio
        features['price_change'] = df['close'].pct_change()
        features['price_change_abs'] = features['price_change'].abs()
        features['high_low_ratio'] = df['high'] / df['low']
        features['close_open_ratio'] = df['close'] / df['open']
        
        # Características de volatilidad
        features['volatility_5'] = df['close'].rolling(5).std()
        features['volatility_10'] = df['close'].rolling(10).std()
        features['volatility_20'] = df['close'].rolling(20).std()
        
        # Características de tendencia
        features['sma_5'] = df['close'].rolling(5).mean()
        features['sma_10'] = df['close'].rolling(10).mean()
        features['sma_20'] = df['close'].rolling(20).mean()
        features['trend_5'] = (df['close'] - features['sma_5']) / features['sma_5']
        features['trend_10'] = (df['close'] - features['sma_10']) / features['sma_10']
        features['trend_20'] = (df['close'] - features['sma_20']) / features['sma_20']
        
        # Características de volumen
        features['volume_ma_5'] = df['volume'].rolling(5).mean()
        features['volume_ratio'] = df['volume'] / features['volume_ma_5']
        
        # Características de momentum
        features['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        features['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        features['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        # Características de rango
        features['range_5'] = (df['high'].rolling(5).max() - df['low'].rolling(5).min()) / df['close']
        features['range_10'] = (df['high'].rolling(10).max() - df['low'].rolling(10).min()) / df['close']
        
        # Características de tiempo
        features['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        features['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        
        # Eliminar filas con NaN
        features = features.dropna()
        
        return features
    
    def predict_volatility(self, df: pd.DataFrame, timeframe: str = "1h") -> VolatilityPrediction:
        """Predecir volatilidad futura"""
        try:
            features = self._extract_advanced_features(df)
            
            if len(features) < 20:
                return VolatilityPrediction(
                    current_volatility=0.02,
                    predicted_volatility=0.02,
                    confidence=0.5,
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
            
            # Preparar datos para volatilidad
            X = features[['volatility_5', 'volatility_10', 'volatility_20', 
                         'price_change_abs', 'range_5', 'range_10']].values
            
            # Entrenar modelo si no está entrenado
            try:
                # Verificar si el modelo ya está entrenado
                if hasattr(self.volatility_model, 'feature_importances_'):
                    # Probar predicción para verificar si está realmente entrenado
                    test_pred = self.volatility_model.predict(X[:1])
                else:
                    # Crear datos sintéticos para entrenamiento
                    y_vol = features['volatility_5'].values
                    X_train, X_test, y_train, y_test = train_test_split(X, y_vol, test_size=0.2, random_state=42)
                    self.volatility_model.fit(X_train, y_train)
                    
                    # Guardar modelo
                    joblib.dump(self.volatility_model, os.path.join(self.model_dir, "volatility_model.joblib"))
            except Exception as e:
                print(f"⚠️ Error entrenando modelo de volatilidad: {e}")
                # Crear modelo por defecto
                self.volatility_model = RandomForestRegressor(n_estimators=100, random_state=42)
                y_vol = features['volatility_5'].values
                self.volatility_model.fit(X, y_vol)
            
            # Predecir
            current_vol = features['volatility_5'].iloc[-1]
            predicted_vol = self.volatility_model.predict(X[-1:])[0]
            
            # Calcular confianza basada en la varianza de predicciones
            predictions = self.volatility_model.predict(X[-5:])
            confidence = 1 - np.std(predictions) / np.mean(predictions) if np.mean(predictions) > 0 else 0.5
            
            return VolatilityPrediction(
                current_volatility=current_vol,
                predicted_volatility=max(0.001, predicted_vol),
                confidence=min(1.0, max(0.0, confidence)),
                timeframe=timeframe,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"⚠️ Error prediciendo volatilidad: {e}")
            return VolatilityPrediction(
                current_volatility=0.02,
                predicted_volatility=0.02,
                confidence=0.5,
                timeframe=timeframe,
                timestamp=datetime.now()
            )
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detectar anomalías en los datos"""
        try:
            features = self._extract_advanced_features(df)
            
            if len(features) < 10:
                return []
            
            # Características para detección de anomalías
            X_anomaly = features[['price_change_abs', 'volatility_5', 'volume_ratio', 
                                 'high_low_ratio', 'range_5']].values
            
            # Entrenar detector si no está entrenado
            try:
                # Verificar si el detector ya está entrenado
                if hasattr(self.anomaly_detector, 'predict'):
                    # Probar predicción para verificar si está realmente entrenado
                    test_pred = self.anomaly_detector.predict(X_anomaly[:1])
                else:
                    # Entrenar detector
                    self.anomaly_detector.fit(X_anomaly)
                    joblib.dump(self.anomaly_detector, os.path.join(self.model_dir, "anomaly_detector.joblib"))
            except Exception as e:
                print(f"⚠️ Error entrenando detector de anomalías: {e}")
                # Crear detector por defecto y entrenarlo
                self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
                self.anomaly_detector.fit(X_anomaly)
                # Guardar el detector entrenado
                joblib.dump(self.anomaly_detector, os.path.join(self.model_dir, "anomaly_detector.joblib"))
            
            # Asegurar que el detector esté entrenado
            if not hasattr(self.anomaly_detector, 'predict'):
                self.anomaly_detector.fit(X_anomaly)
            
            # Detectar anomalías
            anomaly_scores = self.anomaly_detector.decision_function(X_anomaly)
            anomaly_predictions = self.anomaly_detector.predict(X_anomaly)
            
            anomalies = []
            for i, (is_anomaly, score) in enumerate(zip(anomaly_predictions, anomaly_scores)):
                if is_anomaly == -1:  # Anomalía detectada
                    # Determinar tipo de anomalía
                    price_change = features['price_change'].iloc[i]
                    volume_ratio = features['volume_ratio'].iloc[i]
                    
                    if abs(price_change) > 0.05:  # 5% de cambio
                        anomaly_type = "price_spike"
                    elif volume_ratio > 3:  # 3x volumen promedio
                        anomaly_type = "volume_spike"
                    else:
                        anomaly_type = "general_anomaly"
                    
                    anomalies.append(AnomalyDetection(
                        is_anomaly=True,
                        anomaly_score=abs(score),
                        anomaly_type=anomaly_type,
                        confidence=min(1.0, abs(score) / 0.5),
                        timestamp=pd.to_datetime(df['timestamp'].iloc[i])
                    ))
            
            return anomalies
            
        except Exception as e:
            print(f"⚠️ Error detectando anomalías: {e}")
            return []
    
    def classify_patterns(self, df: pd.DataFrame) -> List[PatternClassification]:
        """Clasificar patrones de mercado"""
        try:
            features = self._extract_advanced_features(df)
            
            if len(features) < 20:
                return []
            
            # Características para clasificación de patrones
            X_pattern = features[['trend_5', 'trend_10', 'trend_20', 'momentum_5', 
                                'momentum_10', 'range_5', 'volume_ratio']].values
            
            # Crear etiquetas de patrones basadas en características
            pattern_labels = []
            for _, row in features.iterrows():
                if row['trend_5'] > 0.02 and row['momentum_5'] > 0.01:
                    pattern_labels.append('bullish')
                elif row['trend_5'] < -0.02 and row['momentum_5'] < -0.01:
                    pattern_labels.append('bearish')
                elif abs(row['trend_5']) < 0.01 and row['range_5'] < 0.02:
                    pattern_labels.append('consolidation')
                else:
                    pattern_labels.append('sideways')
            
            # Entrenar clasificador si no está entrenado
            try:
                # Verificar si el clasificador ya está entrenado
                if hasattr(self.pattern_classifier, 'feature_importances_'):
                    # Probar predicción para verificar si está realmente entrenado
                    test_pred = self.pattern_classifier.predict(X_pattern[:1])
                else:
                    # Codificar etiquetas
                    y_pattern = self.label_encoder.fit_transform(pattern_labels)
                    X_train, X_test, y_train, y_test = train_test_split(X_pattern, y_pattern, test_size=0.2, random_state=42)
                    self.pattern_classifier.fit(X_train, y_train)
                    
                    joblib.dump(self.pattern_classifier, os.path.join(self.model_dir, "pattern_classifier.joblib"))
            except Exception as e:
                print(f"⚠️ Error entrenando clasificador de patrones: {e}")
                # Crear clasificador por defecto y entrenarlo
                self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
                self.label_encoder = LabelEncoder()
                y_pattern = self.label_encoder.fit_transform(pattern_labels)
                self.pattern_classifier.fit(X_pattern, y_pattern)
                # Guardar el clasificador entrenado
                joblib.dump(self.pattern_classifier, os.path.join(self.model_dir, "pattern_classifier.joblib"))
            
            # Asegurar que el clasificador esté entrenado
            if not hasattr(self.pattern_classifier, 'feature_importances_'):
                y_pattern = self.label_encoder.fit_transform(pattern_labels)
                self.pattern_classifier.fit(X_pattern, y_pattern)
            
            # Asegurar que el label_encoder esté entrenado
            if not hasattr(self.label_encoder, 'classes_'):
                self.label_encoder.fit(pattern_labels)
            
            # Clasificar patrones
            try:
                pattern_predictions = self.pattern_classifier.predict(X_pattern)
                pattern_probabilities = self.pattern_classifier.predict_proba(X_pattern)
                
                patterns = []
                for i, (pred, probs) in enumerate(zip(pattern_predictions, pattern_probabilities)):
                    confidence = max(probs)
                    pattern_type = PatternType(self.label_encoder.inverse_transform([pred])[0])
            except Exception as e:
                print(f"⚠️ Error en clasificación de patrones: {e}")
                # Fallback: crear predicciones por defecto
                patterns = []
                for i in range(len(X_pattern)):
                    patterns.append(PatternClassification(
                        pattern_type=PatternType.NEUTRAL,
                        confidence=0.5,
                        strength=0.5,
                        duration=5,
                        timestamp=pd.to_datetime(df['timestamp'].iloc[i])
                    ))
                return patterns
                
                # Calcular fuerza del patrón
                strength = abs(features['trend_5'].iloc[i]) + abs(features['momentum_5'].iloc[i])
                
                # Mapear string a PatternType
                pattern_type_map = {
                    'bullish': PatternType.BULLISH,
                    'bearish': PatternType.BEARISH,
                    'sideways': PatternType.SIDEWAYS,
                    'consolidation': PatternType.CONSOLIDATION,
                    'neutral': PatternType.NEUTRAL
                }
                
                pattern_type = pattern_type_map.get(self.label_encoder.inverse_transform([pred])[0], PatternType.NEUTRAL)
                
                patterns.append(PatternClassification(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    strength=min(1.0, strength),
                    duration=5,  # 5 períodos
                    timestamp=pd.to_datetime(df['timestamp'].iloc[i])
                ))
            
            return patterns
            
        except Exception as e:
            print(f"⚠️ Error clasificando patrones: {e}")
            return []
    
    def predict_trend(self, df: pd.DataFrame) -> TrendPrediction:
        """Predecir dirección de tendencia"""
        try:
            features = self._extract_advanced_features(df)
            
            if len(features) < 20:
                return TrendPrediction(
                    direction=TrendDirection.NEUTRAL,
                    confidence=0.5,
                    strength=0.5,
                    duration_hours=24,
                    timestamp=datetime.now()
                )
            
            # Características para predicción de tendencia
            X_trend = features[['trend_5', 'trend_10', 'trend_20', 'momentum_5', 
                              'momentum_10', 'momentum_20', 'volume_ratio']].values
            
            # Crear etiquetas de tendencia
            trend_labels = []
            for _, row in features.iterrows():
                if row['trend_20'] > 0.05 and row['momentum_10'] > 0.02:
                    trend_labels.append('strong_up')
                elif row['trend_20'] > 0.01 and row['momentum_5'] > 0.005:
                    trend_labels.append('weak_up')
                elif row['trend_20'] < -0.05 and row['momentum_10'] < -0.02:
                    trend_labels.append('strong_down')
                elif row['trend_20'] < -0.01 and row['momentum_5'] < -0.005:
                    trend_labels.append('weak_down')
                else:
                    trend_labels.append('neutral')
            
            # Entrenar predictor si no está entrenado
            try:
                # Verificar si el predictor ya está entrenado
                if hasattr(self.trend_predictor, 'feature_importances_'):
                    # Probar predicción para verificar si está realmente entrenado
                    test_pred = self.trend_predictor.predict(X_trend[:1])
                else:
                    y_trend = self.label_encoder.fit_transform(trend_labels)
                    X_train, X_test, y_train, y_test = train_test_split(X_trend, y_trend, test_size=0.2, random_state=42)
                    self.trend_predictor.fit(X_train, y_train)
                    
                    joblib.dump(self.trend_predictor, os.path.join(self.model_dir, "trend_predictor.joblib"))
            except Exception as e:
                print(f"⚠️ Error entrenando predictor de tendencia: {e}")
                # Crear predictor por defecto y entrenarlo
                self.trend_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
                self.label_encoder = LabelEncoder()
                y_trend = self.label_encoder.fit_transform(trend_labels)
                self.trend_predictor.fit(X_trend, y_trend)
                # Guardar el predictor entrenado
                joblib.dump(self.trend_predictor, os.path.join(self.model_dir, "trend_predictor.joblib"))
            
            # Asegurar que el predictor esté entrenado
            if not hasattr(self.trend_predictor, 'feature_importances_'):
                y_trend = self.label_encoder.fit_transform(trend_labels)
                self.trend_predictor.fit(X_trend, y_trend)
            
            # Asegurar que el label_encoder esté entrenado
            if not hasattr(self.label_encoder, 'classes_'):
                self.label_encoder.fit(trend_labels)
            
            # Predecir tendencia
            try:
                trend_prediction = self.trend_predictor.predict(X_trend[-1:])[0]
                trend_probabilities = self.trend_predictor.predict_proba(X_trend[-1:])[0]
                
                # Mapear string a TrendDirection
                direction_map = {
                    'strong_up': TrendDirection.STRONG_UP,
                    'weak_up': TrendDirection.WEAK_UP,
                    'neutral': TrendDirection.NEUTRAL,
                    'weak_down': TrendDirection.WEAK_DOWN,
                    'strong_down': TrendDirection.STRONG_DOWN
                }
                
                direction = direction_map.get(self.label_encoder.inverse_transform([trend_prediction])[0], TrendDirection.NEUTRAL)
                confidence = max(trend_probabilities)
            except Exception as e:
                print(f"⚠️ Error en predicción de tendencia: {e}")
                # Fallback: predicción por defecto
                direction = TrendDirection.NEUTRAL
                confidence = 0.5
            
            # Calcular fuerza de la tendencia
            current_trend = features['trend_20'].iloc[-1]
            current_momentum = features['momentum_10'].iloc[-1]
            strength = min(1.0, abs(current_trend) + abs(current_momentum))
            
            return TrendPrediction(
                direction=direction,
                confidence=confidence,
                strength=strength,
                duration_hours=24,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"⚠️ Error prediciendo tendencia: {e}")
            return TrendPrediction(
                direction=TrendDirection.NEUTRAL,
                confidence=0.5,
                strength=0.5,
                duration_hours=24,
                timestamp=datetime.now()
            )
    
    def analyze_sentiment(self, df: pd.DataFrame) -> SentimentAnalysis:
        """Analizar sentimiento del mercado"""
        try:
            features = self._extract_advanced_features(df)
            
            if len(features) < 10:
                return SentimentAnalysis(
                    sentiment_score=0.0,
                    sentiment_label="neutral",
                    confidence=0.5,
                    factors={},
                    timestamp=datetime.now()
                )
            
            # Calcular factores de sentimiento
            price_momentum = features['momentum_5'].iloc[-1]
            volume_trend = features['volume_ratio'].iloc[-1] - 1
            volatility_trend = features['volatility_5'].iloc[-1] - features['volatility_20'].iloc[-1]
            range_expansion = features['range_5'].iloc[-1] - features['range_10'].iloc[-1]
            
            # Calcular score de sentimiento
            sentiment_score = (
                np.tanh(price_momentum * 10) * 0.4 +
                np.tanh(volume_trend * 2) * 0.3 +
                np.tanh(-volatility_trend * 5) * 0.2 +
                np.tanh(range_expansion * 10) * 0.1
            )
            
            # Determinar etiqueta de sentimiento
            if sentiment_score > 0.3:
                sentiment_label = "bullish"
            elif sentiment_score < -0.3:
                sentiment_label = "bearish"
            else:
                sentiment_label = "neutral"
            
            # Calcular confianza
            confidence = min(1.0, abs(sentiment_score) + 0.3)
            
            # Factores que contribuyen al sentimiento
            factors = {
                "price_momentum": price_momentum,
                "volume_trend": volume_trend,
                "volatility_trend": volatility_trend,
                "range_expansion": range_expansion
            }
            
            return SentimentAnalysis(
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=confidence,
                factors=factors,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"⚠️ Error analizando sentimiento: {e}")
            return SentimentAnalysis(
                sentiment_score=0.0,
                sentiment_label="neutral",
                confidence=0.5,
                factors={},
                timestamp=datetime.now()
            )
    
    def get_comprehensive_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Obtener análisis completo de ML avanzado"""
        try:
            print("🔍 Iniciando análisis ML avanzado...")
            
            # Ejecutar todos los análisis
            volatility = self.predict_volatility(df)
            anomalies = self.detect_anomalies(df)
            patterns = self.classify_patterns(df)
            trend = self.predict_trend(df)
            sentiment = self.analyze_sentiment(df)
            
            # Resumen de análisis
            analysis = {
                "volatility": {
                    "current": volatility.current_volatility,
                    "predicted": volatility.predicted_volatility,
                    "confidence": volatility.confidence,
                    "timeframe": volatility.timeframe
                },
                "anomalies": {
                    "count": len(anomalies),
                    "recent": [a for a in anomalies if pd.to_datetime(a.timestamp).tz_localize(None) > pd.to_datetime(datetime.now() - timedelta(hours=24)).tz_localize(None)],
                    "types": list(set([a.anomaly_type for a in anomalies]))
                },
                "patterns": {
                    "current": patterns[-1] if patterns else None,
                    "recent": patterns[-5:] if patterns else [],
                    "distribution": {p.value: len([pat for pat in patterns if pat.pattern_type == p]) 
                                  for p in PatternType}
                },
                "trend": {
                    "direction": trend.direction.value,
                    "confidence": trend.confidence,
                    "strength": trend.strength,
                    "duration_hours": trend.duration_hours
                },
                "sentiment": {
                    "score": sentiment.sentiment_score,
                    "label": sentiment.sentiment_label,
                    "confidence": sentiment.confidence,
                    "factors": sentiment.factors
                },
                "timestamp": datetime.now()
            }
            
            print("✅ Análisis ML avanzado completado")
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error en análisis completo: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now()
            }

# Función de conveniencia para crear instancia
def create_advanced_ml_system(model_dir: str = "models") -> AdvancedMLSystem:
    """Crear instancia del sistema ML avanzado"""
    return AdvancedMLSystem(model_dir)
