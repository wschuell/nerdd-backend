import logging

from nerdd_link import Action, Channel, ResultCheckpointMessage, SerializationRequestMessage
from omegaconf import DictConfig

from ..data import Repository
from ..models import JobUpdate

__all__ = ["SaveResultCheckpointToDb"]

logger = logging.getLogger(__name__)


class SaveResultCheckpointToDb(Action[ResultCheckpointMessage]):
    def __init__(self, channel: Channel, repository: Repository, config: DictConfig) -> None:
        super().__init__(channel.result_checkpoints_topic())
        self.repository = repository
        self.config = config

    async def _process_message(self, message: ResultCheckpointMessage) -> None:
        job_id = message.job_id
        checkpoint_id = message.checkpoint_id
        logger.info(f"Received result checkpoint {checkpoint_id} for job {job_id}")
        job = await self.repository.update_job(
            JobUpdate(id=job_id, new_checkpoints_processed=[checkpoint_id])
        )

        # check if all checkpoints have been processed
        unique_checkpoints = set(job.checkpoints_processed)
        if len(unique_checkpoints) == job.num_checkpoints_total:
            # send request to write output files
            output_formats = self.config.output_formats
            for output_format in output_formats:
                await self.channel.serialization_requests_topic().send(
                    SerializationRequestMessage(
                        job_id=job_id,
                        job_type=job.job_type,
                        params=job.params,
                        output_format=output_format,
                    )
                )

    def _get_group_name(self):
        return "save-result-checkpoint-to-db"
