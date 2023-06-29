from socket import socket

import pytest
import requests
from MicroWebSrv2 import MicroWebSrv2 as MicroWebSrv2Class

from garden_water.web_server import create_web_server


def _get_free_port() -> int:
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def server_location() -> MicroWebSrv2Class:
    port = _get_free_port()
    server = create_web_server(port, "localhost")
    server.StartManaged()
    yield f"http://localhost:{port}"
    server.Stop()


def test_get_timers(server_location: str):
    response = requests.get(f"{server_location}/timers")
    assert response.status_code == 200
    assert response.json() == []


def test_post_timer(server_location: str):
    response = requests.post(
        f"{server_location}/timer", json={"name": "bar", "start_time": "01:02:03", "duration": 60, "enabled": True}
    )
    print(response.content)
    assert response.status_code == 200


def test_post_timer_no_payload(server_location: str):
    response = requests.post(f"{server_location}/timer")
    assert response.status_code == 400


def test_post_timer_wrong_json_properties(server_location: str):
    response = requests.post(f"{server_location}/timer", json={"foo": "bar"})
    assert response.status_code == 400
