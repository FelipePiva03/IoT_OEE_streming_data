"""
Fixtures compartilhadas para os testes
"""
import pytest
import time
from src.producer.simulator.machine_simulator import MachineSimulator, MachineConfig
from src.producer.simulator.state_machine import StateMachine
from src.producer.schemas.events import MachineStatus


@pytest.fixture
def basic_machine_config():
    """Configuração básica de máquina para testes"""
    return MachineConfig(
        machine_id="TEST_001",
        machine_type="TEST_CNC",
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
        failure_injection_rate=0.0  # Desabilitado para testes unitários
    )


@pytest.fixture
def machine_config_with_failures():
    """Configuração de máquina com injeção de falhas habilitada"""
    return MachineConfig(
        machine_id="TEST_002",
        machine_type="TEST_CNC",
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
        failure_injection_rate=1.0  # 100% para testes garantidos
    )


@pytest.fixture
def machine_simulator(basic_machine_config):
    """Instância básica de MachineSimulator"""
    return MachineSimulator(basic_machine_config)


@pytest.fixture
def machine_simulator_with_failures(machine_config_with_failures):
    """Instância de MachineSimulator com falhas habilitadas"""
    return MachineSimulator(machine_config_with_failures)


@pytest.fixture
def state_machine():
    """Instância de StateMachine em estado IDLE"""
    return StateMachine(initial_state=MachineStatus.IDLE)


@pytest.fixture
def current_time():
    """Timestamp atual para testes"""
    return time.time()


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock das configurações para testes"""
    from src.producer.config.settings import settings

    # Desabilita injeção de falhas por padrão
    monkeypatch.setattr(settings, 'ENABLE_FAILURE_INJECTION', False)
    monkeypatch.setattr(settings, 'SIMULATION_SPEED', 1.0)
    monkeypatch.setattr(settings, 'TIME_MULTIPLIER', 1.0)

    return settings


@pytest.fixture
def mock_settings_with_failures(monkeypatch):
    """Mock das configurações com falhas habilitadas"""
    from src.producer.config.settings import settings

    monkeypatch.setattr(settings, 'ENABLE_FAILURE_INJECTION', True)
    monkeypatch.setattr(settings, 'SIMULATION_SPEED', 1.0)
    monkeypatch.setattr(settings, 'TIME_MULTIPLIER', 1.0)

    return settings
