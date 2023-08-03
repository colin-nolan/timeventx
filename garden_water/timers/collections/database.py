import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, ContextManager

try:
    # Note that `btree` is not currently included in the standard MicroPython build for rp2. Posts from the past
    # suggests that it was unstable on Pico Pis: https://github.com/micropython/micropython/issues/6186. More recent
    # discussions suggest that it may work now though: https://github.com/orgs/micropython/discussions/9626.
    import btree
except ImportError:
    import garden_water.timers.collections._btree as btree


from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.serialisation import (
    timer_to_json,
    json_to_identifiable_timer,
)
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId


class TimersDatabase(IdentifiableTimersCollection):
    @staticmethod
    def _get_unique_key(open_database: btree.BTree) -> int:
        keys = tuple(open_database.keys())
        if len(keys) == 0:
            return 1
        return int(max(keys)) + 1

    def __init__(self, database_location: Path):
        self.database_location = database_location

    def __iter__(self) -> Iterable[IdentifiableTimer]:
        with self._open_database(read_only=True) as database:
            for value in database.values():
                try:
                    yield json_to_identifiable_timer(json.loads(value.decode()))
                except KeyError:
                    raise

    def __len__(self) -> int:
        try:
            with self._open_database(read_only=True) as database:
                return sum(1 for _ in database.keys())
        # TODO: likely MicroPython gives a different error?
        except FileNotFoundError:
            return 0

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        with self._open_database(read_only=True) as database:
            try:
                data = database[str(timer_id).encode()]
            except KeyError as e:
                raise KeyError(f"Timer with id {timer_id} does not exist") from e

        serialised_timer = json.loads(data.decode())
        return json_to_identifiable_timer(serialised_timer)

    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        with self._open_database() as database:
            key = timer.id if isinstance(timer, IdentifiableTimer) else TimersDatabase._get_unique_key(database)

            if str(key).encode() in database:
                raise ValueError(f"Timer with id {key} already exists")

            identifiable_timer = (
                IdentifiableTimer.from_timer(timer, TimerId(key)) if not isinstance(timer, IdentifiableTimer) else timer
            )

            database[str(key).encode()] = json.dumps(timer_to_json(identifiable_timer)).encode()

        return identifiable_timer

    def remove(self, timer_id: TimerId) -> bool:
        with self._open_database() as database:
            try:
                del database[str(timer_id).encode()]
                return True
            except KeyError:
                return False

    @contextmanager
    def _open_database(self, read_only: bool = False) -> ContextManager[btree.BTree]:
        if not self.database_location.exists():
            self.database_location.touch()

        with open(self.database_location, "r+b" if read_only else "a+b") as file:
            try:
                database = btree.open(file)
                yield database
            finally:
                database.close()
