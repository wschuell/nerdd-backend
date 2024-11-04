import logging

from ..data import repository

__all__ = ["KafkaJobConsumer"]

logger = logging.getLogger(__name__)


class KafkaJobConsumer:
    def __init__(self):
        pass

    async def start(self):
        pass

    async def consume(self, message):
        if message["action_type"] in ["create", "update"]:
            logger.info(f"Upsert job {message}")
            message.pop("action_type")
            await repository.upsert_job(message)
