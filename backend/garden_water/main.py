import os
import sys
from pathlib import Path
from time import sleep
from typing import Optional

from garden_water._common import RP2040_DETECTED
from garden_water._logging import get_logger, setup_logging
from garden_water.configuration import DEFAULT_CONFIGURATION_FILE_NAME, Configuration
from garden_water.rp2040 import setup_device
from garden_water.timer_runner import TimerRunner
from garden_water.timers.collections.database import TimersDatabase
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.web_server import app

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio


DEFAULT_CONFIGURATION_FILE_LOCATION = Path("/") / DEFAULT_CONFIGURATION_FILE_NAME


logger = get_logger(__name__)


async def inner_main(configuration: Configuration):
    setup_device(configuration)

    logger.info("Setting up database")
    timers_database = ListenableTimersCollection(TimersDatabase(configuration[Configuration.TIMERS_DATABASE_LOCATION]))

    logger.info("Starting task runner")
    # TODO: setup on/off actions
    on_action = lambda: None
    off_action = lambda: None
    timer_runner = TimerRunner(timers_database, on_action, off_action)
    timer_runner_task = asyncio.create_task(timer_runner.run())

    logger.info("Starting web server")
    app.configuration = configuration
    app.database = timers_database
    app.timer_runner = timer_runner
    server_task = asyncio.create_task(
        app.start_server(
            host=configuration.get_with_standard_default(Configuration.BACKEND_HOST),
            port=configuration.get_with_standard_default(Configuration.BACKEND_PORT),
        )
    )

    logger.info("Awaiting tasks")
    await server_task

    timer_runner.run_stop_event.set()
    timer_runner.timers_change_event.set()
    await timer_runner_task

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
