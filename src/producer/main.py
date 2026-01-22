"""
Simulador principal - Orquestra múltiplas máquinas industriais
"""
import time
import json
import yaml
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from src.producer.simulator.machine_simulator import MachineSimulator, MachineConfig
from src.producer.config.settings import settings


class IoTSimulator:
    """
    Orquestrador principal do simulador IoT
    Gerencia múltiplas máquinas e coleta eventos
    """

    def __init__(self, machine_configs: List[MachineConfig]):
        self.machines: List[MachineSimulator] = []

        # Cria instância de cada máquina
        for config in machine_configs:
            machine = MachineSimulator(config)
            self.machines.append(machine)

        self.start_time = time.time()
        self.simulation_time = time.time()  # Tempo simulado (pode ser acelerado)
        self.iteration = 0

        print(f"IoT Simulator iniciado com {len(self.machines)} máquinas")
        print(f"Intervalo de atualização: {settings.EVENT_INTERNAL_SECONDS}s")
        print(f"Velocidade de simulação: {settings.SIMULATION_SPEED}x")
        print(f"Multiplicador de tempo: {settings.TIME_MULTIPLIER}x")
        if settings.TIME_MULTIPLIER > 1:
            days_per_minute = settings.TIME_MULTIPLIER * 60 / 86400
            print(f"  -> {days_per_minute:.2f} dias simulados por minuto real")
        print("=" * 80)

    def run(self, duration_seconds: int = None):
        """
        Executa o simulador

        Args:
            duration_seconds: Duração da simulação (None = infinito)
        """
        try:
            while True:
                iteration_start = time.time()

                # Atualiza todas as máquinas
                self._update_all_machines()

                # Mostra estatísticas periodicamente
                if self.iteration % 12 == 0:  # A cada 1 minuto (12 * 5s)
                    self._print_statistics()

                self.iteration += 1

                # Verifica se deve encerrar
                if duration_seconds and (time.time() - self.start_time) >= duration_seconds:
                    print("\nSimulacao finalizada por tempo")
                    break

                # Aguarda próximo ciclo
                elapsed = time.time() - iteration_start
                sleep_time = max(0, settings.EVENT_INTERNAL_SECONDS / settings.SIMULATION_SPEED - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\nSimulacao interrompida pelo usuario")
        finally:
            self._print_final_statistics()

    def _update_all_machines(self):
        """Atualiza todas as máquinas e coleta eventos"""
        # Tempo simulado (acelerado pelo TIME_MULTIPLIER)
        elapsed_simulated = settings.EVENT_INTERNAL_SECONDS * settings.TIME_MULTIPLIER
        self.simulation_time += elapsed_simulated
        current_time = self.simulation_time

        all_events = {
            "machine_events": [],
            "sensor_metrics": [],
            "quality_events": []
        }

        for machine in self.machines:
            machine_event, sensor_metric, quality_event = machine.update(
                current_time, elapsed_simulated
            )

            # Coleta eventos gerados
            if machine_event:
                all_events["machine_events"].append(machine_event.to_dict())

            if sensor_metric:
                all_events["sensor_metrics"].append(sensor_metric.to_dict())

            if quality_event:
                all_events["quality_events"].append(quality_event.to_dict())

        # Exibe eventos gerados (por enquanto no console)
        self._display_events(all_events)

    def _display_events(self, events: Dict):
        """Exibe eventos gerados no console"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Machine Events
        for event in events["machine_events"]:
            if event["event_type"] == "status_change":
                print(
                    f"[{timestamp}] {event['machine_id']}: "
                    f"{event['previous_status']} -> {event['status']} "
                    f"(Reason: {event['reason']})"
                )
            elif event["event_type"] == "cycle_complete":
                print(
                    f"[{timestamp}] {event['machine_id']}: "
                    f"Cycle #{event['cycle_count']} completed"
                )

        # Quality Events
        for event in events["quality_events"]:
            icon = "[OK]" if event["result"] == "ok" else "[NOK]"
            details = ""
            if event["result"] == "nok":
                details = f" - {event['defect_type']} (severity: {event['defect_severity']})"

            print(
                f"{icon} [{timestamp}] {event['machine_id']}: "
                f"Quality check {event['result'].upper()}{details}"
            )

        # Sensor Metrics (exibe detalhes de cada sensor)
        if events["sensor_metrics"]:
            print(f"\n[SENSORS] [{timestamp}] Metricas coletadas:")
            for sensor in events["sensor_metrics"]:
                print(
                    f"  {sensor['machine_id']:15} | "
                    f"Temp: {sensor['temperature']:5.1f}C | "
                    f"Vib: {sensor['vibration']:5.2f}mm/s | "
                    f"Press: {sensor['pressure']:5.2f}bar | "
                    f"RPM: {sensor['speed_rpm']:4.0f} | "
                    f"Power: {sensor['power_consumption']:5.1f}kW"
                )

    def _print_statistics(self):
        """Imprime estatísticas gerais"""
        print("\n" + "=" * 80)
        print(f"ESTATÍSTICAS - Iteração #{self.iteration}")
        print("=" * 80)

        for machine in self.machines:
            stats = machine.get_statistics()
            print(
                f"  {stats['machine_id']:<12} | "
                f"Estado: {stats['current_state']:<20} | "
                f"Ciclos: {stats['total_cycles']:>4} | "
                f"Qualidade: {stats['quality_rate']:>6.2f}% | "
                f"Desgaste: {stats['wear_factor']:>5.1f}% | "
                f"Horas: {stats['operating_hours']:>6.2f}h"
            )

        print("=" * 80 + "\n")

    def _print_final_statistics(self):
        """Imprime estatísticas finais da simulação"""
        elapsed_time = time.time() - self.start_time

        print("\n" + "=" * 80)
        print("ESTATISTICAS FINAIS")
        print("=" * 80)
        print(f"Tempo de simulacao: {elapsed_time:.1f}s ({self.iteration} iteracoes)")
        print(f"Maquinas simuladas: {len(self.machines)}")
        print("\nDesempenho por máquina:")
        print("-" * 80)

        total_cycles = 0
        total_good = 0
        total_bad = 0

        for machine in self.machines:
            stats = machine.get_statistics()
            total_cycles += stats['total_cycles']
            total_good += stats['good_parts']
            total_bad += stats['bad_parts']

            print(
                f"  {stats['machine_id']:<12} | "
                f"Ciclos: {stats['total_cycles']:>5} | "
                f"OK: {stats['good_parts']:>4} | "
                f"NOK: {stats['bad_parts']:>4} | "
                f"Qualidade: {stats['quality_rate']:>6.2f}% | "
                f"Horas operação: {stats['operating_hours']:>6.2f}h"
            )

        print("-" * 80)
        total_inspected = total_good + total_bad
        overall_quality = (total_good / total_inspected * 100) if total_inspected > 0 else 0

        print(f"\nTotal geral:")
        print(f"   Ciclos totais: {total_cycles}")
        print(f"   Peças inspecionadas: {total_inspected}")
        print(f"   Peças OK: {total_good}")
        print(f"   Peças NOK: {total_bad}")
        print(f"   Taxa de qualidade global: {overall_quality:.2f}%")
        print("=" * 80 + "\n")


def load_machines_from_yaml(yaml_path: str = None) -> List[MachineConfig]:
    """
    Carrega configurações de máquinas do arquivo YAML

    Args:
        yaml_path: Caminho para o arquivo YAML. Se None, usa o padrão.

    Returns:
        Lista de MachineConfig carregadas do YAML
    """
    if yaml_path is None:
        yaml_path = Path(__file__).parent / "config" / "machines.yaml"

    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    machines = []
    for machine_data in config['machines']:
        # Mapeia tipo do YAML para formato esperado
        machine_type = machine_data['type'].upper()
        specs = machine_data['specs']
        reliability = machine_data.get('reliability', {})

        machines.append(MachineConfig(
            machine_id=machine_data['id'],
            machine_type=machine_type,
            rated_speed=specs['optimal_rpm'],
            cycle_time=float(specs['cycle_time']),
            operator_id=f"operator_{machine_data['id']}",
            shift="day",  # Pode ser melhorado para usar shift_schedule do YAML
            # Limites dos sensores
            max_temperature=specs.get('max_temperature', 85.0),
            optimal_temperature=specs.get('optimal_temperature', 65.0),
            max_vibration=specs.get('max_vibration', 5.0),
            optimal_vibration=specs.get('optimal_vibration', 1.5),
            max_pressure=specs.get('max_pressure', 8.0),
            optimal_pressure=specs.get('optimal_pressure', 6.5),
            # Taxa de injeção de falhas
            failure_injection_rate=reliability.get('failure_injection_rate', 0.05)
        ))

    return machines


def create_default_machines() -> List[MachineConfig]:
    """Cria configuração padrão para 5 máquinas"""
    machines = [
        MachineConfig(
            machine_id="machine_001",
            machine_type="CNC_MILL",
            rated_speed=3000,
            cycle_time=8.0,  # Reduzido para testes (era 45s)
            operator_id="operator_A",
            shift="day"
        ),
        MachineConfig(
            machine_id="machine_002",
            machine_type="CNC_LATHE",
            rated_speed=2500,
            cycle_time=10.0,  # Reduzido para testes (era 60s)
            operator_id="operator_B",
            shift="day"
        ),
        MachineConfig(
            machine_id="machine_003",
            machine_type="INJECTION_MOLD",
            rated_speed=1500,
            cycle_time=12.0,  # Reduzido para testes (era 90s)
            operator_id="operator_C",
            shift="day"
        ),
        MachineConfig(
            machine_id="machine_004",
            machine_type="PRESS",
            rated_speed=800,
            cycle_time=6.0,  # Reduzido para testes (era 30s)
            operator_id="operator_D",
            shift="night"
        ),
        MachineConfig(
            machine_id="machine_005",
            machine_type="ASSEMBLY_ROBOT",
            rated_speed=1200,
            cycle_time=5.0,  # Reduzido para testes (era 25s)
            operator_id="operator_E",
            shift="night"
        ),
    ]
    return machines


def main():
    """Ponto de entrada do simulador"""
    print("\n" + "=" * 80)
    print("IoT/OEE STREAMING DATA SIMULATOR")
    print("=" * 80 + "\n")

    # Cria configuração das máquinas
    machine_configs = create_default_machines()

    # Inicializa e executa simulador
    simulator = IoTSimulator(machine_configs)

    # Roda indefinidamente (Ctrl+C para parar)
    # Ou especifique duração em segundos: simulator.run(duration_seconds=300)
    simulator.run()


if __name__ == "__main__":
    main()
