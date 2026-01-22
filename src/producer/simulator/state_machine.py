"""
Máquina de estados para simular transições realistas
"""
import random
from typing import Dict, List, Optional
from enum import Enum
from src.producer.schemas.events import MachineStatus

class StateMachine:
    """
    Gerencia as transições de estado da máquina industrial
    """
    
    # Transições válidas: estado_atual -> [estados_possíveis]
    TRANSITIONS: Dict[MachineStatus, List[MachineStatus]] = {
        MachineStatus.IDLE: [
            MachineStatus.WARMUP,
            MachineStatus.MAINTENANCE,
        ],
        MachineStatus.WARMUP: [
            MachineStatus.RUNNING,
            MachineStatus.UNPLANNED_DOWNTIME,
        ],
        MachineStatus.RUNNING: [
            MachineStatus.SETUP,
            MachineStatus.PLANNED_DOWNTIME,
            MachineStatus.UNPLANNED_DOWNTIME,
            MachineStatus.MAINTENANCE,
            MachineStatus.COOLDOWN,
        ],
        MachineStatus.SETUP: [
            MachineStatus.RUNNING,
            MachineStatus.UNPLANNED_DOWNTIME,
        ],
        MachineStatus.PLANNED_DOWNTIME: [
            MachineStatus.WARMUP,
        ],
        MachineStatus.UNPLANNED_DOWNTIME: [
            MachineStatus.MAINTENANCE,
            MachineStatus.WARMUP,
        ],
        MachineStatus.MAINTENANCE: [
            MachineStatus.WARMUP,
        ],
        MachineStatus.COOLDOWN: [
            MachineStatus.IDLE,
        ],
    }
    
    # Durações típicas (em segundos)
    STATE_DURATIONS: Dict[MachineStatus, tuple] = {
        MachineStatus.IDLE: (5, 15),               # 5s - 15s (para testes rápidos)
        MachineStatus.WARMUP: (10, 20),            # 10s - 20s
        MachineStatus.RUNNING: (30, 120),          # 30s - 2min
        MachineStatus.SETUP: (15, 30),             # 15s - 30s
        MachineStatus.PLANNED_DOWNTIME: (20, 40),  # 20s - 40s
        MachineStatus.UNPLANNED_DOWNTIME: (25, 60), # 25s - 1min
        MachineStatus.MAINTENANCE: (40, 80),       # 40s - 80s
        MachineStatus.COOLDOWN: (10, 20),          # 10s - 20s
    }

    def __init__(self, initial_state: MachineStatus = MachineStatus.IDLE):
        self.current_state: MachineStatus = initial_state
        self.state_start_time = 0
        self.time_in_state = 0

        # Define duração inicial do estado
        min_duration, max_duration = self.STATE_DURATIONS[initial_state]
        self.state_duration = random.uniform(min_duration, max_duration)

    def can_transition_to(self, target_state: MachineStatus) -> bool:
        """
        Verifica se a transição para o estado alvo é válida
        """
        return target_state in self.TRANSITIONS.get(self.current_state, [])
    
    def transition_to(self, target_state: MachineStatus, current_time: float) -> bool:
        """
        Realiza transição de estado se for válida
        
        Args:
            target_state: Estado de destino
            current_time: Timestamp atual
            
        Returns:
            True se transição foi realizada, False caso contrário
        """
        if not self.can_transition_to(target_state):
            return False
        
        self.current_state = target_state
        self.state_start_time = current_time
        self.time_in_state = 0

        min_duration, max_duration = self.STATE_DURATIONS[target_state]
        self.state_duration = random.uniform(min_duration, max_duration)

        return True
    
    def update(self, current_time: float, elapsed: float) -> Optional[MachineStatus]:
        """
        Atualiza o tempo no estado atual e verifica se deve transitar
        
        Args:
            current_time: Timestamp atual
            elapsed: Tempo decorrido desde última atualização
            
        Returns:
            Novo estado se houve transição, None caso contrário
        """
        self.time_in_state += elapsed
        
        # Verifica se deve fazer a transição automática
        if self.time_in_state >= self.state_duration:
            next_state = self._get_next_automatic_state()
            if next_state and self.transition_to(next_state, current_time):
                return next_state
        
        return None
    
    def _get_next_automatic_state(self) -> Optional[MachineStatus]:
        """Determina próximo estado automático baseado no estado atual"""
        auto_transitions = {
            MachineStatus.IDLE: MachineStatus.WARMUP,  # IDLE sempre vai para WARMUP
            MachineStatus.WARMUP: MachineStatus.RUNNING,
            MachineStatus.COOLDOWN: MachineStatus.IDLE,
            MachineStatus.MAINTENANCE: MachineStatus.WARMUP,
            MachineStatus.PLANNED_DOWNTIME: MachineStatus.WARMUP,
            MachineStatus.SETUP: MachineStatus.RUNNING,
        }
        return auto_transitions.get(self.current_state)
    
    def get_state_progress(self) -> float:
        """Retorna progresso no estado atual (0.0 - 1.0)"""
        if self.state_duration == 0:
            return 0.0
        return min(1.0, self.time_in_state / self.state_duration)
