import logging

from nerdd_link import Action, Channel, ResultMessage

from ..data import RecordNotFoundError, Repository
from ..models import JobUpdate, Result

__all__ = ["SaveResultToDb"]

logger = logging.getLogger(__name__)


class SaveResultToDb(Action[ResultMessage]):
    def __init__(self, channel: Channel, repository: Repository) -> None:
        super().__init__(channel.results_topic())
        self.repository = repository

    async def _process_message(self, message: ResultMessage) -> None:
        job_id = message.job_id

        try:
            job = await self.repository.get_job_by_id(job_id)
        except RecordNotFoundError:
            logger.error(f"Job with id {job_id} not found")
            return

        # TODO: check if corresponding module has correct task type (e.g. "derivative_prediction")

        # generate an id for the result
        try:
            if hasattr(message, "atom_id"):
                id = f"{job_id}-{message.mol_id}-{message.atom_id}"
            elif hasattr(message, "derivative_id"):
                id = f"{job_id}-{message.mol_id}-{message.derivative_id}"
            else:
                id = f"{job_id}-{message.mol_id}"
            await self.repository.create_result(Result(id=id, **message.model_dump()))
        except Exception as e:
            logger.error(f"Error consuming message: {e}")

        # update job
        # TODO: there might be a RaceCondition here (no atomic transaction)
        num_entries_processed = await self.repository.get_num_processed_entries_by_job_id(job_id)
        await self.repository.update_job(
            JobUpdate(id=job_id, num_entries_processed=num_entries_processed)
        )

    def _get_group_name(self):
        return "save-result-to-db"
