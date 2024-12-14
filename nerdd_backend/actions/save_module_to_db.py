import logging

from nerdd_link import Action, Channel, ModuleMessage

from ..data import Repository
from ..models import Module

__all__ = ["SaveModuleToDb"]

logger = logging.getLogger(__name__)


class SaveModuleToDb(Action[ModuleMessage]):
    def __init__(self, channel: Channel, repository: Repository) -> None:
        super().__init__(channel.modules_topic())
        self.repository = repository

    async def _process_message(self, message: ModuleMessage) -> None:
        logger.info(f"Creating a new module called {message.name}")
        await self.repository.upsert_module(Module(**message.model_dump()))

    def _get_group_name(self):
        return "save-module-to-db"
