import logging

from ..data import repository

__all__ = ["KafkaLogConsumer"]

logger = logging.getLogger(__name__)


class KafkaLogConsumer:
    def __init__(self):
        pass

    async def start(self):
        pass

    async def consume(self, message):
        if message["message_type"] == "report_job_size":
            logger.info(f"Update job {message}")

            # get job
            job = await repository.get_job_by_id(message["job_id"])

            # update job size
            job["num_entries_total"] = message["size"]

            await repository.upsert_job(job)
