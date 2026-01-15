"""
Configurações gerais para o simulador de dados
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

@dataclass
class SimulatorSettings:
    """Configurações do simulador de IoT"""

    # Frequencia de geração de eventos
    EVENT_INTERNAL_SECONDS: int = 5

    # Formato do timestamp
    TIMESTAMP_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%fZ"

    # Probabilidades de eventos
    QUALITY_CHECK_PROBABILTY: float = 0.15
    PLANNED_DOWNTIME_PROBABILTY: float = 0.02
    UNPLANNED_FAILURE_BASE_PROBABILTY: float = 0.005

    # Limites de alerta
    TEMPERATURE_WARNING_THRESHOLD: float = 0.85  
    VIBRATION_WARNING_THRESHOLD: float = 0.80    
    QUALITY_WARNING_THRESHOLD: float = 0.90

    # Manutenção preventiva
    MAINTENANCE_INTERVAL_HOURS: int = 168  # 1 semana
    MAINTENANCE_DURATION_HOURS: int = 4

    # Warm-up e cool-down
    WARMUP_DURATION_SECONDS: int = 300     # 5 minutos para aquecer
    COOLDOWN_DURATION_SECONDS: int = 180   # 3 minutos para esfriar

    # Paths
    CONFIG_DIR: Path = Path(__file__).parent
    MACHINES_CONFIG: Path = CONFIG_DIR / "machines.yaml"

    # Output
    OUTPUT_DIR: Path = Path(__file__).parent.parent / "output"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Simulação
    SIMULATION_SPEED: float = 1.0  # 1.0 = tempo real, 10.0 = 10x mais rápido

settings = SimulatorSettings()
