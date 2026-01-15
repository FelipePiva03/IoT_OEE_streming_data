---
title: Pipeline IoT/OEE - Streaming Architecture
---

flowchart LR
    subgraph PRODUCER["🐍 Python Producer"]
        direction TB
        P1["Simulador IoT"]
        P2["3-5 Máquinas"]
        P3["Eventos em tempo real"]
    end

    subgraph KAFKA["☁️ Confluent Cloud"]
        direction TB
        T1["📦 machine_events\n(status, ciclos, paradas)"]
        T2["📦 sensor_metrics\n(temp, vibração, velocidade)"]
        T3["📦 quality_events\n(inspeção OK/NOK)"]
    end

    subgraph SPARK["⚡ Spark Structured Streaming"]
        direction TB
        S1["Databricks"]
        S2["Janelas: 1min, 5min, 1h"]
        S3["Cálculo OEE"]
    end

    subgraph DELTA["💾 Delta Lake"]
        direction TB
        D1["🥉 Bronze\n(eventos raw)"]
        D2["🥈 Silver\n(métricas agregadas)"]
        D3["🥇 Gold\n(OEE máquina/turno)"]
    end

    subgraph DASH["📊 Dashboard"]
        direction TB
        V1["Power BI"]
        V2["Real-time OEE"]
        V3["Alertas"]
    end

    PRODUCER -->|stream| KAFKA
    KAFKA -->|consume| SPARK
    SPARK -->|write| DELTA
    DELTA -->|read| DASH

    style PRODUCER fill:#2d5a3d,stroke:#1a3d2a,color:#ffffff
    style KAFKA fill:#4a90a4,stroke:#2d6073,color:#ffffff
    style SPARK fill:#e85a19,stroke:#b34512,color:#ffffff
    style DELTA fill:#1a5a9e,stroke:#0d3d6e,color:#ffffff
    style DASH fill:#6b4c9a,stroke:#4a3570,color:#ffffff
