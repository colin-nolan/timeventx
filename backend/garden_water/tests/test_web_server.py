import logging
from copy import deepcopy
from socket import socket

import pytest
import requests
from microdot_asyncio_test_client import TestClient

from garden_water._logging import get_logger, setup_logging
from garden_water.configuration import Configuration
from garden_water.tests._common import (
    EXAMPLE_IDENTIFIABLE_TIMER_1,
    EXAMPLE_IDENTIFIABLE_TIMER_2,
    EXAMPLE_TIMER_1,
)
from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.timers.serialisation import timer_to_json
from garden_water.web_server import API_VERSION, app

# Logs are written to `pytest.log`
setup_logging(logging.DEBUG)
# logger = get_logger(__name__)


def _get_free_port() -> int:
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def database() -> IdentifiableTimersCollection:
    return ListenableTimersCollection(InMemoryIdentifiableTimersCollection())


@pytest.fixture
def api_test_client(database: IdentifiableTimersCollection) -> TestClient:
    test_app = deepcopy(app)
    test_app.configuration = Configuration()
    test_app.database = database
    return TestClient(test_app)


@pytest.mark.asyncio
async def test_healthcheck(api_test_client: TestClient):
    response = await api_test_client.get(f"/api/{API_VERSION}/healthcheck")
    assert response.status_code == 200, response.text
    assert response.json


@pytest.mark.asyncio
async def test_get_timers(api_test_client: TestClient, database: IdentifiableTimersCollection):
    database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
    database.add(EXAMPLE_IDENTIFIABLE_TIMER_2)

    response = await api_test_client.get(f"/api/{API_VERSION}/timers")
    assert response.status_code == 200, response.text
    assert response.json == [
        timer_to_json(timer) for timer in (EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_IDENTIFIABLE_TIMER_2)
    ]


@pytest.mark.asyncio
async def test_get_timers_when_none(api_test_client: TestClient):
    response = await api_test_client.get(f"/api/{API_VERSION}/timers")
    assert response.status_code == 200, response.text
    assert response.json == []


@pytest.mark.asyncio
async def test_post_timer(api_test_client: TestClient):
    response = await api_test_client.post(f"/api/{API_VERSION}/timer", body=timer_to_json(EXAMPLE_TIMER_1))
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_post_timer_with_id(api_test_client: TestClient):
    response = await api_test_client.post(
        f"/api/{API_VERSION}/timer",
        body=timer_to_json(EXAMPLE_IDENTIFIABLE_TIMER_1),
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_post_timer_no_payload(api_test_client: TestClient):
    response = await api_test_client.post(f"/api/{API_VERSION}/timer")
    assert response.status_code == 400, response.text


@pytest.mark.asyncio
async def test_post_timer_wrong_json_properties(api_test_client: TestClient):
    response = await api_test_client.post(f"/api/{API_VERSION}/timer", body={"foo": "bar"})
    assert response.status_code == 400, response.text
