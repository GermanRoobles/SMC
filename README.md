# SMC TradingView - Sistema de Trading Smart Money Concepts

Este proyecto implementa un sistema de análisis y backtesting de estrategias SMC (Smart Money Concepts) con visualización tipo TradingView, generación de señales, gestión de riesgo y robustez ante condiciones extremas de mercado.

## Características principales

- Detección de liquidez, order blocks, FVG, BOS/CHOCH y swings
- Generación de señales adaptativas según volatilidad y gaps
- Backtesting preciso y validación automática de SL/TP
- Visualización avanzada con Streamlit
- Soporte para múltiples activos y timeframes
- Robusto ante datos extremos y gaps de mercado

## Requisitos

- Python 3.9+
- Recomendado: ejecutar en entorno virtual (`python -m venv .venv`)

## Instalación

1. Clona este repositorio o sube tu carpeta a GitHub.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución local

```bash
streamlit run app_streamlit.py
```

## Despliegue en la nube

- **Streamlit Cloud**: Sube tu repo a GitHub y conéctalo en https://streamlit.io/cloud
- **Render/Railway**: Sube tu repo y usa el comando de inicio:
  ```
  streamlit run app_streamlit.py --server.port $PORT
  ```

## Archivos principales

- `app_streamlit.py`: Interfaz principal
- `smc_analysis.py`: Lógica de análisis SMC
- `smc_trade_engine.py`: Motor de señales
- `smc_backtester.py`: Backtesting y métricas
- `requirements.txt`: Dependencias

## Notas

- El sistema es robusto, pero la detección de liquidez puede ser limitada en mercados muy laterales o timeframes bajos.
- Para soporte o mejoras, revisa la lógica de los indicadores en el paquete SMC.

---

**Desarrollado por [Tu Nombre/Equipo] - 2025**
