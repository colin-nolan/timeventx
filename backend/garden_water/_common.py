import os
import sys
from _thread import LockType
from pathlib import Path

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# XXX: it is likely this would need to be changed for a RP2040 that is not a Raspberry Pi Pico
RP2040_DETECTED = sys.platform == "rp2"


def noop_if_not_rp2040(wrappable: callable) -> callable:
    from garden_water._logging import get_logger

    logger = get_logger(__name__)

    def wrapped(*args, **kwargs):
        if not RP2040_DETECTED:
            logger.info(f"Skipping {wrappable.__name__} as not running on a RP2040")
            return
        return wrappable(*args, **kwargs)

    return wrapped


# `pathlib.resolve` and `os.path.abspath` do not work as expected in the MicroPython modules
def resolve_path(path: Path) -> Path:
    is_file = path.is_file()
    os.chdir(str(path.parent if is_file else path))
    return Path(f"{os.getcwd()}/{path.name}") if is_file else os.getcwd()
