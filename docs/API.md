# 📚 API Documentation

## Core Modules

### fetch_data.py
```python
get_ohlcv(symbol, timeframe, limit=100)
get_ohlcv_extended(symbol, timeframe, days=30)
get_ohlcv_with_cache(symbol, timeframe, limit=100)
```

### smc_analysis.py
```python
analyze(df, timeframe='15m')
get_current_session()
get_session_color(session)
```

### smc_ml_predictor.py
```python
SMCMLPredictor()
predict_signal_probability(df, smc_analysis)
```

### smc_backtester.py
```python
run_backtest_analysis(df, signals, initial_capital=10000)
```

## Configuration

### ML Settings
- `min_probability`: 0.4 (40%)
- `min_confidence`: 0.5 (50%)
- `model_dir`: "models/"

### SMC Settings
- `base_threshold`: 0.001
- `vol_factor`: 0.006
- `timeframes`: ["15m", "1h", "4h", "1d", "1w"]

### Backtesting Settings
- `initial_capital`: 10000
- `risk_per_trade`: 0.01 (1%)
- `min_rr_ratio`: 2.0
