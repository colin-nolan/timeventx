import logging
import os
import tempfile
from base64 import b64encode
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
from microdot_asyncio_test_client import TestClient

from timeventx._logging import get_logger, reset_logging, setup_logging
from timeventx.app import API_VERSION, app
from timeventx.configuration import Configuration
from timeventx.tests._common import (
    EXAMPLE_IDENTIFIABLE_TIMER_1,
    EXAMPLE_IDENTIFIABLE_TIMER_2,
    EXAMPLE_TIMER_1,
)
from timeventx.timers.collections.abc import IdentifiableTimersCollection
from timeventx.timers.collections.listenable import ListenableTimersCollection
from timeventx.timers.collections.memory import InMemoryIdentifiableTimersCollection
from timeventx.timers.serialisation import timer_to_json

logger = get_logger(__name__)

# Keep for debugging whilst writing tests
# setup_logging(logging.DEBUG)


@pytest.fixture
def database() -> IdentifiableTimersCollection:
    return ListenableTimersCollection(InMemoryIdentifiableTimersCollection())


@pytest.fixture
def configuration() -> Configuration:
    return Configuration()


@pytest.fixture
def api_test_client(database: IdentifiableTimersCollection, configuration: Configuration) -> TestClient:
    test_app = deepcopy(app)
    test_app.configuration = configuration
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


@pytest.mark.asyncio
async def test_post_timer_invalid_json(api_test_client: TestClient):
    response = await api_test_client.post(f"/api/{API_VERSION}/timer", body="{{nope}}")
    assert response.status_code == 400, response.text


@pytest.mark.asyncio
async def test_put_timer(api_test_client: TestClient):
    response = await api_test_client.put(
        f"/api/{API_VERSION}/timer/{EXAMPLE_IDENTIFIABLE_TIMER_1.id}", body=timer_to_json(EXAMPLE_IDENTIFIABLE_TIMER_1)
    )
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_delete_timer(api_test_client: TestClient, database: IdentifiableTimersCollection):
    database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
    response = await api_test_client.delete(f"/api/{API_VERSION}/timer/{EXAMPLE_IDENTIFIABLE_TIMER_1.id}")
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_delete_timer_that_does_not_exist(api_test_client: TestClient):
    response = await api_test_client.delete(f"/api/{API_VERSION}/timer/{EXAMPLE_IDENTIFIABLE_TIMER_1.id}")
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_serve_root(api_test_client: TestClient, configuration: Configuration):
    with tempfile.TemporaryDirectory() as temp_directory:
        with open(os.path.join(temp_directory, "index.html"), "w") as index_file:
            index_file.write("hello")

        with patch.dict(os.environ, {Configuration.FRONTEND_ROOT_DIRECTORY.environment_variable_name: temp_directory}):
            response = await api_test_client.get(f"/")
    assert response.status_code == 200, response.text
    assert response.text == "hello"
    assert response.headers["Content-Type"] == "text/html"


@pytest.mark.asyncio
async def test_serve_file(api_test_client: TestClient, configuration: Configuration):
    with tempfile.TemporaryDirectory() as temp_directory:
        Path(temp_directory, "test.jpg").touch()

        with patch.dict(os.environ, {Configuration.FRONTEND_ROOT_DIRECTORY.environment_variable_name: temp_directory}):
            response = await api_test_client.get(f"/test.jpg")
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_serve_file_unknown_type(api_test_client: TestClient, configuration: Configuration):
    with tempfile.TemporaryDirectory() as temp_directory:
        Path(temp_directory, "test").touch()

        with patch.dict(os.environ, {Configuration.FRONTEND_ROOT_DIRECTORY.environment_variable_name: temp_directory}):
            response = await api_test_client.get(f"/test")
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_serve_outside_frontend_directory(api_test_client: TestClient, configuration: Configuration):
    with tempfile.TemporaryDirectory() as temp_directory_outer:
        temp_directory = f"{temp_directory_outer}/inner"
        os.makedirs(temp_directory)
        Path(temp_directory_outer, "secret").touch()

        relative_secret_path = "../secret"
        assert Path(temp_directory, relative_secret_path).exists()

        with patch.dict(os.environ, {Configuration.FRONTEND_ROOT_DIRECTORY.environment_variable_name: temp_directory}):
            response = await api_test_client.get(f"/{relative_secret_path}")
    assert response.status_code == 404, response.text


# TODO: cannot run in parallel with tests against `_logging`
@pytest.mark.asyncio
async def test_get_logging(api_test_client: TestClient):
    with NamedTemporaryFile(mode="r") as file:
        with patch.dict(
            os.environ,
            {
                Configuration.LOG_FILE_LOCATION.environment_variable_name: file.name,
                Configuration.LOG_LEVEL.environment_variable_name: str(logging.DEBUG),
            },
        ):
            reset_logging()
            setup_logging(logging.INFO, Path(file.name))
            logger.info("test")

            response = await api_test_client.get(f"/api/{API_VERSION}/logs")
            assert response.status_code == 200, response.text


# TODO: cannot run in parallel with tests against `_logging`
@pytest.mark.asyncio
async def test_delete_logs(api_test_client: TestClient):
    with NamedTemporaryFile(mode="r", delete=False) as file:
        with patch.dict(
            os.environ,
            {
                Configuration.LOG_FILE_LOCATION.environment_variable_name: file.name,
                Configuration.LOG_LEVEL.environment_variable_name: str(logging.DEBUG),
            },
        ):
            reset_logging()
            setup_logging(logging.INFO, Path(file.name))

            response = await api_test_client.delete(f"/api/{API_VERSION}/logs")
            assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_double_slash_root(api_test_client: TestClient):
    response = await api_test_client.get(f"//")
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_get_config(api_test_client: TestClient):
    example_wifi_ssid = "example_wifi_ssid"
    with patch.dict(
        os.environ,
        {Configuration.WIFI_SSID.environment_variable_name: example_wifi_ssid},
    ):
        response = await api_test_client.get(f"/api/{API_VERSION}/config")
        assert response.status_code == 200, response.text
        assert response.json[Configuration.WIFI_SSID.ini_section][Configuration.WIFI_SSID.ini_option] == example_wifi_ssid


@pytest.mark.asyncio
async def test_authorisation(api_test_client: TestClient, configuration: Configuration):
    with patch.dict(
        os.environ,
        {Configuration.BASE64_ENCODED_CREDENTIALS.environment_variable_name: b64encode(b"user:pass").decode("UTF-8")},
    ):
        response = await api_test_client.get(f"/api/{API_VERSION}/timers")
        assert response.status_code == 401, response.text

        response = await api_test_client.get(
            f"/api/{API_VERSION}/timers", headers={"Authorization": f"Basic {b64encode(b'user:pass2').decode('UTF-8')}"}
        )
        assert response.status_code == 401, response.text

        response = await api_test_client.get(
            f"/api/{API_VERSION}/timers", headers={"Authorization": f"Basic {b64encode(b'user:pass').decode('UTF-8')}"}
        )
        assert response.status_code == 200, response.text
