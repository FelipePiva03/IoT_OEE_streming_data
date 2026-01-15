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

