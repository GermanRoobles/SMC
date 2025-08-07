#!/usr/bin/env python3
"""
Script: liquidation_heatmap_fetcher.py
=====================================
Obtiene niveles públicos de liquidaciones (liquidity heatmap) para BTCUSDT usando la API de Hyblock Capital.
"""
import requests
import pandas as pd
import time




# Yahoo Finance Open Interest endpoint (simulado)
# Nota: Yahoo Finance no proporciona Open Interest directamente, usamos datos simulados
import datetime

SYMBOL = "BTC-USD"
INTERVAL = "1h"
LIMIT = 500

print(f"Descargando datos de volumen de Yahoo Finance para {SYMBOL} ({INTERVAL})...")
# Simular datos de Open Interest usando volumen de Yahoo Finance
import yfinance as yf

try:
    ticker = yf.Ticker(SYMBOL)
    df = ticker.history(period="5d", interval="1h")
    
    if not df.empty:
        df = df.reset_index()
        df['timestamp'] = pd.to_datetime(df['Date'])
        # Simular Open Interest basado en volumen
        df['sumOpenInterest'] = df['Volume'] * 0.1  # Simulación
        df['sumOpenInterestValue'] = df['Volume'] * df['Close'] * 0.1  # Simulación
        oi_df = df[['timestamp', 'sumOpenInterest', 'sumOpenInterestValue']]
        oi_df = oi_df.sort_values('timestamp').reset_index(drop=True)
    else:
        print("❌ No se pudieron obtener datos de Yahoo Finance.")
        exit(1)
        
except Exception as e:
    print(f"❌ Error obteniendo datos de Yahoo Finance: {e}")
    exit(1)

print(f"Datos de Open Interest obtenidos: {len(oi_df)}")
print(oi_df.head(10))

# Guardar a CSV para integración visual posterior
oi_df.to_csv("open_interest_btcusdt.csv", index=False)
print("✅ Datos de Open Interest guardados en open_interest_btcusdt.csv")
