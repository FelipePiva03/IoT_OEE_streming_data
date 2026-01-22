# Testes do Simulador IoT/OEE

Este diretório contém os testes unitários e de integração para o simulador IoT/OEE.

## Estrutura dos Testes

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures compartilhadas
├── test_schemas.py                # Testes dos schemas de eventos
├── test_state_machine.py          # Testes da máquina de estados
├── test_machine_simulator.py      # Testes do simulador de máquina
├── test_anomaly_injection.py      # Testes de injeção de falhas
└── test_integration.py            # Testes de integração
```

## Executar Testes

### Instalar Dependências

```bash
pip install -r requirements.txt
```

### Rodar Todos os Testes

```bash
pytest
```

### Rodar com Verbosidade

```bash
pytest -v
```

### Rodar com Cobertura

```bash
pytest --cov=src --cov-report=html
```

## Rodar Testes Específicos

### Por Arquivo

```bash
# Testes de schemas
pytest tests/test_schemas.py

# Testes de state machine
pytest tests/test_state_machine.py

# Testes do simulador
pytest tests/test_machine_simulator.py

# Testes de anomalias
pytest tests/test_anomaly_injection.py

# Testes de integração
pytest tests/test_integration.py
```

### Por Classe

```bash
# Testes de enums
pytest tests/test_schemas.py::TestEnums

# Testes de transições
pytest tests/test_state_machine.py::TestStateMachineTransitions

# Testes de anomalias
pytest tests/test_anomaly_injection.py::TestAnomalyEffects
```

### Por Teste Individual

```bash
# Teste específico
pytest tests/test_schemas.py::TestMachineEvent::test_create_machine_event

# Teste de anomalia específica
pytest tests/test_anomaly_injection.py::TestAnomalyEffects::test_temperature_spike_anomaly
```

## Rodar por Markers

Os testes estão organizados com markers:

```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Apenas testes de anomalias
pytest -m anomaly

# Apenas testes de state machine
pytest -m state_machine

# Apenas testes do simulador
pytest -m simulator

# Excluir testes lentos
pytest -m "not slow"
```

## Combinando Markers

```bash
# Testes unitários de anomalias
pytest -m "unit and anomaly"

# Testes de integração que não são lentos
pytest -m "integration and not slow"
```

## Estatísticas de Cobertura

### Gerar Relatório HTML

```bash
pytest --cov=src --cov-report=html
```

Depois abra `htmlcov/index.html` no navegador.

### Relatório no Terminal

```bash
pytest --cov=src --cov-report=term-missing
```

## Testes em Modo Watch

Para desenvolvimento contínuo:

```bash
pytest-watch
```

ou

```bash
ptw
```

## Estrutura dos Testes

### test_schemas.py
- ✅ Testa enums (MachineStatus, EventType, QualityResult, DefectType)
- ✅ Testa criação de MachineEvent
- ✅ Testa criação de SensorMetric
- ✅ Testa criação de QualityEvent
- ✅ Testa serialização para dict
- ✅ Testa geração de IDs únicos

### test_state_machine.py
- ✅ Testa inicialização de estados
- ✅ Testa transições válidas e inválidas
- ✅ Testa transições automáticas
- ✅ Testa cálculo de progresso
- ✅ Testa mapeamento completo de estados

### test_machine_simulator.py
- ✅ Testa configuração de máquina
- ✅ Testa inicialização do simulador
- ✅ Testa geração de eventos
- ✅ Testa geração de métricas
- ✅ Testa acumulação de horas operacionais
- ✅ Testa desgaste progressivo
- ✅ Testa lógica de manutenção
- ✅ Testa estatísticas

### test_anomaly_injection.py
- ✅ Testa configuração de injeção
- ✅ Testa ativação de anomalias
- ✅ Testa efeitos de cada tipo de anomalia:
  - temperature_spike
  - vibration_anomaly
  - pressure_drop
  - speed_fluctuation
  - power_surge
- ✅ Testa duração das anomalias
- ✅ Testa múltiplos ciclos de anomalias
- ✅ Testa desabilitação de injeção

### test_integration.py
- ✅ Testa inicialização do IoTSimulator
- ✅ Testa criação de máquinas padrão
- ✅ Testa execução do simulador
- ✅ Testa carregamento de configuração YAML
- ✅ Testa independência de máquinas
- ✅ Testa agregação de estatísticas
- ✅ Testa simulação end-to-end

## Fixtures Disponíveis

Definidas em `conftest.py`:

- `basic_machine_config` - Configuração básica de máquina
- `machine_config_with_failures` - Configuração com falhas habilitadas (100%)
- `machine_simulator` - Simulador básico
- `machine_simulator_with_failures` - Simulador com falhas
- `state_machine` - Máquina de estados em IDLE
- `current_time` - Timestamp atual
- `mock_settings` - Mock das configurações (falhas desabilitadas)
- `mock_settings_with_failures` - Mock com falhas habilitadas

## Exemplo de Uso

```python
def test_my_feature(machine_simulator, mock_settings):
    """Testa minha funcionalidade"""
    current_time = time.time()

    machine_simulator.state_machine.transition_to(
        MachineStatus.RUNNING, current_time
    )

    _, sensor_metric, _ = machine_simulator.update(
        current_time, elapsed=5.0
    )

    assert sensor_metric.temperature > 0
```

## Troubleshooting

### ImportError

Se encontrar erros de import:

```bash
# Certifique-se de estar no diretório raiz
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Testes Lentos

Se os testes estão demorando muito:

```bash
# Rode apenas testes rápidos
pytest -m "not slow"

# Ou rode em paralelo (precisa instalar pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

### Falhas Aleatórias

Se testes com probabilidade falham às vezes:

```bash
# Rode várias vezes
pytest --count=10 tests/test_anomaly_injection.py
```

## Próximos Passos

- [ ] Adicionar testes de performance
- [ ] Adicionar testes de Kafka integration
- [ ] Adicionar testes de Schema Registry
- [ ] Adicionar testes de serialização Avro
- [ ] Adicionar mutation testing (mutpy)
