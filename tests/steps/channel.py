from nerdd_link.tests import async_step
from pytest_bdd import given


@given("a mocked channel")
@async_step
async def mock_channel(mocker, channel):
    mocker.patch(
        "nerdd_backend.main.get_channel",
        return_value=channel,
    )
