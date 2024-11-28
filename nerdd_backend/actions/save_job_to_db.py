import logging

from nerdd_link import Action, Channel, JobMessage

from ..data import RethinkDbRepository

__all__ = ["SaveJobToDb"]

logger = logging.getLogger(__name__)


class SaveJobToDb(Action[JobMessage]):
    def __init__(self, channel: Channel, repository: RethinkDbRepository) -> None:
        super().__init__(channel.jobs_topic())
        self.repository = repository

    async def _process_message(self, message: JobMessage) -> None:
        await self.repository.upsert_job(message)

    def _get_group_name(self):
        return "save-jobs-to-db"
