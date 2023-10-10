import logging
from logging import makeLogRecord
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock, Thread
from time import sleep
from unittest.mock import MagicMock

import pytest

from garden_water._logging import _LOG_FILE_LOCK as fl
from garden_water._logging import (
    LockableHandler,
    clear_logs,
    flush_file_logs,
    get_logger,
    reset_logging,
    setup_logging,
)

_TEST_LOCK = Lock()


# To be used for tests that interact with logging globals, and hence cannot be ran in parallel
def _non_parallel_test(wrappable: callable):
    def wrapper(*args, **kwargs):
        with _TEST_LOCK:
            return wrappable(*args, **kwargs)

    return wrapper


@pytest.fixture()
def handler() -> LockableHandler:
    wrapped_handler = MagicMock()
    lock = Lock()
    return LockableHandler(wrapped_handler, lock)


@_non_parallel_test
def test_setup_logging():
    reset_logging()
    logger = get_logger(f"{__name__}.example")

    with NamedTemporaryFile(mode="r") as file:
        setup_logging(logging.INFO, Path(file.name))
        logger.error("hello")
        flush_file_logs()

        assert file.read().strip() == "hello"


@_non_parallel_test
def test_clear_logs():
    reset_logging()
    logger = get_logger(f"{__name__}.example2")

    with NamedTemporaryFile(mode="r", delete=False) as file:
        file_path = Path(file.name)
        setup_logging(logging.INFO, file_path)
        logger.error("hello")
        flush_file_logs()

        clear_logs()
        if file_path.exists():
            assert len(file_path.read_text()) == 0
            file_path.unlink()


class TestLockableHandler:
    def test_emit(self, handler: LockableHandler):
        record = makeLogRecord({1: 2})
        handler.lock.acquire()

        emit_thread = Thread(target=handler.emit, args=(record,))
        emit_thread.start()

        sleep(0.05)
        handler.lock.release()
        emit_thread.join()

        handler.wrapped_handler.emit.assert_called_once_with(record)

    def test_other(self, handler: LockableHandler):
        handler.other(123)
        handler.wrapped_handler.other.assert_called_once_with(123)
