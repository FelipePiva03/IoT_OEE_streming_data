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
        MachineStatus.IDLE: (600, 3600),           # 10min - 1h
        MachineStatus.WARMUP: (180, 420),          # 3min - 7min
        MachineStatus.RUNNING: (1800, 14400),      # 30min - 4h
        MachineStatus.SETUP: (300, 900),           # 5min - 15min
        MachineStatus.PLANNED_DOWNTIME: (1800, 3600),  # 30min - 1h
        MachineStatus.UNPLANNED_DOWNTIME: (600, 7200), # 10min - 2h
        MachineStatus.MAINTENANCE: (7200, 18000),  # 2h - 5h
        MachineStatus.COOLDOWN: (120, 300),        # 2min - 5min
    }

    def __init__(self, initial_state: MachineStatus = MachineStatus.IDLE):
        self.current_state: MachineStatus = initial_state
        self.state_start_time = 0
        self.state_duration = 0
        self.time_in_state = 0

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
            MachineStatus.WARMUP: MachineStatus.RUNNING,
            MachineStatus.COOLDOWN: MachineStatus.IDLE,
            MachineStatus.MAINTENANCE: MachineStatus.WARMUP,
            MachineStatus.PLANNED_DOWNTIME: MachineStatus.WARMUP,
            MachineStatus.SETUP: MachineStatus.RUNNING,
        }
        return auto_transitions.get(self.current_state)
