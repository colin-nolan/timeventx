"""
A basic implementation with the same interface as btree, in case it is not available:
https://docs.micropython.org/en/latest/library/btree.html#module-btree

TODO: consider splitting out
"""
import json
import os
from typing import IO, Iterable


# Not using `typing.Callable` as not available in MicroPython
def fail_if_closed(method: callable):
    def wrapper(*args, **kwargs):
        self = args[0]
        assert isinstance(self, BTree)
        if self._closed:
            raise RuntimeError("Operation not allowed because the database is closed.")
        return method(*args, **kwargs)

    return wrapper


class BTree:
    def __init__(self, storage: IO):
        # Not using `collections.UserDict`
        self._storage = storage
        self._closed = False
        self._data = self._read()

    @fail_if_closed
    def close(self):
        self.flush()
        self._closed = True

    @fail_if_closed
    def flush(self):
        self._storage.seek(0)

        try:
            self._storage.truncate()
        except AttributeError:
            # MicroPython does not support `truncate` on `BytesIO`(!) at least not on rp2
            file_location = self._storage.name
            os.remove(file_location)
            self.storage

        serialised_json = json.dumps({key.decode(): value.decode() for key, value in self._data.items()})
        self._storage.write(serialised_json.encode())
        self._storage.flush()

    @fail_if_closed
    def __getitem__(self, key: str) -> str:
        return self._data.__getitem__(key)

    @fail_if_closed
    def get(self, key: str, default: str = None) -> str:
        return self._data.get(key, default)

    @fail_if_closed
    def __setitem__(self, key: str, value: str):
        self._data.__setitem__(key, value)

    @fail_if_closed
    def __delitem__(self, key: str):
        self._data.__delitem__(key)

    @fail_if_closed
    def __contains__(self, key: str) -> bool:
        return self._data.__contains__(key)

    @fail_if_closed
    def __iter__(self) -> Iterable[str]:
        return self._data.__iter__()

    @fail_if_closed
    def keys(self) -> Iterable[str]:
        return self._data.keys()

    @fail_if_closed
    def values(self) -> Iterable[str]:
        return self._data.values()

    @fail_if_closed
    def items(self) -> Iterable[tuple[str, str]]:
        return self._data.items()

    # Note: __len__ is missing on purpose, as it is not referenced in MicroPython's btree docs

    def _read(self) -> dict[str, str]:
        self._storage.seek(0)

        data = self._storage.read()
        if len(data) == 0:
            return {}

        deserialised_json = json.loads(data.decode())
        return {key.encode(): value.encode() for key, value in deserialised_json.items()}


def open(storage: IO):
    return BTree(storage)
