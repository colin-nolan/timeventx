import math
import os
import sys
import time
from pathlib import Path
from time import sleep
from typing import Optional

from garden_water._common import RP2040_DETECTED, noop_if_not_rp2040
from garden_water._logging import flush_file_logs, get_logger, setup_logging
from garden_water.configuration import DEFAULT_CONFIGURATION_FILE_NAME, Configuration
from garden_water.timer_runner import TimerRunner
from garden_water.timers.collections.database import TimersDatabase
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.web_server import app

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio


DEFAULT_CONFIGURATION_FILE_LOCATION = Path("/") / DEFAULT_CONFIGURATION_FILE_NAME
WIFI_CONNECTION_CHECK_PERIOD = 0.5


logger = get_logger(__name__)


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


@noop_if_not_rp2040
def sync_time():
    # Deferring import to allow testing using MicroPython without a network module
    import ntptime

    # FIXME: harden against network failures
    ntptime.settime()


@noop_if_not_rp2040
def setup_device(configuration: Configuration):
    wifi_ssid = configuration[Configuration.WIFI_SSID]
    wifi_password = configuration[Configuration.WIFI_PASSWORD]
    logger.info(f"Connecting to WiFi: {wifi_ssid}")
    connect_to_wifi(wifi_ssid, wifi_password)

    logger.info("Synchronising time")
    sync_time()
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    logger.info(f"Time synchronised: {formatted_time}")


async def inner_main(configuration: Configuration):
    setup_device(configuration)

    logger.info("Setting up database")
    timers_database = ListenableTimersCollection(TimersDatabase(configuration[Configuration.TIMERS_DATABASE_LOCATION]))

    # TODO: setup on/off actions
    timer_runner = TimerRunner(timers_database, lambda: None, lambda: None)

    tasks = []

    logger.info("Starting web server")
    app.configuration = configuration
    app.database = timers_database
    app.timer_runner = timer_runner
    tasks.append(
        asyncio.create_task(
            app.start_server(
                host=configuration.get_with_standard_default(Configuration.BACKEND_HOST),
                port=configuration.get_with_standard_default(Configuration.BACKEND_PORT),
                # TODO: debug
                debug=True,
            )
        )
    )

    logger.info("Awaiting tasks")
    await asyncio.gather(*tasks)

    logger.error("Website has shutdown")


def reset(cooldown_time_in_seconds: int = 10):
    logger.info(f"Resetting after a cooldown of {cooldown_time_in_seconds}s (prevents rapid reset loops)")
    sleep(cooldown_time_in_seconds)

    if RP2040_DETECTED:
        import machine

        machine.soft_reset()
    else:
        os.execv(sys.executable, ["python"] + sys.argv)


def main(configuration_location: Optional[Path] = DEFAULT_CONFIGURATION_FILE_LOCATION):
    configuration = Configuration(configuration_location if configuration_location.exists() else None)

    setup_logging(
        configuration.get_with_standard_default(Configuration.LOG_LEVEL),
        configuration.get(Configuration.LOG_FILE_LOCATION),
    )
    logger.info("Device turned on")

    try:
        asyncio.run(inner_main(configuration))
    except KeyboardInterrupt:
        logger.info("Terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        if configuration.get_with_standard_default(Configuration.RESTART_ON_ERROR):
            reset()
        else:
            raise


if __name__ == "__main__":
    main()
