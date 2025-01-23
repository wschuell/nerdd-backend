import asyncio
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

        # If a job was submitted and deleted during processing, results might still be generated.
        # In this case, we ignore the results of the deleted job.
        try:
            job = await self.repository.get_job_by_id(job_id)
        except RecordNotFoundError:
            logger.error(f"Job with id {job_id} not found. Ignoring this result.")
            return

        # TODO: check if corresponding module has correct task type (e.g. "derivative_prediction")

        # generate an id for the result
        if hasattr(message, "atom_id"):
            id = f"{job_id}-{message.mol_id}-{message.atom_id}"
        elif hasattr(message, "derivative_id"):
            id = f"{job_id}-{message.mol_id}-{message.derivative_id}"
        else:
            id = f"{job_id}-{message.mol_id}"

        # map sources to original file names
        if hasattr(message, "source") and not isinstance(message.source, str):

            async def _replace_source(source_id, repository):
                try:
                    source = await repository.get_source_by_id(source_id)
                except RecordNotFoundError:
                    return source_id
                return source.filename

            translated_sources = await asyncio.gather(
                *(_replace_source(source_id, self.repository) for source_id in message.source)
            )
            message.source = [s for s in translated_sources if s is not None]

        # save result
        await self.repository.create_result(Result(id=id, **message.model_dump()))

        # update set of processed entries in job
        await self.repository.update_job(
            JobUpdate(id=job_id, entries_processed=[message.mol_id])
        )

    def _get_group_name(self):
        return "save-result-to-db"
