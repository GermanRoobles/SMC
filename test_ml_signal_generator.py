#!/usr/bin/env python3
"""
Test completo del ML Signal Generator
====================================

Test exhaustivo del sistema de generación de señales ML completas.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smc_ml_signal_generator import get_ml_signal_generator, SignalType, SignalStrength
from smc_ml_signal_integration import get_ml_signal_integration

def create_test_data():
    """Crear datos de prueba realistas"""
    np.random.seed(42)
    
    # Crear datos OHLCV simulando BTC
    dates = pd.date_range('2024-01-01', periods=200, freq='15T')
    base_price = 50000
    
    # Simular movimiento de precios realista
    price_changes = np.random.normal(0, 0.002, 200).cumsum()
    prices = base_price * (1 + price_changes)
    
    # Crear OHLCV
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.normal(0, 0.001, 200)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.002, 200))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.002, 200))),
        'close': prices,
        'volume': np.random.lognormal(10, 0.5, 200)
    })
    
    return data

def create_test_smc_analysis():
    """Crear análisis SMC de prueba"""
    return {
        'fvg': [
            {'top': 51000, 'bottom': 50800, 'timestamp': datetime.now()},
            {'top': 50500, 'bottom': 50300, 'timestamp': datetime.now()},
        ],
        'ob': [
            {'top': 51200, 'bottom': 51000, 'volume': 1000000, 'timestamp': datetime.now()},
        ],
        'liquidity': [
            {'level': 51500, 'type': 'resistance', 'strength': 0.8},
            {'level': 50000, 'type': 'support', 'strength': 0.7},
            {'level': 49500, 'type': 'support', 'strength': 0.6},
        ],
        'market_structure': 'bullish',
        'bos_choch_strength': 0.75
    }

def create_test_ml_prediction(scenario='strong_buy'):
    """Crear predicción ML de prueba"""
    scenarios = {
        'strong_buy': {
            'probability': 0.92,
            'confidence': 0.88,
            'recommendation': 'STRONG_BUY'
        },
        'buy': {
            'probability': 0.78,
            'confidence': 0.75,
            'recommendation': 'BUY'
        },
        'weak_signal': {
            'probability': 0.55,
            'confidence': 0.60,
            'recommendation': 'HOLD'
        },
        'low_confidence': {
            'probability': 0.85,
            'confidence': 0.45,
            'recommendation': 'BUY'
        }
    }
    return scenarios.get(scenario, scenarios['strong_buy'])

def test_ml_signal_generator_basic():
    """Test básico del generador de señales"""
    print("🧪 Test 1: Generación básica de señales ML")
    
    try:
        generator = get_ml_signal_generator()
        data = create_test_data()
        ml_prediction = create_test_ml_prediction('strong_buy')
        smc_analysis = create_test_smc_analysis()
        current_price = 50000.0
        
        # Generar señal
        signal = generator.generate_signal(data, ml_prediction, smc_analysis, current_price)
        
        if signal:
            print("✅ Señal generada exitosamente")
            print(f"   Tipo: {signal.signal_type.value}")
            print(f"   Fuerza: {signal.strength.value}")
            print(f"   Entry: ${signal.entry_price:.2f}")
            print(f"   SL: ${signal.stop_loss:.2f}")
            print(f"   TP1: ${signal.take_profit_1:.2f} (RR: {signal.risk_reward_1:.2f})")
            print(f"   TP2: ${signal.take_profit_2:.2f} (RR: {signal.risk_reward_2:.2f})")
            print(f"   TP3: ${signal.take_profit_3:.2f} (RR: {signal.risk_reward_3:.2f})")
            print(f"   Validez: {signal.signal_validity_hours}h")
            print(f"   Confluencia: {signal.confluence_score:.2%}")
            return True
        else:
            print("❌ No se pudo generar señal")
            return False
            
    except Exception as e:
        print(f"❌ Error en test básico: {str(e)}")
        return False

def test_signal_scenarios():
    """Test de diferentes escenarios de señales"""
    print("\n🧪 Test 2: Diferentes escenarios de señales")
    
    generator = get_ml_signal_generator()
    data = create_test_data()
    smc_analysis = create_test_smc_analysis()
    current_price = 50000.0
    
    scenarios = ['strong_buy', 'buy', 'weak_signal', 'low_confidence']
    results = {}
    
    for scenario in scenarios:
        try:
            ml_prediction = create_test_ml_prediction(scenario)
            signal = generator.generate_signal(data, ml_prediction, smc_analysis, current_price)
            
            if signal:
                results[scenario] = {
                    'generated': True,
                    'type': signal.signal_type.value,
                    'strength': signal.strength.value,
                    'rr': signal.risk_reward_1,
                    'confluence': signal.confluence_score
                }
                print(f"✅ {scenario}: {signal.signal_type.value} (RR: {signal.risk_reward_1:.2f})")
            else:
                results[scenario] = {'generated': False}
                print(f"❌ {scenario}: No generada")
                
        except Exception as e:
            print(f"❌ Error en {scenario}: {str(e)}")
            results[scenario] = {'generated': False, 'error': str(e)}
    
    # Verificar que señales fuertes se generen y débiles no
    strong_generated = results.get('strong_buy', {}).get('generated', False)
    weak_rejected = not results.get('weak_signal', {}).get('generated', True)
    
    if strong_generated and weak_rejected:
        print("✅ Filtrado de señales funciona correctamente")
        return True
    else:
        print("❌ Problemas con filtrado de señales")
        return False

def test_risk_management():
    """Test de gestión de riesgo"""
    print("\n🧪 Test 3: Gestión de riesgo")
    
    try:
        generator = get_ml_signal_generator()
        data = create_test_data()
        ml_prediction = create_test_ml_prediction('strong_buy')
        smc_analysis = create_test_smc_analysis()
        current_price = 50000.0
        
        signal = generator.generate_signal(data, ml_prediction, smc_analysis, current_price)
        
        if not signal:
            print("❌ No se pudo generar señal para test de riesgo")
            return False
        
        # Verificar Risk/Reward ratios
        rr_valid = all([
            signal.risk_reward_1 >= 1.5,  # RR mínimo
            signal.risk_reward_2 > signal.risk_reward_1,  # RR creciente
            signal.risk_reward_3 > signal.risk_reward_2
        ])
        
        # Verificar tamaño de posición
        position_valid = 0.1 <= signal.position_size_percent <= 2.5  # Entre 0.1% y 2.5%
        
        # Verificar stop loss lógico
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            sl_valid = signal.stop_loss < signal.entry_price
        else:
            sl_valid = signal.stop_loss > signal.entry_price
        
        # Verificar take profits lógicos
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            tp_valid = (signal.take_profit_1 > signal.entry_price and
                       signal.take_profit_2 > signal.take_profit_1 and
                       signal.take_profit_3 > signal.take_profit_2)
        else:
            tp_valid = (signal.take_profit_1 < signal.entry_price and
                       signal.take_profit_2 < signal.take_profit_1 and
                       signal.take_profit_3 < signal.take_profit_2)
        
        print(f"   RR Ratios válidos: {'✅' if rr_valid else '❌'}")
        print(f"   Tamaño posición válido: {'✅' if position_valid else '❌'} ({signal.position_size_percent:.2f}%)")
        print(f"   Stop Loss lógico: {'✅' if sl_valid else '❌'}")
        print(f"   Take Profits lógicos: {'✅' if tp_valid else '❌'}")
        
        return all([rr_valid, position_valid, sl_valid, tp_valid])
        
    except Exception as e:
        print(f"❌ Error en test de riesgo: {str(e)}")
        return False

def test_signal_integration():
    """Test de integración completa"""
    print("\n🧪 Test 4: Integración ML Signal")
    
    try:
        integration = get_ml_signal_integration()
        data = create_test_data()
        smc_analysis = create_test_smc_analysis()
        
        # Generar señal integrada
        signal = integration.generate_ml_signal(
            data, smc_analysis, "BTC/USDT", "15m"
        )
        
        if signal:
            print("✅ Señal integrada generada exitosamente")
            
            # Verificar características adicionales
            features_valid = signal.symbol == "BTC/USDT"
            timing_valid = 1 <= signal.signal_validity_hours <= 24
            id_valid = len(signal.signal_id) > 10
            
            print(f"   Símbolo correcto: {'✅' if features_valid else '❌'}")
            print(f"   Timing válido: {'✅' if timing_valid else '❌'} ({signal.signal_validity_hours}h)")
            print(f"   ID único: {'✅' if id_valid else '❌'}")
            
            # Test de estadísticas
            stats = integration.get_integration_stats()
            stats_valid = 'ml_signal_generator' in stats and 'ml_predictor' in stats
            
            print(f"   Estadísticas disponibles: {'✅' if stats_valid else '❌'}")
            
            return all([features_valid, timing_valid, id_valid, stats_valid])
        else:
            print("❌ No se pudo generar señal integrada")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de integración: {str(e)}")
        return False

def test_signal_cooldown():
    """Test de cooldown entre señales"""
    print("\n🧪 Test 5: Cooldown entre señales")
    
    try:
        integration = get_ml_signal_integration()
        data = create_test_data()
        smc_analysis = create_test_smc_analysis()
        
        # Reducir cooldown para test
        integration.signal_cooldown_minutes = 0.1  # 6 segundos
        
        # Generar primera señal
        signal1 = integration.generate_ml_signal(data, smc_analysis, "BTC/USDT", "15m")
        
        # Intentar generar segunda señal inmediatamente
        signal2 = integration.generate_ml_signal(data, smc_analysis, "BTC/USDT", "15m")
        
        # Esperar cooldown
        import time
        time.sleep(0.2)  # 200ms > 100ms cooldown
        
        # Generar tercera señal
        signal3 = integration.generate_ml_signal(data, smc_analysis, "BTC/USDT", "15m")
        
        first_generated = signal1 is not None
        second_blocked = signal2 is None  # Debe ser bloqueada por cooldown
        third_generated = signal3 is not None  # Debe pasar después del cooldown
        
        print(f"   Primera señal generada: {'✅' if first_generated else '❌'}")
        print(f"   Segunda señal bloqueada: {'✅' if second_blocked else '❌'}")
        print(f"   Tercera señal generada: {'✅' if third_generated else '❌'}")
        
        return first_generated and second_blocked and third_generated
        
    except Exception as e:
        print(f"❌ Error en test de cooldown: {str(e)}")
        return False

def test_signal_expiry():
    """Test de expiración de señales"""
    print("\n🧪 Test 6: Expiración de señales")
    
    try:
        generator = get_ml_signal_generator()
        
        # Limpiar señales previas
        generator.active_signals = []
        generator.signal_history = []
        
        data = create_test_data()
        ml_prediction = create_test_ml_prediction('strong_buy')
        smc_analysis = create_test_smc_analysis()
        current_price = 50000.0
        
        # Generar señal con validez corta
        signal = generator.generate_signal(data, ml_prediction, smc_analysis, current_price)
        
        if not signal:
            print("❌ No se pudo generar señal para test de expiración")
            return False
        
        # Modificar tiempo de expiración para test
        signal.expiry_time = datetime.now() - timedelta(seconds=1)  # Expirada
        generator.active_signals = [signal]
        
        # Verificar señales activas
        active_before = len(generator.get_active_signals())
        
        # Forzar limpieza (get_active_signals ya limpia automáticamente)
        active_after = len(generator.get_active_signals())
        
        print(f"   Señales antes de limpieza: {active_before}")
        print(f"   Señales después de limpieza: {active_after}")
        
        expiry_works = active_after == 0  # Señal expirada debe ser removida
        
        print(f"   Expiración funciona: {'✅' if expiry_works else '❌'}")
        
        return expiry_works
        
    except Exception as e:
        print(f"❌ Error en test de expiración: {str(e)}")
        return False

def test_signal_formatting():
    """Test de formateo de señales para UI"""
    print("\n🧪 Test 7: Formateo para UI")
    
    try:
        generator = get_ml_signal_generator()
        data = create_test_data()
        ml_prediction = create_test_ml_prediction('strong_buy')
        smc_analysis = create_test_smc_analysis()
        current_price = 50000.0
        
        signal = generator.generate_signal(data, ml_prediction, smc_analysis, current_price)
        
        if not signal:
            print("❌ No se pudo generar señal para test de formateo")
            return False
        
        # Formatear para display
        formatted = generator.format_signal_for_display(signal)
        
        # Verificar campos requeridos
        required_fields = [
            'id', 'timestamp', 'symbol', 'type', 'strength',
            'entry', 'sl', 'tp1', 'tp2', 'tp3',
            'rr1', 'rr2', 'rr3', 'ml_prob', 'ml_conf',
            'position_size', 'validity', 'expires', 'confluence'
        ]
        
        fields_present = all(field in formatted for field in required_fields)
        
        # Verificar formato de precios (deben incluir $)
        price_format_ok = all(
            formatted[field].startswith('$') 
            for field in ['entry', 'sl', 'tp1', 'tp2', 'tp3']
        )
        
        # Verificar formato de porcentajes
        percentage_format_ok = all(
            formatted[field].endswith('%')
            for field in ['ml_prob', 'ml_conf', 'position_size', 'confluence']
        )
        
        print(f"   Campos requeridos presentes: {'✅' if fields_present else '❌'}")
        print(f"   Formato de precios correcto: {'✅' if price_format_ok else '❌'}")
        print(f"   Formato de porcentajes correcto: {'✅' if percentage_format_ok else '❌'}")
        
        if fields_present and price_format_ok and percentage_format_ok:
            print("   Ejemplo de señal formateada:")
            for key, value in list(formatted.items())[:5]:
                print(f"     {key}: {value}")
        
        return fields_present and price_format_ok and percentage_format_ok
        
    except Exception as e:
        print(f"❌ Error en test de formateo: {str(e)}")
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests completos del ML Signal Generator")
    print("=" * 60)
    
    tests = [
        test_ml_signal_generator_basic,
        test_signal_scenarios,
        test_risk_management,
        test_signal_integration,
        test_signal_cooldown,
        test_signal_expiry,
        test_signal_formatting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Error ejecutando test {test.__name__}: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests pasados")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON! ML Signal Generator está listo.")
        return True
    else:
        print("⚠️ Algunos tests fallaron. Revisar implementación.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n✅ ML Signal Generator completamente funcional")
        
        # Mostrar ejemplo de uso
        print("\n📋 EJEMPLO DE USO:")
        print("-" * 40)
        
        integration = get_ml_signal_integration()
        stats = integration.get_integration_stats()
        
        print("📊 Estadísticas del sistema:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    print(f"    {subkey}: {subvalue}")
            else:
                print(f"  {key}: {value}")
    else:
        print("\n❌ ML Signal Generator requiere correcciones")
        sys.exit(1)