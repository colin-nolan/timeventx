import os
import sys
from pathlib import Path
from time import sleep
from typing import Optional

from timeventx._common import RP2040_DETECTED
from timeventx._logging import get_logger, setup_logging
from timeventx.actions.actions import ActionController, get_global_action_controller
from timeventx.app import app
from timeventx.configuration import DEFAULT_CONFIGURATION_FILE_NAME, Configuration
from timeventx.rp2040 import setup_device
from timeventx.timer_runner import TimerRunner
from timeventx.timers.collections.database import TimersDatabase
from timeventx.timers.collections.listenable import ListenableTimersCollection

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
    action_controller = get_action_controller(configuration)
    timer_runner = TimerRunner(timers_database, action_controller)
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


def get_action_controller(configuration: Configuration) -> ActionController:
    # Not using `imp` module as not implemented on MicroPython
    __import__(configuration[Configuration.ACTION_CONTROLLER_MODULE])

    action_controller = get_global_action_controller()
    if action_controller is None:
        raise RuntimeError("Action controller not set up")


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
