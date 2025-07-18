# 🚀 SMC TradingView Bot - Sistema de Trading Smart Money Concepts

## 📋 Proyecto Completo

Sistema avanzado para análisis, backtesting y visualización de estrategias SMC (Smart Money Concepts) con estilo TradingView. Incluye generación de señales, gestión de riesgo, métricas históricas y robustez ante condiciones extremas de mercado.

## 🏗️ Arquitectura y Componentes

```
smc_tradingview/
├── app_streamlit.py        # Interfaz principal Streamlit
├── fetch_data.py           # Obtención y cacheo de datos OHLCV (Binance/Yahoo)
├── smc_analysis.py         # Lógica de análisis SMC (liquidez, FVG, OB, BOS/CHOCH, swings)
├── smc_trade_engine.py     # Motor de señales (TJR), gestión de entradas/salidas, scoring
├── smc_backtester.py       # Backtesting, simulación de trades, métricas de performance
├── smc_integration.py      # Integración bot/UI, métricas y visualización
├── smc_visualization_advanced.py # Visualización avanzada estilo TradingView
├── requirements.txt        # Dependencias
├── data_cache/             # Cache local de datos OHLCV
```

## 🚦 Flujo de Trabajo

1. **Obtención de datos**: `fetch_data.py` (cache local, UTC)
2. **Análisis SMC**: `smc_analysis.py` (detección adaptativa)
3. **Generación de señales**: `smc_trade_engine.py` (TJR, SL/TP, scoring)
4. **Backtesting**: `smc_backtester.py` (simulación, métricas)
5. **Visualización**: `app_streamlit.py` + `smc_visualization_advanced.py` (dashboard, controles, métricas)
6. **Integración y métricas**: `smc_integration.py` (sidebar, consolidación)

## 🛠️ Instalación y Ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación visual
streamlit run app_streamlit.py

# Probar bot independiente
python ejemplo_uso_bot.py
```

## ⚙️ Configuración y Personalización

- Parámetros configurables en sidebar (pares, timeframes, días, refresh, SMC Bot, señales, métricas, trading engine, backtesting, análisis histórico)
- Visualización avanzada, gestión de riesgo, market sentiment, performance tracker
- Soporte multi-activo y multi-timeframe

## 📊 Métricas y Resultados

- Detección automática de todos los indicadores SMC
- Simulación realista de trades con SL/TP
- Métricas: Win Rate, Profit Factor, Expectancy, Drawdown, retornos, duración, MAE/MFE
- Visualización profesional con emojis, colores, overlays y reportes descargables

## 🔔 Integraciones y Alertas

- Telegram: alertas automáticas en eventos clave (inicio, señales)
- Cache local para reproducibilidad y performance

## 🧩 Extensión y Desarrollo

- Modularidad: cada indicador y visualización en su propio módulo
- Añadir nuevos indicadores: editar `smc_analysis.py`, actualizar integración y visualización
- Añadir nuevos exchanges/símbolos: modificar `fetch_data.py`, actualizar UI
- Testing: scripts dedicados y validación visual

## 🧪 Requisitos

- Python 3.9+
- `streamlit`, `pandas`, `numpy`, `plotly`, `smartmoneyconcepts`, `ccxt`, `scipy`, `kaleido`, `yfinance`

## 📚 Documentación y Referencias

- `README_SMC_STRATEGY.md`, `README_FINAL.md`, `README_VISUALIZATION.md`, `INFORME_COMPLETO_PROYECTO.md`
- Ejemplo de uso: `ejemplo_uso_bot.py`
- Configuración avanzada: `smc_config.py`

## 🚀 Casos de Uso

- Trading algorítmico, análisis manual, backtesting, visualización profesional, gestión de riesgo

---

**Desarrollado por GermanRoobles y equipo - 2025**
