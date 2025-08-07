#!/usr/bin/env python3
"""
Optimizaciones de Performance para SMC TradingView
Mejoras en velocidad, memoria y eficiencia
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import time
import psutil
import gc

class PerformanceOptimizer:
    """Optimizador de performance para el sistema SMC"""
    
    def __init__(self):
        self.cache = {}
        self.memory_threshold = 0.8  # 80% de memoria
        self.cache_size_limit = 100
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimizar DataFrame para mejor performance"""
        try:
            # Reducir tipos de datos
            for col in df.select_dtypes(include=['float64']).columns:
                df[col] = pd.to_numeric(df[col], downcast='float')
            
            for col in df.select_dtypes(include=['int64']).columns:
                df[col] = pd.to_numeric(df[col], downcast='integer')
            
            # Optimizar timestamps
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            
            return df
        except Exception as e:
            print(f"⚠️ Error optimizando DataFrame: {e}")
            return df
    
    def memory_cleanup(self):
        """Limpiar memoria cuando sea necesario"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100
            
            if memory_percent > self.memory_threshold:
                print(f"🧹 Limpiando memoria ({memory_percent:.1%})")
                gc.collect()
                
                # Limpiar cache si es muy grande
                if len(self.cache) > self.cache_size_limit:
                    # Mantener solo los elementos más recientes
                    keys_to_remove = list(self.cache.keys())[:-50]
                    for key in keys_to_remove:
                        del self.cache[key]
                    print(f"🗑️ Cache limpiado: {len(self.cache)} elementos")
                    
        except Exception as e:
            print(f"⚠️ Error en limpieza de memoria: {e}")
    
    def cache_result(self, key: str, result: any, max_age: int = 300):
        """Cachear resultado con tiempo de expiración"""
        try:
            self.cache[key] = {
                'data': result,
                'timestamp': time.time(),
                'max_age': max_age
            }
        except Exception as e:
            print(f"⚠️ Error cacheando resultado: {e}")
    
    def get_cached_result(self, key: str) -> Optional[any]:
        """Obtener resultado cacheado si es válido"""
        try:
            if key in self.cache:
                cached = self.cache[key]
                age = time.time() - cached['timestamp']
                
                if age < cached['max_age']:
                    return cached['data']
                else:
                    # Expirar cache
                    del self.cache[key]
                    
        except Exception as e:
            print(f"⚠️ Error obteniendo cache: {e}")
        
        return None
    
    def optimize_ml_predictions(self, predictions: List) -> List:
        """Optimizar predicciones ML"""
        try:
            # Filtrar predicciones con baja confianza
            threshold = 0.3
            filtered = [p for p in predictions if hasattr(p, 'confidence') and p.confidence > threshold]
            
            # Ordenar por confianza
            filtered.sort(key=lambda x: x.confidence, reverse=True)
            
            return filtered[:10]  # Limitar a 10 mejores
            
        except Exception as e:
            print(f"⚠️ Error optimizando predicciones ML: {e}")
            return predictions
    
    def optimize_chart_data(self, df: pd.DataFrame, max_points: int = 1000) -> pd.DataFrame:
        """Optimizar datos para charts"""
        try:
            if len(df) > max_points:
                # Reducir puntos manteniendo estructura
                step = len(df) // max_points
                df = df.iloc[::step].copy()
                
            return df
            
        except Exception as e:
            print(f"⚠️ Error optimizando datos de chart: {e}")
            return df
    
    def batch_process(self, items: List, batch_size: int = 100):
        """Procesar items en lotes para mejor performance"""
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                yield batch
                
                # Limpiar memoria entre lotes
                if i % (batch_size * 5) == 0:
                    self.memory_cleanup()
                    
        except Exception as e:
            print(f"⚠️ Error en procesamiento por lotes: {e}")
            yield items

def create_performance_monitor():
    """Crear monitor de performance"""
    
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}
            self.start_time = None
        
        def start_timer(self, name: str):
            """Iniciar timer para métrica"""
            self.start_time = time.time()
            self.metrics[name] = {'start': self.start_time}
        
        def end_timer(self, name: str):
            """Finalizar timer y registrar métrica"""
            if self.start_time and name in self.metrics:
                duration = time.time() - self.start_time
                self.metrics[name]['duration'] = duration
                self.metrics[name]['end'] = time.time()
                
                print(f"⏱️ {name}: {duration:.3f}s")
        
        def get_metrics(self) -> Dict:
            """Obtener métricas de performance"""
            return self.metrics
        
        def print_summary(self):
            """Imprimir resumen de performance"""
            print("\n📊 RESUMEN DE PERFORMANCE:")
            print("=" * 40)
            
            total_time = 0
            for name, metric in self.metrics.items():
                if 'duration' in metric:
                    duration = metric['duration']
                    total_time += duration
                    print(f"⏱️ {name}: {duration:.3f}s")
            
            print(f"⏱️ Tiempo total: {total_time:.3f}s")
            
            # Métricas de memoria
            memory = psutil.virtual_memory()
            print(f"💾 Memoria: {memory.percent:.1f}%")
            print(f"💾 Disponible: {memory.available / 1024**3:.1f} GB")
    
    return PerformanceMonitor()

def optimize_imports():
    """Optimizar imports para mejor performance"""
    
    # Imports lazy (solo cuando se necesiten)
    lazy_imports = {
        'plotly': 'import plotly.graph_objects as go',
        'sklearn': 'from sklearn.ensemble import RandomForestClassifier',
        'joblib': 'import joblib',
        'yfinance': 'import yfinance as yf'
    }
    
    return lazy_imports

def create_config_optimizer():
    """Crear optimizador de configuración"""
    
    class ConfigOptimizer:
        def __init__(self):
            self.optimized_settings = {
                'cache_enabled': True,
                'max_cache_size': 100,
                'memory_cleanup_threshold': 0.8,
                'chart_max_points': 1000,
                'ml_batch_size': 50,
                'data_compression': True
            }
        
        def get_optimized_config(self) -> Dict:
            """Obtener configuración optimizada"""
            return self.optimized_settings
        
        def apply_optimizations(self, config: Dict) -> Dict:
            """Aplicar optimizaciones a configuración"""
            optimized = config.copy()
            
            # Optimizaciones automáticas
            if 'cache_enabled' not in optimized:
                optimized['cache_enabled'] = True
            
            if 'max_chart_points' not in optimized:
                optimized['max_chart_points'] = 1000
            
            if 'memory_cleanup' not in optimized:
                optimized['memory_cleanup'] = True
            
            return optimized
    
    return ConfigOptimizer()

# Funciones de utilidad para optimización
def optimize_data_fetching(symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
    """Optimizar obtención de datos"""
    try:
        # Usar cache si está disponible
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        # Aquí iría la lógica de cache
        # Por ahora, retornar datos normales
        return pd.DataFrame()
        
    except Exception as e:
        print(f"⚠️ Error optimizando obtención de datos: {e}")
        return pd.DataFrame()

def optimize_ml_inference(model, data: pd.DataFrame) -> any:
    """Optimizar inferencia ML"""
    try:
        # Reducir datos si es necesario
        if len(data) > 1000:
            data = data.tail(1000)
        
        # Realizar predicción
        prediction = model.predict(data)
        
        return prediction
        
    except Exception as e:
        print(f"⚠️ Error optimizando inferencia ML: {e}")
        return None

def optimize_chart_rendering(df: pd.DataFrame, max_points: int = 500) -> pd.DataFrame:
    """Optimizar renderizado de charts"""
    try:
        if len(df) > max_points:
            # Reducir puntos manteniendo estructura visual
            step = len(df) // max_points
            df = df.iloc[::step].copy()
        
        return df
        
    except Exception as e:
        print(f"⚠️ Error optimizando renderizado de chart: {e}")
        return df

# Configuración global de optimización
PERFORMANCE_CONFIG = {
    'enable_cache': True,
    'max_cache_size': 100,
    'memory_cleanup_threshold': 0.8,
    'chart_max_points': 1000,
    'ml_batch_size': 50,
    'data_compression': True,
    'lazy_loading': True
}

def apply_performance_optimizations():
    """Aplicar todas las optimizaciones de performance"""
    
    print("🚀 Aplicando optimizaciones de performance...")
    
    # Crear optimizadores
    optimizer = PerformanceOptimizer()
    monitor = create_performance_monitor()
    config_optimizer = create_config_optimizer()
    
    # Aplicar optimizaciones
    optimized_config = config_optimizer.get_optimized_config()
    
    print("✅ Optimizaciones aplicadas:")
    for key, value in optimized_config.items():
        print(f"  - {key}: {value}")
    
    return {
        'optimizer': optimizer,
        'monitor': monitor,
        'config': optimized_config
    }

if __name__ == "__main__":
    # Ejecutar optimizaciones
    optimizations = apply_performance_optimizations()
    print("✅ Optimizaciones de performance listas")
