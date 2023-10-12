import logging
import os
import socket
from multiprocessing import Process
from pathlib import Path
from time import sleep
from typing import TypeAlias
from unittest.mock import patch

import pytest
import requests

from garden_water.configuration import Configuration
from garden_water.main import main

ServiceLocation: TypeAlias = str


def _get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


@pytest.fixture()
def service(tmp_path: Path) -> ServiceLocation:
    frontend_path = tmp_path / "frontend"
    os.mkdir(frontend_path)

    port = _get_free_port()
    config_location = tmp_path / "config.ini"
    with patch.dict(
        os.environ,
        {
            key.environment_variable_name: str(value)
            for key, value in {
                Configuration.WIFI_SSID: "example-ssid",
                Configuration.WIFI_PASSWORD: "example-password",
                Configuration.FRONTEND_ROOT_DIRECTORY: frontend_path,
                Configuration.TIMERS_DATABASE_LOCATION: tmp_path / "timers.sqlite",
                Configuration.LOG_FILE_LOCATION: tmp_path / "log.txt",
                Configuration.BACKEND_PORT: port,
                Configuration.BACKEND_HOST: "127.0.0.1",
                Configuration.RESTART_ON_ERROR: False,
                Configuration.LOG_LEVEL: logging.DEBUG,
            }.items()
        },
    ):
        Configuration.write_env_to_config_file(config_location)

    service_process = Process(target=main, args=(config_location,))
    service_process.start()
    url = f"http://localhost:{port}"

    while service_process.is_alive():
        try:
            requests.head(url)
            break
        except requests.exceptions.ConnectionError:
            pass
        sleep(0.1)

    yield url

    response = requests.post(f"{url}/api/v1/shutdown")
    assert response.status_code == 202
    service_process.join()


def test_main(service: ServiceLocation):
    response = requests.get(f"{service}/api/v1/timers")
    assert response.status_code == 200
    assert response.json() == []
