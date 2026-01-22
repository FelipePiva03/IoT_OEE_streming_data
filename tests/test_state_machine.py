"""
Testes para StateMachine
"""
import pytest
import time
from src.producer.simulator.state_machine import StateMachine
from src.producer.schemas.events import MachineStatus


@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineInitialization:
    """Testes para inicialização da StateMachine"""

    def test_initialization_idle(self):
        """Testa inicialização em estado IDLE"""
        sm = StateMachine(initial_state=MachineStatus.IDLE)

        assert sm.current_state == MachineStatus.IDLE
        assert sm.time_in_state == 0
        assert sm.state_duration > 0

    def test_initialization_running(self):
        """Testa inicialização em estado RUNNING"""
        sm = StateMachine(initial_state=MachineStatus.RUNNING)

        assert sm.current_state == MachineStatus.RUNNING
        assert sm.time_in_state == 0

    def test_state_duration_within_bounds(self):
        """Testa que duração do estado está dentro dos limites"""
        sm = StateMachine(initial_state=MachineStatus.IDLE)
        min_dur, max_dur = StateMachine.STATE_DURATIONS[MachineStatus.IDLE]

        assert min_dur <= sm.state_duration <= max_dur


@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineTransitions:
    """Testes para transições de estado"""

    def test_can_transition_valid(self, state_machine):
        """Testa verificação de transição válida"""
        # IDLE pode ir para WARMUP
        assert state_machine.can_transition_to(MachineStatus.WARMUP) is True
        assert state_machine.can_transition_to(MachineStatus.MAINTENANCE) is True

    def test_can_transition_invalid(self, state_machine):
        """Testa verificação de transição inválida"""
        # IDLE não pode ir direto para RUNNING
        assert state_machine.can_transition_to(MachineStatus.RUNNING) is False
        assert state_machine.can_transition_to(MachineStatus.COOLDOWN) is False

    def test_transition_to_valid(self, state_machine, current_time):
        """Testa transição válida de estado"""
        result = state_machine.transition_to(MachineStatus.WARMUP, current_time)

        assert result is True
        assert state_machine.current_state == MachineStatus.WARMUP
        assert state_machine.time_in_state == 0
        assert state_machine.state_start_time == current_time

    def test_transition_to_invalid(self, state_machine, current_time):
        """Testa tentativa de transição inválida"""
        result = state_machine.transition_to(MachineStatus.RUNNING, current_time)

        assert result is False
        assert state_machine.current_state == MachineStatus.IDLE

    def test_transition_chain(self, current_time):
        """Testa cadeia de transições válidas"""
        sm = StateMachine(initial_state=MachineStatus.IDLE)

        # IDLE -> WARMUP
        assert sm.transition_to(MachineStatus.WARMUP, current_time) is True
        assert sm.current_state == MachineStatus.WARMUP

        # WARMUP -> RUNNING
        assert sm.transition_to(MachineStatus.RUNNING, current_time + 10) is True
        assert sm.current_state == MachineStatus.RUNNING

        # RUNNING -> COOLDOWN
        assert sm.transition_to(MachineStatus.COOLDOWN, current_time + 20) is True
        assert sm.current_state == MachineStatus.COOLDOWN

        # COOLDOWN -> IDLE
        assert sm.transition_to(MachineStatus.IDLE, current_time + 30) is True
        assert sm.current_state == MachineStatus.IDLE


@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineUpdate:
    """Testes para atualização de estado"""

    def test_update_increases_time(self, state_machine, current_time):
        """Testa que update incrementa tempo no estado"""
        initial_time = state_machine.time_in_state
        state_machine.update(current_time, elapsed=5.0)

        assert state_machine.time_in_state == initial_time + 5.0

    def test_update_triggers_automatic_transition(self, current_time):
        """Testa transição automática quando duração é atingida"""
        sm = StateMachine(initial_state=MachineStatus.IDLE)

        # Força duração curta para teste
        sm.state_duration = 1.0

        # Atualiza com tempo suficiente para transição
        new_state = sm.update(current_time, elapsed=2.0)

        # Deve transitar automaticamente para WARMUP
        assert new_state == MachineStatus.WARMUP
        assert sm.current_state == MachineStatus.WARMUP

    def test_update_no_transition(self, state_machine, current_time):
        """Testa que não há transição se tempo não atingido"""
        state_machine.state_duration = 100.0  # Duração longa

        new_state = state_machine.update(current_time, elapsed=5.0)

        assert new_state is None
        assert state_machine.current_state == MachineStatus.IDLE

    def test_automatic_transitions_mapping(self, current_time):
        """Testa mapeamento de transições automáticas"""
        test_cases = [
            (MachineStatus.IDLE, MachineStatus.WARMUP),
            (MachineStatus.WARMUP, MachineStatus.RUNNING),
            (MachineStatus.COOLDOWN, MachineStatus.IDLE),
            (MachineStatus.MAINTENANCE, MachineStatus.WARMUP),
            (MachineStatus.PLANNED_DOWNTIME, MachineStatus.WARMUP),
            (MachineStatus.SETUP, MachineStatus.RUNNING),
        ]

        for initial, expected in test_cases:
            sm = StateMachine(initial_state=initial)
            sm.state_duration = 0.1  # Duração mínima

            new_state = sm.update(current_time, elapsed=1.0)

            assert new_state == expected, f"Expected {initial} -> {expected}, got {new_state}"


@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineProgress:
    """Testes para progresso no estado"""

    def test_get_state_progress_zero(self, state_machine):
        """Testa progresso no início do estado"""
        progress = state_machine.get_state_progress()

        assert progress == 0.0

    def test_get_state_progress_partial(self, state_machine, current_time):
        """Testa progresso parcial"""
        state_machine.state_duration = 100.0
        state_machine.update(current_time, elapsed=25.0)

        progress = state_machine.get_state_progress()

        assert progress == 0.25

    def test_get_state_progress_complete(self, state_machine, current_time):
        """Testa progresso completo"""
        state_machine.state_duration = 10.0
        # Incrementa time_in_state diretamente sem causar transição
        state_machine.time_in_state = 10.0

        progress = state_machine.get_state_progress()

        assert progress == 1.0

    def test_get_state_progress_over_complete(self, state_machine, current_time):
        """Testa que progresso não excede 1.0"""
        state_machine.state_duration = 10.0
        # Incrementa time_in_state diretamente sem causar transição
        state_machine.time_in_state = 20.0

        progress = state_machine.get_state_progress()

        assert progress == 1.0

    def test_get_state_progress_zero_duration(self):
        """Testa progresso com duração zero"""
        sm = StateMachine(initial_state=MachineStatus.IDLE)
        sm.state_duration = 0

        progress = sm.get_state_progress()

        assert progress == 0.0


@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineTransitionsValidity:
    """Testes para validação de todas as transições possíveis"""

    def test_all_states_have_transitions(self):
        """Testa que todos os estados têm transições definidas"""
        for state in MachineStatus:
            assert state in StateMachine.TRANSITIONS, f"Estado {state} não tem transições definidas"

    def test_all_states_have_durations(self):
        """Testa que todos os estados têm durações definidas"""
        for state in MachineStatus:
            assert state in StateMachine.STATE_DURATIONS, f"Estado {state} não tem duração definida"

    def test_transitions_are_valid_states(self):
        """Testa que todas as transições apontam para estados válidos"""
        for state, transitions in StateMachine.TRANSITIONS.items():
            for target in transitions:
                assert isinstance(target, MachineStatus), f"Transição inválida: {state} -> {target}"

    def test_no_self_transitions_except_running(self):
        """Testa que estados não fazem transição para si mesmos (exceto RUNNING)"""
        for state, transitions in StateMachine.TRANSITIONS.items():
            if state != MachineStatus.RUNNING:
                assert state not in transitions, f"Estado {state} transita para si mesmo"
