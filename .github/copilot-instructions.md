# Copilot Instructions for SMC TradingView

## Project Overview

Advanced SMC (Smart Money Concepts) trading system for multi-asset, multi-timeframe analysis, backtesting, and visualization. Implements adaptive signal generation, risk management, and professional TradingView-style dashboards.

## Architecture & Key Components

- `app_streamlit.py`: Main Streamlit UI, orchestrates analysis, visualization, bot integration, and Telegram alerts.
- `fetch_data.py`: OHLCV loader with local cache, supports Binance/Yahoo, UTC normalization, incremental updates.
- `smc_analysis.py`: Core SMC logic (liquidity, order blocks, FVG, BOS/CHOCH, swings) with adaptive thresholds.
- `smc_trade_engine.py`: Signal engine (TJR strategy), entry/exit/SL/TP logic, confidence scoring.
- `smc_backtester.py`: Backtesting engine, trade/result structures, performance metrics, reporting.
- `smc_integration.py`: Connects bot logic to UI, consolidates metrics, sidebar controls.
- `smc_visualization_advanced.py`: Advanced TradingView-style chart overlays and metrics.

## Developer Workflows

- **Install:** `pip install -r requirements.txt`
- **Run UI:** `streamlit run app_streamlit.py`
- **Backtesting:** Use `smc_backtester.py` directly or via Streamlit UI (sidebar controls)
- **Standalone bot:** `python ejemplo_uso_bot.py`
- **Debugging:** Use print/logging, Telegram alerts, and sidebar toggles for metrics/visualization
- **Cloud deploy:** `streamlit run app_streamlit.py --server.port $PORT`

## Project-Specific Patterns

- **Session state:** Use `st.session_state` for caching, lifecycle flags, incremental updates
- **Data cache:** OHLCV data cached in `data_cache/` for reproducibility and speed
- **Adaptive detection:** Liquidity/FVG thresholds adapt to volatility/timeframe (`smc_analysis.py`)
- **Sidebar controls:** All major features toggled/configured via sidebar (see UI code)
- **Telegram integration:** Alerts sent on app start and key events
- **Modular indicators:** New indicators follow modular pattern in `smc_analysis.py` and visualization modules

## Coding Conventions & Tips

- Use UTC for all datetime operations (see `fetch_data.py`)
- Always use provided data loaders and analysis functions for consistency
- For new UI features, extend `app_streamlit.py` and add sidebar controls
- For debugging, use print/logging and Telegram alerts
- For new signals: define in `smc_analysis.py`, add structure in `smc_trade_engine.py`, integrate in UI/metrics

## Example: Adding a New Indicator or Signal

1. Add detection logic in `smc_analysis.py`
2. Update signal structure in `smc_trade_engine.py`
3. Integrate visualization in `app_streamlit.py` and/or `smc_visualization_advanced.py`
4. Add sidebar controls for configuration
5. Test with dedicated script or Streamlit UI

## Testing & Validation

- Para validar nuevas funcionalidades, usa scripts dedicados (`test_*.py`) y verifica visualmente en la UI.
- Revisa métricas y overlays en el dashboard para asegurar consistencia.
- Usa logs y alertas Telegram para debugging en producción.

## Extension Best Practices

- Mantén la modularidad: cada nuevo indicador, métrica o visualización debe estar en su propio módulo.
- Documenta cada función nueva con docstrings claros y ejemplos de uso.
- Para integración externa (API, brokers), sigue el patrón de `fetch_data.py` y `smc_integration.py`.

## References & Documentation

- Main: `README.md`, `README_FINAL.md`, `README_SMC_STRATEGY.md`, `README_VISUALIZATION.md`, `INFORME_COMPLETO_PROYECTO.md`
- Key files: `app_streamlit.py`, `smc_analysis.py`, `smc_trade_engine.py`, `smc_backtester.py`, `fetch_data.py`, `smc_integration.py`, `smc_visualization_advanced.py`

---

For questions or unclear patterns, review the above files or ask for clarification.
