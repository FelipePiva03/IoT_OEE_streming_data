"""
Schemas dos eventos gerados pelo simulador
"""
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Literal
from enum import Enum

class MachineStatus(str, Enum):
    """Estados possíveis da máquina"""
    IDLE = "idle"
    WARMUP = "warmup"
    RUNNING = "running"
    SETUP = "setup"
    PLANNED_DOWNTIME = "planned_downtime"
    UNPLANNED_DOWNTIME = "unplanned_downtime"
    MAINTENANCE = "maintance"
    COOLDOWN = "cooldown"

class EventType(str, Enum):
    """Tipos de eventos"""
    STATUS_CHANGE = "status_change"
    CYCLE_COMPLETE = "cycle_complete"
    ALERT = "alert"

class QualityResult(str, Enum):
    """Resultados possíveis de qualidade"""
    OK = "ok"
    NOK = "nok"

class DefectType(str, Enum):
    """Tipos de defeitos"""
    DIMENSIONAL = "dimensional"
    SURFACE = "surface"
    MATERIAL = "material"
    ASSEMBLY = "assembly"

class AlertLevel(str, Enum):
    """Níveis de alerta"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Tipos de anomalias para detecção por ML"""
    # Anomalias térmicas
    TEMPERATURE_SPIKE = "temperature_spike"           # Pico súbito de temperatura
    TEMPERATURE_DRIFT = "temperature_drift"           # Aumento gradual (degradação)
    OVERHEATING = "overheating"                       # Superaquecimento crítico

    # Anomalias de vibração
    VIBRATION_SPIKE = "vibration_spike"               # Pico de vibração
    VIBRATION_PATTERN = "vibration_pattern"           # Padrão anormal (desbalanceamento)
    BEARING_WEAR = "bearing_wear"                     # Desgaste de rolamento

    # Anomalias de pressão
    PRESSURE_DROP = "pressure_drop"                   # Queda súbita de pressão
    PRESSURE_LEAK = "pressure_leak"                   # Vazamento (queda gradual)
    PRESSURE_SPIKE = "pressure_spike"                 # Pico de pressão

    # Anomalias elétricas
    POWER_SURGE = "power_surge"                       # Pico de consumo
    POWER_FLUCTUATION = "power_fluctuation"           # Oscilação de energia
    MOTOR_DEGRADATION = "motor_degradation"           # Degradação do motor

    # Anomalias mecânicas
    SPEED_FLUCTUATION = "speed_fluctuation"           # RPM instável
    SPEED_DROP = "speed_drop"                         # Queda de velocidade
    MECHANICAL_WEAR = "mechanical_wear"               # Desgaste mecânico geral


class AnomalySeverity(str, Enum):
    """Severidade das anomalias - usado para priorização e ML"""
    LOW = "low"           # Monitorar - não requer ação imediata
    MEDIUM = "medium"     # Atenção - agendar manutenção
    HIGH = "high"         # Urgente - manutenção em breve
    CRITICAL = "critical" # Parar máquina - risco de dano


# Mapeamento de anomalias para severidades típicas e características
ANOMALY_PROFILES = {
    AnomalyType.TEMPERATURE_SPIKE: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.HIGH),
        "duration_range": (30, 180),      # 30s a 3min
        "multiplier_range": (1.1, 1.3),   # 10-30% acima do normal
        "leads_to_failure": 0.15,         # 15% chance de causar falha
        "precursor_pattern": False,       # Não é padrão gradual
    },
    AnomalyType.TEMPERATURE_DRIFT: {
        "severity_range": (AnomalySeverity.LOW, AnomalySeverity.MEDIUM),
        "duration_range": (300, 1800),    # 5-30min (gradual)
        "multiplier_range": (1.05, 1.15), # 5-15% acima
        "leads_to_failure": 0.25,         # 25% chance
        "precursor_pattern": True,        # Padrão detectável antes da falha
    },
    AnomalyType.OVERHEATING: {
        "severity_range": (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL),
        "duration_range": (60, 300),
        "multiplier_range": (1.25, 1.5),  # 25-50% acima
        "leads_to_failure": 0.60,         # 60% chance
        "precursor_pattern": False,
    },
    AnomalyType.VIBRATION_SPIKE: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.HIGH),
        "duration_range": (30, 120),
        "multiplier_range": (1.2, 1.6),
        "leads_to_failure": 0.20,
        "precursor_pattern": False,
    },
    AnomalyType.VIBRATION_PATTERN: {
        "severity_range": (AnomalySeverity.LOW, AnomalySeverity.MEDIUM),
        "duration_range": (600, 3600),    # 10min-1h
        "multiplier_range": (1.1, 1.3),
        "leads_to_failure": 0.30,
        "precursor_pattern": True,        # Padrão repetitivo detectável
    },
    AnomalyType.BEARING_WEAR: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.CRITICAL),
        "duration_range": (1800, 7200),   # 30min-2h (progressivo)
        "multiplier_range": (1.15, 1.8),
        "leads_to_failure": 0.50,
        "precursor_pattern": True,        # Vibração aumenta gradualmente
    },
    AnomalyType.PRESSURE_DROP: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.HIGH),
        "duration_range": (60, 300),
        "multiplier_range": (0.4, 0.7),   # 30-60% do normal
        "leads_to_failure": 0.25,
        "precursor_pattern": False,
    },
    AnomalyType.PRESSURE_LEAK: {
        "severity_range": (AnomalySeverity.LOW, AnomalySeverity.MEDIUM),
        "duration_range": (600, 3600),
        "multiplier_range": (0.7, 0.9),   # Queda gradual
        "leads_to_failure": 0.20,
        "precursor_pattern": True,
    },
    AnomalyType.PRESSURE_SPIKE: {
        "severity_range": (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL),
        "duration_range": (10, 60),
        "multiplier_range": (1.3, 1.6),
        "leads_to_failure": 0.40,
        "precursor_pattern": False,
    },
    AnomalyType.POWER_SURGE: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.HIGH),
        "duration_range": (30, 180),
        "multiplier_range": (1.5, 2.5),
        "leads_to_failure": 0.20,
        "precursor_pattern": False,
    },
    AnomalyType.POWER_FLUCTUATION: {
        "severity_range": (AnomalySeverity.LOW, AnomalySeverity.MEDIUM),
        "duration_range": (120, 600),
        "multiplier_range": (0.8, 1.3),   # Oscila para cima e baixo
        "leads_to_failure": 0.15,
        "precursor_pattern": True,
    },
    AnomalyType.MOTOR_DEGRADATION: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.CRITICAL),
        "duration_range": (1800, 7200),
        "multiplier_range": (1.2, 1.6),
        "leads_to_failure": 0.55,
        "precursor_pattern": True,        # Consumo aumenta gradualmente
    },
    AnomalyType.SPEED_FLUCTUATION: {
        "severity_range": (AnomalySeverity.LOW, AnomalySeverity.MEDIUM),
        "duration_range": (60, 300),
        "multiplier_range": (0.85, 1.15),
        "leads_to_failure": 0.10,
        "precursor_pattern": False,
    },
    AnomalyType.SPEED_DROP: {
        "severity_range": (AnomalySeverity.MEDIUM, AnomalySeverity.HIGH),
        "duration_range": (120, 600),
        "multiplier_range": (0.5, 0.8),
        "leads_to_failure": 0.35,
        "precursor_pattern": True,
    },
    AnomalyType.MECHANICAL_WEAR: {
        "severity_range": (AnomalySeverity.LOW, AnomalySeverity.HIGH),
        "duration_range": (3600, 14400),  # 1-4h
        "multiplier_range": (1.1, 1.4),
        "leads_to_failure": 0.45,
        "precursor_pattern": True,        # Múltiplos sensores afetados
    },
}

@dataclass
class MachineEvent:
    """Evento relacionado ao estado da máquina"""
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    machine_id: str = ""
    timestamp: str = ""
    event_type: str = EventType.STATUS_CHANGE.value
    status: str = MachineStatus.IDLE.value
    previous_status: Optional[str] = None
    cycle_count: int = 0
    shift: str = "day"
    operator_id: Optional[str] = None
    reason: Optional[str] = None  # Motivo da parada
    
    def to_dict(self):
        return asdict(self)
    
@dataclass
class SensorMetric:
    """Métricas dos sensores da máquina"""
    metric_id: str = field(default_factory=lambda: f"met_{uuid.uuid4().hex[:12]}")
    machine_id: str = ""
    timestamp: str = ""
    temperature: float = 0.0        # °C
    vibration: float = 0.0          # mm/s
    speed_rpm: int = 0              # RPM
    pressure: float = 0.0           # bar
    power_consumption: float = 0.0  # kW
    operating_hours: float = 0.0    # horas desde última manutenção
    
    def to_dict(self):
        return asdict(self)
    
@dataclass
class QualityEvent:
    """Evento de inspeção de qualidade"""
    inspection_id: str = field(default_factory=lambda: f"qlt_{uuid.uuid4().hex[:12]}")
    machine_id: str = ""
    timestamp: str = ""
    cycle_count: int = 0
    result: str = QualityResult.OK.value
    defect_type: Optional[str] = None
    defect_severity: Optional[int] = None  # 1-5
    inspector_id: Optional[str] = None
    batch_id: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class AnomalyEvent:
    """
    Evento de anomalia detectada - usado para treinar modelos de ML

    Campos importantes para ML:
    - anomaly_type: Tipo da anomalia (label para classificação)
    - severity: Severidade (pode ser target de regressão)
    - is_precursor: Se é padrão que precede falha (importante para predição)
    - led_to_failure: Se resultou em falha (ground truth)
    - sensor_values: Snapshot dos sensores no momento da anomalia
    """
    anomaly_id: str = field(default_factory=lambda: f"ano_{uuid.uuid4().hex[:12]}")
    machine_id: str = ""
    timestamp: str = ""
    anomaly_type: str = ""                    # Tipo da anomalia (AnomalyType)
    severity: str = AnomalySeverity.LOW.value # Severidade

    # Contexto da anomalia
    duration_seconds: float = 0.0             # Duração da anomalia
    is_precursor: bool = False                # Se é padrão que precede falha
    led_to_failure: bool = False              # Se resultou em falha (preenchido depois)

    # Valores dos sensores no momento da anomalia
    temperature: float = 0.0
    temperature_delta: float = 0.0            # Diferença do valor normal
    vibration: float = 0.0
    vibration_delta: float = 0.0
    pressure: float = 0.0
    pressure_delta: float = 0.0
    speed_rpm: int = 0
    speed_delta: int = 0
    power_consumption: float = 0.0
    power_delta: float = 0.0

    # Contexto da máquina
    operating_hours: float = 0.0
    wear_factor: float = 0.0                  # 0.0-1.0
    cycles_since_maintenance: int = 0

    # Metadados para ML
    time_to_failure: Optional[float] = None   # Segundos até falha (se houver)
    failure_type: Optional[str] = None        # Tipo de falha resultante

    def to_dict(self):
        return asdict(self)

