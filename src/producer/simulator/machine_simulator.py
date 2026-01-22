"""
Simulador de máquina industrial com geração de eventos e métricas
"""
import random
import time
from datetime import datetime
from typing import Optional, List, Tuple
from dataclasses import dataclass

from src.producer.schemas.events import (
    MachineEvent,
    SensorMetric,
    QualityEvent,
    MachineStatus,
    EventType,
    QualityResult,
    DefectType,
    AlertLevel
)
from src.producer.simulator.state_machine import StateMachine
from src.producer.config.settings import settings


@dataclass
class MachineConfig:
    """Configuração de uma máquina específica"""
    machine_id: str
    machine_type: str
    rated_speed: int  # RPM nominal
    cycle_time: float  # segundos por ciclo
    operator_id: str
    shift: str = "day"

    # Limites dos sensores (do YAML)
    max_temperature: float = 85.0
    optimal_temperature: float = 65.0
    max_vibration: float = 5.0
    optimal_vibration: float = 1.5
    max_pressure: float = 8.0
    optimal_pressure: float = 6.5

    # Taxa de injeção de falhas para ML
    failure_injection_rate: float = 0.05  # 5% padrão


class MachineSimulator:
    """
    Simula uma máquina industrial gerando eventos realistas
    """

    def __init__(self, config: MachineConfig):
        self.config = config
        self.state_machine = StateMachine(initial_state=MachineStatus.IDLE)

        # Contadores
        self.cycle_count = 0
        self.total_cycles = 0
        self.good_parts = 0
        self.bad_parts = 0

        # Histórico
        self.operating_hours = 0.0
        self.last_maintenance = time.time()

        # Estado dos sensores (valores base)
        self.base_temperature = 45.0  # °C
        self.base_vibration = 2.5     # mm/s
        self.base_pressure = 6.0      # bar

        # Degração ao longo do tempo (simula desgaste)
        self.wear_factor = 0.0  # 0.0 a 1.0

        # Injeção de falhas (para treinamento de ML)
        self.anomaly_active = False
        self.anomaly_type = None
        self.anomaly_duration = 0

    def update(self, current_time: float, elapsed: float) -> Tuple[
        Optional[MachineEvent],
        Optional[SensorMetric],
        Optional[QualityEvent]
    ]:
        """
        Atualiza estado da máquina e retorna eventos gerados

        Args:
            current_time: timestamp atual
            elapsed: tempo decorrido desde última atualização

        Returns:
            Tupla com (MachineEvent, SensorMetric, QualityEvent)
            Qualquer um pode ser None se não houver evento nesse ciclo
        """
        machine_event = None
        sensor_metric = None
        quality_event = None

        # Atualiza máquina de estados
        previous_state = self.state_machine.current_state
        new_state = self.state_machine.update(current_time, elapsed)

        # Verifica transições baseadas em probabilidade quando RUNNING
        if not new_state and previous_state == MachineStatus.RUNNING:
            new_state = self._check_random_transitions(current_time)

        # Se houve transição de estado, gera evento
        if new_state:
            machine_event = self._generate_machine_event(
                current_time, new_state, previous_state
            )

        # Atualiza métricas baseadas no estado atual
        if self.state_machine.current_state == MachineStatus.RUNNING:
            self.operating_hours += elapsed / 3600.0  # converte para horas
            self._update_wear()

            # Simula conclusão de ciclos
            if random.random() < (elapsed / self.config.cycle_time):
                self.cycle_count += 1
                self.total_cycles += 1

                # Gera evento de ciclo completo ocasionalmente
                if random.random() < 0.3:  # 30% dos ciclos geram evento
                    machine_event = self._generate_cycle_event(current_time)

                # Verifica se deve fazer inspeção de qualidade
                if random.random() < settings.QUALITY_CHECK_PROBABILTY:
                    quality_event = self._generate_quality_event(current_time)

        # Sempre gera métricas dos sensores
        sensor_metric = self._generate_sensor_metrics(current_time)

        # Injeta anomalias se habilitado (para ML)
        if settings.ENABLE_FAILURE_INJECTION and sensor_metric:
            sensor_metric = self._inject_anomaly(sensor_metric, current_time, elapsed)

        # Verifica se precisa de manutenção
        self._check_maintenance_need(current_time)

        return machine_event, sensor_metric, quality_event

    def _generate_machine_event(
        self,
        current_time: float,
        new_state: MachineStatus,
        previous_state: MachineStatus
    ) -> MachineEvent:
        """Gera evento de mudança de estado"""
        timestamp = datetime.fromtimestamp(current_time).strftime(
            settings.TIMESTAMP_FORMAT
        )

        # Define motivo da mudança de estado
        reason = self._get_state_change_reason(new_state, previous_state)

        return MachineEvent(
            machine_id=self.config.machine_id,
            timestamp=timestamp,
            event_type=EventType.STATUS_CHANGE.value,
            status=new_state.value,
            previous_status=previous_state.value,
            cycle_count=self.cycle_count,
            shift=self.config.shift,
            operator_id=self.config.operator_id,
            reason=reason
        )

    def _generate_cycle_event(self, current_time: float) -> MachineEvent:
        """Gera evento de ciclo completo"""
        timestamp = datetime.fromtimestamp(current_time).strftime(
            settings.TIMESTAMP_FORMAT
        )

        return MachineEvent(
            machine_id=self.config.machine_id,
            timestamp=timestamp,
            event_type=EventType.CYCLE_COMPLETE.value,
            status=self.state_machine.current_state.value,
            previous_status=None,
            cycle_count=self.cycle_count,
            shift=self.config.shift,
            operator_id=self.config.operator_id,
            reason=f"Cycle {self.cycle_count} completed"
        )

    def _generate_sensor_metrics(self, current_time: float) -> SensorMetric:
        """Gera métricas dos sensores baseadas no estado atual"""
        timestamp = datetime.fromtimestamp(current_time).strftime(
            settings.TIMESTAMP_FORMAT
        )

        state = self.state_machine.current_state

        # Ajusta métricas baseado no estado
        if state == MachineStatus.IDLE:
            temperature = self.base_temperature + random.uniform(-2, 2)
            vibration = random.uniform(0.1, 0.5)
            speed_rpm = 0
            pressure = random.uniform(0, 1)
            power = random.uniform(0.5, 2.0)

        elif state == MachineStatus.WARMUP:
            progress = self.state_machine.get_state_progress()
            temperature = self.base_temperature * (0.5 + 0.5 * progress) + random.uniform(-3, 3)
            vibration = 1.0 + progress * 1.5 + random.uniform(-0.3, 0.3)
            speed_rpm = int(self.config.rated_speed * progress * 0.5)
            pressure = self.base_pressure * (0.3 + 0.7 * progress)
            power = 5.0 + progress * 10

        elif state == MachineStatus.RUNNING:
            # Adiciona variação e efeito do desgaste
            # Temperatura aumenta com desgaste, mas não deve exceder limites
            temperature = (
                self.base_temperature * (1 + self.wear_factor * 0.2)
                + random.uniform(-5, 8)
            )
            vibration = (
                self.base_vibration * (1 + self.wear_factor * 0.5)
                + random.uniform(-0.5, 0.5)
            )
            # RPM fica próximo ao rated_speed (90-98%), nunca acima
            speed_rpm = int(
                self.config.rated_speed * random.uniform(0.90, 0.98)
            )
            pressure = self.base_pressure + random.uniform(-0.5, 0.5)
            power = 15.0 + random.uniform(-3, 5)

        elif state == MachineStatus.SETUP:
            temperature = self.base_temperature * 0.8 + random.uniform(-2, 2)
            vibration = random.uniform(0.5, 2.0)
            speed_rpm = int(self.config.rated_speed * random.uniform(0, 0.3))
            pressure = self.base_pressure * 0.5
            power = random.uniform(3, 8)

        elif state in [MachineStatus.PLANNED_DOWNTIME, MachineStatus.UNPLANNED_DOWNTIME]:
            temperature = self.base_temperature * 0.6 + random.uniform(-5, 0)
            vibration = random.uniform(0, 0.2)
            speed_rpm = 0
            pressure = random.uniform(0, 1)
            power = random.uniform(0.2, 1.0)

        elif state == MachineStatus.MAINTENANCE:
            temperature = 25.0 + random.uniform(-2, 2)
            vibration = random.uniform(0, 0.1)
            speed_rpm = 0
            pressure = 0
            power = random.uniform(0, 0.5)

        elif state == MachineStatus.COOLDOWN:
            progress = self.state_machine.get_state_progress()
            temperature = self.base_temperature * (1 - progress * 0.5) + random.uniform(-3, 3)
            vibration = (1 - progress) * 2.0 + random.uniform(0, 0.2)
            speed_rpm = int(self.config.rated_speed * (1 - progress) * 0.3)
            pressure = self.base_pressure * (1 - progress * 0.7)
            power = 5.0 * (1 - progress)

        else:  # default
            temperature = self.base_temperature
            vibration = self.base_vibration
            speed_rpm = 0
            pressure = 0
            power = 1.0

        return SensorMetric(
            machine_id=self.config.machine_id,
            timestamp=timestamp,
            temperature=round(temperature, 2),
            vibration=round(vibration, 2),
            speed_rpm=speed_rpm,
            pressure=round(pressure, 2),
            power_consumption=round(power, 2),
            operating_hours=round(self.operating_hours, 2)
        )

    def _inject_anomaly(
        self,
        sensor_metric: SensorMetric,
        current_time: float,
        elapsed: float
    ) -> SensorMetric:
        """
        Injeta anomalias nos dados dos sensores para treinamento de ML
        """
        # Verifica se deve iniciar uma nova anomalia
        if not self.anomaly_active:
            if random.random() < self.config.failure_injection_rate:
                self.anomaly_active = True
                self.anomaly_type = random.choice(settings.FAILURE_TYPES)
                self.anomaly_duration = random.uniform(30, 180)  # 30s a 3min
                print(f"\n[ANOMALY INJECTED] {self.config.machine_id}: {self.anomaly_type} for {self.anomaly_duration:.0f}s")

        # Se há anomalia ativa, modifica as métricas
        if self.anomaly_active:
            if self.anomaly_type == "temperature_spike":
                # Temperatura acima do limite
                sensor_metric.temperature = self.config.max_temperature * random.uniform(1.05, 1.25)

            elif self.anomaly_type == "vibration_anomaly":
                # Vibração anormal
                sensor_metric.vibration = self.config.max_vibration * random.uniform(1.1, 1.5)

            elif self.anomaly_type == "pressure_drop":
                # Queda de pressão
                sensor_metric.pressure = self.config.optimal_pressure * random.uniform(0.3, 0.6)

            elif self.anomaly_type == "speed_fluctuation":
                # RPM oscilando
                fluctuation = random.choice([-1, 1]) * random.randint(200, 500)
                sensor_metric.speed_rpm = max(0, sensor_metric.speed_rpm + fluctuation)

            elif self.anomaly_type == "power_surge":
                # Pico de consumo
                sensor_metric.power_consumption *= random.uniform(1.5, 2.5)

            # Decrementa duração da anomalia
            self.anomaly_duration -= elapsed
            if self.anomaly_duration <= 0:
                self.anomaly_active = False
                self.anomaly_type = None
                print(f"\n[ANOMALY ENDED] {self.config.machine_id}: Anomalia finalizada")

        return sensor_metric

    def _generate_quality_event(self, current_time: float) -> QualityEvent:
        """Gera evento de inspeção de qualidade"""
        timestamp = datetime.fromtimestamp(current_time).strftime(
            settings.TIMESTAMP_FORMAT
        )

        # Probabilidade de defeito aumenta com desgaste
        defect_probability = 0.05 + (self.wear_factor * 0.15)

        is_defective = random.random() < defect_probability

        if is_defective:
            result = QualityResult.NOK.value
            defect_type = random.choice(list(DefectType)).value
            defect_severity = random.randint(1, 5)
            self.bad_parts += 1
        else:
            result = QualityResult.OK.value
            defect_type = None
            defect_severity = None
            self.good_parts += 1

        return QualityEvent(
            machine_id=self.config.machine_id,
            timestamp=timestamp,
            cycle_count=self.cycle_count,
            result=result,
            defect_type=defect_type,
            defect_severity=defect_severity,
            inspector_id=f"inspector_{random.randint(1, 5)}",
            batch_id=f"batch_{int(current_time / 3600)}"  # batch por hora
        )

    def _check_random_transitions(self, current_time: float) -> Optional[MachineStatus]:
        """
        Verifica se deve fazer transições aleatórias quando em RUNNING
        Simula eventos como paradas planejadas, falhas, setup, etc.
        """
        # Falha não planejada (aumenta com desgaste)
        failure_prob = settings.UNPLANNED_FAILURE_BASE_PROBABILTY * (1 + self.wear_factor * 3)
        if random.random() < failure_prob:
            if self.state_machine.transition_to(MachineStatus.UNPLANNED_DOWNTIME, current_time):
                return MachineStatus.UNPLANNED_DOWNTIME

        # Parada planejada (almoço, coffee break, etc)
        if random.random() < settings.PLANNED_DOWNTIME_PROBABILTY:
            if self.state_machine.transition_to(MachineStatus.PLANNED_DOWNTIME, current_time):
                return MachineStatus.PLANNED_DOWNTIME

        # Setup/troca de ferramentas (5% de chance)
        if random.random() < 0.05:
            if self.state_machine.transition_to(MachineStatus.SETUP, current_time):
                return MachineStatus.SETUP

        return None

    def _update_wear(self):
        """Atualiza fator de desgaste baseado em horas de operação"""
        # Aumenta desgaste gradualmente até próxima manutenção
        hours_since_maintenance = self.operating_hours
        self.wear_factor = min(
            1.0,
            hours_since_maintenance / settings.MAINTENANCE_INTERVAL_HOURS
        )

    def _check_maintenance_need(self, current_time: float):
        """Verifica se máquina precisa de manutenção"""
        if self.wear_factor >= 0.95:
            # Força transição para manutenção se possível
            if self.state_machine.can_transition_to(MachineStatus.MAINTENANCE):
                if self.state_machine.current_state == MachineStatus.RUNNING:
                    # Primeiro cooldown, depois manutenção
                    self.state_machine.transition_to(
                        MachineStatus.COOLDOWN, current_time
                    )

    def perform_maintenance(self, current_time: float):
        """Executa manutenção e reseta desgaste"""
        self.wear_factor = 0.0
        self.operating_hours = 0.0
        self.last_maintenance = current_time

        if self.state_machine.current_state != MachineStatus.MAINTENANCE:
            self.state_machine.transition_to(MachineStatus.MAINTENANCE, current_time)

    def _get_state_change_reason(
        self,
        new_state: MachineStatus,
        previous_state: MachineStatus
    ) -> Optional[str]:
        """Determina motivo da mudança de estado"""
        reasons = {
            (MachineStatus.IDLE, MachineStatus.WARMUP): "Starting production shift",
            (MachineStatus.WARMUP, MachineStatus.RUNNING): "Machine ready for production",
            (MachineStatus.RUNNING, MachineStatus.SETUP): "Tool change required",
            (MachineStatus.RUNNING, MachineStatus.PLANNED_DOWNTIME): "Scheduled break",
            (MachineStatus.RUNNING, MachineStatus.UNPLANNED_DOWNTIME): "Unexpected failure",
            (MachineStatus.RUNNING, MachineStatus.MAINTENANCE): "Preventive maintenance",
            (MachineStatus.RUNNING, MachineStatus.COOLDOWN): "End of shift",
            (MachineStatus.SETUP, MachineStatus.RUNNING): "Setup completed",
            (MachineStatus.PLANNED_DOWNTIME, MachineStatus.WARMUP): "Resuming production",
            (MachineStatus.UNPLANNED_DOWNTIME, MachineStatus.MAINTENANCE): "Repair needed",
            (MachineStatus.UNPLANNED_DOWNTIME, MachineStatus.WARMUP): "Issue resolved",
            (MachineStatus.MAINTENANCE, MachineStatus.WARMUP): "Maintenance completed",
            (MachineStatus.COOLDOWN, MachineStatus.IDLE): "Machine stopped",
        }

        return reasons.get((previous_state, new_state), f"Transition from {previous_state.value} to {new_state.value}")

    def get_current_state(self) -> MachineStatus:
        """Retorna estado atual da máquina"""
        return self.state_machine.current_state

    def get_statistics(self) -> dict:
        """Retorna estatísticas da máquina"""
        total_inspected = self.good_parts + self.bad_parts
        quality_rate = (
            (self.good_parts / total_inspected * 100)
            if total_inspected > 0 else 100.0
        )

        return {
            "machine_id": self.config.machine_id,
            "current_state": self.state_machine.current_state.value,
            "total_cycles": self.total_cycles,
            "good_parts": self.good_parts,
            "bad_parts": self.bad_parts,
            "quality_rate": round(quality_rate, 2),
            "operating_hours": round(self.operating_hours, 2),
            "wear_factor": round(self.wear_factor * 100, 2)
        }
