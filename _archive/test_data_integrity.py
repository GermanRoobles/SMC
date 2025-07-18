"""
Test de integridad de datos OHLCV en tiempo real para SMC TradingView
Valida que no haya gaps temporales, columnas vacías ni inconsistencias en los datos.
"""
import pandas as pd
from fetch_data import get_ohlcv_with_cache


SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "FARTCOIN/USDT"]
TIMEFRAME = "15m"
DAYS = 3

def test_data_integrity(symbol, timeframe=TIMEFRAME, days=DAYS):
    print(f"\n📊 Verificando integridad de datos para {symbol} ({timeframe}, {days} días)...")
    from datetime import datetime, timedelta
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)
    df = get_ohlcv_with_cache(symbol, timeframe, start_dt, end_dt)

    # 1. Verificar que el DataFrame no está vacío
    assert not df.empty, f"❌ DataFrame vacío para {symbol}"
    print(f"✅ {len(df)} filas cargadas")

    # 2. Verificar columnas esenciales
    required_cols = ["open", "high", "low", "close", "timestamp"]
    for col in required_cols:
        assert col in df.columns, f"❌ Falta columna: {col} en {symbol}"
    print(f"✅ Todas las columnas presentes: {required_cols}")

    # 3. Verificar que no hay valores nulos
    null_counts = df[required_cols].isnull().sum()
    assert null_counts.sum() == 0, f"❌ Columnas vacías en {symbol}: {null_counts.to_dict()}"
    print("✅ Sin columnas vacías")

    # 4. Verificar consistencia de precios
    assert (df["high"] >= df["low"]).all(), f"❌ high < low detectado en {symbol}"
    assert (df["high"] >= df[["open", "close"]].max(axis=1)).all(), f"❌ high < open/close detectado en {symbol}"
    assert (df["low"] <= df[["open", "close"]].min(axis=1)).all(), f"❌ low > open/close detectado en {symbol}"
    print("✅ Consistencia de precios OK")

    # 5. Verificar continuidad temporal
    df_sorted = df.sort_values("timestamp")
    time_diffs = df_sorted["timestamp"].diff().dt.total_seconds().dropna()
    expected_interval = 15 * 60  # 15 minutos en segundos
    gaps = time_diffs[(time_diffs > expected_interval * 1.5) | (time_diffs < expected_interval * 0.5)]
    assert gaps.empty, f"❌ Gaps temporales detectados en {symbol}: {gaps}"
    print("✅ Sin gaps temporales")

    print(f"\n🎉 Test de integridad de datos PASADO para {symbol}")

if __name__ == "__main__":
    for symbol in SYMBOLS:
        try:
            test_data_integrity(symbol)
        except AssertionError as e:
            print(str(e))
