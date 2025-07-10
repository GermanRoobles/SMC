#!/usr/bin/env python3
"""
Configuración avanzada del SMC Bot
==================================

Archivo de configuración que permite personalizar completamente la estrategia
Smart Money Concepts Simplified by TJR según las preferencias del usuario.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum

class TradingSession(Enum):
    """Sesiones de trading"""
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "new_york"
    ALL = "all"

class ConfirmationStrength(Enum):
    """Niveles de confirmación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

@dataclass
class AdvancedSMCConfig:
    """
    Configuración avanzada para el bot SMC
    """
    # ==================== CONFIGURACIÓN GENERAL ====================

    # Configuración básica
    swing_length: int = 10
    equal_tolerance: float = 0.15  # Porcentaje de tolerancia para equal highs/lows
    min_rr: float = 2.0  # Risk-Reward mínimo
    risk_per_trade: float = 1.0  # Riesgo por operación (% del balance)

    # ==================== CONFIGURACIÓN DE ESTRUCTURA ====================

    # Detección de estructura
    min_structure_strength: ConfirmationStrength = ConfirmationStrength.MEDIUM
    structure_confirmation_candles: int = 3  # Velas para confirmar estructura

    # CHoCH y BOS
    choch_min_strength: ConfirmationStrength = ConfirmationStrength.HIGH
    bos_min_strength: ConfirmationStrength = ConfirmationStrength.MEDIUM
    require_choch_for_entry: bool = True  # Requerir CHoCH para entradas

    # ==================== CONFIGURACIÓN DE LIQUIDEZ ====================

    # Zonas de liquidez
    min_equal_points: int = 2  # Mínimo número de puntos iguales
    max_equal_age_hours: int = 24  # Máxima antigüedad de zonas (horas)

    # Barridos de liquidez
    sweep_confirmation_pct: float = 0.1  # % mínimo de penetración para barrido
    require_sweep_for_entry: bool = True  # Requerir barrido para entradas

    # ==================== CONFIGURACIÓN DE ORDER BLOCKS ====================

    # Order Blocks
    ob_min_size_pct: float = 0.2  # Tamaño mínimo del OB (% del ATR)
    ob_max_age_hours: int = 48  # Máxima antigüedad de OB (horas)
    ob_require_impulse: bool = True  # Requerir movimiento impulsivo
    ob_min_impulse_pct: float = 0.5  # % mínimo de movimiento impulsivo

    # Mitigación de OB
    ob_full_mitigation: bool = False  # Requerir mitigación completa
    ob_partial_mitigation_pct: float = 0.5  # % para mitigación parcial

    # ==================== CONFIGURACIÓN DE FVG ====================

    # Fair Value Gaps
    fvg_min_size: float = 0.1  # Tamaño mínimo de FVG (% del precio)
    fvg_max_age_hours: int = 72  # Máxima antigüedad de FVG (horas)
    fvg_require_volume: bool = False  # Requerir volumen alto en FVG
    fvg_min_volume_multiplier: float = 1.5  # Multiplicador de volumen promedio

    # ==================== CONFIGURACIÓN DE CONFIRMACIÓN ====================

    # Patrones de confirmación
    min_confirmation_body: float = 0.6  # % mínimo del cuerpo de la vela
    confirmation_patterns: List[str] = field(default_factory=lambda: [
        'bullish_engulfing', 'bearish_engulfing',
        'hammer', 'shooting_star',
        'strong_bullish', 'strong_bearish'
    ])

    # Fuerza de confirmación
    min_confirmation_strength: ConfirmationStrength = ConfirmationStrength.MEDIUM
    multiple_confirmation_bonus: float = 0.2  # Bonus por múltiples confirmaciones

    # ==================== CONFIGURACIÓN DE GESTIÓN DE RIESGO ====================

    # Stop Loss
    sl_method: str = "atr"  # "atr", "structure", "fixed"
    sl_atr_multiplier: float = 1.5  # Multiplicador ATR para SL
    sl_fixed_pct: float = 2.0  # % fijo para SL

    # Take Profit
    tp_method: str = "rr"  # "rr", "structure", "fibonacci"
    tp_rr_multiplier: float = 2.0  # Multiplicador R:R para TP
    tp_fibonacci_levels: List[float] = field(default_factory=lambda: [0.618, 1.0, 1.618])

    # Trailing Stop
    enable_trailing_stop: bool = False
    trailing_stop_pct: float = 1.0  # % para trailing stop
    trailing_activation_rr: float = 1.0  # R:R para activar trailing

    # ==================== CONFIGURACIÓN DE FILTROS ====================

    # Filtros de tiempo
    trading_sessions: List[TradingSession] = field(default_factory=lambda: [TradingSession.ALL])
    avoid_news_hours: bool = True
    high_impact_news_buffer_hours: int = 1

    # Filtros de mercado
    min_volume_filter: bool = False
    min_volume_multiplier: float = 1.2  # Multiplicador de volumen promedio
    max_spread_pct: float = 0.1  # % máximo de spread permitido

    # Filtros de volatilidad
    min_volatility_filter: bool = False
    min_atr_multiplier: float = 0.8  # Multiplicador ATR mínimo
    max_atr_multiplier: float = 3.0  # Multiplicador ATR máximo

    # ==================== CONFIGURACIÓN DE ENTRADAS ====================

    # Criterios de entrada
    require_all_conditions: bool = True  # Requerir todas las condiciones
    allow_partial_conditions: bool = False  # Permitir condiciones parciales
    partial_condition_threshold: float = 0.75  # % mínimo de condiciones

    # Múltiples entradas
    allow_multiple_entries: bool = False
    max_concurrent_trades: int = 3
    min_distance_between_entries: float = 2.0  # % mínimo entre entradas

    # ==================== CONFIGURACIÓN DE ALERTAS ====================

    # Alertas
    send_alerts: bool = True
    alert_methods: List[str] = field(default_factory=lambda: ["console", "file"])
    alert_file_path: str = "smc_alerts.log"

    # Niveles de alerta
    alert_on_structure_change: bool = True
    alert_on_liquidity_sweep: bool = True
    alert_on_order_block_touch: bool = True
    alert_on_fvg_fill: bool = True
    alert_on_signal_generation: bool = True

    # ==================== CONFIGURACIÓN DE BACKTESTING ====================

    # Backtesting
    enable_backtesting: bool = False
    backtest_start_date: str = "2024-01-01"
    backtest_end_date: str = "2024-12-31"
    initial_balance: float = 10000.0

    # Métricas
    save_trade_log: bool = True
    trade_log_path: str = "smc_trades.csv"
    calculate_metrics: bool = True

# ==================== CONFIGURACIONES PREDEFINIDAS ====================

def get_conservative_config() -> AdvancedSMCConfig:
    """
    Configuración conservadora para traders con aversión al riesgo
    """
    return AdvancedSMCConfig(
        swing_length=15,
        equal_tolerance=0.1,
        min_rr=3.0,
        risk_per_trade=0.5,
        choch_min_strength=ConfirmationStrength.HIGH,
        require_choch_for_entry=True,
        require_sweep_for_entry=True,
        min_confirmation_strength=ConfirmationStrength.HIGH,
        sl_atr_multiplier=2.0,
        tp_rr_multiplier=3.0,
        require_all_conditions=True
    )

def get_aggressive_config() -> AdvancedSMCConfig:
    """
    Configuración agresiva para traders que buscan más oportunidades
    """
    return AdvancedSMCConfig(
        swing_length=5,
        equal_tolerance=0.2,
        min_rr=1.5,
        risk_per_trade=2.0,
        choch_min_strength=ConfirmationStrength.MEDIUM,
        require_choch_for_entry=False,
        require_sweep_for_entry=False,
        min_confirmation_strength=ConfirmationStrength.LOW,
        sl_atr_multiplier=1.0,
        tp_rr_multiplier=1.5,
        allow_partial_conditions=True,
        partial_condition_threshold=0.6
    )

def get_scalping_config() -> AdvancedSMCConfig:
    """
    Configuración para scalping (timeframes bajos)
    """
    return AdvancedSMCConfig(
        swing_length=3,
        equal_tolerance=0.05,
        min_rr=1.2,
        risk_per_trade=0.5,
        ob_max_age_hours=6,
        fvg_max_age_hours=12,
        sl_atr_multiplier=0.8,
        tp_rr_multiplier=1.2,
        enable_trailing_stop=True,
        trailing_stop_pct=0.5,
        allow_multiple_entries=True,
        max_concurrent_trades=5
    )

def get_swing_config() -> AdvancedSMCConfig:
    """
    Configuración para swing trading (timeframes altos)
    """
    return AdvancedSMCConfig(
        swing_length=20,
        equal_tolerance=0.3,
        min_rr=3.0,
        risk_per_trade=1.5,
        ob_max_age_hours=168,  # 1 semana
        fvg_max_age_hours=336,  # 2 semanas
        sl_atr_multiplier=2.5,
        tp_rr_multiplier=3.0,
        require_all_conditions=True,
        min_confirmation_strength=ConfirmationStrength.HIGH
    )

# ==================== UTILIDADES ====================

def validate_config(config: AdvancedSMCConfig) -> List[str]:
    """
    Validar configuración y devolver lista de errores

    Args:
        config: Configuración a validar

    Returns:
        Lista de errores encontrados
    """
    errors = []

    # Validaciones básicas
    if config.swing_length < 1:
        errors.append("swing_length debe ser mayor a 0")

    if config.equal_tolerance < 0 or config.equal_tolerance > 10:
        errors.append("equal_tolerance debe estar entre 0 y 10%")

    if config.min_rr < 0.5:
        errors.append("min_rr debe ser mayor a 0.5")

    if config.risk_per_trade < 0.1 or config.risk_per_trade > 10:
        errors.append("risk_per_trade debe estar entre 0.1% y 10%")

    # Validaciones de coherencia
    if config.tp_rr_multiplier < config.min_rr:
        errors.append("tp_rr_multiplier debe ser mayor o igual a min_rr")

    if config.enable_trailing_stop and config.trailing_activation_rr > config.min_rr:
        errors.append("trailing_activation_rr debe ser menor o igual a min_rr")

    return errors

def save_config(config: AdvancedSMCConfig, filename: str = "smc_config.json"):
    """
    Guardar configuración en archivo JSON

    Args:
        config: Configuración a guardar
        filename: Nombre del archivo
    """
    import json
    import dataclasses

    config_dict = dataclasses.asdict(config)

    # Convertir enums a strings
    for key, value in config_dict.items():
        if isinstance(value, list):
            config_dict[key] = [str(v) if hasattr(v, 'value') else v for v in value]
        elif hasattr(value, 'value'):
            config_dict[key] = value.value

    with open(filename, 'w') as f:
        json.dump(config_dict, f, indent=2)

    print(f"Configuración guardada en {filename}")

def load_config(filename: str = "smc_config.json") -> AdvancedSMCConfig:
    """
    Cargar configuración desde archivo JSON

    Args:
        filename: Nombre del archivo

    Returns:
        Configuración cargada
    """
    import json

    with open(filename, 'r') as f:
        config_dict = json.load(f)

    # Reconstruir enums
    if 'min_structure_strength' in config_dict:
        config_dict['min_structure_strength'] = ConfirmationStrength(config_dict['min_structure_strength'])

    if 'choch_min_strength' in config_dict:
        config_dict['choch_min_strength'] = ConfirmationStrength(config_dict['choch_min_strength'])

    if 'bos_min_strength' in config_dict:
        config_dict['bos_min_strength'] = ConfirmationStrength(config_dict['bos_min_strength'])

    if 'min_confirmation_strength' in config_dict:
        config_dict['min_confirmation_strength'] = ConfirmationStrength(config_dict['min_confirmation_strength'])

    if 'trading_sessions' in config_dict:
        config_dict['trading_sessions'] = [TradingSession(s) for s in config_dict['trading_sessions']]

    return AdvancedSMCConfig(**config_dict)

# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    print("🔧 Configuración avanzada del SMC Bot")
    print("=" * 50)

    # Mostrar configuraciones predefinidas
    configs = {
        "Conservadora": get_conservative_config(),
        "Agresiva": get_aggressive_config(),
        "Scalping": get_scalping_config(),
        "Swing Trading": get_swing_config()
    }

    for name, config in configs.items():
        print(f"\n📊 {name}:")
        print(f"   Swing Length: {config.swing_length}")
        print(f"   Min R:R: {config.min_rr}")
        print(f"   Risk per Trade: {config.risk_per_trade}%")
        print(f"   Confirmación: {config.min_confirmation_strength.value}")

        # Validar configuración
        errors = validate_config(config)
        if errors:
            print(f"   ⚠️ Errores: {', '.join(errors)}")
        else:
            print("   ✅ Configuración válida")

    # Ejemplo de guardado
    print(f"\n💾 Guardando configuración conservadora...")
    save_config(get_conservative_config(), "conservative_config.json")

    print("✅ Configuraciones listas para usar")
