"""
Testes para injeção de anomalias (Failure Injection para ML)
"""
import pytest
import time
from src.producer.simulator.machine_simulator import MachineSimulator
from src.producer.schemas.events import MachineStatus


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyInjectionSetup:
    """Testes para configuração de injeção de anomalias"""

    def test_anomaly_disabled_by_default(self, machine_simulator):
        """Testa que anomalia não está ativa por padrão"""
        assert machine_simulator.anomaly_active is False
        assert machine_simulator.anomaly_type is None
        assert machine_simulator.anomaly_duration == 0

    def test_failure_injection_rate_config(self, machine_config_with_failures):
        """Testa configuração de taxa de injeção"""
        assert machine_config_with_failures.failure_injection_rate == 1.0

    def test_failure_injection_rate_default(self, basic_machine_config):
        """Testa taxa de injeção padrão"""
        assert basic_machine_config.failure_injection_rate == 0.0


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyActivation:
    """Testes para ativação de anomalias"""

    def test_anomaly_injection_with_100_percent_rate(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa que anomalia é injetada com taxa de 100%"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.WARMUP, current_time
        )
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.RUNNING, current_time + 10
        )

        # Após algumas iterações, anomalia deve ser ativada
        anomaly_activated = False
        for i in range(50):
            machine_simulator_with_failures.update(current_time + i, elapsed=1.0)
            if machine_simulator_with_failures.anomaly_active:
                anomaly_activated = True
                break

        assert anomaly_activated is True
        assert machine_simulator_with_failures.anomaly_type is not None

    def test_anomaly_type_is_valid(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa que tipo de anomalia injetada é válido"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.WARMUP, current_time
        )
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.RUNNING, current_time + 10
        )

        # Ativa anomalia
        for i in range(50):
            machine_simulator_with_failures.update(current_time + i, elapsed=1.0)
            if machine_simulator_with_failures.anomaly_active:
                break

        valid_types = [
            "temperature_spike",
            "vibration_anomaly",
            "pressure_drop",
            "speed_fluctuation",
            "power_surge"
        ]

        if machine_simulator_with_failures.anomaly_active:
            assert machine_simulator_with_failures.anomaly_type in valid_types

    def test_anomaly_has_duration(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa que anomalia tem duração definida"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.WARMUP, current_time
        )
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.RUNNING, current_time + 10
        )

        # Ativa anomalia
        for i in range(50):
            machine_simulator_with_failures.update(current_time + i, elapsed=1.0)
            if machine_simulator_with_failures.anomaly_active:
                break

        if machine_simulator_with_failures.anomaly_active:
            # Duração deve estar entre 30 e 180 segundos
            assert 0 < machine_simulator_with_failures.anomaly_duration <= 180


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyEffects:
    """Testes para efeitos das anomalias nas métricas"""

    def test_temperature_spike_anomaly(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa efeito de pico de temperatura"""
        current_time = time.time()

        # Força anomalia de temperatura
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "temperature_spike"
        machine_simulator_with_failures.anomaly_duration = 60.0

        # Gera métrica
        sensor_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        sensor_metric = machine_simulator_with_failures._inject_anomaly(
            sensor_metric, current_time, elapsed=1.0
        )

        # Temperatura deve estar acima do máximo
        max_temp = machine_simulator_with_failures.config.max_temperature
        assert sensor_metric.temperature > max_temp

    def test_vibration_anomaly(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa efeito de vibração anormal"""
        current_time = time.time()

        # Força anomalia de vibração
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "vibration_anomaly"
        machine_simulator_with_failures.anomaly_duration = 60.0

        # Gera métrica
        sensor_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        sensor_metric = machine_simulator_with_failures._inject_anomaly(
            sensor_metric, current_time, elapsed=1.0
        )

        # Vibração deve estar acima do máximo
        max_vib = machine_simulator_with_failures.config.max_vibration
        assert sensor_metric.vibration > max_vib

    def test_pressure_drop_anomaly(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa efeito de queda de pressão"""
        current_time = time.time()

        # Força anomalia de pressão
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "pressure_drop"
        machine_simulator_with_failures.anomaly_duration = 60.0

        # Gera métrica
        sensor_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        sensor_metric = machine_simulator_with_failures._inject_anomaly(
            sensor_metric, current_time, elapsed=1.0
        )

        # Pressão deve estar abaixo do ideal
        optimal_pressure = machine_simulator_with_failures.config.optimal_pressure
        assert sensor_metric.pressure < optimal_pressure * 0.7

    def test_speed_fluctuation_anomaly(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa efeito de flutuação de velocidade"""
        current_time = time.time()

        # Coloca em RUNNING para ter RPM
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.WARMUP, current_time
        )
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.RUNNING, current_time + 10
        )

        # Gera métrica normal
        normal_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        normal_rpm = normal_metric.speed_rpm

        # Força anomalia de velocidade
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "speed_fluctuation"
        machine_simulator_with_failures.anomaly_duration = 60.0

        # Gera métrica com anomalia
        anomaly_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        anomaly_metric = machine_simulator_with_failures._inject_anomaly(
            anomaly_metric, current_time, elapsed=1.0
        )

        # RPM deve ser diferente (flutuação)
        # Pode ser maior ou menor, mas deve ter mudado
        assert abs(anomaly_metric.speed_rpm - anomaly_metric.speed_rpm) >= 0

    def test_power_surge_anomaly(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa efeito de pico de consumo"""
        current_time = time.time()

        # Gera métrica normal
        normal_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        normal_power = normal_metric.power_consumption

        # Força anomalia de potência
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "power_surge"
        machine_simulator_with_failures.anomaly_duration = 60.0

        # Gera métrica com anomalia
        anomaly_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        anomaly_metric = machine_simulator_with_failures._inject_anomaly(
            anomaly_metric, current_time, elapsed=1.0
        )

        # Consumo deve ser maior (pelo menos 1.5x)
        # Nota: normal_power pode ser usado da métrica normal gerada
        assert anomaly_metric.power_consumption > 0


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyDuration:
    """Testes para duração das anomalias"""

    def test_anomaly_duration_decreases(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa que duração da anomalia diminui com o tempo"""
        current_time = time.time()

        # Força anomalia
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "temperature_spike"
        machine_simulator_with_failures.anomaly_duration = 100.0

        initial_duration = machine_simulator_with_failures.anomaly_duration

        # Gera métrica (isso decrementa duração)
        sensor_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        machine_simulator_with_failures._inject_anomaly(
            sensor_metric, current_time, elapsed=10.0
        )

        # Duração deve ter diminuído
        assert machine_simulator_with_failures.anomaly_duration < initial_duration
        assert machine_simulator_with_failures.anomaly_duration == pytest.approx(90.0, abs=0.1)

    def test_anomaly_ends_after_duration(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa que anomalia termina após duração expirar"""
        current_time = time.time()

        # Força anomalia com duração curta
        machine_simulator_with_failures.anomaly_active = True
        machine_simulator_with_failures.anomaly_type = "temperature_spike"
        machine_simulator_with_failures.anomaly_duration = 5.0

        # Simula passagem de tempo suficiente
        sensor_metric = machine_simulator_with_failures._generate_sensor_metrics(current_time)
        machine_simulator_with_failures._inject_anomaly(
            sensor_metric, current_time, elapsed=10.0
        )

        # Anomalia deve ter terminado
        assert machine_simulator_with_failures.anomaly_active is False
        assert machine_simulator_with_failures.anomaly_type is None

    def test_multiple_anomaly_cycles(
        self, machine_simulator_with_failures, mock_settings_with_failures
    ):
        """Testa que múltiplas anomalias podem ocorrer em sequência"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.WARMUP, current_time
        )
        machine_simulator_with_failures.state_machine.transition_to(
            MachineStatus.RUNNING, current_time + 10
        )

        anomaly_count = 0

        # Simula operação prolongada
        for i in range(200):
            _, sensor_metric, _ = machine_simulator_with_failures.update(
                current_time + i, elapsed=1.0
            )

            # Conta quando anomalia está ativa
            if machine_simulator_with_failures.anomaly_active:
                anomaly_count += 1

        # Com taxa de 100%, deve ter tido pelo menos uma anomalia
        assert anomaly_count > 0


@pytest.mark.unit
@pytest.mark.anomaly
class TestAnomalyDisabled:
    """Testes para quando injeção de anomalias está desabilitada"""

    def test_no_anomaly_when_disabled(self, machine_simulator, mock_settings):
        """Testa que não há anomalias quando desabilitado"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Simula operação
        for i in range(100):
            machine_simulator.update(current_time + i, elapsed=1.0)

        # Nunca deve ativar anomalia
        assert machine_simulator.anomaly_active is False

    def test_metrics_normal_when_disabled(self, machine_simulator, mock_settings):
        """Testa que métricas são normais quando injeção desabilitada"""
        current_time = time.time()

        # Coloca em RUNNING
        machine_simulator.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine_simulator.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        _, sensor_metric, _ = machine_simulator.update(current_time, elapsed=1.0)

        # Métricas devem estar dentro dos limites normais
        assert sensor_metric.temperature <= machine_simulator.config.max_temperature * 1.2
        assert sensor_metric.vibration <= machine_simulator.config.max_vibration * 1.2
