#!/usr/bin/env python3
"""
Configuraciones personalizadas para SMC Bot
==========================================

Este archivo permite crear, guardar y cargar configuraciones personalizadas
para diferentes perfiles de trading.
"""

import json
import os
from smc_bot import SMCConfig

# Directorio para guardar configuraciones
CONFIG_DIR = "configs"

def get_config_by_profile(profile: str) -> SMCConfig:
    """
    Obtiene configuración por perfil predefinido

    Args:
        profile: Perfil de trading ('conservative', 'balanced', 'aggressive')

    Returns:
        SMCConfig: Configuración correspondiente al perfil
    """
    configs = {
        'conservative': SMCConfig(
            swing_length=7,
            equal_tolerance=0.05,
            min_rr=3.0,
            risk_per_trade=0.5,
            min_confirmation_body=0.7,
            fvg_min_size=0.08
        ),
        'balanced': SMCConfig(
            swing_length=5,
            equal_tolerance=0.075,
            min_rr=2.0,
            risk_per_trade=1.0,
            min_confirmation_body=0.6,
            fvg_min_size=0.05
        ),
        'aggressive': SMCConfig(
            swing_length=3,
            equal_tolerance=0.1,
            min_rr=1.5,
            risk_per_trade=2.0,
            min_confirmation_body=0.5,
            fvg_min_size=0.03
        ),
        'scalping': SMCConfig(
            swing_length=3,
            equal_tolerance=0.15,
            min_rr=1.2,
            risk_per_trade=1.5,
            min_confirmation_body=0.4,
            fvg_min_size=0.02
        ),
        'swing_trading': SMCConfig(
            swing_length=10,
            equal_tolerance=0.05,
            min_rr=4.0,
            risk_per_trade=0.8,
            min_confirmation_body=0.8,
            fvg_min_size=0.1
        )
    }

    return configs.get(profile, configs['balanced'])

def save_config(config: SMCConfig, name: str):
    """
    Guarda una configuración en archivo JSON

    Args:
        config: Configuración a guardar
        name: Nombre del archivo (sin extensión)
    """
    # Crear directorio si no existe
    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Convertir configuración a diccionario
    config_dict = {
        'swing_length': config.swing_length,
        'equal_tolerance': config.equal_tolerance,
        'min_rr': config.min_rr,
        'risk_per_trade': config.risk_per_trade,
        'min_confirmation_body': config.min_confirmation_body,
        'fvg_min_size': config.fvg_min_size
    }

    # Guardar en archivo
    file_path = os.path.join(CONFIG_DIR, f"{name}.json")
    with open(file_path, 'w') as f:
        json.dump(config_dict, f, indent=2)

    print(f"✅ Configuración guardada en: {file_path}")

def load_config(name: str) -> SMCConfig:
    """
    Carga una configuración desde archivo JSON

    Args:
        name: Nombre del archivo (sin extensión)

    Returns:
        SMCConfig: Configuración cargada
    """
    file_path = os.path.join(CONFIG_DIR, f"{name}.json")

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo no encontrado: {file_path}")
        return get_config_by_profile('balanced')

    try:
        with open(file_path, 'r') as f:
            config_dict = json.load(f)

        config = SMCConfig(
            swing_length=config_dict['swing_length'],
            equal_tolerance=config_dict['equal_tolerance'],
            min_rr=config_dict['min_rr'],
            risk_per_trade=config_dict['risk_per_trade'],
            min_confirmation_body=config_dict['min_confirmation_body'],
            fvg_min_size=config_dict['fvg_min_size']
        )

        print(f"✅ Configuración cargada desde: {file_path}")
        return config

    except Exception as e:
        print(f"❌ Error al cargar configuración: {e}")
        return get_config_by_profile('balanced')

def list_configs():
    """
    Lista todas las configuraciones disponibles
    """
    print("📋 Configuraciones disponibles:")
    print("\n🔧 Perfiles predefinidos:")
    print("   - conservative (Conservador)")
    print("   - balanced (Balanceado)")
    print("   - aggressive (Agresivo)")
    print("   - scalping (Scalping)")
    print("   - swing_trading (Swing Trading)")

    if os.path.exists(CONFIG_DIR):
        custom_configs = [f.replace('.json', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
        if custom_configs:
            print("\n💾 Configuraciones personalizadas:")
            for config in custom_configs:
                print(f"   - {config}")
    else:
        print("\n💾 No hay configuraciones personalizadas guardadas")

def create_custom_config():
    """
    Asistente interactivo para crear configuración personalizada
    """
    print("🎯 Creando configuración personalizada")
    print("=" * 40)

    # Recolectar parámetros
    try:
        swing_length = int(input("Swing Length (3-15, recomendado 5): ") or "5")
        equal_tolerance = float(input("Equal Tolerance % (0.01-0.2, recomendado 0.075): ") or "0.075")
        min_rr = float(input("Risk:Reward mínimo (1.0-5.0, recomendado 2.0): ") or "2.0")
        risk_per_trade = float(input("Riesgo por operación % (0.1-5.0, recomendado 1.0): ") or "1.0")
        min_confirmation_body = float(input("Confirmación mínima % (0.3-0.9, recomendado 0.6): ") or "0.6")
        fvg_min_size = float(input("FVG tamaño mínimo % (0.01-0.1, recomendado 0.05): ") or "0.05")

        name = input("Nombre de la configuración: ") or "mi_config"

        # Crear configuración
        config = SMCConfig(
            swing_length=swing_length,
            equal_tolerance=equal_tolerance,
            min_rr=min_rr,
            risk_per_trade=risk_per_trade,
            min_confirmation_body=min_confirmation_body,
            fvg_min_size=fvg_min_size
        )

        # Guardar
        save_config(config, name)

        print(f"\n✅ Configuración '{name}' creada y guardada!")
        print("🚀 Puedes usarla con: load_config('{}')".format(name))

        return config

    except ValueError as e:
        print(f"❌ Error en los valores ingresados: {e}")
        return None
    except KeyboardInterrupt:
        print("\n⚠️ Creación cancelada por el usuario")
        return None

def compare_configs(*config_names):
    """
    Compara múltiples configuraciones

    Args:
        *config_names: Nombres de configuraciones a comparar
    """
    print("📊 COMPARACIÓN DE CONFIGURACIONES")
    print("=" * 50)

    configs = {}

    # Cargar configuraciones
    for name in config_names:
        if name in ['conservative', 'balanced', 'aggressive', 'scalping', 'swing_trading']:
            configs[name] = get_config_by_profile(name)
        else:
            configs[name] = load_config(name)

    # Tabla comparativa
    print(f"{'Config':<15} {'Swing':<6} {'Tol%':<6} {'R:R':<5} {'Risk%':<6} {'Conf':<5} {'FVG':<5}")
    print("-" * 60)

    for name, config in configs.items():
        print(f"{name:<15} {config.swing_length:<6} {config.equal_tolerance:<6.3f} "
              f"{config.min_rr:<5.1f} {config.risk_per_trade:<6.1f} "
              f"{config.min_confirmation_body:<5.2f} {config.fvg_min_size:<5.3f}")

def main():
    """
    Función principal para gestionar configuraciones
    """
    print("🔧 SMC Bot - Gestor de Configuraciones")
    print("=" * 40)

    while True:
        print("\n📋 Opciones:")
        print("1. Listar configuraciones")
        print("2. Crear configuración personalizada")
        print("3. Comparar configuraciones")
        print("4. Salir")

        choice = input("\nSelecciona una opción (1-4): ").strip()

        if choice == "1":
            list_configs()
        elif choice == "2":
            create_custom_config()
        elif choice == "3":
            print("Ingresa los nombres de configuraciones a comparar (separados por coma):")
            names = input("Ejemplo: conservative,balanced,aggressive: ").strip().split(",")
            names = [name.strip() for name in names if name.strip()]
            if names:
                compare_configs(*names)
            else:
                print("❌ No se ingresaron configuraciones válidas")
        elif choice == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()
