import logging
import sys
from _thread import LockType, allocate_lock
from logging import FileHandler, Formatter, Logger, StreamHandler, Handler
from pathlib import Path
from typing import Collection, Optional, Callable, Iterable, Any, AsyncIterable, Coroutine, TypeAlias, Union

from garden_water.configuration import Configuration
import inspect

try:
    from io import TextIOBase
except ImportError:
    from io import IOBase as TextIOBase

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio


SyncLogListener: TypeAlias = Callable[[str], None]
AsyncLogListener: TypeAlias = Coroutine
LogListener: TypeAlias = Union[SyncLogListener, AsyncLogListener]


_LOGGERS_TO_SETUP: list[Logger] = []
_LOGGER_LEVEL: Optional[int] = None
_LOGGER_HANDLERS: Optional[Collection[FileHandler]] = None
_LOGGERS: list[Logger] = []
_LOG_FILE_LOCATION: Optional[Path] = None
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


def setup_logging(configuration: Configuration):
    global _LOGGER_LEVEL
    if _LOGGER_LEVEL is not None:
        raise RuntimeError("Logging already setup")

    formatter = Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")

    # Create a FileHandler for logging to a file
    global _LOG_FILE_LOCATION
    _LOG_FILE_LOCATION = configuration[Configuration.LOG_FILE_LOCATION]

    file_handler = LockableHandler(FileHandler(str(_LOG_FILE_LOCATION)), _LOG_FILE_LOCK)
    file_handler.setLevel(configuration[Configuration.LOG_LEVEL])
    file_handler.setFormatter(formatter)

    # Create a StreamHandler for logging to stderr
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setLevel(configuration[Configuration.LOG_LEVEL])
    stream_handler.setFormatter(formatter)

    # Create a stream that can be listened to
    listenable_stream = StreamHandler(ListenableStream())
    # TODO: it would be nice if this could be set dynamically when listened to
    listenable_stream.setLevel(configuration[Configuration.LOG_LEVEL])
    listenable_stream.setFormatter(formatter)

    log_level = configuration[Configuration.LOG_LEVEL]

    global _LOGGER_HANDLERS, _LOGGER_LEVEL
    _LOGGER_LEVEL = log_level
    _LOGGER_HANDLERS = (file_handler, stream_handler, listenable_stream)

    while len(_LOGGERS_TO_SETUP) > 0:
        logger = _LOGGERS_TO_SETUP.pop()
        logger.setLevel(log_level)
        for handler in _LOGGER_HANDLERS:
            logger.addHandler(handler)


def flush_file_logs():
    for logger in _LOGGERS:
        for handler in logger.handlers:
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
        self._wrapped_handler = wrapped_handler
        self._lock = lock

    def __getattribute__(self, name: str) -> callable:
        print("__getattribute__")
        attr = getattr(self._wrapped_handler if name != "emit" else self, name)
        print(f"{name} == {attr}")
        return attr

    def __getattr__(self, name: str) -> callable:
        print("__getattr__")

    def emit(self, *args, **kwargs):
        with self._lock:
            self._wrapped_handler.emit(*args, **kwargs)


class ListenableStream(TextIOBase):
    def __init__(self, listeners: Iterable[LogListener] = ()):
        self.listeners = list(listeners)

    def write(self, content: str) -> int:
        # print(f"Listeners: {self.listeners}")
        i = 0
        for listener in self.listeners:
            i += 1
            # Unfortunately, `iscoroutinefunction` is not implemented in the MicroPython `inspect` library in use
            # TODO: put listeners in buckets when added?
            if inspect.isfunction(listener):
                listener(content)
            else:
                # print(f"----- Calling listener {i}: {content}")
                asyncio.run(listener(content))
                # print("----- Finished calling listener")
        # print(f"Written: {len(content)}")
        return len(content)


def add_log_listener(listener: LogListener):
    # All loggers share the same handlers so don't need to add to each logger's handlers
    for handler in _LOGGER_HANDLERS:
        if not isinstance(handler, StreamHandler) or not isinstance(handler.stream, ListenableStream):
            continue
        handler.stream.listeners.append(listener)


def remove_log_listener(listener: LogListener):
    # All loggers share the same handlers so don't need to remove from each logger's handlers
    for handler in _LOGGER_HANDLERS:
        if not isinstance(handler, StreamHandler) or not isinstance(handler.stream, ListenableStream):
            continue
        try:
            handler.stream.listeners.remove(listener)
        except ValueError:
            pass


# `asynccontextmanager` is unfortunately not available yet (https://github.com/micropython/micropython-lib/pull/657)
class LogEmitter(AsyncIterable):
    def __init__(self):
        self._log_receive_event = asyncio.Event()
        self._log_receive_event_lock = asyncio.Lock()
        self._logs = []
        self._logs_lock = asyncio.Lock()

        # FIXME: context managed, with removal!
        add_log_listener(self._on_log)

    def __aiter__(self):
        return self

    async def __anext__(self):
        # print(f"Going for next: {len(self._logs)}")

        if len(self._logs) == 0:
            await self._log_receive_event.wait()

        # async with self._logs_lock:
        #     log = self._logs.pop(0)
        #
        # if len(self._logs) == 0:
        #     async with self._log_receive_event_lock:
        #         # Need to check for logs again, as logs may have been added whilst waiting for the lock
        #         if len(self._logs) == 0:
        #             self._log_receive_event.clear()

        log = "test"

        return log

    async def _on_log(self, line: str):
        async with self._logs_lock:
            self._logs.append(line)
        # TODO: are both locks required?
        async with self._log_receive_event_lock:
            self._log_receive_event.set()
