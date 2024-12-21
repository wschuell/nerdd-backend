import logging

from nerdd_link import Action, Channel, ResultCheckpointMessage, SerializationResultMessage

from ..data import Repository
from ..models import JobUpdate

__all__ = ["ProcessSerializationResult"]

logger = logging.getLogger(__name__)


class ProcessSerializationResult(Action[SerializationResultMessage]):
    def __init__(self, channel: Channel, repository: Repository) -> None:
        super().__init__(channel.serialization_results_topic())
        self.repository = repository

    async def _process_message(self, message: ResultCheckpointMessage) -> None:
        job_id = message.job_id
        output_format = message.output_format
        logger.info(f"Received serialization result for job {job_id} in format {output_format}")
        await self.repository.update_job(JobUpdate(id=job_id, new_output_formats=[output_format]))

    def _get_group_name(self):
        return "save-result-checkpoint-to-db"
