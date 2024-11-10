from ..kafka import get_kafka_producer
from .abstract_lifespan import AbstractLifespan

__all__ = ["KafkaProducerLifespan"]


class KafkaProducerLifespan(AbstractLifespan):
    def __init__(self):
        pass

    async def start(self, app):
        producer = await get_kafka_producer()
        await producer.start()

    async def run(self):
        pass

    async def stop(self):
        producer = await get_kafka_producer()
        await producer.stop()
