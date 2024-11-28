import logging

from nerdd_link import Action, Channel, ResultMessage

from ..data import RethinkDbRepository

__all__ = ["SaveResultToDb"]

logger = logging.getLogger(__name__)


class SaveResultToDb(Action[ResultMessage]):
    def __init__(self, channel: Channel, repository: RethinkDbRepository) -> None:
        super().__init__(channel.results_topic())
        self.repository = repository

    async def _process_message(self, message: ResultMessage) -> None:
        try:
            await self.repository.upsert_result(message)
        except Exception as e:
            logger.error(f"Error consuming message: {e}")

    def _get_group_name(self):
        return "save-result-to-db"
