from ..data import repository
from .abstract_lifespan import AbstractLifespan


class InitializeDatabaseLifespan(AbstractLifespan):
    def __init__(self):
        super().__init__()

    async def start(self, app):
        await repository.initialize()
