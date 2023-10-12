import logging
import sys
from _thread import LockType, allocate_lock
from logging import FileHandler, Formatter, Handler, Logger, StreamHandler
from pathlib import Path
from typing import Any, Callable, Collection, Coroutine, Optional, TypeAlias, Union

from garden_water._common import RP2040_DETECTED

SyncLogListener: TypeAlias = Callable[[str], None]
AsyncLogListener: TypeAlias = Coroutine
LogListener: TypeAlias = Union[SyncLogListener, AsyncLogListener]


_LOGGERS_TO_SETUP: list[Logger] = []
_LOGGER_LEVEL: Optional[int] = None
_LOGGER_HANDLERS: Optional[Collection[FileHandler]] = None
_LOGGERS: list[Logger] = []
_LOG_FILE_LOCATION: Optional[Path] = None
# FIXME: does allocate_lock work with asyncio?
_LOG_FILE_LOCK = allocate_lock()


def get_logger(name: str) -> Logger:
    # XXX: hack to deal with main module
    name = name if name != "__main__" else f"{__name__.split('.')[0]}.main"
    logger = logging.getLogger(name)

    if _LOGGER_HANDLERS is not None and _LOGGER_LEVEL is not None:
        for handler in _LOGGER_HANDLERS:
            logger.addHandler(handler)
        logger.setLevel(_LOGGER_LEVEL)
    else:
        global _LOGGERS_TO_SETUP
        _LOGGERS_TO_SETUP.append(logger)

    _LOGGERS.append(logger)
    return logger


logger = get_logger(__name__)


def setup_logging(logger_level: int, log_file_location: Optional[Path] = None) -> bool:
    from garden_water.configuration import Configuration, ConfigurationNotFoundError

    global _LOGGER_LEVEL, _LOGGER_HANDLERS, _LOG_FILE_LOCATION

    if _LOGGER_LEVEL is not None:
        logger.info("Logging already setup")
        return False

    _LOGGER_HANDLERS = []
    _LOGGER_LEVEL = logger_level
    formatter = Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")

    if log_file_location is not None:
        _LOG_FILE_LOCATION = log_file_location
        file_handler = LockableHandler(FileHandler(str(_LOG_FILE_LOCATION)), _LOG_FILE_LOCK)
        file_handler.setLevel(_LOGGER_LEVEL)
        file_handler.setFormatter(formatter)
        _LOGGER_HANDLERS.append(file_handler)

    # Create a StreamHandler for logging to stderr
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setLevel(_LOGGER_LEVEL)
    stream_handler.setFormatter(formatter)
    _LOGGER_HANDLERS.append(stream_handler)

    while len(_LOGGERS_TO_SETUP) > 0:
        setting_up_logger = _LOGGERS_TO_SETUP.pop()
        setting_up_logger.setLevel(_LOGGER_LEVEL)
        for handler in _LOGGER_HANDLERS:
            setting_up_logger.addHandler(handler)

    return True


def reset_logging():
    global _LOGGER_LEVEL, _LOGGER_HANDLERS, _LOG_FILE_LOCATION, _LOGGERS_TO_SETUP
    _LOGGER_LEVEL = None
    _LOGGER_HANDLERS = None
    _LOG_FILE_LOCATION = None
    _LOGGERS_TO_SETUP = _LOGGERS


def flush_file_logs():
    for _logger in _LOGGERS:
        for handler in _logger.handlers:
            if isinstance(handler, LockableHandler):
                handler = handler.wrapped_handler
            if not isinstance(handler, FileHandler):
                continue
            try:
                handler.flush()
            except AttributeError:
                # MicroPython logger doesn't implement flush but does allow access to the underling file handle
                handler.stream.flush()


def clear_logs():
    if _LOG_FILE_LOCATION is None:
        raise RuntimeError("Logging not setup yet")

    if _LOG_FILE_LOCATION.exists():
        with _LOG_FILE_LOCK:
            _LOG_FILE_LOCATION.unlink()


class LockableHandler(Handler):
    """
    A logging handler that wraps another handler and uses a lock to allow the handler to be stopped as the logs are
    cleared.

    The micropython-lib version of the `logging` module does not use locks so it is not possible to ab(use) them for
    log rotation.
    """

    def __init__(self, wrapped_handler: Handler, lock: LockType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wrapped_handler = wrapped_handler
        # Do NOT use the property `lock`, as the CPython implementation already uses this property
        self.custom_lock = lock

    def __getattr__(self, name: str) -> callable:
        if RP2040_DETECTED:
            # MicroPython uses `__getattribute__` instead
            return super().__getattr__(name)
        return getattr(self.wrapped_handler if name != "emit" else self, name)

    def __getattribute__(self, name: str) -> Any:
        if not RP2040_DETECTED:
            # CPython uses `__getattr__` instead
            return super().__getattribute__(name)
        return getattr(self.wrapped_handler if name != "emit" else self, name)

    def emit(self, *args, **kwargs):
        with self.custom_lock:
            self.wrapped_handler.emit(*args, **kwargs)
