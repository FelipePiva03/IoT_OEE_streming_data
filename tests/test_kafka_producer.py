"""
Testes para o Kafka Producer
"""
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.producer.kafka.producer import KafkaEventProducer
from src.producer.schemas.events import (
    MachineEvent,
    SensorMetric,
    QualityEvent,
    MachineStatus,
    EventType,
    QualityResult,
    DefectType
)


class TestKafkaProducerConfiguration:
    """Testes de configuração do producer"""

    def test_default_configuration(self):
        """Testa configuração padrão quando Kafka não está disponível"""
        with patch("src.producer.kafka.producer.Producer") as mock_producer:
            mock_producer.side_effect = Exception("Kafka not available")

            with pytest.raises(Exception):
                producer = KafkaEventProducer(enabled=True)

    def test_disabled_producer(self):
        """Testa producer desabilitado"""
        producer = KafkaEventProducer(enabled=False)

        assert producer.enabled is False
        assert producer._producer is None
        assert producer.messages_sent == 0
        assert producer.messages_failed == 0

    def test_configuration_from_params(self):
        """Testa configuração via parâmetros"""
        producer = KafkaEventProducer(
            bootstrap_servers="custom:9092",
            topic_machine_events="custom-machine",
            topic_sensor_metrics="custom-sensor",
            topic_quality_events="custom-quality",
            enabled=False
        )

        assert producer.bootstrap_servers == "custom:9092"
        assert producer.topic_machine_events == "custom-machine"
        assert producer.topic_sensor_metrics == "custom-sensor"
        assert producer.topic_quality_events == "custom-quality"

    def test_configuration_from_env(self):
        """Testa configuração via variáveis de ambiente"""
        with patch.dict(os.environ, {
            "KAFKA_BOOTSTRAP_SERVERS": "env-kafka:9092",
            "KAFKA_TOPIC_MACHINE_EVENTS": "env-machine",
            "KAFKA_TOPIC_SENSOR_METRICS": "env-sensor",
            "KAFKA_TOPIC_QUALITY_EVENTS": "env-quality"
        }):
            producer = KafkaEventProducer(enabled=False)

            assert producer.bootstrap_servers == "env-kafka:9092"
            assert producer.topic_machine_events == "env-machine"
            assert producer.topic_sensor_metrics == "env-sensor"
            assert producer.topic_quality_events == "env-quality"

    def test_params_override_env(self):
        """Testa que parâmetros têm prioridade sobre env"""
        with patch.dict(os.environ, {
            "KAFKA_BOOTSTRAP_SERVERS": "env-kafka:9092"
        }):
            producer = KafkaEventProducer(
                bootstrap_servers="param-kafka:9092",
                enabled=False
            )

            assert producer.bootstrap_servers == "param-kafka:9092"


class TestKafkaProducerSerialization:
    """Testes de serialização de eventos"""

    @pytest.fixture
    def producer(self):
        """Producer desabilitado para testes"""
        return KafkaEventProducer(enabled=False)

    @pytest.fixture
    def machine_event(self):
        """Evento de máquina para testes"""
        return MachineEvent(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            event_type=EventType.STATUS_CHANGE.value,
            status=MachineStatus.RUNNING.value,
            previous_status=MachineStatus.WARMUP.value,
            cycle_count=10,
            shift="day",
            operator_id="op_1",
            reason="Test transition"
        )

    @pytest.fixture
    def sensor_metric(self):
        """Métrica de sensor para testes"""
        return SensorMetric(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            temperature=65.5,
            vibration=2.3,
            speed_rpm=2500,
            pressure=6.5,
            power_consumption=15.2,
            operating_hours=100.5
        )

    @pytest.fixture
    def quality_event(self):
        """Evento de qualidade para testes"""
        return QualityEvent(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            cycle_count=10,
            result=QualityResult.NOK.value,
            defect_type=DefectType.DIMENSIONAL.value,
            defect_severity=3,
            inspector_id="inspector_1",
            batch_id="batch_001"
        )

    def test_serialize_machine_event(self, producer, machine_event):
        """Testa serialização de evento de máquina"""
        data = machine_event.to_dict()
        serialized = producer._serialize(data)

        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode("utf-8"))
        assert deserialized["machine_id"] == "test_machine"
        assert deserialized["status"] == "running"

    def test_serialize_sensor_metric(self, producer, sensor_metric):
        """Testa serialização de métrica de sensor"""
        data = sensor_metric.to_dict()
        serialized = producer._serialize(data)

        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode("utf-8"))
        assert deserialized["temperature"] == 65.5
        assert deserialized["speed_rpm"] == 2500

    def test_serialize_quality_event(self, producer, quality_event):
        """Testa serialização de evento de qualidade"""
        data = quality_event.to_dict()
        serialized = producer._serialize(data)

        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode("utf-8"))
        assert deserialized["result"] == "nok"
        assert deserialized["defect_type"] == "dimensional"


class TestKafkaProducerSending:
    """Testes de envio de mensagens"""

    @pytest.fixture
    def mock_producer(self):
        """Producer com Kafka mockado"""
        with patch("src.producer.kafka.producer.Producer") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            producer = KafkaEventProducer(
                bootstrap_servers="test:9092",
                enabled=True
            )

            yield producer, mock_instance

    @pytest.fixture
    def machine_event(self):
        return MachineEvent(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            event_type=EventType.STATUS_CHANGE.value,
            status=MachineStatus.RUNNING.value,
            previous_status=MachineStatus.WARMUP.value,
            cycle_count=10,
            shift="day",
            operator_id="op_1"
        )

    @pytest.fixture
    def sensor_metric(self):
        return SensorMetric(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            temperature=65.5,
            vibration=2.3,
            speed_rpm=2500,
            pressure=6.5,
            power_consumption=15.2,
            operating_hours=100.5
        )

    @pytest.fixture
    def quality_event(self):
        return QualityEvent(
            machine_id="test_machine",
            timestamp="2024-01-01T10:00:00.000Z",
            cycle_count=10,
            result=QualityResult.OK.value,
            inspector_id="inspector_1",
            batch_id="batch_001"
        )

    def test_send_machine_event(self, mock_producer, machine_event):
        """Testa envio de evento de máquina"""
        producer, mock_kafka = mock_producer

        result = producer.send_machine_event(machine_event)

        assert result is True
        mock_kafka.produce.assert_called_once()
        call_args = mock_kafka.produce.call_args
        assert call_args.kwargs["topic"] == "machine-events"
        assert call_args.kwargs["key"] == b"test_machine"

    def test_send_sensor_metric(self, mock_producer, sensor_metric):
        """Testa envio de métrica de sensor"""
        producer, mock_kafka = mock_producer

        result = producer.send_sensor_metric(sensor_metric)

        assert result is True
        mock_kafka.produce.assert_called_once()
        call_args = mock_kafka.produce.call_args
        assert call_args.kwargs["topic"] == "sensor-metrics"
        assert call_args.kwargs["key"] == b"test_machine"

    def test_send_quality_event(self, mock_producer, quality_event):
        """Testa envio de evento de qualidade"""
        producer, mock_kafka = mock_producer

        result = producer.send_quality_event(quality_event)

        assert result is True
        mock_kafka.produce.assert_called_once()
        call_args = mock_kafka.produce.call_args
        assert call_args.kwargs["topic"] == "quality-events"
        assert call_args.kwargs["key"] == b"test_machine"

    def test_send_disabled(self, machine_event):
        """Testa que envio retorna False quando desabilitado"""
        producer = KafkaEventProducer(enabled=False)

        result = producer.send_machine_event(machine_event)

        assert result is False

    def test_send_multiple_events(self, mock_producer, machine_event, sensor_metric, quality_event):
        """Testa envio de múltiplos eventos"""
        producer, mock_kafka = mock_producer

        producer.send_machine_event(machine_event)
        producer.send_sensor_metric(sensor_metric)
        producer.send_quality_event(quality_event)

        assert mock_kafka.produce.call_count == 3


class TestKafkaProducerStats:
    """Testes de estatísticas"""

    def test_initial_stats(self):
        """Testa estatísticas iniciais"""
        producer = KafkaEventProducer(enabled=False)
        stats = producer.get_stats()

        assert stats["messages_sent"] == 0
        assert stats["messages_failed"] == 0

    def test_delivery_callback_success(self):
        """Testa callback de entrega bem sucedida"""
        producer = KafkaEventProducer(enabled=False)

        producer._delivery_callback(None, MagicMock())

        assert producer.messages_sent == 1
        assert producer.messages_failed == 0

    def test_delivery_callback_failure(self):
        """Testa callback de falha de entrega"""
        producer = KafkaEventProducer(enabled=False)

        producer._delivery_callback(Exception("Error"), MagicMock())

        assert producer.messages_sent == 0
        assert producer.messages_failed == 1


class TestKafkaProducerFlushClose:
    """Testes de flush e close"""

    def test_flush_with_producer(self):
        """Testa flush quando producer está ativo"""
        with patch("src.producer.kafka.producer.Producer") as mock_class:
            mock_instance = MagicMock()
            mock_instance.flush.return_value = 0
            mock_class.return_value = mock_instance

            producer = KafkaEventProducer(enabled=True)
            producer.flush(5.0)

            mock_instance.flush.assert_called_once_with(5.0)

    def test_flush_without_producer(self):
        """Testa flush quando producer está desabilitado"""
        producer = KafkaEventProducer(enabled=False)
        # Não deve lançar exceção
        producer.flush()

    def test_close_with_producer(self):
        """Testa close quando producer está ativo"""
        with patch("src.producer.kafka.producer.Producer") as mock_class:
            mock_instance = MagicMock()
            mock_instance.flush.return_value = 0
            mock_class.return_value = mock_instance

            producer = KafkaEventProducer(enabled=True)
            producer.close()

            mock_instance.flush.assert_called_once()

    def test_close_without_producer(self):
        """Testa close quando producer está desabilitado"""
        producer = KafkaEventProducer(enabled=False)
        # Não deve lançar exceção
        producer.close()


class TestKafkaProducerPoll:
    """Testes de poll"""

    def test_poll_with_producer(self):
        """Testa poll quando producer está ativo"""
        with patch("src.producer.kafka.producer.Producer") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            producer = KafkaEventProducer(enabled=True)
            producer.poll(1.0)

            mock_instance.poll.assert_called_once_with(1.0)

    def test_poll_without_producer(self):
        """Testa poll quando producer está desabilitado"""
        producer = KafkaEventProducer(enabled=False)
        # Não deve lançar exceção
        producer.poll()
