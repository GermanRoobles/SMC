#!/usr/bin/env python3
"""
Comparación: Método TJR vs ATR para cálculo SL/TP
===============================================

Script para comparar y validar los dos métodos de cálculo
de Stop Loss y Take Profit.
"""

import pandas as pd
import numpy as np
from smc_bot import SMCBot, SMCConfig
from smc_advanced import calculate_sl_tp_advanced, calculate_atr

def generar_datos_ejemplo():
    """Generar datos de ejemplo para prueba"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='15T')

    price = 100000.0
    data = []

    for i in range(100):
        change = np.random.normal(0, 0.002)
        open_price = price
        close_price = price * (1 + change)
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))

        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': np.random.randint(1000, 5000)
        })

        price = close_price

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def comparar_metodos():
    """Comparar método TJR vs ATR"""

    print("🔬 COMPARACIÓN: Método TJR vs ATR")
    print("=" * 50)

    # Generar datos
    df = generar_datos_ejemplo()

    # Configurar bot para análisis
    config = SMCConfig(use_tjr_method=True)
    bot = SMCBot(config)
    analysis = bot.analyze_market(df)

    # Datos de ejemplo para prueba
    entry_price = 101500.0
    signal_type = 'buy'
    atr_value = 150.0
    min_rr = 2.0

    # Simular Order Block
    order_block = {
        'type': 'bullish_ob',
        'top': 101480.0,
        'bottom': 101420.0,
        'timestamp': df.index[-10]
    }

    # Simular sweep
    sweep_info = {
        'type': 'bullish_sweep',
        'sweep_low': 101350.0,
        'timestamp': df.index[-15]
    }

    print(f"📊 DATOS DE PRUEBA:")
    print(f"   💰 Entry Price: ${entry_price:,.2f}")
    print(f"   📈 Signal Type: {signal_type.upper()}")
    print(f"   📊 ATR: ${atr_value:.2f}")
    print(f"   🎯 Min R:R: {min_rr}:1")
    print(f"   📦 Order Block: ${order_block['bottom']:.2f} - ${order_block['top']:.2f}")
    print(f"   🌊 Sweep Low: ${sweep_info['sweep_low']:.2f}")

    print(f"\n" + "="*50)

    # ==================== MÉTODO ATR ====================
    print("🔧 MÉTODO ATR (Tradicional):")

    sl_atr, tp_atr, rr_atr = calculate_sl_tp_advanced(
        entry_price, signal_type, atr_value, min_rr,
        use_tjr_method=False
    )

    risk_atr = entry_price - sl_atr
    reward_atr = tp_atr - entry_price

    print(f"   🛑 Stop Loss: ${sl_atr:,.2f}")
    print(f"   🎯 Take Profit: ${tp_atr:,.2f}")
    print(f"   📉 Riesgo: ${risk_atr:.2f}")
    print(f"   📈 Recompensa: ${reward_atr:.2f}")
    print(f"   📊 R:R: {rr_atr:.2f}:1")
    print(f"   📏 SL Distance: {((entry_price - sl_atr) / entry_price * 100):.2f}%")
    print(f"   📏 TP Distance: {((tp_atr - entry_price) / entry_price * 100):.2f}%")

    # ==================== MÉTODO TJR ====================
    print(f"\n🎯 MÉTODO TJR (SMC Simplified by TJR):")

    try:
        sl_tjr, tp_tjr, rr_tjr = calculate_sl_tp_advanced(
            entry_price, signal_type, atr_value, min_rr,
            order_block=order_block,
            sweep_info=sweep_info,
            swings=bot.swings,
            use_tjr_method=True
        )

        risk_tjr = entry_price - sl_tjr
        reward_tjr = tp_tjr - entry_price

        print(f"   🛑 Stop Loss: ${sl_tjr:,.2f} (Debajo del Order Block)")
        print(f"   🎯 Take Profit: ${tp_tjr:,.2f} (Próximo swing high)")
        print(f"   📉 Riesgo: ${risk_tjr:.2f}")
        print(f"   📈 Recompensa: ${reward_tjr:.2f}")
        print(f"   📊 R:R: {rr_tjr:.2f}:1")
        print(f"   📏 SL Distance: {((entry_price - sl_tjr) / entry_price * 100):.2f}%")
        print(f"   📏 TP Distance: {((tp_tjr - entry_price) / entry_price * 100):.2f}%")

        # ==================== COMPARACIÓN ====================
        print(f"\n📈 COMPARACIÓN:")
        print(f"   {'Método':<12} {'SL':<12} {'TP':<12} {'R:R':<8} {'Riesgo%':<10} {'Lógica'}")
        print(f"   {'-'*70}")
        print(f"   {'ATR':<12} ${sl_atr:<11.2f} ${tp_atr:<11.2f} {rr_atr:<7.2f} {((entry_price - sl_atr) / entry_price * 100):<9.2f}% {'Volatilidad'}")
        print(f"   {'TJR':<12} ${sl_tjr:<11.2f} ${tp_tjr:<11.2f} {rr_tjr:<7.2f} {((entry_price - sl_tjr) / entry_price * 100):<9.2f}% {'Estructura'}")

        # Diferencias
        sl_diff = abs(sl_atr - sl_tjr)
        tp_diff = abs(tp_atr - tp_tjr)
        rr_diff = abs(rr_atr - rr_tjr)

        print(f"\n🔍 DIFERENCIAS:")
        print(f"   SL Difference: ${sl_diff:.2f}")
        print(f"   TP Difference: ${tp_diff:.2f}")
        print(f"   R:R Difference: {rr_diff:.2f}")

        # Recomendación
        print(f"\n💡 RECOMENDACIÓN:")
        if rr_tjr >= rr_atr:
            print("   ✅ Método TJR ofrece mejor R:R y se basa en estructura del mercado")
            print("   ✅ Más preciso según la estrategia SMC Simplified by TJR")
        else:
            print("   ⚠️ Método ATR ofrece mejor R:R pero ignora estructura del mercado")
            print("   ⚠️ TJR es más conservador pero más lógico")

    except Exception as e:
        print(f"   ❌ Error en método TJR: {e}")
        print("   ⚠️ Usando método ATR como fallback")

def probar_configuraciones():
    """Probar diferentes configuraciones TJR"""

    print(f"\n🧪 PRUEBA DE CONFIGURACIONES TJR")
    print("=" * 40)

    # Configuraciones a probar
    configs = [
        {'name': 'Conservador', 'use_tjr': True, 'min_rr': 3.0, 'sl_buffer': 0.002},
        {'name': 'Balanceado', 'use_tjr': True, 'min_rr': 2.0, 'sl_buffer': 0.001},
        {'name': 'Agresivo', 'use_tjr': True, 'min_rr': 1.5, 'sl_buffer': 0.0005},
        {'name': 'ATR_Fallback', 'use_tjr': False, 'min_rr': 2.0, 'sl_buffer': 0.001}
    ]

    for config_data in configs:
        print(f"\n🔧 {config_data['name']}:")

        config = SMCConfig(
            use_tjr_method=config_data['use_tjr'],
            min_rr=config_data['min_rr'],
            sl_buffer=config_data['sl_buffer']
        )

        print(f"   Método: {'TJR' if config.use_tjr_method else 'ATR'}")
        print(f"   Min R:R: {config.min_rr}:1")
        print(f"   SL Buffer: {config.sl_buffer*100:.2f}%")

def main():
    """Función principal"""
    print("🚀 Comparación de Métodos SL/TP")
    print("=" * 50)

    comparar_metodos()
    probar_configuraciones()

    print(f"\n✅ CONCLUSIÓN:")
    print("   📊 Método TJR: Basado en estructura del mercado (recomendado)")
    print("   📊 Método ATR: Basado en volatilidad (fallback)")
    print("   🎯 TJR sigue la estrategia SMC Simplified by TJR")
    print("   ⚙️ Configurable en SMCConfig.use_tjr_method")

if __name__ == "__main__":
    main()
