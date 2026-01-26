# Docker Quick Start - IoT/OEE Simulator

## Pré-requisitos

- Docker instalado
- Docker Compose instalado

## Comandos Rápidos

### 1. Build da Imagem

```bash
docker-compose build
```

### 2. Iniciar Kafka (sem simulador)

```bash
docker-compose up -d zookeeper kafka schema-registry kafka-ui
```

**Acesse**:
- Kafka UI: http://localhost:8080
- Schema Registry: http://localhost:8081

### 3. Rodar Simulador

#### Modo Normal (Tempo Real)
```bash
docker-compose --profile normal up -d
docker logs -f iot-simulator
```

#### Modo Mensal (1 mês em 10 minutos)
```bash
docker-compose --profile monthly up
```
Aguarde ~10 minutos e os dados de 30 dias estarão no Kafka!

#### Modo Ultra Rápido (1 mês em 1 minuto)
```bash
docker-compose --profile ultra-fast up
```

### 4. Verificar Dados no Kafka

**Via Kafka UI**:
1. Acesse http://localhost:8080
2. Vá em "Topics"
3. Selecione `sensor-metrics`
4. Veja as mensagens em tempo real

**Via Console Consumer**:
```bash
# Sensor Metrics
docker exec -it iot-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensor-metrics \
  --from-beginning \
  --max-messages 10

# Machine Events
docker exec -it iot-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic machine-events \
  --from-beginning

# Quality Events
docker exec -it iot-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic quality-events \
  --from-beginning
```

### 5. Exportar Dados para Arquivo

```bash
# Exportar todas as métricas de sensores
docker exec -it iot-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensor-metrics \
  --from-beginning > sensor_data.jsonl
```

### 6. Parar Tudo

```bash
docker-compose down
```

### 7. Limpar Volumes (CUIDADO: apaga dados)

```bash
docker-compose down -v
```

## Configurações Personalizadas

### Customizar Tempo de Simulação

Edite `docker-compose.yml`:

```yaml
simulator-custom:
  build: .
  environment:
    SIMULATION_SPEED: "20.0"      # Processar 20x mais rápido
    TIME_MULTIPLIER: "8640.0"     # 60 dias em 10 minutos
    ENABLE_FAILURE_INJECTION: "true"
    KAFKA_BOOTSTRAP_SERVERS: "kafka:29092"
```

Execute:
```bash
docker-compose up simulator-custom
```

### Desabilitar Injeção de Falhas

```yaml
environment:
  ENABLE_FAILURE_INJECTION: "false"
```

## Troubleshooting

### Kafka não está disponível
```bash
# Verificar saúde do Kafka
docker-compose ps

# Ver logs
docker logs iot-kafka
docker logs iot-zookeeper
```

### Simulador não conecta ao Kafka
```bash
# Verificar se Kafka está rodando
docker-compose up -d kafka

# Aguardar healthcheck
docker-compose ps kafka

# Iniciar simulador após Kafka estar healthy
docker-compose --profile normal up
```

### Limpar e Recomeçar
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Exemplos Práticos

### Exemplo 1: Gerar 1 semana de dados

```bash
# 1 semana = 7 dias = 168 horas = 10080 minutos
# Para simular em 10 minutos: 10080 / 10 = 1008x

# Edite docker-compose.yml para criar um profile:
simulator-weekly:
  environment:
    TIME_MULTIPLIER: "1008.0"
    SIMULATION_SPEED: "10.0"

# Execute
docker-compose up simulator-weekly
```

### Exemplo 2: Teste Rápido (1 dia em 1 minuto)

```yaml
simulator-daily:
  environment:
    TIME_MULTIPLIER: "1440.0"  # 24h * 60min = 1440
    SIMULATION_SPEED: "10.0"
```

### Exemplo 3: Produção Realista (Kafka + Simulador Contínuo)

```bash
# Inicia tudo em background
docker-compose --profile normal up -d

# Monitora logs
docker logs -f iot-simulator

# Para quando necessário
docker-compose down
```

## Próximos Passos

Após ter dados no Kafka:

1. **Spark Streaming**: Processar eventos em tempo real
2. **ML Training**: Usar dados históricos para treinar modelos
3. **Dashboard**: Criar visualizações com Grafana
4. **Alertas**: Configurar alertas baseados em anomalias

Ver `USAGE.md` para mais detalhes!
