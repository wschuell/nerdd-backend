import logging

from .abstract_lifespan import AbstractLifespan

__all__ = ["ActionLifespan"]

logger = logging.getLogger(__name__)


class ActionLifespan(AbstractLifespan):
    def __init__(self, action_creator):
        super().__init__()
        self.action_creator = action_creator

    async def start(self, app):
        self.action = self.action_creator(app)
        logger.info(f"Start action {self.action}")

    async def run(self):
        logger.info(f"Run action {self.action}")
        await self.action.run()

    async def stop(self):
        logger.info(f"Stop action {self.action}")
        self.action = None
