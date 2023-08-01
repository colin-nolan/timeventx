import os
from pathlib import Path
from socket import socket

import pytest
import requests

from garden_water.tests._common import EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_IDENTIFIABLE_TIMER_2, EXAMPLE_TIMER_1
from garden_water.timers.serialisation import timer_to_json
from garden_water.web_server import get_timers_database


def _get_free_port() -> int:
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def server_location(tmpdir: Path) -> str:
    os.environ[DATABASE_LOCATION_ENVIRONMENT_VARIABLE] = f"sqlite:///{Path(tmpdir / 'test.db')}"
    port = _get_free_port()
    # FIXME
    server = create_web_server(port, "localhost")
    server.StartManaged()
    yield f"http://localhost:{port}"
    server.Stop()


def test_healthcheck(server_location: str):
    response = requests.get(f"{server_location}/healthcheck")
    assert response.status_code == 200, response.text
    assert response.json()


def test_get_timers(server_location: str):
    database = get_timers_database()
    database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
    database.add(EXAMPLE_IDENTIFIABLE_TIMER_2)

    response = requests.get(f"{server_location}/timers")
    assert response.status_code == 200, response.text
    assert response.json() == [
        timer_to_json(timer) for timer in (EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_IDENTIFIABLE_TIMER_2)
    ]


def test_get_timers_when_none(server_location: str):
    response = requests.get(f"{server_location}/timers")
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_post_timer(server_location: str):
    response = requests.post(
        f"{server_location}/timer",
        json=timer_to_json(EXAMPLE_TIMER_1),
    )
    assert response.status_code == 200, response.text


def test_post_timer_with_id(server_location: str):
    response = requests.post(
        f"{server_location}/timer",
        json=timer_to_json(EXAMPLE_IDENTIFIABLE_TIMER_1),
    )
    assert response.status_code == 403, response.text


def test_post_timer_no_payload(server_location: str):
    response = requests.post(f"{server_location}/timer")
    assert response.status_code == 400, response.text


def test_post_timer_wrong_json_properties(server_location: str):
    response = requests.post(f"{server_location}/timer", json={"foo": "bar"})
    assert response.status_code == 400, response.text
