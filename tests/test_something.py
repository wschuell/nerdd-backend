import asyncio
import json

from pytest_bdd import given, parsers, scenarios, then, when

from .async_step import async_step

scenarios("features")


@when(
    parsers.parse("the client sends a POST request to {url} with content\n{data}"),
    target_fixture="response",
)
def post_request(client, url, data):
    response = client.post(url, json=json.loads(data))
    print(response.json())
    return response


@when(parsers.parse("the client requests {url}"), target_fixture="response")
def response(client, url):
    response = client.get(url)
    return response


@then(parsers.parse("the status code of the response is {expected_status_code:d}"))
def check_status_code(response, expected_status_code):
    status_code = response.status_code
    assert status_code == expected_status_code


@then(parsers.parse("the client receives {expected_response}"))
def check_response(response, expected_response):
    decoded = json.loads(expected_response)
    assert response.json() == decoded, f"Expected {decoded}, got {response.json()}"


@when(parsers.parse("we wait for {seconds:d} seconds"))
@async_step
async def wait_for_seconds(seconds):
    await asyncio.sleep(seconds)
