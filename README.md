# Pipeline IoT/OEE - Streaming Architecture

Pipeline de streaming para monitoramento de OEE (Overall Equipment Effectiveness) em tempo real, simulando dados de sensores industriais.

## Arquitetura

```mermaid
flowchart LR
    subgraph INGESTION["Data Ingestion"]
        PY[["Python Producer"]]
        SIM[("IoT Simulator\n5 Machines")]
    end

    subgraph STREAMING["Message Broker"]
        direction TB
        K{{"Apache Kafka\nConfluent Cloud"}}
        T1[(machine_events)]
        T2[(sensor_metrics)]
        T3[(quality_events)]
        K --- T1
        K --- T2
        K --- T3
    end

    subgraph PROCESSING["Stream Processing"]
        SPK[["Spark Structured\nStreaming"]]
        DBR[("Databricks\nRuntime")]
    end

    subgraph STORAGE["Data Lake"]
        direction TB
        B[(Bronze)]
        S[(Silver)]
        G[(Gold)]
        B --> S --> G
    end

    subgraph SERVING["Analytics"]
        PBI[["Power BI"]]
        API[("REST API")]
    end

    SIM --> PY
    PY -->|JSON/Avro| K
    T1 & T2 & T3 -->|Consumer Group| SPK
    SPK <--> DBR
    SPK -->|Delta Format| B
    G --> PBI
    G --> API
```

## Fluxo de Dados

```mermaid
flowchart TB
    subgraph INPUT["📥 Eventos Gerados"]
        E1["machine_events\nstatus, ciclos, paradas"]
        E2["sensor_metrics\ntemperatura, vibração, velocidade"]
        E3["quality_events\ninspeção OK/NOK"]
    end

    subgraph PROCESS["⚙️ Processamento"]
        W1["Janela 1 min"]
        W2["Janela 5 min"]
        W3["Janela 1 hora"]
    end

    subgraph OUTPUT["📤 Camadas Delta Lake"]
        D1["🥉 Bronze - eventos raw"]
        D2["🥈 Silver - métricas agregadas"]
        D3["🥇 Gold - OEE por máquina/turno"]
    end

    INPUT --> PROCESS --> OUTPUT
```

## Componentes

| Componente | Tecnologia | Descrição |
|------------|------------|-----------|
| Producer | Python | Simula máquinas industriais gerando eventos |
| Broker | Confluent Cloud (Kafka) | Gerencia streaming dos eventos |
| Processamento | Spark Structured Streaming | Calcula OEE em tempo real |
| Storage | Delta Lake | Armazena dados em camadas Bronze/Silver/Gold |
| Visualização | Power BI | Dashboard de monitoramento |

## Métricas OEE

O OEE é calculado como:

**OEE = Disponibilidade × Performance × Qualidade**

- **Disponibilidade**: Tempo produzindo / Tempo programado
- **Performance**: Produção real / Produção teórica
- **Qualidade**: Peças boas / Total produzido

## Stack

- Python 3.11+
- Apache Kafka (Confluent Cloud)
- Apache Spark (Databricks)
- Delta Lake
- Power BI
