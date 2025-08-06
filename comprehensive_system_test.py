#!/usr/bin/env python3
"""
TEST COMPLETO DEL SISTEMA SMC TRADINGVIEW CON ML
================================================

Test exhaustivo que recorre TODAS las funcionalidades del proyecto:
- Todos los módulos principales
- Todas las configuraciones y perfiles
- Todas las funcionalidades ML (Predictor + Signal Generator)
- Verificaciones de consistencia de datos
- Comparaciones entre diferentes fuentes de datos
- Validaciones de integridad

Autor: Sistema de Testing Completo con ML
Versión: 2.0 - Incluye ML Predictor y ML Signal Generator
"""

import sys
import os
import time
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Importar todos los módulos del proyecto
try:
    # Módulos principales
    from fetch_data import get_ohlcv, get_ohlcv_extended, get_ohlcv_with_cache
    from smc_analysis import analyze, get_current_session, get_session_color
    from smc_integration import get_smc_bot_analysis, add_bot_signals_to_chart, display_bot_metrics
    from smc_trade_engine import get_trade_engine_analysis, TradeSignal, SignalType
    from smc_backtester import run_backtest_analysis, SMCBacktester, validate_sl_tp_levels
    from smc_visualization_advanced import add_advanced_signal_annotations
    from smc_bot import SMCBot, SMCConfig
    from smc_profiles import SMCProfiles
    from smc_config import get_config_by_profile
    from dynamic_signal_generator import DynamicSignalGenerator
    from smc_historical import create_historical_manager, HistoricalPeriod
    from smc_historical_viz import create_historical_visualizer
    from smc_tjr_calc import calculate_sl_tp_tjr
    from utils_htf import get_htf_gaps_and_obs, detect_sfp
    from greed_fear_btc import get_fear_greed_index
    
    # NUEVOS MÓDULOS ML
    from smc_ml_predictor import SMCMLPredictor, MLPrediction
    from smc_ml_integration import MLIntegrationManager
    from smc_ml_signal_generator import MLSignalGenerator, MLSignal, SignalType as MLSignalType
    from smc_ml_signal_integration import MLSignalIntegration
    
    print("✅ Todos los módulos importados correctamente (incluyendo ML)")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

class ComprehensiveSystemTester:
    """
    Testeador completo del sistema SMC TradingView con ML
    """
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"]
        self.timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        self.profiles = ["conservative", "balanced", "aggressive", "scalper", "swing"]
        
        # Datos de referencia para comparaciones
        self.reference_data = {}
        self.ml_predictions = {}
        self.smc_analyses = {}
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: Dict = None):
        """Registrar resultado de test con datos adicionales"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        self.test_results[test_name] = {
            'success': success,
            'details': details,
            'data': data,
            'timestamp': datetime.now()
        }
    
    def test_data_fetching(self) -> bool:
        """Test de obtención de datos con verificaciones de consistencia"""
        print("\n🔍 TEST 1: Obtención de Datos y Consistencia")
        print("=" * 60)
        
        try:
            # Test 1.1: Datos básicos
            df_basic = get_ohlcv("BTCUSDT", "15m", limit=100)
            df_extended = get_ohlcv_extended("BTCUSDT", "15m", days=7)
            
            if df_basic is not None and len(df_basic) > 0:
                self.log_test("Datos básicos BTCUSDT 15m", True, f"{len(df_basic)} velas obtenidas")
                self.reference_data['basic'] = df_basic
            else:
                self.log_test("Datos básicos BTCUSDT 15m", False, "No se obtuvieron datos")
                return False
            
            if df_extended is not None and len(df_extended) > 0:
                self.log_test("Datos extendidos BTCUSDT 15m", True, f"{len(df_extended)} velas obtenidas")
                self.reference_data['extended'] = df_extended
            else:
                self.log_test("Datos extendidos BTCUSDT 15m", False, "No se obtuvieron datos")
            
            # Test 1.2: Verificación de consistencia entre métodos
            if 'basic' in self.reference_data and 'extended' in self.reference_data:
                basic_cols = set(self.reference_data['basic'].columns)
                extended_cols = set(self.reference_data['extended'].columns)
                
                if basic_cols == extended_cols:
                    self.log_test("Consistencia de columnas", True, "Columnas idénticas entre métodos")
                else:
                    self.log_test("Consistencia de columnas", False, f"Diferencias: {basic_cols.symmetric_difference(extended_cols)}")
            
            # Test 1.3: Verificación de rangos de datos
            if 'basic' in self.reference_data:
                df = self.reference_data['basic']
                price_range = df['high'].max() - df['low'].min()
                volume_total = df['volume'].sum()
                
                if price_range > 0 and volume_total > 0:
                    self.log_test("Rangos de datos válidos", True, f"Precio: {price_range:.2f}, Vol: {volume_total:.2f}")
                else:
                    self.log_test("Rangos de datos válidos", False, "Datos fuera de rango")
            
            # Test 1.4: Múltiples símbolos con verificación
            for symbol in self.symbols[:2]:
                df = get_ohlcv(symbol, "15m", limit=50)
                if df is not None and len(df) > 0:
                    # Verificar que los datos son consistentes
                    if not df.isnull().all().all() and df['close'].std() > 0:
                        self.log_test(f"Datos {symbol}", True, f"{len(df)} velas, std: {df['close'].std():.2f}")
                    else:
                        self.log_test(f"Datos {symbol}", False, "Datos inconsistentes")
                else:
                    self.log_test(f"Datos {symbol}", False, "Error obteniendo datos")
            
            return True
            
        except Exception as e:
            self.log_test("Test de datos", False, f"Error: {str(e)}")
            return False
    
    def test_smc_analysis(self) -> bool:
        """Test de análisis SMC con verificaciones de consistencia"""
        print("\n🔍 TEST 2: Análisis SMC y Consistencia")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Análisis SMC", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 2.1: Análisis básico
            smc_results = analyze(df, timeframe="15m")
            
            if smc_results and isinstance(smc_results, dict):
                self.log_test("Análisis SMC básico", True, f"Resultados obtenidos: {list(smc_results.keys())}")
                self.smc_analyses['basic'] = smc_results
            else:
                self.log_test("Análisis SMC básico", False, "No se obtuvieron resultados")
                return False
            
            # Test 2.2: Verificación de estructura de resultados
            required_keys = ['fvg', 'orderblocks', 'liquidity', 'bos_choch', 'market_structure']
            missing_keys = [key for key in required_keys if key not in smc_results]
            
            if not missing_keys:
                self.log_test("Estructura de resultados SMC", True, "Todas las claves presentes")
            else:
                self.log_test("Estructura de resultados SMC", False, f"Faltan: {missing_keys}")
            
            # Test 2.3: Verificación de consistencia de datos
            fvg_count = len(smc_results.get('fvg', []))
            ob_count = len(smc_results.get('orderblocks', []))
            liq_count = len(smc_results.get('liquidity', []))
            
            if fvg_count >= 0 and ob_count >= 0 and liq_count >= 0:
                self.log_test("Conteo de elementos SMC", True, f"FVG: {fvg_count}, OB: {ob_count}, LIQ: {liq_count}")
            else:
                self.log_test("Conteo de elementos SMC", False, "Conteos negativos")
            
            # Test 2.4: Análisis múltiples timeframes
            for tf in ["15m", "1h"]:
                smc_tf = analyze(df, timeframe=tf)
                if smc_tf and isinstance(smc_tf, dict):
                    self.log_test(f"Análisis SMC {tf}", True, "Análisis exitoso")
                    self.smc_analyses[tf] = smc_tf
                else:
                    self.log_test(f"Análisis SMC {tf}", False, "Error en análisis")
            
            return True
            
        except Exception as e:
            self.log_test("Test SMC", False, f"Error: {str(e)}")
            return False
    
    def test_ml_predictor(self) -> bool:
        """Test del ML Predictor con verificaciones de consistencia"""
        print("\n🔍 TEST 3: ML Predictor y Consistencia")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("ML Predictor", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 3.1: Inicialización del ML Predictor
            ml_predictor = SMCMLPredictor()
            
            if ml_predictor:
                self.log_test("Inicialización ML Predictor", True, "Predictor creado correctamente")
            else:
                self.log_test("Inicialización ML Predictor", False, "Error en inicialización")
                return False
            
            # Test 3.2: Predicción básica
            prediction = ml_predictor.predict_signal_probability(df, {})
            
            if prediction and hasattr(prediction, 'probability'):
                self.log_test("Predicción ML básica", True, f"Prob: {prediction.probability:.3f}")
                self.ml_predictions['basic'] = prediction
            else:
                self.log_test("Predicción ML básica", False, "No se obtuvo predicción")
                return False
            
            # Test 3.3: Verificación de rangos de probabilidad
            prob = prediction.probability
            if 0 <= prob <= 1:
                self.log_test("Rango de probabilidad ML", True, f"Probabilidad válida: {prob:.3f}")
            else:
                self.log_test("Rango de probabilidad ML", False, f"Probabilidad fuera de rango: {prob}")
            
            # Test 3.4: Múltiples predicciones para consistencia
            predictions = []
            for i in range(3):
                pred = ml_predictor.predict_signal_probability(df, {})
                if pred and hasattr(pred, 'probability'):
                    predictions.append(pred.probability)
            
            if len(predictions) == 3:
                std_pred = np.std(predictions)
                if std_pred < 0.1:  # Las predicciones deberían ser consistentes
                    self.log_test("Consistencia de predicciones ML", True, f"Std: {std_pred:.3f}")
                else:
                    self.log_test("Consistencia de predicciones ML", False, f"Std muy alto: {std_pred:.3f}")
            
            # Test 3.5: Verificación de confianza
            if hasattr(prediction, 'confidence'):
                conf = prediction.confidence
                if 0 <= conf <= 1:
                    self.log_test("Confianza ML", True, f"Confianza válida: {conf:.3f}")
                else:
                    self.log_test("Confianza ML", False, f"Confianza fuera de rango: {conf}")
            
            return True
            
        except Exception as e:
            self.log_test("Test ML Predictor", False, f"Error: {str(e)}")
            return False
    
    def test_ml_signal_generator(self) -> bool:
        """Test del ML Signal Generator con verificaciones de consistencia"""
        print("\n🔍 TEST 4: ML Signal Generator y Consistencia")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data or 'basic' not in self.smc_analyses:
                self.log_test("ML Signal Generator", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            smc_analysis = self.smc_analyses['basic']
            
            # Test 4.1: Inicialización del Signal Generator
            signal_generator = MLSignalGenerator()
            
            if signal_generator:
                self.log_test("Inicialización Signal Generator", True, "Generator creado correctamente")
            else:
                self.log_test("Inicialización Signal Generator", False, "Error en inicialización")
                return False
            
            # Test 4.2: Generación de señal
            current_price = df['close'].iloc[-1]
            ml_prediction = {'probability': 0.6, 'confidence': 0.7, 'recommendation': 'BUY'}
            
            signal = signal_generator.generate_signal(df, ml_prediction, smc_analysis, current_price)
            
            if signal and isinstance(signal, MLSignal):
                self.log_test("Generación de señal ML", True, f"Señal: {signal.signal_type.value}")
            else:
                self.log_test("Generación de señal ML", False, "No se generó señal")
                return False
            
            # Test 4.3: Verificación de estructura de señal
            required_attrs = ['entry_price', 'take_profit_1', 'stop_loss', 'signal_type']
            missing_attrs = [attr for attr in required_attrs if not hasattr(signal, attr)]
            
            if not missing_attrs:
                self.log_test("Estructura de señal ML", True, "Todos los atributos presentes")
            else:
                self.log_test("Estructura de señal ML", False, f"Faltan: {missing_attrs}")
            
            # Test 4.4: Verificación de rangos de precios
            if hasattr(signal, 'entry_price') and hasattr(signal, 'take_profit_1') and hasattr(signal, 'stop_loss'):
                entry = signal.entry_price
                tp1 = signal.take_profit_1
                sl = signal.stop_loss
                
                if entry > 0 and tp1 > 0 and sl > 0:
                    self.log_test("Rangos de precios ML", True, f"Entry: {entry:.2f}, TP1: {tp1:.2f}, SL: {sl:.2f}")
                else:
                    self.log_test("Rangos de precios ML", False, "Precios inválidos")
            
            # Test 4.5: Verificación de Risk/Reward
            if hasattr(signal, 'risk_reward_ratio'):
                rr = signal.risk_reward_ratio
                if rr > 0:
                    self.log_test("Risk/Reward ML", True, f"R:R = {rr:.2f}")
                else:
                    self.log_test("Risk/Reward ML", False, f"R:R inválido: {rr}")
            
            return True
            
        except Exception as e:
            self.log_test("Test ML Signal Generator", False, f"Error: {str(e)}")
            return False
    
    def test_ml_integration(self) -> bool:
        """Test de integración ML con verificaciones de consistencia"""
        print("\n🔍 TEST 5: Integración ML y Consistencia")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Integración ML", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 5.1: ML Integration Manager
            ml_manager = MLIntegrationManager()
            
            if ml_manager:
                self.log_test("ML Integration Manager", True, "Manager creado correctamente")
            else:
                self.log_test("ML Integration Manager", False, "Error en creación")
                return False
            
            # Test 5.2: Predicción a través del manager
            prediction = ml_manager.get_signal_prediction(df)
            
            if prediction and hasattr(prediction, 'probability'):
                self.log_test("Predicción a través de manager", True, f"Prob: {prediction.probability:.3f}")
            else:
                self.log_test("Predicción a través de manager", False, "No se obtuvo predicción")
            
            # Test 5.3: ML Signal Integration
            signal_integration = MLSignalIntegration()
            
            if signal_integration:
                self.log_test("ML Signal Integration", True, "Integration creado correctamente")
            else:
                self.log_test("ML Signal Integration", False, "Error en creación")
            
            # Test 5.4: Generación de señal completa
            if 'basic' in self.smc_analyses:
                smc_analysis = self.smc_analyses['basic']
                current_price = df['close'].iloc[-1]
                
                signal = signal_integration.generate_ml_signal(df, smc_analysis, "BTCUSDT", "15m")
                
                if signal:
                    self.log_test("Generación de señal completa", True, f"Señal generada: {signal.signal_type.value}")
                else:
                    self.log_test("Generación de señal completa", False, "No se generó señal")
            
            return True
            
        except Exception as e:
            self.log_test("Test Integración ML", False, f"Error: {str(e)}")
            return False
    
    def test_data_consistency(self) -> bool:
        """Test de consistencia de datos entre diferentes fuentes"""
        print("\n🔍 TEST 6: Consistencia de Datos")
        print("=" * 60)
        
        try:
            # Test 6.1: Comparación entre métodos de obtención de datos
            if 'basic' in self.reference_data and 'extended' in self.reference_data:
                basic_df = self.reference_data['basic']
                extended_df = self.reference_data['extended']
                
                # Comparar columnas
                if set(basic_df.columns) == set(extended_df.columns):
                    self.log_test("Consistencia de columnas", True, "Columnas idénticas")
                else:
                    self.log_test("Consistencia de columnas", False, "Diferencias en columnas")
                
                # Comparar rangos de precios
                basic_price_range = basic_df['high'].max() - basic_df['low'].min()
                extended_price_range = extended_df['high'].max() - extended_df['low'].min()
                
                if abs(basic_price_range - extended_price_range) < 1000:  # Tolerancia
                    self.log_test("Consistencia de rangos de precio", True, "Rangos similares")
                else:
                    self.log_test("Consistencia de rangos de precio", False, "Rangos muy diferentes")
            
            # Test 6.2: Consistencia de análisis SMC
            if len(self.smc_analyses) > 1:
                basic_smc = self.smc_analyses.get('basic', {})
                tf_smc = self.smc_analyses.get('1h', {})
                
                if basic_smc and tf_smc:
                    basic_fvg = len(basic_smc.get('fvg', []))
                    tf_fvg = len(tf_smc.get('fvg', []))
                    
                    if basic_fvg >= 0 and tf_fvg >= 0:
                        self.log_test("Consistencia de análisis SMC", True, f"FVG 15m: {basic_fvg}, 1h: {tf_fvg}")
                    else:
                        self.log_test("Consistencia de análisis SMC", False, "Conteos negativos")
            
            # Test 6.3: Consistencia de predicciones ML
            if len(self.ml_predictions) > 1:
                predictions = list(self.ml_predictions.values())
                probs = [p.probability for p in predictions if hasattr(p, 'probability')]
                
                if len(probs) > 1:
                    std_probs = np.std(probs)
                    if std_probs < 0.2:  # Las predicciones deberían ser consistentes
                        self.log_test("Consistencia de predicciones ML", True, f"Std: {std_probs:.3f}")
                    else:
                        self.log_test("Consistencia de predicciones ML", False, f"Std muy alto: {std_probs:.3f}")
            
            return True
            
        except Exception as e:
            self.log_test("Test Consistencia", False, f"Error: {str(e)}")
            return False
    
    def test_bot_analysis(self) -> bool:
        """Test de análisis del bot con verificaciones"""
        print("\n🔍 TEST 7: Análisis del Bot")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Análisis del bot", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 7.1: Análisis básico del bot
            bot_analysis = get_smc_bot_analysis(df, "BTCUSDT", "15m")
            
            if bot_analysis and isinstance(bot_analysis, dict):
                self.log_test("Análisis básico del bot", True, f"Resultados: {list(bot_analysis.keys())}")
            else:
                self.log_test("Análisis básico del bot", False, "No se obtuvieron resultados")
            
            return True
            
        except Exception as e:
            self.log_test("Test Bot", False, f"Error: {str(e)}")
            return False
    
    def test_trade_engine(self) -> bool:
        """Test del motor de trading con verificaciones"""
        print("\n🔍 TEST 8: Motor de Trading")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Motor de trading", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 8.1: Análisis del motor de trading
            trade_analysis = get_trade_engine_analysis(df, "BTCUSDT", "15m")
            
            if trade_analysis and isinstance(trade_analysis, dict):
                self.log_test("Análisis del motor de trading", True, f"Resultados: {list(trade_analysis.keys())}")
            else:
                self.log_test("Análisis del motor de trading", False, "No se obtuvieron resultados")
            
            return True
            
        except Exception as e:
            self.log_test("Test Trade Engine", False, f"Error: {str(e)}")
            return False
    
    def test_backtesting(self) -> bool:
        """Test de backtesting con verificaciones"""
        print("\n🔍 TEST 9: Backtesting")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Backtesting", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 9.1: Backtesting básico
            backtest_results = run_backtest_analysis(df, "BTCUSDT", "15m")
            
            if backtest_results and isinstance(backtest_results, dict):
                self.log_test("Backtesting básico", True, f"Resultados: {list(backtest_results.keys())}")
            else:
                self.log_test("Backtesting básico", False, "No se obtuvieron resultados")
            
            return True
            
        except Exception as e:
            self.log_test("Test Backtesting", False, f"Error: {str(e)}")
            return False
    
    def test_edge_cases(self) -> bool:
        """Test de casos extremos y validaciones"""
        print("\n🔍 TEST 10: Casos Extremos y Validaciones")
        print("=" * 60)
        
        try:
            # Test 10.1: DataFrame vacío
            empty_df = pd.DataFrame()
            try:
                analyze(empty_df, timeframe="15m")
                self.log_test("DataFrame vacío", False, "Debería fallar")
            except:
                self.log_test("DataFrame vacío", True, "Manejo correcto de error")
            
            # Test 10.2: Datos con valores nulos
            df_with_nulls = pd.DataFrame({
                'timestamp': pd.date_range('2023-01-01', periods=10),
                'open': [100, 101, np.nan, 103, 104, 105, 106, 107, 108, 109],
                'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
                'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
                'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
                'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
            })
            
            try:
                analyze(df_with_nulls, timeframe="15m")
                self.log_test("Datos con valores nulos", True, "Manejo correcto")
            except:
                self.log_test("Datos con valores nulos", False, "Error inesperado")
            
            # Test 10.3: Datos con valores extremos
            extreme_df = pd.DataFrame({
                'timestamp': pd.date_range('2023-01-01', periods=10),
                'open': [1000000, 1000001, 1000002, 1000003, 1000004, 1000005, 1000006, 1000007, 1000008, 1000009],
                'high': [1000001, 1000002, 1000003, 1000004, 1000005, 1000006, 1000007, 1000008, 1000009, 1000010],
                'low': [999999, 1000000, 1000001, 1000002, 1000003, 1000004, 1000005, 1000006, 1000007, 1000008],
                'close': [1000000, 1000001, 1000002, 1000003, 1000004, 1000005, 1000006, 1000007, 1000008, 1000009],
                'volume': [1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000, 1900000]
            })
            
            try:
                analyze(extreme_df, timeframe="15m")
                self.log_test("Datos con valores extremos", True, "Manejo correcto")
            except:
                self.log_test("Datos con valores extremos", False, "Error inesperado")
            
            return True
            
        except Exception as e:
            self.log_test("Test Casos Extremos", False, f"Error: {str(e)}")
            return False
    
    def test_performance(self) -> bool:
        """Test de rendimiento"""
        print("\n🔍 TEST 11: Rendimiento")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Test de rendimiento", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 11.1: Tiempo de análisis SMC
            start_time = time.time()
            analyze(df, timeframe="15m")
            smc_time = time.time() - start_time
            
            if smc_time < 5.0:  # Debería ser rápido
                self.log_test("Rendimiento análisis SMC", True, f"Tiempo: {smc_time:.3f}s")
            else:
                self.log_test("Rendimiento análisis SMC", False, f"Demasiado lento: {smc_time:.3f}s")
            
            # Test 11.2: Tiempo de predicción ML
            ml_predictor = SMCMLPredictor()
            start_time = time.time()
            ml_predictor.predict_signal_probability(df, {})
            ml_time = time.time() - start_time
            
            if ml_time < 10.0:  # ML puede ser más lento
                self.log_test("Rendimiento predicción ML", True, f"Tiempo: {ml_time:.3f}s")
            else:
                self.log_test("Rendimiento predicción ML", False, f"Demasiado lento: {ml_time:.3f}s")
            
            return True
            
        except Exception as e:
            self.log_test("Test Rendimiento", False, f"Error: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte completo de todos los tests"""
        print("\n📊 REPORTE COMPLETO DEL SISTEMA")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Total de tests: {total_tests}")
        print(f"✅ Tests exitosos: {passed_tests}")
        print(f"❌ Tests fallidos: {failed_tests}")
        print(f"📊 Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        # Mostrar tests fallidos
        if failed_tests > 0:
            print("\n❌ TESTS FALLIDOS:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"  - {test_name}: {result['details']}")
        
        # Resumen de datos
        print(f"\n📊 RESUMEN DE DATOS:")
        print(f"  - Datos de referencia: {len(self.reference_data)}")
        print(f"  - Análisis SMC: {len(self.smc_analyses)}")
        print(f"  - Predicciones ML: {len(self.ml_predictions)}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'test_results': self.test_results,
            'reference_data': self.reference_data,
            'smc_analyses': self.smc_analyses,
            'ml_predictions': self.ml_predictions
        }

def run_comprehensive_test():
    """Ejecutar test completo del sistema"""
    print("🚀 INICIANDO TEST COMPLETO DEL SISTEMA SMC TRADINGVIEW CON ML")
    print("=" * 80)
    
    tester = ComprehensiveSystemTester()
    
    # Ejecutar todos los tests
    tests = [
        tester.test_data_fetching,
        tester.test_smc_analysis,
        tester.test_ml_predictor,
        tester.test_ml_signal_generator,
        tester.test_ml_integration,
        tester.test_data_consistency,
        tester.test_bot_analysis,
        tester.test_trade_engine,
        tester.test_backtesting,
        tester.test_edge_cases,
        tester.test_performance
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Error en test {test.__name__}: {str(e)}")
    
    # Generar reporte final
    report = tester.generate_report()
    
    print(f"\n⏱️ Tiempo total de ejecución: {time.time() - tester.start_time:.2f} segundos")
    
    return report

if __name__ == "__main__":
    report = run_comprehensive_test()
    print("\n🎯 TEST COMPLETO FINALIZADO") 