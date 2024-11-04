import logging

from ..data import repository

__all__ = ["KafkaModuleConsumer"]

logger = logging.getLogger(__name__)


class KafkaModuleConsumer:
    def __init__(self):
        pass

    async def start(self):
        pass

    async def consume(self, message):
        config = message
        logger.info(f"Processing 'init' message for module {config['name']}")
        await repository.upsert_module(config)
