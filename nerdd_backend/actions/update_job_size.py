import logging

from nerdd_link import Action, Channel, LogMessage

from ..data import Repository

__all__ = ["UpdateJobSize"]

logger = logging.getLogger(__name__)


class UpdateJobSize(Action[LogMessage]):
    def __init__(self, channel: Channel, repository: Repository) -> None:
        super().__init__(channel.logs_topic())
        self.repository = repository

    async def _process_message(self, message: LogMessage) -> None:
        if message.message_type == "report_job_size":
            logger.info(f"Update job size {message}")

            # get job
            job = await self.repository.get_job_by_id(message.job_id)

            # update job size
            job.num_entries_total = message.num_entries
            job.num_checkpoints_total = message.num_checkpoints

            await self.repository.upsert_job(job)

    def _get_group_name(self):
        return "update-job-size"
