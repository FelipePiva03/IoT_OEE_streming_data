"""
Testes para os schemas de eventos
"""
import pytest
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


@pytest.mark.unit
class TestEnums:
    """Testes para os Enums"""

    def test_machine_status_values(self):
        """Testa valores do enum MachineStatus"""
        assert MachineStatus.IDLE.value == "idle"
        assert MachineStatus.RUNNING.value == "running"
        assert MachineStatus.MAINTENANCE.value == "maintance"

    def test_event_type_values(self):
        """Testa valores do enum EventType"""
        assert EventType.STATUS_CHANGE.value == "status_change"
        assert EventType.CYCLE_COMPLETE.value == "cycle_complete"
        assert EventType.ALERT.value == "alert"

    def test_quality_result_values(self):
        """Testa valores do enum QualityResult"""
        assert QualityResult.OK.value == "ok"
        assert QualityResult.NOK.value == "nok"

    def test_defect_type_values(self):
        """Testa valores do enum DefectType"""
        assert DefectType.DIMENSIONAL.value == "dimensional"
        assert DefectType.SURFACE.value == "surface"
        assert DefectType.MATERIAL.value == "material"
        assert DefectType.ASSEMBLY.value == "assembly"


@pytest.mark.unit
class TestMachineEvent:
    """Testes para MachineEvent"""

    def test_create_machine_event(self):
        """Testa criação de evento de máquina"""
        event = MachineEvent(
            machine_id="M001",
            timestamp="2024-01-01T10:00:00.000Z",
            event_type=EventType.STATUS_CHANGE.value,
            status=MachineStatus.RUNNING.value,
            previous_status=MachineStatus.WARMUP.value,
            cycle_count=10,
            shift="day",
            operator_id="OP001",
            reason="Machine ready for production"
        )

        assert event.machine_id == "M001"
        assert event.event_type == "status_change"
        assert event.status == "running"
        assert event.previous_status == "warmup"
        assert event.cycle_count == 10

    def test_machine_event_to_dict(self):
        """Testa conversão de evento para dict"""
        event = MachineEvent(
            machine_id="M001",
            timestamp="2024-01-01T10:00:00.000Z"
        )

        event_dict = event.to_dict()

        assert isinstance(event_dict, dict)
        assert "event_id" in event_dict
        assert "machine_id" in event_dict
        assert event_dict["machine_id"] == "M001"

    def test_machine_event_default_values(self):
        """Testa valores padrão de MachineEvent"""
        event = MachineEvent()

        assert event.machine_id == ""
        assert event.timestamp == ""
        assert event.event_type == "status_change"
        assert event.status == "idle"
        assert event.cycle_count == 0
        assert event.shift == "day"

    def test_machine_event_id_generation(self):
        """Testa que cada evento gera um ID único"""
        event1 = MachineEvent()
        event2 = MachineEvent()

        assert event1.event_id != event2.event_id
        assert event1.event_id.startswith("evt-")
        assert len(event1.event_id) == 16  # "evt-" + 12 caracteres


@pytest.mark.unit
class TestSensorMetric:
    """Testes para SensorMetric"""

    def test_create_sensor_metric(self):
        """Testa criação de métrica de sensor"""
        metric = SensorMetric(
            machine_id="M001",
            timestamp="2024-01-01T10:00:00.000Z",
            temperature=65.5,
            vibration=2.3,
            speed_rpm=3000,
            pressure=6.5,
            power_consumption=15.2,
            operating_hours=120.5
        )

        assert metric.machine_id == "M001"
        assert metric.temperature == 65.5
        assert metric.vibration == 2.3
        assert metric.speed_rpm == 3000
        assert metric.pressure == 6.5
        assert metric.power_consumption == 15.2
        assert metric.operating_hours == 120.5

    def test_sensor_metric_to_dict(self):
        """Testa conversão de métrica para dict"""
        metric = SensorMetric(
            machine_id="M001",
            temperature=70.0
        )

        metric_dict = metric.to_dict()

        assert isinstance(metric_dict, dict)
        assert "metric_id" in metric_dict
        assert "temperature" in metric_dict
        assert metric_dict["temperature"] == 70.0

    def test_sensor_metric_default_values(self):
        """Testa valores padrão de SensorMetric"""
        metric = SensorMetric()

        assert metric.machine_id == ""
        assert metric.temperature == 0.0
        assert metric.vibration == 0.0
        assert metric.speed_rpm == 0
        assert metric.pressure == 0.0
        assert metric.power_consumption == 0.0
        assert metric.operating_hours == 0.0

    def test_sensor_metric_id_generation(self):
        """Testa que cada métrica gera um ID único"""
        metric1 = SensorMetric()
        metric2 = SensorMetric()

        assert metric1.metric_id != metric2.metric_id
        assert metric1.metric_id.startswith("met_")


@pytest.mark.unit
class TestQualityEvent:
    """Testes para QualityEvent"""

    def test_create_quality_event_ok(self):
        """Testa criação de evento de qualidade OK"""
        event = QualityEvent(
            machine_id="M001",
            timestamp="2024-01-01T10:00:00.000Z",
            cycle_count=15,
            result=QualityResult.OK.value,
            inspector_id="INS001",
            batch_id="B12345"
        )

        assert event.machine_id == "M001"
        assert event.result == "ok"
        assert event.defect_type is None
        assert event.defect_severity is None
        assert event.inspector_id == "INS001"

    def test_create_quality_event_nok(self):
        """Testa criação de evento de qualidade NOK"""
        event = QualityEvent(
            machine_id="M001",
            timestamp="2024-01-01T10:00:00.000Z",
            cycle_count=15,
            result=QualityResult.NOK.value,
            defect_type=DefectType.DIMENSIONAL.value,
            defect_severity=3,
            inspector_id="INS001",
            batch_id="B12345"
        )

        assert event.result == "nok"
        assert event.defect_type == "dimensional"
        assert event.defect_severity == 3

    def test_quality_event_to_dict(self):
        """Testa conversão de evento de qualidade para dict"""
        event = QualityEvent(
            machine_id="M001",
            result=QualityResult.OK.value
        )

        event_dict = event.to_dict()

        assert isinstance(event_dict, dict)
        assert "inspection_id" in event_dict
        assert "result" in event_dict
        assert event_dict["result"] == "ok"

    def test_quality_event_default_values(self):
        """Testa valores padrão de QualityEvent"""
        event = QualityEvent()

        assert event.machine_id == ""
        assert event.timestamp == ""
        assert event.cycle_count == 0
        assert event.result == "ok"
        assert event.defect_type is None
        assert event.defect_severity is None

    def test_quality_event_id_generation(self):
        """Testa que cada evento gera um ID único"""
        event1 = QualityEvent()
        event2 = QualityEvent()

        assert event1.inspection_id != event2.inspection_id
        assert event1.inspection_id.startswith("qlt_")
