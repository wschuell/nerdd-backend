from nerdd_link import KafkaChannel

from ..data import RethinkDbRepository
from ..settings import KAFKA_BROKER_URL
from .abstract_lifespan import AbstractLifespan


class InitializeAppLifespan(AbstractLifespan):
    def __init__(self):
        super().__init__()

    async def start(self, app):
        channel = self.get_channel()
        repository = self.get_repository()

        app.state.repository = repository
        app.state.channel = channel

        await repository.initialize()

    def get_channel(self):
        return KafkaChannel(KAFKA_BROKER_URL)

    def get_repository(self):
        return RethinkDbRepository()
