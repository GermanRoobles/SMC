#!/usr/bin/env python3
"""
SMC Strategy Profiles - Perfiles de Estrategia SMC
=================================================

Configuraciones predefinidas para diferentes tipos de traders
"""

from smc_bot import SMCConfig

class SMCProfiles:
    """
    Perfiles de configuración para diferentes tipos de traders
    """

    @staticmethod
    def conservative_trader():
        """
        Perfil conservador - Señales de alta calidad, R:R alto
        """
        return SMCConfig(
            swing_length=5,
            equal_tolerance=0.05,        # Tolerancia estricta
            min_rr=3.0,                  # R:R alto (3:1)
            risk_per_trade=0.5,          # Riesgo bajo
            min_confirmation_body=0.7,   # Confirmación fuerte
            fvg_min_size=0.08,          # FVG más grandes
            htf_timeframe="4h",
            ltf_timeframe="15m",
            enable_engulfing=True,
            enable_pinbar=True,
            enable_rejection_wick=True,
            min_wick_ratio=2.5          # Ratios más estrictos
        )

    @staticmethod
    def aggressive_trader():
        """
        Perfil agresivo - Más señales, R:R menor
        """
        return SMCConfig(
            swing_length=5,
            equal_tolerance=0.1,         # Tolerancia más amplia
            min_rr=1.5,                  # R:R más bajo (1.5:1)
            risk_per_trade=2.0,          # Riesgo más alto
            min_confirmation_body=0.5,   # Confirmación más flexible
            fvg_min_size=0.03,          # FVG más pequeños
            htf_timeframe="4h",
            ltf_timeframe="5m",          # Timeframe más bajo
            enable_engulfing=True,
            enable_pinbar=True,
            enable_rejection_wick=True,
            min_wick_ratio=1.5          # Ratios más flexibles
        )

    @staticmethod
    def balanced_trader():
        """
        Perfil balanceado - Equilibrio entre calidad y cantidad
        """
        return SMCConfig(
            swing_length=5,
            equal_tolerance=0.075,       # Tolerancia balanceada
            min_rr=2.0,                  # R:R estándar (2:1)
            risk_per_trade=1.0,          # Riesgo moderado
            min_confirmation_body=0.6,   # Confirmación estándar
            fvg_min_size=0.05,          # FVG estándar
            htf_timeframe="4h",
            ltf_timeframe="15m",
            enable_engulfing=True,
            enable_pinbar=True,
            enable_rejection_wick=True,
            min_wick_ratio=2.0          # Ratios estándar
        )

    @staticmethod
    def scalper_trader():
        """
        Perfil scalper - Señales rápidas, timeframes bajos
        """
        return SMCConfig(
            swing_length=3,              # Swings más rápidos
            equal_tolerance=0.05,        # Tolerancia estricta
            min_rr=1.8,                  # R:R adaptado
            risk_per_trade=0.8,          # Riesgo moderado-bajo
            min_confirmation_body=0.5,   # Confirmación rápida
            fvg_min_size=0.02,          # FVG pequeños
            htf_timeframe="1h",          # HTF más bajo
            ltf_timeframe="5m",          # LTF muy bajo
            enable_engulfing=True,
            enable_pinbar=True,
            enable_rejection_wick=True,
            min_wick_ratio=1.8          # Ratios adaptados
        )

    @staticmethod
    def swing_trader():
        """
        Perfil swing trader - Señales de largo plazo
        """
        return SMCConfig(
            swing_length=7,              # Swings más largos
            equal_tolerance=0.08,        # Tolerancia moderada
            min_rr=3.0,                  # R:R alto
            risk_per_trade=1.5,          # Riesgo moderado
            min_confirmation_body=0.7,   # Confirmación fuerte
            fvg_min_size=0.1,           # FVG grandes
            htf_timeframe="1d",          # HTF alto
            ltf_timeframe="4h",          # LTF alto
            enable_engulfing=True,
            enable_pinbar=True,
            enable_rejection_wick=True,
            min_wick_ratio=2.5          # Ratios estrictos
        )

    @staticmethod
    def get_profile(profile_name: str) -> SMCConfig:
        """
        Obtener perfil por nombre

        Args:
            profile_name: Nombre del perfil ('conservative', 'aggressive', 'balanced', 'scalper', 'swing')

        Returns:
            Configuración SMC
        """
        profiles = {
            'conservative': SMCProfiles.conservative_trader(),
            'aggressive': SMCProfiles.aggressive_trader(),
            'balanced': SMCProfiles.balanced_trader(),
            'scalper': SMCProfiles.scalper_trader(),
            'swing': SMCProfiles.swing_trader()
        }

        return profiles.get(profile_name.lower(), SMCProfiles.balanced_trader())

    @staticmethod
    def list_profiles():
        """
        Listar todos los perfiles disponibles
        """
        print("📊 PERFILES SMC DISPONIBLES:")
        print("=" * 40)

        profiles = [
            ('conservative', 'Conservador', 'Señales de alta calidad, R:R 3:1, riesgo bajo'),
            ('aggressive', 'Agresivo', 'Más señales, R:R 1.5:1, riesgo alto'),
            ('balanced', 'Balanceado', 'Equilibrio entre calidad y cantidad, R:R 2:1'),
            ('scalper', 'Scalper', 'Señales rápidas, timeframes bajos'),
            ('swing', 'Swing Trader', 'Señales de largo plazo, R:R 3:1')
        ]

        for key, name, description in profiles:
            print(f"🎯 {name} ({key}):")
            print(f"   {description}")
            print()

def compare_profiles():
    """
    Comparar diferentes perfiles
    """
    print("📊 COMPARACIÓN DE PERFILES SMC")
    print("=" * 50)

    profiles = ['conservative', 'aggressive', 'balanced', 'scalper', 'swing']

    print(f"{'Perfil':<12} {'R:R':<5} {'Riesgo':<7} {'Tolerancia':<11} {'HTF':<4} {'LTF':<4}")
    print("-" * 50)

    for profile_name in profiles:
        config = SMCProfiles.get_profile(profile_name)
        print(f"{profile_name:<12} {config.min_rr:<5} {config.risk_per_trade:<7} {config.equal_tolerance:<11} {config.htf_timeframe:<4} {config.ltf_timeframe:<4}")

if __name__ == "__main__":
    # Mostrar perfiles disponibles
    SMCProfiles.list_profiles()

    # Comparar perfiles
    compare_profiles()

    # Ejemplo de uso
    print("\n💡 EJEMPLO DE USO:")
    print("=" * 20)

    # Obtener configuración conservadora
    config = SMCProfiles.get_profile('conservative')
    print(f"Perfil conservador - R:R: {config.min_rr}, Riesgo: {config.risk_per_trade}%")

    # Obtener configuración agresiva
    config = SMCProfiles.get_profile('aggressive')
    print(f"Perfil agresivo - R:R: {config.min_rr}, Riesgo: {config.risk_per_trade}%")
