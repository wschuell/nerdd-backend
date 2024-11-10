import asyncio
from threading import Thread

__all__ = ["AbstractLifespan"]


class AbstractLifespan:
    def __init__(self):
        pass

    async def start(self, app):
        pass

    async def run(self):
        pass

    async def stop(self):
        pass
