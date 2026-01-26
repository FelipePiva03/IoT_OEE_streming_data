# Como Usar o Simulador IoT/OEE

## Executar o Simulador

### Modo Local (Python)

#### Modo Contínuo (rodar até Ctrl+C)
```bash
python -m src.producer.main
```

#### Modo de Teste (30 segundos)
```bash
python test_simulator.py
```

### Modo Docker + Kafka

#### 1. Iniciar apenas Kafka (sem simulador)
```bash
docker-compose up -d zookeeper kafka schema-registry kafka-ui
```
Acesse Kafka UI em: http://localhost:8080

#### 2. Simulador em Tempo Real
```bash
# Inicia Kafka + Simulador em tempo real
docker-compose --profile normal up -d
```

#### 3. Simulador Acelerado (1 mês em 10 minutos)
```bash
# Perfeito para gerar dados históricos para treinar ML
docker-compose --profile monthly up

# Acompanhe os logs
docker logs -f iot-simulator-monthly
```

#### 4. Simulador Ultra Rápido (1 mês em 1 minuto)
```bash
# Para testes rápidos e prototipagem
docker-compose --profile ultra-fast up

# Logs em tempo real
docker logs -f iot-simulator-ultra-fast
```

#### Parar todos os serviços
```bash
docker-compose down
```

## O que o Simulador Faz

O simulador cria **5 máquinas industriais** que operam de forma independente:

| Machine ID  | Tipo              | RPM  | Tempo/Ciclo | Operador   | Turno |
|-------------|-------------------|------|-------------|------------|-------|
| machine_001 | CNC_MILL          | 3000 | 45s         | operator_A | day   |
| machine_002 | CNC_LATHE         | 2500 | 60s         | operator_B | day   |
| machine_003 | INJECTION_MOLD    | 1500 | 90s         | operator_C | day   |
| machine_004 | PRESS             | 800  | 30s         | operator_D | night |
| machine_005 | ASSEMBLY_ROBOT    | 1200 | 25s         | operator_E | night |

## Estados das Máquinas

As máquinas transitam entre 8 estados diferentes:

1. **IDLE** → Máquina parada aguardando início
2. **WARMUP** → Aquecendo (3-7 minutos)
3. **RUNNING** → Produzindo peças (30min-4h)
4. **SETUP** → Ajustes/troca de ferramentas (5-15min)
5. **PLANNED_DOWNTIME** → Parada programada (30min-1h)
6. **UNPLANNED_DOWNTIME** → Falha inesperada (10min-2h)
7. **MAINTENANCE** → Manutenção preventiva (2-5h)
8. **COOLDOWN** → Resfriamento (2-5min)

## Eventos Gerados

A cada 5 segundos, o simulador pode gerar:

### 1. Machine Events
- Mudanças de estado
- Ciclos completos
- Alertas

Exemplo:
```
[10:41:23] machine_001: idle → warmup (Reason: Starting production shift)
[10:41:45] machine_002: Cycle #15 completed
```

### 2. Sensor Metrics
Métricas coletadas de todas as máquinas:
- Temperatura (°C)
- Vibração (mm/s)
- Velocidade (RPM)
- Pressão (bar)
- Consumo de energia (kW)
- Horas de operação

Exemplo:
```
[SENSORS] [10:41:23] Coletadas 5 metricas de sensores
```

### 3. Quality Events
Inspeções de qualidade (15% de probabilidade por ciclo):
- Resultado: OK ou NOK
- Tipo de defeito (se NOK)
- Severidade (1-5)

Exemplo:
```
[OK] [10:42:10] machine_003: Quality check OK
[NOK] [10:43:15] machine_001: Quality check NOK - dimensional (severity: 3)
```

## Características do Simulador

### Desgaste Progressivo
- Máquinas acumulam desgaste ao longo da operação
- Temperatura e vibração aumentam com o desgaste
- Taxa de defeitos aumenta conforme máquina degrada
- Manutenção preventiva reseta o desgaste

### ⚡ Injeção de Falhas para Machine Learning
**Nova funcionalidade** para gerar dados rotulados:

- **Taxa configurável por máquina** (2% a 8% no YAML)
- **5 tipos de anomalias** injetadas aleatoriamente:
  - `temperature_spike`: Temperatura acima do limite (1.05x a 1.25x do máximo)
  - `vibration_anomaly`: Vibração anormal (1.1x a 1.5x do máximo)
  - `pressure_drop`: Queda de pressão (30% a 60% do ideal)
  - `speed_fluctuation`: Flutuação de RPM (±200 a ±500)
  - `power_surge`: Pico de consumo (1.5x a 2.5x)

- **Duração realista**: 30 segundos a 3 minutos
- **Logs detectáveis**: Console mostra início/fim das anomalias
- **Ideal para ML**: Dados rotulados para treinar modelos de detecção

Exemplo de log:
```
[ANOMALY INJECTED] M004: temperature_spike for 142s
[ANOMALY ENDED] M004: Anomalia finalizada
```

### 🚀 Aceleração de Tempo
**Nova funcionalidade** para simular longos períodos rapidamente:

- **TIME_MULTIPLIER**: Acelera o tempo simulado
  - `1.0` = tempo real (1 segundo simulado = 1 segundo real)
  - `4320.0` = 1 mês em 10 minutos
  - `43200.0` = 1 mês em 1 minuto

- **SIMULATION_SPEED**: Processa eventos mais rápido
  - `1.0` = normal
  - `10.0` = 10x mais rápido (reduz sleep)
  - `50.0` = 50x mais rápido

**Casos de uso**:
- Gerar dados históricos para análise
- Treinar modelos de ML com meses de dados
- Testar comportamento de longo prazo
- Validar pipelines de streaming

### Métricas Realistas
- Sensores variam conforme o estado da máquina
- IDLE: temperatura baixa, sem vibração
- WARMUP: valores crescentes
- RUNNING: valores máximos com variação
- MAINTENANCE: valores mínimos

### Estatísticas em Tempo Real
A cada 1 minuto (12 iterações), o simulador exibe:
- Estado atual de cada máquina
- Ciclos completados
- Taxa de qualidade
- Desgaste acumulado
- Horas de operação

## Configurações Avançadas

### Variáveis de Ambiente (Docker)

```bash
# Controle de simulação
SIMULATION_SPEED=10.0          # Velocidade de processamento
TIME_MULTIPLIER=4320.0         # Aceleração de tempo
ENABLE_FAILURE_INJECTION=true  # Ativa anomalias para ML

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC_MACHINE_EVENTS=machine-events
KAFKA_TOPIC_SENSOR_METRICS=sensor-metrics
KAFKA_TOPIC_QUALITY_EVENTS=quality-events
```

### Personalizar Taxas de Falha (YAML)

Edite `config/machines.yaml`:

```yaml
reliability:
  base_uptime: 0.95
  mtbf_hours: 120
  mttr_hours: 2
  failure_injection_rate: 0.05  # 5% de chance de anomalia
```

## Integração com Kafka

### Consumir Eventos do Kafka

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'sensor-metrics',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    sensor_data = message.value
    print(f"Machine: {sensor_data['machine_id']}")
    print(f"Temp: {sensor_data['temperature']}°C")
    print(f"Vibration: {sensor_data['vibration']} mm/s")
```

### Visualizar no Kafka UI

1. Acesse: http://localhost:8080
2. Navegue até "Topics"
3. Visualize mensagens em tempo real
4. Monitore throughput e lag

## Exemplos de Uso para ML

### 1. Gerar Dataset de 1 Mês

```bash
# Gera dados de 30 dias em ~10 minutos
docker-compose --profile monthly up

# Consome e salva em arquivo
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic sensor-metrics \
  --from-beginning > dataset_30days.jsonl
```

### 2. Detecção de Anomalias

As anomalias injetadas permitem treinar modelos de:
- **Classificação**: Normal vs Anômalo
- **Detecção de Outliers**: Isolation Forest, AutoEncoders
- **Série Temporal**: LSTM para prever falhas
- **Análise de Padrões**: Clustering de comportamentos

Labels disponíveis nos logs:
```
[ANOMALY INJECTED] M004: temperature_spike for 142s
```

### 3. Previsão de Manutenção (Predictive Maintenance)

Use `wear_factor` e `operating_hours` para:
- Prever quando manutenção será necessária
- Otimizar intervalos de manutenção
- Reduzir paradas não planejadas

## Próximos Passos

1. ✅ **Kafka Integration** - Publicar eventos em tópicos
2. ✅ **Failure Injection** - Anomalias para ML
3. ✅ **Time Acceleration** - Simular meses rapidamente
4. ⏳ **Schema Registry** - Validar eventos com schemas Avro
5. ⏳ **Spark Streaming** - Processar eventos em tempo real
6. ⏳ **Delta Lake** - Persistir em camadas Bronze/Silver/Gold
7. ⏳ **ML Models** - Detecção de anomalias e manutenção preditiva
8. ⏳ **Dashboard** - Visualização OEE em tempo real
