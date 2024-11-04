import logging

from ..data import repository

__all__ = ["KafkaResultConsumer"]

logger = logging.getLogger(__name__)


class KafkaResultConsumer:
    def __init__(self):
        pass

    async def start(self):
        pass

    async def consume(self, message):
        try:
            await repository.upsert_result(message)
        except Exception as e:
            logger.error(f"Error consuming message: {e}")
