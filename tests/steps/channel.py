from pytest_bdd import given

from ..async_step import async_step


@given("a mocked channel")
@async_step
async def mock_channel(mocker, channel):
    mocker.patch(
        "nerdd_backend.lifespan.InitializeAppLifespan.get_channel",
        return_value=channel,
    )
