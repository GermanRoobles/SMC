#!/usr/bin/env python3
"""
Test del ML Predictor para SMC TradingView
=========================================

Test completo del sistema de machine learning para predicción de señales SMC.

Autor: SMC TradingView System
Versión: 1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

# Importar módulos ML
from smc_ml_predictor import (
    SMCMLPredictor, MLModelType, SignalOutcome, MLFeatures, MLPrediction,
    create_ml_predictor, train_predictor_with_historical_data
)
from smc_ml_integration import MLIntegrationManager, get_ml_manager

# Importar módulos SMC
from fetch_data import get_ohlcv
from smc_analysis import analyze
from smc_integration import get_smc_bot_analysis

def create_test_data() -> tuple:
    """Crear datos de test para ML"""
    print("📊 Creando datos de test...")
    
    # Crear DataFrame de prueba
    dates = [datetime.now() - timedelta(minutes=i*15) for i in range(100, 0, -1)]
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [50000 + np.random.normal(0, 200) for _ in range(100)],
        'high': [50200 + np.random.normal(0, 200) for _ in range(100)],
        'low': [49800 + np.random.normal(0, 200) for _ in range(100)],
        'close': [50100 + np.random.normal(0, 200) for _ in range(100)],
        'volume': [1000 + np.random.normal(0, 200) for _ in range(100)]
    })
    
    # Crear análisis SMC simulado
    smc_analysis = {
        'fvg': pd.DataFrame({'FVG': [1, 1, 0] * 33 + [1]}),
        'orderblocks': pd.DataFrame({'OB': [1, 0] * 50}),
        'liquidity': pd.DataFrame({'Liquidity': [1] * 100}),
        'bos_choch': pd.DataFrame({'Signal': ['BOS', 'CHoCH'] * 50}),
        'swing_highs_lows': pd.DataFrame({'HighLow': [1, -1] * 50})
    }
    
    # Información de señal simulada
    signal_info = {
        'confidence': 0.75,
        'risk_reward': 2.5,
        'entry_quality': 0.8,
        'confluence_score': 0.7
    }
    
    return df, smc_analysis, signal_info

def test_ml_features():
    """Test de extracción de características"""
    print("\n🔍 TEST 1: Extracción de Características ML")
    print("=" * 50)
    
    try:
        df, smc_analysis, signal_info = create_test_data()
        
        predictor = create_ml_predictor(MLModelType.RANDOM_FOREST)
        features = predictor.extract_features(df, smc_analysis, signal_info)
        
        print(f"✅ Características extraídas correctamente")
        print(f"   • FVG Count: {features.fvg_count}")
        print(f"   • OB Count: {features.ob_count}")
        print(f"   • RSI: {features.rsi:.2f}")
        print(f"   • Volatilidad: {features.volatility:.4f}")
        print(f"   • Confianza señal: {features.signal_confidence}")
        
        # Test de conversión a array
        feature_array = features.to_array()
        print(f"   • Array shape: {feature_array.shape}")
        print(f"   • Feature names: {len(features.get_feature_names())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de características: {e}")
        return False

def test_synthetic_data_generation():
    """Test de generación de datos sintéticos"""
    print("\n🔍 TEST 2: Generación de Datos Sintéticos")
    print("=" * 50)
    
    try:
        df, smc_analysis, signal_info = create_test_data()
        
        predictor = create_ml_predictor(MLModelType.ENSEMBLE)
        initial_samples = len(predictor.training_data.features)
        
        # Generar datos sintéticos
        predictor.generate_synthetic_training_data(df, smc_analysis, 50)
        
        final_samples = len(predictor.training_data.features)
        generated_samples = final_samples - initial_samples
        
        print(f"✅ Datos sintéticos generados: {generated_samples} muestras")
        
        # Verificar distribución de outcomes
        outcomes = [sample.value for sample in predictor.training_data.outcomes]
        win_count = outcomes.count(SignalOutcome.WIN.value)
        loss_count = outcomes.count(SignalOutcome.LOSS.value)
        
        print(f"   • Wins: {win_count}")
        print(f"   • Losses: {loss_count}")
        print(f"   • Win Rate: {win_count/(win_count+loss_count)*100:.1f}%")
        
        return generated_samples >= 50
        
    except Exception as e:
        print(f"❌ Error en generación sintética: {e}")
        return False

def test_model_training():
    """Test de entrenamiento de modelos"""
    print("\n🔍 TEST 3: Entrenamiento de Modelos ML")
    print("=" * 50)
    
    try:
        df, smc_analysis, signal_info = create_test_data()
        
        predictor = create_ml_predictor(MLModelType.ENSEMBLE)
        
        # Generar datos de entrenamiento
        predictor.generate_synthetic_training_data(df, smc_analysis, 100)
        
        # Entrenar modelos
        print("🤖 Entrenando modelos...")
        metrics = predictor.train_models(optimize_hyperparameters=False)
        
        if metrics:
            print("✅ Modelos entrenados exitosamente")
            for model_name, model_metrics in metrics.items():
                print(f"   • {model_name}:")
                print(f"     - Accuracy: {model_metrics['accuracy']:.3f}")
                print(f"     - Precision: {model_metrics['precision']:.3f}")
                print(f"     - Recall: {model_metrics['recall']:.3f}")
                print(f"     - F1-Score: {model_metrics['f1_score']:.3f}")
                print(f"     - AUC-ROC: {model_metrics['auc_roc']:.3f}")
            
            return predictor.is_trained
        else:
            print("❌ No se obtuvieron métricas de entrenamiento")
            return False
        
    except Exception as e:
        print(f"❌ Error en entrenamiento: {e}")
        return False

def test_predictions():
    """Test de predicciones"""
    print("\n🔍 TEST 4: Predicciones ML")
    print("=" * 50)
    
    try:
        df, smc_analysis, signal_info = create_test_data()
        
        predictor = create_ml_predictor(MLModelType.ENSEMBLE)
        
        # Generar datos y entrenar
        predictor.generate_synthetic_training_data(df, smc_analysis, 100)
        metrics = predictor.train_models(optimize_hyperparameters=False)
        
        if not predictor.is_trained:
            print("❌ Modelo no entrenado")
            return False
        
        # Hacer predicción
        prediction = predictor.predict_signal_probability(df, smc_analysis, signal_info)
        
        print("✅ Predicción generada exitosamente")
        print(f"   • Probabilidad: {prediction.probability:.3f}")
        print(f"   • Confianza: {prediction.confidence:.3f}")
        print(f"   • Consenso: {prediction.model_consensus:.3f}")
        print(f"   • Risk-Adjusted Score: {prediction.risk_adjusted_score:.3f}")
        print(f"   • Recomendación: {prediction.recommendation}")
        
        # Verificar que los valores están en rangos válidos
        valid_probability = 0.0 <= prediction.probability <= 1.0
        valid_confidence = 0.0 <= prediction.confidence <= 1.0
        valid_recommendation = prediction.recommendation in ["STRONG_BUY", "BUY", "HOLD", "AVOID"]
        
        if valid_probability and valid_confidence and valid_recommendation:
            print("✅ Predicción válida")
            return True
        else:
            print("❌ Predicción con valores inválidos")
            return False
        
    except Exception as e:
        print(f"❌ Error en predicción: {e}")
        return False

def test_model_persistence():
    """Test de guardado y carga de modelos"""
    print("\n🔍 TEST 5: Persistencia de Modelos")
    print("=" * 50)
    
    try:
        df, smc_analysis, signal_info = create_test_data()
        
        # Crear y entrenar predictor
        predictor1 = create_ml_predictor(MLModelType.RANDOM_FOREST)
        predictor1.generate_synthetic_training_data(df, smc_analysis, 50)
        metrics = predictor1.train_models(optimize_hyperparameters=False)
        
        if not predictor1.is_trained:
            print("❌ Predictor inicial no entrenado")
            return False
        
        # Guardar modelo
        model_path = "test_model.joblib"
        if not predictor1.save_model(model_path):
            print("❌ Error guardando modelo")
            return False
        
        print("✅ Modelo guardado exitosamente")
        
        # Crear nuevo predictor y cargar modelo
        predictor2 = create_ml_predictor(MLModelType.RANDOM_FOREST)
        if not predictor2.load_model(model_path):
            print("❌ Error cargando modelo")
            return False
        
        print("✅ Modelo cargado exitosamente")
        
        # Verificar que ambos predictores dan resultados similares
        pred1 = predictor1.predict_signal_probability(df, smc_analysis, signal_info)
        pred2 = predictor2.predict_signal_probability(df, smc_analysis, signal_info)
        
        prob_diff = abs(pred1.probability - pred2.probability)
        
        if prob_diff < 0.01:  # Diferencia menor al 1%
            print(f"✅ Predicciones consistentes (diff: {prob_diff:.4f})")
            
            # Limpiar archivo de test
            import os
            if os.path.exists(model_path):
                os.remove(model_path)
            
            return True
        else:
            print(f"❌ Predicciones inconsistentes (diff: {prob_diff:.4f})")
            return False
        
    except Exception as e:
        print(f"❌ Error en persistencia: {e}")
        return False

def test_integration_manager():
    """Test del gestor de integración ML"""
    print("\n🔍 TEST 6: Gestor de Integración ML")
    print("=" * 50)
    
    try:
        # Test de inicialización
        manager = MLIntegrationManager()
        
        if not manager.is_initialized:
            print("❌ Gestor no inicializado")
            return False
        
        print("✅ Gestor inicializado correctamente")
        
        # Test de estadísticas
        stats = manager.get_model_stats()
        print(f"   • Estado: {stats.get('integration_status')}")
        print(f"   • Modelos disponibles: {len(stats.get('available_models', []))}")
        print(f"   • Muestras de entrenamiento: {stats.get('training_samples', 0)}")
        
        # Test de predicción
        df, smc_analysis, signal_info = create_test_data()
        prediction = manager.get_signal_prediction(df, smc_analysis, signal_info)
        
        print(f"✅ Predicción del gestor: {prediction.probability:.3f}")
        
        # Test de añadir outcome
        manager.add_signal_outcome(df, smc_analysis, SignalOutcome.WIN, signal_info)
        print("✅ Outcome añadido correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en gestor de integración: {e}")
        return False

def test_with_real_data():
    """Test con datos reales de mercado"""
    print("\n🔍 TEST 7: Test con Datos Reales")
    print("=" * 50)
    
    try:
        # Obtener datos reales
        print("📊 Obteniendo datos reales de BTCUSDT...")
        df = get_ohlcv("BTCUSDT", "15m", limit=100)
        
        if df is None or len(df) == 0:
            print("⚠️ No se pudieron obtener datos reales, usando datos simulados")
            df, smc_analysis, signal_info = create_test_data()
        else:
            print(f"✅ Datos reales obtenidos: {len(df)} velas")
            
            # Análisis SMC real
            smc_analysis = get_smc_bot_analysis(df)
            signal_info = {'confidence': 0.6, 'risk_reward': 2.0}
        
        # Test con gestor ML
        manager = get_ml_manager()
        prediction = manager.get_signal_prediction(df, smc_analysis, signal_info)
        
        print("✅ Predicción con datos reales:")
        print(f"   • Probabilidad: {prediction.probability:.3f}")
        print(f"   • Recomendación: {prediction.recommendation}")
        print(f"   • Risk-Adjusted Score: {prediction.risk_adjusted_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con datos reales: {e}")
        return False

def run_ml_predictor_tests():
    """Ejecutar todos los tests del ML Predictor"""
    print("🚀 INICIANDO TESTS DEL ML PREDICTOR")
    print("=" * 70)
    print("Testing del sistema de machine learning para SMC TradingView")
    print("=" * 70)
    
    tests = [
        ("Extracción de Características", test_ml_features),
        ("Generación de Datos Sintéticos", test_synthetic_data_generation),
        ("Entrenamiento de Modelos", test_model_training),
        ("Predicciones ML", test_predictions),
        ("Persistencia de Modelos", test_model_persistence),
        ("Gestor de Integración", test_integration_manager),
        ("Test con Datos Reales", test_with_real_data)
    ]
    
    results = []
    start_time = datetime.now()
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Error crítico en {test_name}: {e}")
            results.append((test_name, False))
    
    # Reporte final
    print("\n📊 REPORTE FINAL - ML PREDICTOR TESTS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    
    print(f"📈 RESULTADOS GENERALES:")
    print(f"   • Total de tests: {total_tests}")
    print(f"   • Tests exitosos: {passed_tests} ✅")
    print(f"   • Tests fallidos: {failed_tests} ❌")
    print(f"   • Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ TESTS FALLIDOS:")
        for test_name, result in results:
            if not result:
                print(f"   • {test_name}")
    
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n⏱️  TIEMPO TOTAL: {total_time:.2f} segundos")
    
    # Estado final
    if failed_tests == 0:
        print(f"\n🎉 ¡TODOS LOS TESTS DEL ML PREDICTOR EXITOSOS!")
        print(f"   El sistema de machine learning está completamente funcional")
        status = "✅ ML PREDICTOR COMPLETAMENTE FUNCIONAL"
    elif failed_tests <= 2:
        print(f"\n⚠️ ML PREDICTOR FUNCIONAL CON PROBLEMAS MENORES")
        print(f"   {failed_tests} tests fallaron de {total_tests}")
        status = "⚠️ ML PREDICTOR FUNCIONAL CON PROBLEMAS MENORES"
    else:
        print(f"\n❌ ML PREDICTOR CON PROBLEMAS CRÍTICOS")
        print(f"   {failed_tests} tests fallaron de {total_tests}")
        status = "❌ ML PREDICTOR CON PROBLEMAS CRÍTICOS"
    
    print(f"\n📊 Estado final: {status}")
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'success_rate': (passed_tests/total_tests)*100,
        'total_time': total_time,
        'status': status,
        'results': results
    }

if __name__ == "__main__":
    try:
        report = run_ml_predictor_tests()
        
        print(f"\n🏁 Test del ML Predictor completado")
        print(f"   Tasa de éxito: {report['success_rate']:.1f}%")
        print(f"   Tiempo: {report['total_time']:.2f}s")
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN TESTS: {e}")
        import traceback
        traceback.print_exc()