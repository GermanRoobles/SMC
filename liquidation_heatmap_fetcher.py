#!/usr/bin/env python3
"""
Script: liquidation_heatmap_fetcher.py
=====================================
Obtiene niveles públicos de liquidaciones (liquidity heatmap) para BTCUSDT usando la API de Hyblock Capital.
"""
import requests
import pandas as pd
import time




# Binance Open Interest endpoint (histórico)
# Documentación: https://binance-docs.github.io/apidocs/futures/en/#open-interest-statistics
import datetime

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 500
API_URL = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={SYMBOL}&period={INTERVAL}&limit={LIMIT}"

print(f"Descargando Open Interest histórico de Binance para {SYMBOL} ({INTERVAL})...")
resp = requests.get(API_URL)
if resp.status_code != 200:
    print(f"❌ Error al consultar la API: {resp.status_code}")
    print(resp.text)
    exit(1)
data = resp.json()

if not isinstance(data, list) or len(data) == 0:
    print("❌ No se encontraron datos de Open Interest.")
    exit(1)

oi_df = pd.DataFrame(data)
oi_df['timestamp'] = pd.to_datetime(oi_df['timestamp'], unit='ms')
oi_df = oi_df[['timestamp', 'sumOpenInterest', 'sumOpenInterestValue']]
oi_df = oi_df.sort_values('timestamp').reset_index(drop=True)

print(f"Datos de Open Interest obtenidos: {len(oi_df)}")
print(oi_df.head(10))

# Guardar a CSV para integración visual posterior
oi_df.to_csv("open_interest_btcusdt.csv", index=False)
print("✅ Datos de Open Interest guardados en open_interest_btcusdt.csv")
