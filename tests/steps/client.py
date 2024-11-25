import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient


@pytest_asyncio.fixture
async def client():
    from nerdd_backend.main import app

    async with LifespanManager(app):
        client = TestClient(app)
        yield client
