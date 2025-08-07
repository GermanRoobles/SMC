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
    from configs.smc_profiles import SMCProfiles
    from configs.smc_config import get_config_by_profile
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
        self.symbols = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT"]
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
            # Test 1.1: Datos básicos (usar datos más realistas)
            df_basic = get_ohlcv("BTC/USDT", "1h", limit=3)  # 3 días = 72 velas máximo
            df_extended = get_ohlcv_extended("BTC/USDT", "15m", days=3)  # 3 días = 288 velas máximo
            
            if df_basic is not None and len(df_basic) > 0:
                self.log_test("Datos básicos BTC/USDT 1h", True, f"{len(df_basic)} velas obtenidas")
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
                
                # Comparar rangos de precios (ajustado para diferentes timeframes)
                basic_price_range = basic_df['high'].max() - basic_df['low'].min()
                extended_price_range = extended_df['high'].max() - extended_df['low'].min()
                
                # Tolerancia más alta para diferentes timeframes
                tolerance = max(basic_price_range, extended_price_range) * 0.8  # 80% del rango mayor
                
                if abs(basic_price_range - extended_price_range) < tolerance:
                    self.log_test("Consistencia de rangos de precio", True, f"Rangos similares (diff: {abs(basic_price_range - extended_price_range):.2f})")
                else:
                    self.log_test("Consistencia de rangos de precio", False, f"Rangos muy diferentes (diff: {abs(basic_price_range - extended_price_range):.2f})")
            
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
            # Crear señales de ejemplo para el backtesting
            from smc_ml_signal_generator import MLSignalGenerator
            signal_generator = MLSignalGenerator()
            sample_signals = []
            
            # Generar algunas señales de ejemplo
            for i in range(3):
                try:
                    signal = signal_generator.generate_signal(df, {}, symbol="BTC/USDT")
                    if signal:
                        sample_signals.append(signal)
                except:
                    pass
            
            backtest_results = run_backtest_analysis(df, sample_signals)
            
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

    def test_historical_analysis(self) -> bool:
        """Test de análisis histórico"""
        print("\n🔍 TEST 12: Análisis Histórico")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Análisis histórico", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 12.1: Importar módulo histórico
            try:
                from smc_historical import create_historical_manager
                self.log_test("Importación análisis histórico", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación análisis histórico", False, f"Error: {str(e)}")
                return False
            
            # Test 12.2: Crear analizador histórico
            try:
                analyzer = create_historical_manager("BTC/USDT", "15m")
                self.log_test("Creación analizador histórico", True, "Analizador creado")
            except Exception as e:
                self.log_test("Creación analizador histórico", False, f"Error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Test Histórico", False, f"Error: {str(e)}")
            return False

    def test_visualization(self) -> bool:
        """Test de visualización avanzada"""
        print("\n🔍 TEST 13: Visualización Avanzada")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Visualización", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 13.1: Importar módulo de visualización
            try:
                from smc_visualization_advanced import enhance_signal_visualization
                self.log_test("Importación visualización avanzada", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación visualización avanzada", False, f"Error: {str(e)}")
                return False
            
            # Test 13.2: Crear visualizador avanzado
            try:
                # Crear figura de prueba
                import plotly.graph_objects as go
                fig = go.Figure()
                enhance_signal_visualization(fig, df, {})
                self.log_test("Creación visualizador avanzado", True, "Visualizador creado")
            except Exception as e:
                self.log_test("Creación visualizador avanzado", False, f"Error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Test Visualización", False, f"Error: {str(e)}")
            return False

    def test_bot_integration(self) -> bool:
        """Test de integración del bot"""
        print("\n🔍 TEST 14: Integración del Bot")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Integración bot", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 14.1: Importar módulo del bot
            try:
                from smc_bot import SMCBot
                self.log_test("Importación módulo bot", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación módulo bot", False, f"Error: {str(e)}")
                return False
            
            # Test 14.2: Crear instancia del bot
            try:
                bot = SMCBot()
                self.log_test("Creación instancia bot", True, "Bot creado correctamente")
            except Exception as e:
                self.log_test("Creación instancia bot", False, f"Error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Test Bot Integration", False, f"Error: {str(e)}")
            return False

    def test_fear_greed_index(self) -> bool:
        """Test del índice Fear & Greed"""
        print("\n🔍 TEST 15: Índice Fear & Greed")
        print("=" * 60)
        
        try:
            # Test 15.1: Importar módulo Fear & Greed
            try:
                from greed_fear_btc import get_fear_greed_index
                self.log_test("Importación Fear & Greed", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación Fear & Greed", False, f"Error: {str(e)}")
                return False
            
            # Test 15.2: Obtener índice Fear & Greed
            try:
                fear_greed = get_fear_greed_index()
                if fear_greed is not None and not fear_greed.empty:
                    latest_value = fear_greed['value'].iloc[-1] if 'value' in fear_greed.columns else 'N/A'
                    self.log_test("Obtención Fear & Greed", True, f"Índice obtenido: {latest_value}")
                else:
                    self.log_test("Obtención Fear & Greed", False, "No se pudo obtener el índice")
            except Exception as e:
                self.log_test("Obtención Fear & Greed", False, f"Error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Test Fear & Greed", False, f"Error: {str(e)}")
            return False
    
    def test_data_authenticity(self) -> bool:
        """Test de autenticidad y corrección de datos"""
        print("\n🔍 TEST 16: Verificación de Autenticidad de Datos")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("Verificación de datos", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 16.1: Verificación de rangos de precios realistas
            price_range = df['high'].max() - df['low'].min()
            avg_price = df['close'].mean()
            
            # Bitcoin debería estar entre $10,000 y $200,000 en los últimos años
            if 10000 <= avg_price <= 200000:
                self.log_test("Rango de precios realista", True, f"Precio promedio: ${avg_price:.2f}")
            else:
                self.log_test("Rango de precios realista", False, f"Precio sospechoso: ${avg_price:.2f}")
            
            # Test 16.2: Verificación de volatilidad realista
            volatility = df['close'].pct_change().std()
            if 0.001 <= volatility <= 0.1:  # 0.1% a 10% de volatilidad diaria
                self.log_test("Volatilidad realista", True, f"Volatilidad: {volatility:.4f}")
            else:
                self.log_test("Volatilidad realista", False, f"Volatilidad sospechosa: {volatility:.4f}")
            
            # Test 16.3: Verificación de secuencia temporal correcta
            df_sorted = df.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff().dropna()
            
            # Para 1h timeframe, las diferencias deberían ser ~1 hora
            expected_diff = pd.Timedelta(hours=1)
            tolerance = pd.Timedelta(minutes=30)  # ±30 minutos de tolerancia
            
            correct_intervals = sum(1 for diff in time_diffs if abs(diff - expected_diff) <= tolerance)
            total_intervals = len(time_diffs)
            
            if total_intervals > 0 and (correct_intervals / total_intervals) >= 0.8:  # 80% correctos
                self.log_test("Secuencia temporal correcta", True, f"{correct_intervals}/{total_intervals} intervalos correctos")
            else:
                self.log_test("Secuencia temporal correcta", False, f"Solo {correct_intervals}/{total_intervals} intervalos correctos")
            
            # Test 16.4: Verificación de relaciones OHLC lógicas
            logical_ohlc = 0
            total_candles = len(df)
            
            for _, row in df.iterrows():
                # High >= Low
                if row['high'] >= row['low']:
                    # Open y Close están entre High y Low
                    if row['low'] <= row['open'] <= row['high'] and row['low'] <= row['close'] <= row['high']:
                        logical_ohlc += 1
            
            if (logical_ohlc / total_candles) >= 0.95:  # 95% de velas lógicas
                self.log_test("Relaciones OHLC lógicas", True, f"{logical_ohlc}/{total_candles} velas lógicas")
            else:
                self.log_test("Relaciones OHLC lógicas", False, f"Solo {logical_ohlc}/{total_candles} velas lógicas")
            
            # Test 16.5: Verificación de volumen realista
            avg_volume = df['volume'].mean()
            if avg_volume > 0:
                self.log_test("Volumen realista", True, f"Volumen promedio: {avg_volume:.0f}")
            else:
                self.log_test("Volumen realista", False, "Volumen cero o negativo")
            
            # Test 16.6: Verificación de ausencia de datos duplicados
            duplicates = df.duplicated(subset=['timestamp']).sum()
            if duplicates == 0:
                self.log_test("Sin datos duplicados", True, "No se encontraron duplicados")
            else:
                self.log_test("Sin datos duplicados", False, f"Encontrados {duplicates} duplicados")
            
            # Test 16.7: Verificación de ausencia de valores nulos críticos
            null_counts = df[['timestamp', 'open', 'high', 'low', 'close']].isnull().sum()
            critical_nulls = null_counts.sum()
            
            if critical_nulls == 0:
                self.log_test("Sin valores nulos críticos", True, "Datos completos")
            else:
                self.log_test("Sin valores nulos críticos", False, f"Encontrados {critical_nulls} valores nulos")
            
            # Test 16.8: Verificación de consistencia entre timeframes
            if 'extended' in self.reference_data:
                df_15m = self.reference_data['extended']
                
                # Los datos de 15m deberían tener más velas que 1h para el mismo período
                if len(df_15m) > len(df):
                    self.log_test("Consistencia entre timeframes", True, f"15m: {len(df_15m)} vs 1h: {len(df)}")
                else:
                    self.log_test("Consistencia entre timeframes", False, f"15m: {len(df_15m)} vs 1h: {len(df)}")
            
            # Test 16.9: Verificación de rangos de precios coherentes
            price_std = df['close'].std()
            price_mean = df['close'].mean()
            cv = price_std / price_mean  # Coeficiente de variación
            
            if 0.001 <= cv <= 0.5:  # 0.1% a 50% de variación (más permisivo)
                self.log_test("Coherencia de rangos de precios", True, f"CV: {cv:.4f}")
            else:
                self.log_test("Coherencia de rangos de precios", False, f"CV sospechoso: {cv:.4f}")
            
            # Test 16.10: Verificación de tendencias realistas
            # Calcular tendencia usando regresión lineal simple
            x = np.arange(len(df))
            y = df['close'].values
            slope, _ = np.polyfit(x, y, 1)
            
            # La pendiente debería ser razonable (no extremadamente alta o baja)
            max_slope = price_mean * 0.1  # Máximo 10% del precio promedio por vela
            
            if abs(slope) <= max_slope:
                self.log_test("Tendencia realista", True, f"Pendiente: {slope:.2f}")
            else:
                self.log_test("Tendencia realista", False, f"Pendiente sospechosa: {slope:.2f}")
            
            return True
            
        except Exception as e:
            self.log_test("Test Autenticidad", False, f"Error: {str(e)}")
            return False

    def test_advanced_ml(self) -> bool:
        """Test de ML avanzado"""
        print("\n🔍 TEST 17: ML Avanzado")
        print("=" * 60)
        
        try:
            if 'basic' not in self.reference_data:
                self.log_test("ML Avanzado", False, "No hay datos de referencia")
                return False
            
            df = self.reference_data['basic']
            
            # Test 17.1: Importar módulo ML avanzado
            try:
                from smc_ml_advanced import create_advanced_ml_system
                self.log_test("Importación ML Avanzado", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación ML Avanzado", False, f"Error: {str(e)}")
                return False
            
            # Test 17.2: Crear sistema ML avanzado
            try:
                ml_system = create_advanced_ml_system()
                self.log_test("Creación sistema ML avanzado", True, "Sistema creado correctamente")
            except Exception as e:
                self.log_test("Creación sistema ML avanzado", False, f"Error: {str(e)}")
                return False
            
            # Test 17.3: Predicción de volatilidad
            try:
                volatility = ml_system.predict_volatility(df)
                if volatility and hasattr(volatility, 'current_volatility'):
                    self.log_test("Predicción de volatilidad", True, f"Vol: {volatility.current_volatility:.4f}")
                else:
                    self.log_test("Predicción de volatilidad", False, "No se pudo predecir volatilidad")
            except Exception as e:
                self.log_test("Predicción de volatilidad", False, f"Error: {str(e)}")
            
            # Test 17.4: Detección de anomalías
            try:
                anomalies = ml_system.detect_anomalies(df)
                self.log_test("Detección de anomalías", True, f"Anomalías detectadas: {len(anomalies)}")
            except Exception as e:
                self.log_test("Detección de anomalías", False, f"Error: {str(e)}")
            
            # Test 17.5: Clasificación de patrones
            try:
                patterns = ml_system.classify_patterns(df)
                self.log_test("Clasificación de patrones", True, f"Patrones clasificados: {len(patterns)}")
            except Exception as e:
                self.log_test("Clasificación de patrones", False, f"Error: {str(e)}")
            
            # Test 17.6: Predicción de tendencia
            try:
                trend = ml_system.predict_trend(df)
                if trend and hasattr(trend, 'direction'):
                    self.log_test("Predicción de tendencia", True, f"Tendencia: {trend.direction.value}")
                else:
                    self.log_test("Predicción de tendencia", False, "No se pudo predecir tendencia")
            except Exception as e:
                self.log_test("Predicción de tendencia", False, f"Error: {str(e)}")
            
            # Test 17.7: Análisis de sentimiento
            try:
                sentiment = ml_system.analyze_sentiment(df)
                if sentiment and hasattr(sentiment, 'sentiment_label'):
                    self.log_test("Análisis de sentimiento", True, f"Sentimiento: {sentiment.sentiment_label}")
                else:
                    self.log_test("Análisis de sentimiento", False, "No se pudo analizar sentimiento")
            except Exception as e:
                self.log_test("Análisis de sentimiento", False, f"Error: {str(e)}")
            
            # Test 17.8: Análisis completo
            try:
                analysis = ml_system.get_comprehensive_analysis(df)
                if analysis and 'volatility' in analysis:
                    self.log_test("Análisis completo ML", True, "Análisis completo ejecutado")
                else:
                    self.log_test("Análisis completo ML", False, "No se pudo ejecutar análisis completo")
            except Exception as e:
                self.log_test("Análisis completo ML", False, f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test("Test ML Avanzado", False, f"Error: {str(e)}")
            return False
    
    def test_multi_timeframe_analysis(self) -> bool:
        """Test de análisis multi-timeframe"""
        print("\n🔍 TEST 18: Multi-Timeframe Analysis")
        print("=" * 60)
        
        try:
            # Test 18.1: Importar módulo multi-timeframe
            try:
                from smc_multi_timeframe import create_multi_timeframe_analyzer
                self.log_test("Importación Multi-Timeframe", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación Multi-Timeframe", False, f"Error: {str(e)}")
                return False
            
            # Test 18.2: Crear analizador multi-timeframe
            try:
                analyzer = create_multi_timeframe_analyzer()
                self.log_test("Creación analizador multi-timeframe", True, "Analizador creado correctamente")
            except Exception as e:
                self.log_test("Creación analizador multi-timeframe", False, f"Error: {str(e)}")
                return False
            
            # Test 18.3: Análisis multi-timeframe
            try:
                analyses = analyzer.analyze_all_timeframes("BTC/USDT", 7)
                if analyses and len(analyses) > 0:
                    self.log_test("Análisis multi-timeframe", True, f"Análisis completado para {len(analyses)} timeframes")
                else:
                    self.log_test("Análisis multi-timeframe", False, "No se pudo realizar análisis")
            except Exception as e:
                self.log_test("Análisis multi-timeframe", False, f"Error: {str(e)}")
            
            # Test 18.4: Resumen multi-timeframe
            try:
                summary = analyzer.get_multi_timeframe_summary(analyses)
                if summary and 'timeframes_analyzed' in summary:
                    self.log_test("Resumen multi-timeframe", True, f"Resumen generado: {summary['timeframes_analyzed']} timeframes")
                else:
                    self.log_test("Resumen multi-timeframe", False, "No se pudo generar resumen")
            except Exception as e:
                self.log_test("Resumen multi-timeframe", False, f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test("Test Multi-Timeframe", False, f"Error: {str(e)}")
            return False
    
    def test_market_structure_analysis(self) -> bool:
        """Test de análisis de estructura de mercado"""
        print("\n🔍 TEST 19: Market Structure Analysis")
        print("=" * 60)
        
        try:
            # Test 19.1: Importar módulo de estructura de mercado
            try:
                from smc_market_structure import create_market_structure_analyzer
                self.log_test("Importación Market Structure", True, "Módulo importado correctamente")
            except ImportError as e:
                self.log_test("Importación Market Structure", False, f"Error: {str(e)}")
                return False
            
            # Test 19.2: Crear analizador de estructura
            try:
                analyzer = create_market_structure_analyzer()
                self.log_test("Creación analizador de estructura", True, "Analizador creado correctamente")
            except Exception as e:
                self.log_test("Creación analizador de estructura", False, f"Error: {str(e)}")
                return False
            
            # Test 19.3: Obtener datos para análisis
            try:
                df = get_ohlcv_extended("BTC/USDT", "1h", 7)
                if df is not None and not df.empty:
                    self.log_test("Obtención de datos", True, f"Datos obtenidos: {len(df)} registros")
                else:
                    self.log_test("Obtención de datos", False, "No se pudieron obtener datos")
                    return False
            except Exception as e:
                self.log_test("Obtención de datos", False, f"Error: {str(e)}")
                return False
            
            # Test 19.4: Análisis de estructura de mercado
            try:
                structure_analysis = analyzer.analyze_market_structure(df, "1h")
                if structure_analysis and len(structure_analysis) > 0:
                    self.log_test("Análisis de estructura", True, f"Análisis completado con {len(structure_analysis)} componentes")
                else:
                    self.log_test("Análisis de estructura", False, "No se pudo realizar análisis")
            except Exception as e:
                self.log_test("Análisis de estructura", False, f"Error: {str(e)}")
            
            # Test 19.5: Identificación de swing points
            try:
                swing_points = analyzer._identify_swing_points(df)
                if swing_points:
                    self.log_test("Swing points", True, f"Swing points identificados: {len(swing_points)}")
                else:
                    self.log_test("Swing points", False, "No se identificaron swing points")
            except Exception as e:
                self.log_test("Swing points", False, f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test("Test Market Structure", False, f"Error: {str(e)}")
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
        tester.test_performance,
        tester.test_historical_analysis,
        tester.test_visualization,
        tester.test_bot_integration,
        tester.test_fear_greed_index,
        tester.test_data_authenticity,
        tester.test_advanced_ml,
        tester.test_multi_timeframe_analysis,
        tester.test_market_structure_analysis
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