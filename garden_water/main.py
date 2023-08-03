import math
import time
from pathlib import Path
from typing import Optional

from garden_water._logging import get_logger, setup_logging
from garden_water.configuration import DEFAULT_CONFIGURATION_FILE_NAME, Configuration
from garden_water.timer_runner import TimerRunner
from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.web_server import app, set_timers_database

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


logger = get_logger(__name__)


# Location is relevant to CWD, which isn't ideal but on the PicoPi will be the root, which is the correct location.
# `__file__` and `os.path` do not work on MicroPython
# TODO: look at micropython-lib `os-path`
DEFAULT_CONFIGURATION_FILE_LOCATION = Path(DEFAULT_CONFIGURATION_FILE_NAME)
WIFI_CONNECTION_CHECK_PERIOD = 0.5


def connect_to_wifi(ssid: str, password: str, retries: int = math.inf, wait_for_connection_time_in_seconds: float = 60):
    # Deferring import to allow testing using MicroPython without a network module
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    retries_remaining = retries
    while not wlan.isconnected() and retries_remaining > 0:
        retries_remaining -= 1
        wlan.disconnect()
        wlan.connect(ssid, password)
        # Using inaccurate measure of wait time to avoid using functions from the `time` module
        waited_for = 0
        while not wlan.isconnected() and waited_for <= wait_for_connection_time_in_seconds:
            time.sleep(WIFI_CONNECTION_CHECK_PERIOD)
            waited_for += WIFI_CONNECTION_CHECK_PERIOD

    if not wlan.isconnected():
        raise RuntimeError("Failed to connect to WiFi")


def sync_time():
    # Deferring import to allow testing using MicroPython without a network module
    import ntptime

    # FIXME: harden against network failures
    ntptime.settime()


def setup_device(configuration: Configuration):
    wifi_ssid = configuration[Configuration.WIFI_SSID]
    wifi_password = configuration[Configuration.WIFI_PASSWORD]
    logger.info(f"Connecting to WiFi: {wifi_ssid}")
    connect_to_wifi(wifi_ssid, wifi_password)

    logger.info("Synchronising time")
    sync_time()
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    logger.info(f"Time synchronised: {formatted_time}")


def inner_main(configuration: Configuration):
    setup_device(configuration)

    logger.info("Setting up database")
    # timers_database = TimersDatabase(
    #     configuration.get(Configuration.TIMERS_DATABASE_LOCATION)
    # )

    timers_database = InMemoryIdentifiableTimersCollection()
    set_timers_database(timers_database)

    logger.info("Starting tweeter")
    asyncio.create_task(tweeter(timers_database))
    logger.info("Starting web server")
    app.run(debug=True)

    logger.error("Web server stopped")
    # FIXME


async def tweeter(timers: IdentifiableTimersCollection):
    # FIXME: `IdentifiableTimersCollection` need to be iterable
    timer_runner = TimerRunner(timers, lambda: None, lambda: None)

    while True:
        logger.info(timer_runner.on_off_intervals)
        await asyncio.sleep(5)


def main(configuration_location: Optional[Path] = DEFAULT_CONFIGURATION_FILE_LOCATION):
    configuration = Configuration(configuration_location if configuration_location.exists() else None)

    setup_logging(configuration)
    logger.info("Device turned on")

    try:
        inner_main(configuration)
    except Exception as e:
        logger.exception(e)

        # TODO: auto-restart mechanism - but care not to rapidly error loop
        raise e


if __name__ == "__main__":
    main()
