from io import BytesIO
from pathlib import Path
from typing import Iterable, IO, Callable, Any

import pytest

import garden_water.timers.collections._btree as btree
from garden_water.timers.collections._btree import BTree

EXAMPLE_KEY_1 = b"example_key_1"
EXAMPLE_KEY_2 = b"example_key_2"
EXAMPLE_KEY_3 = b"example_key_3"
EXAMPLE_VALUE_1 = b"example_value_1"
EXAMPLE_VALUE_2 = b"example_value_2"
EXAMPLE_VALUE_3 = b"example_value_3"


# TODO: add read-only tests
@pytest.fixture
def database_io(tmp_path: Path) -> Iterable[IO]:
    with open(tmp_path / "database.db", "w+b") as file:
        yield file


@pytest.fixture
def database_io_with_examples(tmp_path: Path) -> Iterable[IO]:
    with open(tmp_path / "database.db", "w+b") as file:
        database = btree.open(file)
        database[EXAMPLE_KEY_1] = EXAMPLE_VALUE_1
        database[EXAMPLE_KEY_2] = EXAMPLE_VALUE_2
        database.close()
        file.seek(0)
        yield file


def test_open(database_io: BytesIO):
    database = btree.open(database_io)
    assert isinstance(database, BTree)
    assert len(tuple(database.keys())) == 0


class TestBTree:
    def test_close(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)
        database.close()

        with pytest.raises(RuntimeError):
            database[EXAMPLE_KEY_1] = EXAMPLE_VALUE_2

        database = btree.open(database_io_with_examples)
        assert database[EXAMPLE_KEY_1] == EXAMPLE_VALUE_1
        assert database[EXAMPLE_KEY_2] == EXAMPLE_VALUE_2

    def test_close_no_data(self, database_io: IO):
        database = btree.open(database_io)
        database.close()

        database = btree.open(database_io)
        assert len(database.keys()) == 0

    _INVALID_AFTER_CLOSE = {
        "close": lambda database: database.close(),
        "__getitem__": lambda database: database[EXAMPLE_KEY_1],
        "get": lambda database: database.get(EXAMPLE_KEY_1),
        "__setitem__": lambda database: database.__setitem__(EXAMPLE_KEY_1, EXAMPLE_VALUE_1),
        "__delitem__": lambda database: database.__delitem__(EXAMPLE_KEY_1),
        "__contains__": lambda database: EXAMPLE_KEY_1 in database,
        "__iter__": lambda database: iter(database),
        "keys": lambda database: database.keys(),
        "values": lambda database: database.values(),
        "items": lambda database: database.items(),
    }

    @pytest.mark.parametrize("method", _INVALID_AFTER_CLOSE.values(), ids=list(_INVALID_AFTER_CLOSE.keys()))
    def test_no_usable_after_close(self, database_io: IO, method: Callable[[BTree], Any]):
        database = btree.open(database_io)
        database.close()

        with pytest.raises(RuntimeError):
            method(database)

    def test_flush(self, database_io: IO):
        database = btree.open(database_io)
        database[EXAMPLE_KEY_1] = EXAMPLE_VALUE_1
        database[EXAMPLE_KEY_2] = EXAMPLE_VALUE_2
        database.flush()

        database = btree.open(database_io)
        assert database[EXAMPLE_KEY_1] == EXAMPLE_VALUE_1
        assert database[EXAMPLE_KEY_2] == EXAMPLE_VALUE_2

    def test_getitem(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        assert database[EXAMPLE_KEY_1] == EXAMPLE_VALUE_1
        assert database[EXAMPLE_KEY_2] == EXAMPLE_VALUE_2

    def test_get(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        assert database.get(EXAMPLE_KEY_1) == EXAMPLE_VALUE_1
        assert database.get(b"does_not_exist", EXAMPLE_VALUE_3) is EXAMPLE_VALUE_3

    def test_setitem(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        database[EXAMPLE_KEY_3] = EXAMPLE_VALUE_3
        database[EXAMPLE_KEY_1] = EXAMPLE_VALUE_2
        assert database[EXAMPLE_KEY_1] == EXAMPLE_VALUE_2
        assert database[EXAMPLE_KEY_3] == EXAMPLE_VALUE_3

    def test_delitem(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        del database[EXAMPLE_KEY_1]
        assert EXAMPLE_KEY_1 not in database

    def test_delitem_not_exist(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        with pytest.raises(KeyError):
            del database[b"does_not_exist"]

    def test_contains(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        assert EXAMPLE_KEY_1 in database
        assert b"does_not_exist" not in database

    def test_iter(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        assert set(database) == {EXAMPLE_KEY_1, EXAMPLE_KEY_2}

    def test_keys(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        assert set(database.keys()) == {EXAMPLE_KEY_1, EXAMPLE_KEY_2}

    def test_values(self, database_io_with_examples: IO):
        database = btree.open(database_io_with_examples)

        assert set(database.values()) == {EXAMPLE_VALUE_1, EXAMPLE_VALUE_2}
