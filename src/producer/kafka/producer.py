"""
Kafka Producer para streaming de eventos IoT/OEE
"""
import json
import os
from typing import Optional, Dict, Any, Callable
from confluent_kafka import Producer, KafkaError, KafkaException

from src.producer.schemas.events import MachineEvent, SensorMetric, QualityEvent, AnomalyEvent


class KafkaEventProducer:
    """
    Producer Kafka para envio de eventos do simulador IoT

    Envia eventos para 4 tópicos:
    - machine-events: Mudanças de estado e ciclos
    - sensor-metrics: Métricas dos sensores
    - quality-events: Inspeções de qualidade
    - anomaly-events: Anomalias detectadas (para ML)
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic_machine_events: Optional[str] = None,
        topic_sensor_metrics: Optional[str] = None,
        topic_quality_events: Optional[str] = None,
        topic_anomaly_events: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Inicializa o producer Kafka

        Args:
            bootstrap_servers: Endereço do Kafka (default: env KAFKA_BOOTSTRAP_SERVERS)
            topic_machine_events: Tópico para eventos de máquina
            topic_sensor_metrics: Tópico para métricas de sensores
            topic_quality_events: Tópico para eventos de qualidade
            topic_anomaly_events: Tópico para eventos de anomalia
            enabled: Se False, não envia mensagens (modo dry-run)
        """
        self.enabled = enabled

        # Configurações via env ou parâmetros
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.topic_machine_events = topic_machine_events or os.getenv(
            "KAFKA_TOPIC_MACHINE_EVENTS", "machine-events"
        )
        self.topic_sensor_metrics = topic_sensor_metrics or os.getenv(
            "KAFKA_TOPIC_SENSOR_METRICS", "sensor-metrics"
        )
        self.topic_quality_events = topic_quality_events or os.getenv(
            "KAFKA_TOPIC_QUALITY_EVENTS", "quality-events"
        )
        self.topic_anomaly_events = topic_anomaly_events or os.getenv(
            "KAFKA_TOPIC_ANOMALY_EVENTS", "anomaly-events"
        )

        # Contadores de mensagens
        self.messages_sent = 0
        self.messages_failed = 0

        # Producer Kafka
        self._producer: Optional[Producer] = None

        if self.enabled:
            self._init_producer()

    def _init_producer(self):
        """Inicializa conexão com Kafka"""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": "iot-simulator-producer",
            # Configurações de performance
            "linger.ms": 5,  # Batch messages por 5ms
            "batch.size": 16384,  # 16KB batch
            "compression.type": "lz4",  # Compressão eficiente
            # Configurações de confiabilidade
            "acks": "all",  # Espera confirmação de todas as réplicas
            "retries": 3,
            "retry.backoff.ms": 100,
            # Timeout
            "request.timeout.ms": 30000,
            "delivery.timeout.ms": 120000,
        }

        try:
            self._producer = Producer(config)
            print(f"[KAFKA] Conectado ao Kafka: {self.bootstrap_servers}")
            print(f"[KAFKA] Tópicos: {self.topic_machine_events}, {self.topic_sensor_metrics}, {self.topic_quality_events}, {self.topic_anomaly_events}")
        except KafkaException as e:
            print(f"[KAFKA ERROR] Falha ao conectar: {e}")
            self.enabled = False
            raise

    def _delivery_callback(self, err, msg):
        """Callback chamado quando mensagem é entregue ou falha"""
        if err is not None:
            self.messages_failed += 1
            print(f"[KAFKA ERROR] Falha ao entregar mensagem: {err}")
        else:
            self.messages_sent += 1

    def _serialize(self, data: Dict[str, Any]) -> bytes:
        """Serializa dados para JSON bytes"""
        return json.dumps(data, default=str).encode("utf-8")

    def send_machine_event(self, event: MachineEvent) -> bool:
        """
        Envia evento de máquina para Kafka

        Args:
            event: Evento de mudança de estado ou ciclo

        Returns:
            True se enviado com sucesso
        """
        if not self.enabled or not self._producer:
            return False

        try:
            self._producer.produce(
                topic=self.topic_machine_events,
                key=event.machine_id.encode("utf-8"),
                value=self._serialize(event.to_dict()),
                callback=self._delivery_callback
            )
            return True
        except BufferError:
            print(f"[KAFKA] Buffer cheio, aguardando...")
            self._producer.poll(1.0)
            return self.send_machine_event(event)
        except Exception as e:
            print(f"[KAFKA ERROR] Erro ao enviar machine_event: {e}")
            return False

    def send_sensor_metric(self, metric: SensorMetric) -> bool:
        """
        Envia métrica de sensor para Kafka

        Args:
            metric: Métricas dos sensores da máquina

        Returns:
            True se enviado com sucesso
        """
        if not self.enabled or not self._producer:
            return False

        try:
            self._producer.produce(
                topic=self.topic_sensor_metrics,
                key=metric.machine_id.encode("utf-8"),
                value=self._serialize(metric.to_dict()),
                callback=self._delivery_callback
            )
            return True
        except BufferError:
            print(f"[KAFKA] Buffer cheio, aguardando...")
            self._producer.poll(1.0)
            return self.send_sensor_metric(metric)
        except Exception as e:
            print(f"[KAFKA ERROR] Erro ao enviar sensor_metric: {e}")
            return False

    def send_quality_event(self, event: QualityEvent) -> bool:
        """
        Envia evento de qualidade para Kafka

        Args:
            event: Resultado de inspeção de qualidade

        Returns:
            True se enviado com sucesso
        """
        if not self.enabled or not self._producer:
            return False

        try:
            self._producer.produce(
                topic=self.topic_quality_events,
                key=event.machine_id.encode("utf-8"),
                value=self._serialize(event.to_dict()),
                callback=self._delivery_callback
            )
            return True
        except BufferError:
            print(f"[KAFKA] Buffer cheio, aguardando...")
            self._producer.poll(1.0)
            return self.send_quality_event(event)
        except Exception as e:
            print(f"[KAFKA ERROR] Erro ao enviar quality_event: {e}")
            return False

    def send_anomaly_event(self, event: AnomalyEvent) -> bool:
        """
        Envia evento de anomalia para Kafka (para treinamento de ML)

        Args:
            event: Dados da anomalia detectada

        Returns:
            True se enviado com sucesso
        """
        if not self.enabled or not self._producer:
            return False

        try:
            self._producer.produce(
                topic=self.topic_anomaly_events,
                key=event.machine_id.encode("utf-8"),
                value=self._serialize(event.to_dict()),
                callback=self._delivery_callback
            )
            return True
        except BufferError:
            print(f"[KAFKA] Buffer cheio, aguardando...")
            self._producer.poll(1.0)
            return self.send_anomaly_event(event)
        except Exception as e:
            print(f"[KAFKA ERROR] Erro ao enviar anomaly_event: {e}")
            return False

    def flush(self, timeout: float = 10.0):
        """
        Força envio de todas as mensagens pendentes

        Args:
            timeout: Tempo máximo de espera em segundos
        """
        if self._producer:
            remaining = self._producer.flush(timeout)
            if remaining > 0:
                print(f"[KAFKA WARNING] {remaining} mensagens não foram entregues")

    def poll(self, timeout: float = 0.0):
        """
        Processa callbacks de entrega

        Args:
            timeout: Tempo máximo de espera
        """
        if self._producer:
            self._producer.poll(timeout)

    def close(self):
        """Fecha conexão com Kafka"""
        if self._producer:
            self.flush(30.0)
            print(f"[KAFKA] Fechando conexão. Enviadas: {self.messages_sent}, Falhas: {self.messages_failed}")

    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de envio"""
        return {
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed
        }
