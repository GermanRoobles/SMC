#!/usr/bin/env python3
"""
Test de Detección de Zonas de Liquidez en 5 Meses de BTCUSDT (Binance)
=====================================================================
Descarga datos históricos de 5 meses (1h) y verifica la presencia de zonas de liquidez.
"""
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from smc_analysis import analyze

# Configuración
symbol = 'BTC/USDT'
timeframe = '1h'
months = 5
exchange = ccxt.binance()

# Calcular fechas
now = datetime.utcnow()
since = int((now - timedelta(days=30*months)).timestamp() * 1000)

# Descargar datos OHLCV
print(f"Descargando datos de {symbol} ({timeframe}) para los últimos {months} meses...")
data = []
limit = 1000
fetch_since = since
while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=fetch_since, limit=limit)
    if not ohlcv:
        break
    data.extend(ohlcv)
    if len(ohlcv) < limit:
        break
    fetch_since = ohlcv[-1][0] + 1

df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
print(f"Datos descargados: {len(df)} velas desde {df['timestamp'].iloc[0]} hasta {df['timestamp'].iloc[-1]}")

# Ejecutar análisis SMC
detalles = analyze(df, timeframe=timeframe)
liquidity = detalles['liquidity']

# Contar zonas válidas de liquidez
def count_valid_liquidity(liquidity_df):
    if liquidity_df is None or len(liquidity_df) == 0:
        return 0
    if 'Level' in liquidity_df.columns:
        return liquidity_df['Level'].notna().sum()
    return 0

num_zonas = count_valid_liquidity(liquidity)
print(f"Zonas de liquidez detectadas: {num_zonas}")
if num_zonas > 0:
    print("✅ Se detectaron zonas de liquidez en el periodo analizado.")
else:
    print("❌ No se detectaron zonas de liquidez. Revisa la lógica o los parámetros.")
