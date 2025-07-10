#!/usr/bin/env python3
"""
Script de prueba para validar los datos extendidos
"""

from fetch_data import get_ohlcv_extended, get_ohlcv
import pandas as pd
from datetime import datetime

def test_extended_data():
    """Probar la función de datos extendidos"""
    print("🧪 Probando datos extendidos...")

    # Comparar datos normales vs extendidos
    symbol = "BTC/USDT"
    timeframe = "15m"

    print(f"\n📊 Obteniendo datos normales para {symbol} en {timeframe}...")
    df_normal = get_ohlcv(symbol, timeframe)
    print(f"   ✅ Datos normales: {len(df_normal)} puntos")
    if len(df_normal) > 0:
        print(f"   📅 Desde: {df_normal['timestamp'].min()}")
        print(f"   📅 Hasta: {df_normal['timestamp'].max()}")

    print(f"\n📊 Obteniendo datos extendidos (5 días) para {symbol} en {timeframe}...")
    df_extended = get_ohlcv_extended(symbol, timeframe, days=5)
    print(f"   ✅ Datos extendidos: {len(df_extended)} puntos")
    if len(df_extended) > 0:
        print(f"   📅 Desde: {df_extended['timestamp'].min()}")
        print(f"   📅 Hasta: {df_extended['timestamp'].max()}")

    # Calcular diferencia
    if len(df_normal) > 0 and len(df_extended) > 0:
        ratio = len(df_extended) / len(df_normal)
        print(f"\n📈 Ratio de datos extendidos: {ratio:.2f}x más datos")

        # Verificar que tenemos más datos
        if len(df_extended) > len(df_normal):
            print("✅ Los datos extendidos contienen más información")
        else:
            print("⚠️ Los datos extendidos no contienen más información")

    return df_extended

if __name__ == "__main__":
    test_extended_data()
