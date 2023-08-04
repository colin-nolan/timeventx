import logging
import sys
from logging import FileHandler, Formatter, Logger, StreamHandler
from typing import Collection, Optional

from garden_water.configuration import Configuration

_LOGGERS_TO_SETUP = []
_LOGGER_LEVEL: Optional[int] = None
_LOGGER_HANDLERS: Optional[Collection[FileHandler]] = None
_LOGGERS = []


def setup_logging(configuration: Configuration):
    formatter = Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")

    # Create a FileHandler for logging to a file
    file_handler = FileHandler(str(configuration[Configuration.LOG_FILE_LOCATION]))
    file_handler.setLevel(configuration[Configuration.LOG_LEVEL])
    file_handler.setFormatter(formatter)

    # Create a StreamHandler for logging to stderr
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setLevel(configuration[Configuration.LOG_LEVEL])
    stream_handler.setFormatter(formatter)

    log_level = configuration[Configuration.LOG_LEVEL]

    global _LOGGER_HANDLERS, _LOGGER_LEVEL
    _LOGGER_LEVEL = log_level
    _LOGGER_HANDLERS = (file_handler, stream_handler)

    while len(_LOGGERS_TO_SETUP) > 0:
        logger = _LOGGERS_TO_SETUP.pop()
        logger.setLevel(log_level)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)


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
