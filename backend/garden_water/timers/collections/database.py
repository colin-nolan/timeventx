import itertools
import json
from pathlib import Path
from typing import Iterable

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.serialisation import json_to_identifiable_timer, timer_to_json
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId


class TimersDatabase(IdentifiableTimersCollection):
    _DATABASE_FILE_EXTENSION = ".json"

    @property
    def _database_files(self) -> Iterable[Path]:
        yield from (Path(path) for path in self.database_directory.glob(f"*{TimersDatabase._DATABASE_FILE_EXTENSION}"))

    def __init__(self, database_directory: Path):
        database_directory.mkdir(parents=True, exist_ok=True)
        self.database_directory = database_directory

    def __iter__(self) -> Iterable[IdentifiableTimer]:
        # Read all files in self.database_directory
        # For each file, read the contents and yield the timer
        for location in self._database_files:
            timer_id = self._database_file_to_timer_id(location)
            yield self.get(timer_id)

    def __len__(self) -> int:
        return sum(1 for _ in self._database_files)

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        location = self._timer_id_to_database_file(timer_id)
        try:
            # String cast required with MicroPython due to use of non-standard `Path` lib
            with open(str(location), "r") as file:
                serialised_timer = file.read()
        except OSError:
            raise KeyError(f"Timer with id {timer_id} does not exist")
        return json_to_identifiable_timer(json.loads(serialised_timer))

    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        timer_id = timer.id if isinstance(timer, IdentifiableTimer) else self._get_unique_timer_id()

        location = self._timer_id_to_database_file(timer_id)
        if location.exists():
            raise ValueError(f"Timer with id {timer_id} already exists")

        identifiable_timer = (
            IdentifiableTimer.from_timer(timer, timer_id) if not isinstance(timer, IdentifiableTimer) else timer
        )
        serialised_timer = json.dumps(timer_to_json(identifiable_timer))

        # String cast required with MicroPython due to use of non-standard `Path` lib
        with open(str(location), "w") as file:
            file.write(serialised_timer)

        return identifiable_timer

    def remove(self, timer_id: TimerId) -> bool:
        location = self._timer_id_to_database_file(timer_id)
        if not location.exists():
            return False
        location.unlink()
        return True

    def _timer_id_to_database_file(self, timer_id: TimerId) -> Path:
        return self.database_directory / f"{timer_id}.json"

    def _database_file_to_timer_id(self, database_file: Path) -> TimerId:
        return TimerId(int(database_file.stem))

    def _get_unique_timer_id(self) -> TimerId:
        # `itertools.chain` combines the sorted generator with a fixed value of 1 to work when there are no files
        return TimerId(max(itertools.chain(sorted(int(file.stem) for file in self._database_files), (1,))) + 1)
