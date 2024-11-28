import logging

from nerdd_link import Action, Channel, ModuleMessage

from ..data import RethinkDbRepository

__all__ = ["SaveModuleToDb"]

logger = logging.getLogger(__name__)


class SaveModuleToDb(Action[ModuleMessage]):
    def __init__(self, channel: Channel, repository: RethinkDbRepository) -> None:
        super().__init__(channel.modules_topic())
        self.repository = repository

    async def _process_message(self, message: ModuleMessage) -> None:
        logger.info(f"Creating a new module called {message.name}")
        await self.repository.upsert_module(message)

    def _get_group_name(self):
        return "save-module-to-db"
