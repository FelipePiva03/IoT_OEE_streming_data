# Dockerfile para IoT/OEE Simulator
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código fonte
COPY src/ ./src/
COPY config/ ./config/

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV SIMULATION_SPEED=1.0
ENV TIME_MULTIPLIER=1.0
ENV ENABLE_FAILURE_INJECTION=true
ENV KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENV KAFKA_TOPIC_MACHINE_EVENTS=machine-events
ENV KAFKA_TOPIC_SENSOR_METRICS=sensor-metrics
ENV KAFKA_TOPIC_QUALITY_EVENTS=quality-events

# Comando padrão
CMD ["python", "-m", "src.producer.main"]
