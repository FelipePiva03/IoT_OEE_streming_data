"""
Configurações gerais para o simulador de dados
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, List


def _get_env_bool(key: str, default: bool) -> bool:
    """Lê variável de ambiente como boolean"""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_env_float(key: str, default: float) -> float:
    """Lê variável de ambiente como float"""
    return float(os.getenv(key, str(default)))


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
    SIMULATION_SPEED: float = 2.0  # 1.0 = tempo real, 10.0 = 10x mais rápido
    TIME_MULTIPLIER: float = 60.0   # Multiplicador de tempo simulado (1440 = 1 dia em 1 minuto)

    # Injeção de falhas para ML
    ENABLE_FAILURE_INJECTION: bool = True  # Ativa injeção de anomalias
    FAILURE_TYPES: List[str] = field(default_factory=list)

    # Kafka Configuration
    KAFKA_ENABLED: bool = True
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_MACHINE_EVENTS: str = "machine-events"
    KAFKA_TOPIC_SENSOR_METRICS: str = "sensor-metrics"
    KAFKA_TOPIC_QUALITY_EVENTS: str = "quality-events"
    KAFKA_TOPIC_ANOMALY_EVENTS: str = "anomaly-events"

    def __post_init__(self):
        # Configurações de ambiente
        self.SIMULATION_SPEED = _get_env_float("SIMULATION_SPEED", self.SIMULATION_SPEED)
        self.TIME_MULTIPLIER = _get_env_float("TIME_MULTIPLIER", self.TIME_MULTIPLIER)
        self.ENABLE_FAILURE_INJECTION = _get_env_bool("ENABLE_FAILURE_INJECTION", self.ENABLE_FAILURE_INJECTION)

        # Kafka via ambiente
        self.KAFKA_ENABLED = _get_env_bool("KAFKA_ENABLED", self.KAFKA_ENABLED)
        self.KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", self.KAFKA_BOOTSTRAP_SERVERS)
        self.KAFKA_TOPIC_MACHINE_EVENTS = os.getenv("KAFKA_TOPIC_MACHINE_EVENTS", self.KAFKA_TOPIC_MACHINE_EVENTS)
        self.KAFKA_TOPIC_SENSOR_METRICS = os.getenv("KAFKA_TOPIC_SENSOR_METRICS", self.KAFKA_TOPIC_SENSOR_METRICS)
        self.KAFKA_TOPIC_QUALITY_EVENTS = os.getenv("KAFKA_TOPIC_QUALITY_EVENTS", self.KAFKA_TOPIC_QUALITY_EVENTS)
        self.KAFKA_TOPIC_ANOMALY_EVENTS = os.getenv("KAFKA_TOPIC_ANOMALY_EVENTS", self.KAFKA_TOPIC_ANOMALY_EVENTS)

        # Tipos de falhas padrão
        if not self.FAILURE_TYPES:
            self.FAILURE_TYPES = [
                "temperature_spike",    # Pico de temperatura
                "vibration_anomaly",    # Vibração anormal
                "pressure_drop",        # Queda de pressão
                "speed_fluctuation",    # Flutuação de velocidade
                "power_surge"           # Pico de consumo
            ]


settings = SimulatorSettings()
