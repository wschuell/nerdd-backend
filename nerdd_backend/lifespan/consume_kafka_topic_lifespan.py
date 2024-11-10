import asyncio
import json
import logging
import traceback

from aiokafka import AIOKafkaConsumer

from ..settings import KAFKA_BROKER_URL
from .abstract_lifespan import AbstractLifespan

__all__ = ["ConsumeKafkaTopicLifespan"]

logger = logging.getLogger(__name__)


class ConsumeKafkaTopicLifespan(AbstractLifespan):
    def __init__(self, topic, consumers):
        super().__init__()
        self.topic = topic
        self.consumers = consumers

    async def start(self, app):
        self.kafka_consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=KAFKA_BROKER_URL,
            # api_version="3.3.1",
            enable_auto_commit=False,
            group_id=f"nerdd-consumer-{self.topic}",
            auto_offset_reset="earliest",
        )
        await self.kafka_consumer.start()

    async def run(self):
        logger.info("Starting ConsumeKafkaTopicLifespan")

        logger.info("Starting consumers")
        for consumer in self.consumers:
            await consumer.start()

        try:
            while True:
                # we use polling (instead of iterating through the consumer messages)
                # to be able to cancel the consumer
                messages = await self.kafka_consumer.getmany(timeout_ms=1000)

                if messages:
                    for _, message_list in messages.items():
                        for message in message_list:
                            result = json.loads(message.value)
                            logger.info(f"Received message on {message.topic}")

                            try:
                                for consumer in self.consumers:
                                    await consumer.consume(result)

                                logger.info("Committing message")
                                await self.kafka_consumer.commit()
                            except Exception:
                                logger.info("Rolling back message")
                                logger.error(traceback.format_exc())
        except asyncio.CancelledError:
            logger.info("Stopping ConsumeKafkaTopicLifespan")
            await self.kafka_consumer.stop()
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
