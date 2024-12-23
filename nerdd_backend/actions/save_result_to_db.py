import logging

from nerdd_link import Action, Channel, ResultMessage

from ..data import Repository
from ..models import Result

__all__ = ["SaveResultToDb"]

logger = logging.getLogger(__name__)


class SaveResultToDb(Action[ResultMessage]):
    def __init__(self, channel: Channel, repository: Repository) -> None:
        super().__init__(channel.results_topic())
        self.repository = repository

    async def _process_message(self, message: ResultMessage) -> None:
        # TODO: check if corresponding module has correct task type (e.g. "derivative_prediction")
        try:
            if hasattr(message, "atom_id"):
                id = f"{message.job_id}-{message.mol_id}-{message.atom_id}"
            elif hasattr(message, "derivative_id"):
                id = f"{message.job_id}-{message.mol_id}-{message.derivative_id}"
            else:
                id = f"{message.job_id}-{message.mol_id}"
            await self.repository.create_result(Result(id=id, **message.model_dump()))
        except Exception as e:
            logger.error(f"Error consuming message: {e}")

    def _get_group_name(self):
        return "save-result-to-db"
