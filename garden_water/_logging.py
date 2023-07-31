from logging import Logger, Formatter, FileHandler
import logging
from typing import Optional

from garden_water.configuration import Configuration

DEFAULT_LOG_FILE_LOCATION = "main.log"
DEFAULT_LOG_LEVEL = logging.WARNING

_LOGGERS_TO_SETUP = []
_LOGGER_LEVEL: Optional[int] = None
_LOGGER_HANDLER: Optional[FileHandler] = None


def setup_logging(configuration: Configuration):
    formatter = Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")

    file_handler = FileHandler(configuration.get(Configuration.LOG_FILE_LOCATION, DEFAULT_LOG_FILE_LOCATION))
    file_handler.setLevel(configuration.get(Configuration.LOG_LEVEL, DEFAULT_LOG_LEVEL))
    file_handler.setFormatter(formatter)

    log_level = configuration.get(Configuration.LOG_LEVEL, DEFAULT_LOG_LEVEL)

    global _LOGGER_HANDLER, _LOGGER_LEVEL
    _LOGGER_LEVEL = log_level
    _LOGGER_HANDLER = file_handler

    while len(_LOGGERS_TO_SETUP) > 0:
        logger = _LOGGERS_TO_SETUP.pop()
        logger.setLevel(log_level)
        logger.addHandler(file_handler)


def get_logger(name: str) -> Logger:
    # XXX: hack to deal with main module
    name = name if name != "__main__" else f"{__name__.split('.')[0]}.main"
    logger = logging.getLogger(name)

    if _LOGGER_HANDLER is not None and _LOGGER_LEVEL is not None:
        logger.addHandler(_LOGGER_HANDLER)
        logger.setLevel(_LOGGER_LEVEL)
    else:
        global _LOGGERS_TO_SETUP
        _LOGGERS_TO_SETUP.append(logger)

    return logger
