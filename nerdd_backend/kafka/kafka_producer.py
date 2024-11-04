import json

from aiokafka import AIOKafkaProducer

from ..settings import KAFKA_BROKER_URL

__all__ = ["get_kafka_producer"]

producer = None


async def get_kafka_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    return producer
