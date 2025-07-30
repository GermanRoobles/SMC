import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
from datetime import datetime, timedelta
import numpy as np

# 1. Configuración inicial
end_date = datetime.now()
start_date = end_date - timedelta(days=8*365)  # 8 años atrás

# 2. Obtener datos históricos de BTC - CORREGIDO
btc_data = yf.download('BTC-USD', start=start_date, end=end_date, progress=False)
btc_data = btc_data[['Close']].reset_index()
btc_data.columns = ['Date', 'Close']  # Asegurar nombres de columnas simples

# 3. Obtener datos históricos del Fear & Greed Index (FGI) - CORREGIDO
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=0"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        df = pd.DataFrame(data['data'])

        # Convertir timestamp a entero antes de la conversión
        df['timestamp'] = pd.to_numeric(df['timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s').dt.normalize()

        df['value'] = pd.to_numeric(df['value'])
        return df[['timestamp', 'value']]

    except Exception as e:
        print(f"Error obteniendo datos FGI: {e}")
        return pd.DataFrame(columns=['timestamp', 'value'])

fgi_data = get_fear_greed_index()
fgi_data.columns = ['timestamp', 'value']  # Asegurar nombres de columnas simples

# 4. Combinar datos - CORREGIDO
# Convertir fechas y asegurar formato consistente
btc_data['Date'] = pd.to_datetime(btc_data['Date']).dt.normalize()
if not fgi_data.empty:
    fgi_data['timestamp'] = pd.to_datetime(fgi_data['timestamp']).dt.normalize()

# Hacer merge solo si hay datos FGI
if not fgi_data.empty:
    merged_data = pd.merge(
        btc_data,
        fgi_data,
        left_on='Date',
        right_on='timestamp',
        how='left'
    )
    # Rellenar valores faltantes
    merged_data['value'] = merged_data['value'].ffill()
else:
    merged_data = btc_data.copy()
    merged_data['value'] = np.nan

# Eliminar columna temporal
if 'timestamp' in merged_data.columns:
    merged_data.drop(columns=['timestamp'], inplace=True)

# 5. Identificar extremos
merged_data['Extremo'] = 0
if 'value' in merged_data.columns:
    merged_data.loc[merged_data['value'] <= 20, 'Extremo'] = -1
    merged_data.loc[merged_data['value'] >= 80, 'Extremo'] = 1

# 6. Crear visualización
plt.figure(figsize=(16, 12))

# Gráfico de precio BTC
plt.subplot(2, 1, 1)
plt.plot(merged_data['Date'], merged_data['Close'], 'b-', linewidth=1.5, label='Precio BTC')
plt.title('Precio de Bitcoin (8 años) con Extremos de Miedo/Codicia', fontsize=14)
plt.ylabel('Precio (USD)', fontsize=12)
plt.grid(True, alpha=0.3)

# Marcadores para extremos si existen
if 'Extremo' in merged_data.columns:
    miedo_dates = merged_data[merged_data['Extremo'] == -1]['Date']
    codicia_dates = merged_data[merged_data['Extremo'] == 1]['Date']

    plt.scatter(
        miedo_dates,
        merged_data.loc[merged_data['Extremo'] == -1, 'Close'],
        color='red',
        s=50,
        label='Miedo extremo (FGI <= 20)',
        marker='^',
        alpha=0.7
    )

    plt.scatter(
        codicia_dates,
        merged_data.loc[merged_data['Extremo'] == 1, 'Close'],
        color='green',
        s=50,
        label='Codicia extrema (FGI >= 80)',
        marker='v',
        alpha=0.7
    )

plt.legend(loc='upper left')
plt.yscale('log')  # Escala logarítmica

# Gráfico del Fear & Greed Index si existe
plt.subplot(2, 1, 2)
if 'value' in merged_data.columns:
    plt.plot(merged_data['Date'], merged_data['value'], 'k-', linewidth=1.5)
    plt.fill_between(
        merged_data['Date'],
        merged_data['value'],
        0,
        where=(merged_data['value'] >= 80) if 'value' in merged_data.columns else False,
        color='green',
        alpha=0.2
    )
    plt.fill_between(
        merged_data['Date'],
        merged_data['value'],
        0,
        where=(merged_data['value'] <= 20) if 'value' in merged_data.columns else False,
        color='red',
        alpha=0.2
    )
    plt.axhline(y=80, color='green', linestyle='--', alpha=0.7)
    plt.axhline(y=20, color='red', linestyle='--', alpha=0.7)
    plt.ylim(0, 100)

plt.title('Fear & Greed Index Histórico', fontsize=14)
plt.ylabel('Valor FGI', fontsize=12)
plt.xlabel('Fecha', fontsize=12)
plt.grid(True, alpha=0.3)

# Formatear ejes de fecha
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.gca().xaxis.set_major_locator(mdates.YearLocator())
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.savefig('btc_fear_greed_chart.png', dpi=300)
plt.show()

print("Gráfico generado exitosamente: btc_fear_greed_chart.png")
