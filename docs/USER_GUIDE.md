# 📖 Guía de Usuario - SMC TradingView

## 🎯 Introducción

SMC TradingView es un sistema avanzado de trading basado en Smart Money Concepts que combina análisis técnico tradicional con machine learning para proporcionar señales de trading precisas y confiables.

## 🚀 Primeros Pasos

### 1. Acceso a la Aplicación
- Abrir la aplicación en tu navegador
- La interfaz principal se carga automáticamente
- Seleccionar par de trading y timeframe

### 2. Configuración Inicial
- **Par de Trading**: BTC/USDT (por defecto)
- **Timeframe**: 15m (recomendado para análisis)
- **Período**: Últimos 30 días

## 📊 Análisis SMC

### Fair Value Gaps (FVG)
- **¿Qué son?**: Zonas donde el precio "salta" sin transacciones
- **Color**: Verde (bullish) / Rojo (bearish)
- **Uso**: Niveles de soporte/resistencia dinámicos

### Order Blocks (OB)
- **¿Qué son?**: Zonas donde se acumulan órdenes significativas
- **Identificación**: Velas con volumen alto y movimiento direccional
- **Uso**: Entradas y salidas de posiciones

### Liquidity Zones
- **¿Qué son?**: Zonas donde hay liquidez disponible
- **Tipos**: Highs (resistencias) / Lows (soportes)
- **Uso**: Identificar niveles de stop loss

### BOS/CHOCH
- **BOS**: Break of Structure - Ruptura de estructura
- **CHOCH**: Change of Character - Cambio de carácter
- **Uso**: Confirmar cambios de tendencia

## 🤖 Machine Learning

### ML Predictor
- **Función**: Predice probabilidad de éxito de señales
- **Umbral**: 40% mínimo (configurable)
- **Confianza**: 50% mínimo (configurable)

### ML Signal Generator
- **Función**: Genera señales completas con TP/SL
- **Entrada**: Precio de entrada calculado
- **TP**: Take Profit con ratio 2:1
- **SL**: Stop Loss optimizado

### ML Avanzado
- **Volatilidad**: Predice volatilidad futura
- **Anomalías**: Detecta movimientos anómalos
- **Patrones**: Clasifica patrones de mercado
- **Tendencia**: Predice dirección de tendencia
- **Sentimiento**: Analiza sentimiento del mercado

## 📈 Backtesting

### Configuración
- **Capital Inicial**: $10,000 (por defecto)
- **Risk per Trade**: 1% (configurable)
- **Min R:R**: 2:1 (configurable)

### Métricas
- **Win Rate**: Porcentaje de trades ganadores
- **Profit Factor**: Ratio ganancias/pérdidas
- **Sharpe Ratio**: Retorno ajustado por riesgo
- **Max Drawdown**: Máxima pérdida consecutiva

### Interpretación
- **Win Rate > 50%**: Bueno
- **Profit Factor > 1.5**: Excelente
- **Sharpe Ratio > 1**: Óptimo
- **Max Drawdown < 20%**: Aceptable

## ⚙️ Configuración Avanzada

### Opciones SMC
- **SFP**: Swing Failure Patterns (deshabilitado por defecto)
- **HTF Zones**: Zonas de timeframes superiores (habilitado)
- **Require CHoCH**: Solo SFPs con CHoCH (habilitado)

### Configuración ML
- **Min Probability**: 0.4 (40%)
- **Min Confidence**: 0.5 (50%)
- **Model Update**: Automático

### Alertas
- **Telegram**: Notificaciones en tiempo real
- **Liquidity Sweeps**: Alertas de barridos
- **Zone Creation**: Alertas de nuevas zonas
- **SFP Detection**: Alertas de patrones

## 🎨 Visualización

### Charts
- **Candlestick**: Velas japonesas
- **Volume**: Volumen en barras
- **Indicators**: SMC zones superpuestas
- **Signals**: Señales de entrada/salida

### Colores
- **Verde**: Bullish (alcista)
- **Rojo**: Bearish (bajista)
- **Azul**: Neutral
- **Amarillo**: Advertencia

### Timeframes
- **15m**: Análisis detallado
- **1h**: Análisis intermedio
- **4h**: Análisis de tendencia
- **1d**: Análisis diario
- **1w**: Análisis semanal

## 🔧 Troubleshooting

### Problemas Comunes

#### Datos no se cargan
- Verificar conexión a internet
- Cambiar par de trading
- Refrescar página

#### ML no funciona
- Verificar que ML esté habilitado
- Ajustar umbrales
- Revisar logs de error

#### Backtesting lento
- Reducir período de análisis
- Deshabilitar opciones innecesarias
- Usar timeframes más altos

### Logs y Debug
- **Console**: Ver logs en consola del navegador
- **Sidebar**: Información de debug en sidebar
- **Error Messages**: Mensajes específicos de error

## 📱 Mobile Usage

### Optimización
- **Responsive**: Interfaz adaptada a móviles
- **Touch**: Controles táctiles optimizados
- **Performance**: Carga rápida en dispositivos móviles

### Limitaciones
- **Screen Size**: Charts pueden ser pequeños
- **Interactions**: Algunas funciones limitadas
- **Performance**: Puede ser más lento

## 🔒 Seguridad

### Datos
- **No Storage**: No se almacenan datos personales
- **Cache Local**: Solo cache temporal
- **Privacy**: Sin tracking de usuario

### Trading
- **Paper Trading**: Solo simulación
- **No Real Money**: No conexión a brokers reales
- **Educational**: Propósito educativo

## 📞 Soporte

### Recursos
- **Documentación**: README.md
- **API Docs**: docs/API.md
- **Tests**: comprehensive_system_test.py

### Contacto
- **Issues**: GitHub Issues
- **Community**: Discord/Slack (si existe)
- **Email**: Contacto del desarrollador

## 🎯 Mejores Prácticas

### Análisis
1. **Multi-timeframe**: Usar múltiples timeframes
2. **Confirmación**: Esperar confirmaciones
3. **Risk Management**: Siempre usar stop loss
4. **Patience**: No forzar entradas

### ML
1. **Umbrales**: Ajustar según mercado
2. **Validación**: Confirmar con análisis técnico
3. **Actualización**: Mantener modelos actualizados
4. **Diversificación**: No depender solo de ML

### Backtesting
1. **Períodos**: Probar en diferentes mercados
2. **Parámetros**: Optimizar configuración
3. **Validación**: Usar walk-forward analysis
4. **Realismo**: Considerar slippage y comisiones

---

**¡Disfruta usando SMC TradingView! 🚀**
