"""
Testes para o sistema de injeção de anomalias para ML
"""
import time
import random
import pytest
from unittest.mock import patch, MagicMock

from src.producer.simulator.machine_simulator import MachineSimulator, MachineConfig
from src.producer.schemas.events import (
    MachineStatus,
    AnomalyType,
    AnomalySeverity,
    AnomalyEvent,
    ANOMALY_PROFILES
)


@pytest.fixture
def machine_config():
    """Configuração padrão de máquina para testes"""
    return MachineConfig(
        machine_id="TEST_001",
        machine_type="CNC_MILL",
        rated_speed=3000,
        cycle_time=10.0,
        operator_id="operator_test",
        shift="day",
        max_temperature=85.0,
        optimal_temperature=65.0,
        max_vibration=5.0,
        optimal_vibration=1.5,
        max_pressure=8.0,
        optimal_pressure=6.5,
        failure_injection_rate=0.0  # Desabilitado por padrão
    )


@pytest.fixture
def machine_config_with_failures():
    """Configuração com injeção de falhas ativada"""
    return MachineConfig(
        machine_id="TEST_002",
        machine_type="CNC_LATHE",
        rated_speed=2500,
        cycle_time=8.0,
        operator_id="operator_test",
        shift="day",
        failure_injection_rate=1.0  # 100% de chance para testes
    )


@pytest.fixture
def machine_simulator(machine_config):
    """Simulador sem injeção de falhas"""
    return MachineSimulator(machine_config)


@pytest.fixture
def machine_simulator_with_failures(machine_config_with_failures):
    """Simulador com injeção de falhas"""
    return MachineSimulator(machine_config_with_failures)


@pytest.fixture
def mock_settings():
    """Mock das configurações"""
    with patch('src.producer.simulator.machine_simulator.settings') as mock:
        mock.ENABLE_FAILURE_INJECTION = True
        mock.TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
        mock.QUALITY_CHECK_PROBABILTY = 0.0
        mock.PLANNED_DOWNTIME_PROBABILTY = 0.0
        mock.UNPLANNED_FAILURE_BASE_PROBABILTY = 0.0
        mock.MAINTENANCE_INTERVAL_HOURS = 168
        yield mock


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyProfiles:
    """Testes para os perfis de anomalias"""

    def test_all_anomaly_types_have_profiles(self):
        """Verifica que todos os tipos de anomalia têm perfis definidos"""
        for anomaly_type in AnomalyType:
            assert anomaly_type in ANOMALY_PROFILES, f"Missing profile for {anomaly_type}"

    def test_profiles_have_required_fields(self):
        """Verifica que todos os perfis têm os campos necessários"""
        required_fields = [
            "severity_range",
            "duration_range",
            "multiplier_range",
            "leads_to_failure",
            "precursor_pattern"
        ]

        for anomaly_type, profile in ANOMALY_PROFILES.items():
            for field in required_fields:
                assert field in profile, f"Missing {field} in {anomaly_type} profile"

    def test_severity_ranges_are_valid(self):
        """Verifica que os ranges de severidade são válidos"""
        for anomaly_type, profile in ANOMALY_PROFILES.items():
            low, high = profile["severity_range"]
            assert isinstance(low, AnomalySeverity)
            assert isinstance(high, AnomalySeverity)


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyInjectionSetup:
    """Testes de configuração da injeção de anomalias"""

    def test_anomaly_disabled_by_default(self, machine_simulator):
        """Testa que anomalia está desabilitada por padrão"""
        assert machine_simulator.anomaly_active is False
        assert machine_simulator.anomaly_type is None
        assert machine_simulator.anomaly_severity is None

    def test_failure_injection_rate_config(self, machine_config_with_failures):
        """Testa configuração de taxa de injeção"""
        assert machine_config_with_failures.failure_injection_rate == 1.0

    def test_failure_injection_rate_default(self, machine_config):
        """Testa valor padrão da taxa de injeção"""
        assert machine_config.failure_injection_rate == 0.0


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyActivation:
    """Testes de ativação de anomalias"""

    def test_anomaly_activation_with_high_rate(self, machine_simulator_with_failures, mock_settings):
        """Testa que anomalia é ativada com taxa alta"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Atualiza até ativar anomalia
        for i in range(10):
            machine_simulator_with_failures.update(current_time + i, elapsed=1.0)
            if machine_simulator_with_failures.anomaly_active:
                break

        assert machine_simulator_with_failures.anomaly_active is True

    def test_anomaly_type_is_valid_enum(self, machine_simulator_with_failures, mock_settings):
        """Testa que tipo de anomalia é um enum válido"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Atualiza até ativar anomalia
        for i in range(10):
            machine_simulator_with_failures.update(current_time + i, elapsed=1.0)
            if machine_simulator_with_failures.anomaly_active:
                break

        assert machine_simulator_with_failures.anomaly_type in list(AnomalyType)

    def test_anomaly_severity_is_valid_enum(self, machine_simulator_with_failures, mock_settings):
        """Testa que severidade é um enum válido"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Atualiza até ativar anomalia
        for i in range(10):
            machine_simulator_with_failures.update(current_time + i, elapsed=1.0)
            if machine_simulator_with_failures.anomaly_active:
                break

        assert machine_simulator_with_failures.anomaly_severity in list(AnomalySeverity)


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyEvent:
    """Testes para eventos de anomalia"""

    def test_anomaly_event_creation(self):
        """Testa criação de evento de anomalia"""
        event = AnomalyEvent(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            anomaly_type=AnomalyType.TEMPERATURE_SPIKE.value,
            severity=AnomalySeverity.HIGH.value,
            duration_seconds=120.0,
            is_precursor=False,
            temperature=95.0,
            vibration=3.5,
            pressure=6.0,
            speed_rpm=2500,
            power_consumption=18.0,
            operating_hours=50.0,
            wear_factor=0.3
        )

        assert event.machine_id == "test_machine"
        assert event.anomaly_type == "temperature_spike"
        assert event.severity == "high"

    def test_anomaly_event_to_dict(self):
        """Testa conversão para dicionário"""
        event = AnomalyEvent(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            anomaly_type=AnomalyType.VIBRATION_SPIKE.value,
            severity=AnomalySeverity.MEDIUM.value
        )

        data = event.to_dict()
        assert isinstance(data, dict)
        assert data["machine_id"] == "test_machine"
        assert data["anomaly_type"] == "vibration_spike"


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyEffects:
    """Testes dos efeitos das anomalias nos sensores"""

    def test_anomaly_affects_sensor_values(self, machine_simulator_with_failures, mock_settings):
        """Testa que anomalia afeta valores dos sensores"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator_with_failures.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Coleta métricas normais primeiro
        _, normal_metric, _, _ = machine_simulator_with_failures.update(current_time, elapsed=1.0)

        # Força ativação de anomalia específica
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = AnomalyType.TEMPERATURE_SPIKE
        machine_simulator_with_failures.anomaly_severity = AnomalySeverity.HIGH
        machine_simulator_with_failures.anomaly_duration = 100
        machine_simulator_with_failures.anomaly_start_time = current_time
        machine_simulator_with_failures.anomaly_is_precursor = False
        machine_simulator_with_failures.anomaly_base_values = {
            "temperature": normal_metric.temperature,
            "vibration": normal_metric.vibration,
            "pressure": normal_metric.pressure,
            "speed_rpm": normal_metric.speed_rpm,
            "power_consumption": normal_metric.power_consumption,
        }

        # Coleta métricas com anomalia
        _, anomaly_metric, _, _ = machine_simulator_with_failures.update(current_time + 1, elapsed=1.0)

        # Temperatura deve ser elevada durante anomalia de temperatura
        assert anomaly_metric.temperature > machine_simulator_with_failures.config.optimal_temperature


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyDisabled:
    """Testes quando injeção está desabilitada"""

    def test_no_anomaly_when_disabled(self, machine_simulator, mock_settings):
        """Testa que não há anomalia quando desabilitado"""
        mock_settings.ENABLE_FAILURE_INJECTION = False
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Atualiza várias vezes
        for i in range(50):
            machine_simulator.update(current_time + i, elapsed=1.0)

        # Anomalia nunca deve ativar
        assert machine_simulator.anomaly_active is False

    def test_metrics_normal_when_disabled(self, machine_simulator, mock_settings):
        """Testa que métricas são normais quando desabilitado"""
        mock_settings.ENABLE_FAILURE_INJECTION = False
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        _, sensor_metric, _, _ = machine_simulator.update(current_time, elapsed=1.0)

        # Métricas devem estar dentro dos limites normais
        assert sensor_metric.temperature <= machine_simulator.config.max_temperature * 1.2
        assert sensor_metric.vibration <= machine_simulator.config.max_vibration * 1.2


@pytest.mark.unit
@pytest.mark.anomaly
class TestPrecursorPatterns:
    """Testes para padrões precursores de falhas"""

    def test_precursor_anomalies_exist(self):
        """Verifica que existem anomalias precursoras"""
        precursor_types = [
            anomaly_type for anomaly_type, profile in ANOMALY_PROFILES.items()
            if profile["precursor_pattern"]
        ]
        assert len(precursor_types) > 0

    def test_precursor_anomalies_have_longer_duration(self):
        """Verifica que anomalias precursoras tendem a ter durações mais longas"""
        precursor_durations = []
        non_precursor_durations = []

        for anomaly_type, profile in ANOMALY_PROFILES.items():
            avg_duration = sum(profile["duration_range"]) / 2
            if profile["precursor_pattern"]:
                precursor_durations.append(avg_duration)
            else:
                non_precursor_durations.append(avg_duration)

        # Em média, precursores devem ter durações maiores
        avg_precursor = sum(precursor_durations) / len(precursor_durations)
        avg_non_precursor = sum(non_precursor_durations) / len(non_precursor_durations)

        assert avg_precursor > avg_non_precursor


@pytest.mark.unit
@pytest.mark.anomaly
class TestFailureProbability:
    """Testes para probabilidade de falhas"""

    def test_all_anomalies_have_failure_probability(self):
        """Verifica que todas anomalias têm probabilidade de falha"""
        for anomaly_type, profile in ANOMALY_PROFILES.items():
            assert 0 <= profile["leads_to_failure"] <= 1

    def test_critical_anomalies_have_higher_failure_rate(self):
        """Verifica que anomalias críticas têm maior probabilidade de falha"""
        critical_rates = []
        non_critical_rates = []

        for anomaly_type, profile in ANOMALY_PROFILES.items():
            _, high_severity = profile["severity_range"]
            if high_severity == AnomalySeverity.CRITICAL:
                critical_rates.append(profile["leads_to_failure"])
            else:
                non_critical_rates.append(profile["leads_to_failure"])

        if critical_rates and non_critical_rates:
            avg_critical = sum(critical_rates) / len(critical_rates)
            avg_non_critical = sum(non_critical_rates) / len(non_critical_rates)
            # Anomalias críticas devem ter maior probabilidade de falha
            assert avg_critical >= avg_non_critical
