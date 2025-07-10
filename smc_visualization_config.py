#!/usr/bin/env python3
"""
Configuración de Visualización SMC Bot
======================================

Este archivo contiene todas las configuraciones visuales para personalizar
la apariencia de las señales del SMC Bot en el gráfico.
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class VisualizationConfig:
    """
    Configuración de visualización para el SMC Bot
    """

    # Colores principales (TradingView style)
    buy_color: str = '#26A69A'          # Verde TradingView
    sell_color: str = '#EF5350'         # Rojo TradingView
    sl_color: str = '#F23645'           # Rojo Stop Loss
    tp_color: str = '#26A69A'           # Verde Take Profit

    # Colores de zonas
    risk_zone_color: str = 'rgba(242, 54, 69, 0.15)'      # Rojo semitransparente
    profit_zone_color: str = 'rgba(38, 166, 154, 0.15)'   # Verde semitransparente

    # Colores de calidad
    high_quality_color: str = '#4CAF50'    # Verde brillante
    medium_quality_color: str = '#FF9800'  # Naranja
    low_quality_color: str = '#F44336'     # Rojo

    # Configuración de marcadores
    marker_size: int = 20
    marker_border_width: int = 3
    marker_border_color: str = 'white'
    marker_opacity: float = 0.9

    # Configuración de líneas
    line_width: int = 3
    line_opacity: float = 0.9
    entry_line_opacity: float = 0.8

    # Configuración de texto
    font_family: str = 'Arial'
    font_size_large: int = 14
    font_size_medium: int = 12
    font_size_small: int = 10
    font_size_tiny: int = 8

    # Configuración de etiquetas
    label_padding: int = 10
    label_border_width: int = 2
    label_opacity: float = 0.95

    # Configuración de zonas
    zone_opacity: float = 0.8
    zone_border_width: int = 1
    zone_border_dash: str = 'dot'

    # Emojis para señales
    buy_emoji: str = '🚀'
    sell_emoji: str = '🎯'
    sl_emoji: str = '🛑'
    tp_emoji: str = '🎯'
    risk_emoji: str = '⚠️'
    profit_emoji: str = '💰'

# Configuración por defecto
DEFAULT_CONFIG = VisualizationConfig()

# Configuraciones predefinidas
TRADINGVIEW_CLASSIC = VisualizationConfig(
    buy_color='#26A69A',
    sell_color='#EF5350',
    sl_color='#F23645',
    tp_color='#26A69A',
    marker_size=18,
    line_width=2,
    font_family='Arial'
)

TRADINGVIEW_DARK = VisualizationConfig(
    buy_color='#00BCD4',
    sell_color='#FF5722',
    sl_color='#E91E63',
    tp_color='#4CAF50',
    risk_zone_color='rgba(233, 30, 99, 0.1)',
    profit_zone_color='rgba(76, 175, 80, 0.1)',
    marker_size=22,
    line_width=3,
    font_family='Arial Black'
)

TRADINGVIEW_LIGHT = VisualizationConfig(
    buy_color='#2E7D32',
    sell_color='#C62828',
    sl_color='#D32F2F',
    tp_color='#388E3C',
    risk_zone_color='rgba(211, 47, 47, 0.2)',
    profit_zone_color='rgba(56, 142, 60, 0.2)',
    marker_size=16,
    line_width=2,
    font_family='Arial'
)

NEON_STYLE = VisualizationConfig(
    buy_color='#00FF94',
    sell_color='#FF0040',
    sl_color='#FF1744',
    tp_color='#00E676',
    risk_zone_color='rgba(255, 23, 68, 0.2)',
    profit_zone_color='rgba(0, 230, 118, 0.2)',
    marker_size=24,
    line_width=4,
    font_family='Arial Black',
    buy_emoji='⬆️',
    sell_emoji='⬇️'
)

MINIMALIST = VisualizationConfig(
    buy_color='#4CAF50',
    sell_color='#F44336',
    sl_color='#9E9E9E',
    tp_color='#9E9E9E',
    risk_zone_color='rgba(158, 158, 158, 0.1)',
    profit_zone_color='rgba(158, 158, 158, 0.1)',
    marker_size=14,
    line_width=1,
    font_family='Arial',
    buy_emoji='↗',
    sell_emoji='↘'
)

# Diccionario de configuraciones
VISUALIZATION_THEMES = {
    'default': DEFAULT_CONFIG,
    'tradingview_classic': TRADINGVIEW_CLASSIC,
    'tradingview_dark': TRADINGVIEW_DARK,
    'tradingview_light': TRADINGVIEW_LIGHT,
    'neon': NEON_STYLE,
    'minimalist': MINIMALIST
}

def get_visualization_config(theme: str = 'default') -> VisualizationConfig:
    """
    Obtener configuración de visualización por tema

    Args:
        theme: Nombre del tema ('default', 'tradingview_classic', etc.)

    Returns:
        Configuración de visualización
    """
    return VISUALIZATION_THEMES.get(theme, DEFAULT_CONFIG)

def get_signal_colors(config: VisualizationConfig, signal_type: str) -> Dict[str, str]:
    """
    Obtener colores para un tipo de señal específico

    Args:
        config: Configuración de visualización
        signal_type: Tipo de señal ('BUY' o 'SELL')

    Returns:
        Diccionario con colores para la señal
    """
    if signal_type.upper() == 'BUY':
        return {
            'signal': config.buy_color,
            'sl': config.sl_color,
            'tp': config.tp_color,
            'risk_zone': config.risk_zone_color,
            'profit_zone': config.profit_zone_color,
            'emoji': config.buy_emoji
        }
    else:  # SELL
        return {
            'signal': config.sell_color,
            'sl': config.sl_color,
            'tp': config.tp_color,
            'risk_zone': config.risk_zone_color,
            'profit_zone': config.profit_zone_color,
            'emoji': config.sell_emoji
        }

def get_quality_color(config: VisualizationConfig, quality_score: float) -> str:
    """
    Obtener color basado en la calidad de la señal

    Args:
        config: Configuración de visualización
        quality_score: Puntuación de calidad (0-1)

    Returns:
        Color correspondiente a la calidad
    """
    if quality_score >= 0.8:
        return config.high_quality_color
    elif quality_score >= 0.6:
        return config.medium_quality_color
    else:
        return config.low_quality_color

def apply_custom_theme(custom_colors: Dict[str, str]) -> VisualizationConfig:
    """
    Aplicar tema personalizado

    Args:
        custom_colors: Diccionario con colores personalizados

    Returns:
        Configuración personalizada
    """
    config = VisualizationConfig()

    # Aplicar colores personalizados
    for key, value in custom_colors.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config

# Ejemplos de uso
if __name__ == "__main__":
    print("🎨 Configuración de Visualización SMC Bot")
    print("=" * 45)

    # Mostrar temas disponibles
    print("\n📋 Temas disponibles:")
    for theme_name in VISUALIZATION_THEMES.keys():
        config = get_visualization_config(theme_name)
        print(f"   • {theme_name}: Buy={config.buy_color}, Sell={config.sell_color}")

    # Ejemplo de uso
    print("\n🔧 Ejemplo de uso:")
    print("from smc_visualization_config import get_visualization_config")
    print("config = get_visualization_config('tradingview_dark')")
    print("colors = get_signal_colors(config, 'BUY')")

    # Mostrar configuración por defecto
    print("\n⚙️ Configuración por defecto:")
    config = get_visualization_config('default')
    print(f"   Buy Color: {config.buy_color}")
    print(f"   Sell Color: {config.sell_color}")
    print(f"   Marker Size: {config.marker_size}")
    print(f"   Line Width: {config.line_width}")
    print(f"   Font Family: {config.font_family}")
