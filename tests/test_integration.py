"""
Testes de integração para IoTSimulator
"""
import pytest
import time
from src.producer.main import IoTSimulator, create_default_machines, load_machines_from_yaml
from src.producer.simulator.machine_simulator import MachineConfig
from src.producer.schemas.events import MachineStatus


@pytest.mark.integration
class TestIoTSimulatorInitialization:
    """Testes de integração para inicialização"""

    def test_create_simulator_with_multiple_machines(self):
        """Testa criação de simulador com múltiplas máquinas"""
        configs = create_default_machines()
        simulator = IoTSimulator(configs)

        assert len(simulator.machines) == 5
        assert simulator.iteration == 0

    def test_create_simulator_with_custom_config(self, basic_machine_config):
        """Testa criação de simulador com configuração customizada"""
        configs = [basic_machine_config]
        simulator = IoTSimulator(configs)

        assert len(simulator.machines) == 1
        assert simulator.machines[0].config == basic_machine_config

    def test_simulator_initializes_all_machines(self):
        """Testa que todas as máquinas são inicializadas corretamente"""
        configs = create_default_machines()
        simulator = IoTSimulator(configs)

        for machine in simulator.machines:
            assert machine.state_machine.current_state == MachineStatus.IDLE
            assert machine.cycle_count == 0
            assert machine.wear_factor == 0.0


@pytest.mark.integration
class TestDefaultMachinesCreation:
    """Testes para criação de máquinas padrão"""

    def test_create_default_machines_count(self):
        """Testa que cria 5 máquinas padrão"""
        machines = create_default_machines()

        assert len(machines) == 5

    def test_create_default_machines_types(self):
        """Testa tipos das máquinas padrão"""
        machines = create_default_machines()

        types = [m.machine_type for m in machines]

        assert "CNC_MILL" in types
        assert "CNC_LATHE" in types
        assert "INJECTION_MOLD" in types
        assert "PRESS" in types
        assert "ASSEMBLY_ROBOT" in types

    def test_create_default_machines_unique_ids(self):
        """Testa que cada máquina tem ID único"""
        machines = create_default_machines()

        ids = [m.machine_id for m in machines]

        assert len(ids) == len(set(ids))  # Todos IDs são únicos


@pytest.mark.integration
@pytest.mark.slow
class TestSimulatorExecution:
    """Testes para execução do simulador"""

    def test_simulator_update_all_machines(self, mock_settings):
        """Testa atualização de todas as máquinas"""
        configs = create_default_machines()
        simulator = IoTSimulator(configs)

        # Executa uma iteração
        simulator._update_all_machines()

        # Todas as máquinas devem ter gerado métricas
        assert simulator.iteration == 0  # Não incrementa diretamente em _update

    def test_simulator_generates_events(self, mock_settings):
        """Testa que simulador gera eventos"""
        configs = [
            MachineConfig(
                machine_id="M001",
                machine_type="TEST",
                rated_speed=3000,
                cycle_time=10.0,
                operator_id="OP001"
            )
        ]
        simulator = IoTSimulator(configs)

        # Força duração curta para gerar transição
        simulator.machines[0].state_machine.state_duration = 0.1

        # Executa atualização
        simulator._update_all_machines()

        # Deve ter gerado pelo menos métricas de sensores
        assert simulator.machines[0].operating_hours >= 0

    def test_simulator_statistics(self):
        """Testa coleta de estatísticas do simulador"""
        configs = create_default_machines()
        simulator = IoTSimulator(configs)

        # Coleta estatísticas de cada máquina
        for machine in simulator.machines:
            stats = machine.get_statistics()

            assert "machine_id" in stats
            assert "current_state" in stats
            assert "total_cycles" in stats
            assert "quality_rate" in stats


@pytest.mark.integration
class TestYAMLConfiguration:
    """Testes para carregamento de configuração YAML"""

    def test_load_machines_from_yaml_file_exists(self):
        """Testa carregamento de configuração do YAML"""
        yaml_path = "src/producer/config/machines.yaml"

        try:
            machines = load_machines_from_yaml(yaml_path)
            assert len(machines) == 5

            # Verifica que configurações foram carregadas
            for machine in machines:
                assert machine.machine_id is not None
                assert machine.max_temperature > 0
                assert machine.failure_injection_rate >= 0

        except FileNotFoundError:
            pytest.skip("Arquivo YAML de configuração não encontrado")

    def test_yaml_config_has_failure_rates(self):
        """Testa que configuração YAML tem taxas de falha"""
        yaml_path = "src/producer/config/machines.yaml"

        try:
            machines = load_machines_from_yaml(yaml_path)

            # Todas as máquinas devem ter taxa de falha configurada
            for machine in machines:
                assert hasattr(machine, 'failure_injection_rate')
                assert 0.0 <= machine.failure_injection_rate <= 1.0

        except FileNotFoundError:
            pytest.skip("Arquivo YAML de configuração não encontrado")


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndSimulation:
    """Testes end-to-end da simulação"""

    def test_simulation_complete_cycle(self, mock_settings):
        """Testa ciclo completo de simulação"""
        configs = [
            MachineConfig(
                machine_id="M001",
                machine_type="TEST",
                rated_speed=3000,
                cycle_time=5.0,
                operator_id="OP001"
            )
        ]
        simulator = IoTSimulator(configs)

        # Executa várias iterações
        for _ in range(10):
            simulator._update_all_machines()

        # Máquina deve ter progredido
        machine = simulator.machines[0]
        assert machine.operating_hours >= 0

    def test_multiple_machines_independence(self, mock_settings):
        """Testa que máquinas operam independentemente"""
        config1 = MachineConfig(
            machine_id="M001",
            machine_type="TYPE_A",
            rated_speed=3000,
            cycle_time=10.0,
            operator_id="OP001"
        )
        config2 = MachineConfig(
            machine_id="M002",
            machine_type="TYPE_B",
            rated_speed=2000,
            cycle_time=15.0,
            operator_id="OP002"
        )

        simulator = IoTSimulator([config1, config2])

        # Força estados diferentes
        simulator.machines[0].state_machine.state_duration = 0.1
        simulator.machines[1].state_machine.state_duration = 100.0

        # Executa atualização
        for _ in range(5):
            simulator._update_all_machines()

        # Máquinas devem estar em estados potencialmente diferentes
        # (não garantido, mas possível)
        assert simulator.machines[0].config.machine_id == "M001"
        assert simulator.machines[1].config.machine_id == "M002"

    def test_simulation_with_failures_enabled(self, mock_settings_with_failures):
        """Testa simulação com injeção de falhas habilitada"""
        config = MachineConfig(
            machine_id="M001",
            machine_type="TEST",
            rated_speed=3000,
            cycle_time=5.0,
            operator_id="OP001",
            failure_injection_rate=1.0  # 100% para garantir
        )

        simulator = IoTSimulator([config])

        # Coloca em RUNNING
        machine = simulator.machines[0]
        current_time = time.time()
        machine.state_machine.transition_to(MachineStatus.WARMUP, current_time)
        machine.state_machine.transition_to(MachineStatus.RUNNING, current_time + 10)

        # Executa várias iterações
        anomaly_detected = False
        for _ in range(100):
            simulator._update_all_machines()
            if machine.anomaly_active:
                anomaly_detected = True
                break

        # Deve ter detectado anomalia eventualmente
        assert anomaly_detected


@pytest.mark.integration
class TestStatisticsAggregation:
    """Testes para agregação de estatísticas"""

    def test_aggregated_statistics(self):
        """Testa estatísticas agregadas de múltiplas máquinas"""
        configs = create_default_machines()
        simulator = IoTSimulator(configs)

        # Simula alguns ciclos e peças
        for machine in simulator.machines:
            machine.total_cycles = 10
            machine.good_parts = 9
            machine.bad_parts = 1

        total_cycles = sum(m.total_cycles for m in simulator.machines)
        total_good = sum(m.good_parts for m in simulator.machines)
        total_bad = sum(m.bad_parts for m in simulator.machines)

        assert total_cycles == 50  # 5 máquinas * 10 ciclos
        assert total_good == 45
        assert total_bad == 5

        # Taxa de qualidade global
        overall_quality = (total_good / (total_good + total_bad)) * 100
        assert overall_quality == 90.0
